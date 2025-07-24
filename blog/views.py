from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from users.decorators import tacgia_required, bientapvien_required
from .models import Post, Tag, Feedback, PostView, Category
from .forms import PostForm, FeedbackForm, SchedulePostForm
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.db.models import Q
from django.db.models import Count
from django.utils.text import slugify

# --- CÁC VIEW CHO TÁC GIẢ VÀ PUBLIC ---
@login_required
def user_dashboard(request):
    return render(request, 'blog/dashboard.html', {'user': request.user})

def home_page(request):
    latest_posts = Post.objects.filter(status=Post.Status.DA_XUAT_BAN).order_by('-publish_at')[:3]
    context = {
        'latest_posts': latest_posts,
        'page_title': 'Trang Chủ ProjectBlobWeb'
    }
    return render(request, 'blog/home.html', context)

@login_required
@tacgia_required
@bientapvien_required
def create_post_view(request):
    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post_instance = form.save(commit=False)
            post_instance.author = request.user

            if 'save_draft' in request.POST:
                post_instance.status = Post.Status.NHAP
                messages.success(request, 'Bài viết đã được lưu nháp thành công!')
            elif 'submit_review' in request.POST:
                post_instance.status = Post.Status.CHO_DUYET
                messages.success(request, 'Bài viết đã được gửi đi chờ duyệt!')
            else:
                post_instance.status = Post.Status.NHAP
                messages.warning(request, 'Bài viết đã được lưu nháp do không rõ hành động.')

            post_instance.save() # Lưu instance Post chính trước

            # Xử lý tags từ tags_input
            tags_string = form.cleaned_data.get('tags_input', '')
            process_tags_input(tags_string, post_instance)

            return redirect('blog:author_posts_list')
    else:
        form = PostForm()

    context = {
        'form': form,
        'page_title': 'Tạo Bài Viết Mới'
    }
    return render(request, 'blog/post_form.html', context)

@login_required
@tacgia_required
def edit_post_view(request, slug):
    post_instance = get_object_or_404(Post, slug=slug)

    # Kiểm tra quyền: Chỉ tác giả của bài viết mới được sửa
    if request.user != post_instance.author:
        messages.error(request, "Bạn không có quyền chỉnh sửa bài viết này.")
        return redirect('blog:author_posts_list') # Hoặc trang home
    
    # Lưu lại trạng thái ban đầu của bài viết trước khi form được xử lý
    original_status = post_instance.status

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post_instance)
        if form.is_valid():
            edited_post = form.save(commit=False)

            if 'save_draft' in request.POST:
                edited_post.status = Post.Status.NHAP
                messages.success(request, 'Bài viết đã được cập nhật và lưu nháp!')
            elif 'submit_review' in request.POST:
                # Nếu bài viết trước đó đã được duyệt/xuất bản và giờ tác giả submit lại
                if original_status == Post.Status.DA_DUYET or original_status == Post.Status.DA_XUAT_BAN:
                    edited_post.status = Post.Status.CHO_DUYET
                    messages.success(request, 'Bài viết đã được cập nhật và gửi lại để chờ duyệt do có thay đổi sau khi đã được duyệt/xuất bản.')
                else: # Các trường hợp khác (Nháp, Từ chối, Chờ duyệt cũ) gửi duyệt lại
                    edited_post.status = Post.Status.CHO_DUYET
                    messages.success(request, 'Bài viết đã được cập nhật và gửi đi chờ duyệt!')
            else:
                if original_status == Post.Status.DA_DUYET or original_status == Post.Status.DA_XUAT_BAN:
                    edited_post.status = Post.Status.CHO_DUYET
                    messages.warning(request, 'Bài viết đã được cập nhật và cần được duyệt lại.')
                else:
                    messages.info(request, 'Bài viết đã được cập nhật.')

            edited_post.save() # Lưu instance Post chính

            # Xử lý tags từ tags_input
            tags_string = form.cleaned_data.get('tags_input', '')
            process_tags_input(tags_string, edited_post) # Gọi hàm helper
            
            return redirect('blog:post_detail', slug=edited_post.slug)
    else: # GET request
        form = PostForm(instance=post_instance)

    context = {
        'form': form,
        'page_title': f'Chỉnh Sửa: {post_instance.title}',
        'post_instance': post_instance,
        'original_status': original_status
    }
    return render(request, 'blog/post_form.html', context)

@login_required
@tacgia_required
def author_posts_list_view(request):
    query = request.GET.get('q_author', '')
    status_filter = request.GET.get('status', '') # Lấy tham số status từ URL

    author_posts_query = Post.objects.filter(author=request.user) # Đổi tên biến để rõ ràng hơn

    if query:
        author_posts_query = author_posts_query.filter(title__icontains=query)

    valid_statuses = [s[0] for s in Post.Status.choices]
    if status_filter and status_filter in valid_statuses:
        author_posts_query = author_posts_query.filter(status=status_filter)
    
    author_posts = author_posts_query.order_by('-created_at')
    
    all_user_posts_for_counts = Post.objects.filter(author=request.user) # Query riêng cho counts
    pending_count = all_user_posts_for_counts.filter(status=Post.Status.CHO_DUYET).count()
    approved_count = all_user_posts_for_counts.filter(status__in=[Post.Status.DA_DUYET, Post.Status.DA_XUAT_BAN]).count()
    rejected_count = all_user_posts_for_counts.filter(status=Post.Status.TU_CHOI).count()
    draft_count = all_user_posts_for_counts.filter(status=Post.Status.NHAP).count()
    all_posts_count = all_user_posts_for_counts.count()

    page_title_display = "Bài Viết Của Tôi"
    if status_filter:
        try:
            status_display_name = Post.Status(status_filter).label
            page_title_display = f"Bài Viết Của Tôi ({status_display_name})"
        except ValueError:
            page_title_display = f"Bài Viết Của Tôi (Lọc theo: {status_filter.upper()})"


    context = {
        'author_posts': author_posts,
        'page_title': page_title_display, # Cập nhật tiêu đề trang
        'current_query': query,
        'current_status_filter': status_filter,
        'pending_count': pending_count,
        'approved_count': approved_count,
        'rejected_count': rejected_count,
        'draft_count': draft_count,
        'all_posts_count': all_posts_count,
        'post_statuses': Post.Status, # Để dùng trong template cho các link filter
    }
    return render(request, 'blog/author_posts_list.html', context)

def post_detail_view(request, slug):
    post = None

    try:
        possible_post = Post.objects.get(slug=slug)

        # Nếu người dùng đã đăng nhập và là tác giả của bài viết
        if request.user.is_authenticated and request.user == possible_post.author:
            post = possible_post
        else:
            # Người dùng khác hoặc khách chỉ xem được bài đã xuất bản/duyệt
            if possible_post.status in [Post.Status.DA_XUAT_BAN, Post.Status.DA_DUYET]:
                post = possible_post
    except Post.DoesNotExist:
        raise Http404("Bài viết không tồn tại hoặc không được phép xem.")
    
    if not post:
        raise Http404("Bài viết không tồn tại hoặc bạn không có quyền xem.")

    # --- Ghi nhận lượt xem (chỉ cho bài đã xuất bản/duyệt và không phải tác giả đang xem nháp) ---
    if post.status in [Post.Status.DA_XUAT_BAN, Post.Status.DA_DUYET]:
        ip_address = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        # Nếu người dùng đã đăng nhập, liên kết lượt xem với user đó
        if request.user.is_authenticated:
            if request.user != post.author or post.status != Post.Status.NHAP : 
                recent_view = PostView.objects.filter(
                    post=post,
                    user=request.user,
                    ip_address=ip_address,
                    viewed_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).first()
                
            if not recent_view:
                PostView.objects.create(post=post, user=request.user, ip_address=ip_address, user_agent=user_agent)

        else:
            # Với người dùng chưa đăng nhập, có thể dùng session key kết hợp IP
            session_key = request.session.session_key
            if not session_key: # Tạo session nếu chưa có
                request.session.create()
                session_key = request.session.session_key

            recent_view_anonymous = PostView.objects.filter(
                post=post,
                session_key=session_key,
                ip_address=ip_address,
                viewed_at__gte=timezone.now() - timezone.timedelta(hours=1)
            ).first()

            if not recent_view_anonymous:
                PostView.objects.create(post=post, session_key=session_key, ip_address=ip_address, user_agent=user_agent)

    context = {
        'post': post,
        'page_title': post.title,
        'post_statuses': Post.Status,
        'can_author_edit': (request.user.is_authenticated and
                            request.user == post.author and
                            post.status in [Post.Status.NHAP, Post.Status.CHO_DUYET, Post.Status.TU_CHOI])
    }
    return render(request, 'blog/post_detail.html', context)

# View để liệt kê bài viết theo một đề tài cụ thể:
def posts_by_category_view(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug)

    posts_in_category = Post.objects.filter(
        category=category,
        status=Post.Status.DA_XUAT_BAN
    ).order_by('-publish_at')

    all_categories = Category.objects.all()

    context = {
        'category': category,
        'posts_in_category': posts_in_category,
        'all_categories': all_categories,
        'page_title': f'Bài viết trong đề tài: {category.ten_de_tai}'
    }
    return render(request, 'blog/posts_by_category.html', context)

# Hàm helper để xử lý tags
def process_tags_input(tags_string, post_instance):
    post_instance.tags.clear() # Xóa các tags cũ của bài viết
    if tags_string:
        tag_names = [name.strip().lower() for name in tags_string.split(',') if name.strip()]
        for name in tag_names:
            # Bỏ dấu # ở đầu nếu có
            if name.startswith('#'):
                name = name[1:]
            
            if not name: # Bỏ qua tag rỗng sau khi xử lý
                continue

            # Tạo hoặc lấy tag
            # slugify(name) để tạo slug cho tag nếu model Tag của bạn có trường slug
            tag, created = Tag.objects.get_or_create(
                ten_tag=name,
                defaults={'slug': slugify(name)} # Chỉ tạo slug nếu tag mới được tạo
            )
            # Gán tag cho bài viết
            post_instance.tags.add(tag)


@login_required
@tacgia_required
@require_POST # Chỉ cho phép POST request để xóa
def delete_post_view(request, slug): # Hoặc dùng post_id nếu bạn thích
    post_to_delete = get_object_or_404(Post, slug=slug, author=request.user)

    # Chỉ cho phép xóa nếu bài viết ở trạng thái Nháp, Chờ Duyệt, hoặc Bị Từ Chối
    allowed_delete_statuses = [Post.Status.NHAP, Post.Status.CHO_DUYET, Post.Status.TU_CHOI]
    if post_to_delete.status not in allowed_delete_statuses:
        messages.error(request, f"Bạn không thể xóa bài viết đang ở trạng thái '{post_to_delete.get_status_display()}'.")
        return redirect('blog:author_posts_list') # Hoặc trang chi tiết bài viết

    post_title = post_to_delete.title
    post_to_delete.delete()
    messages.success(request, f'Bài viết "{post_title}" đã được xóa thành công.')
    return redirect('blog:author_posts_list')

def search_results_view(request):
    query = request.GET.get('q', '') # Lấy từ khóa tìm kiếm từ URL (ví dụ: ?q=django)
    results = []
    page_title = "Kết Quả Tìm Kiếm"

    if query:
        page_title = f'Kết quả tìm kiếm cho: "{query}"'

        title_content_query = Q(title__icontains=query) | Q(content__icontains=query)
        status_query = Q(status=Post.Status.DA_XUAT_BAN) # Chỉ tìm trong bài đã xuất bản

        matching_tags = Tag.objects.filter(ten_tag__icontains=query)

        tags_query = Q(tags__ten_tag__iexact=query.replace("#", ""))

        results = Post.objects.filter(
            (title_content_query | tags_query) & status_query
        ).distinct().order_by('-publish_at')
    else:
        pass

    context = {
        'query': query,
        'results': results,
        'page_title': page_title,
        'result_count': results.count() if query else 0
    }
    return render(request, 'blog/search_results.html', context)


# --- CÁC VIEW CỦA BIÊN TẬP VIÊN (BTV) ---
@login_required
@bientapvien_required
def btv_manage_posts_view(request):
    query = request.GET.get('q_btv', '')
    status_filter = request.GET.get('status', Post.Status.CHO_DUYET) # Mặc định là "Chờ duyệt"

    posts_query = Post.objects.all() # BTV có thể xem tất cả bài viết

    page_title_main = "Quản Lý Bài Viết BTV"
    active_filter_name = "Chờ Duyệt" # Mặc định

    if query:
        posts_query = posts_query.filter(
            Q(title__icontains=query) |
            Q(author__ho_ten__icontains=query) |
            Q(author__email__icontains=query)
        )

    if status_filter == Post.Status.CHO_DUYET:
        posts_query = posts_query.filter(status=Post.Status.CHO_DUYET)
        active_filter_name = "Chờ Duyệt"
    elif status_filter == 'APPROVED_ALL':
        posts_query = posts_query.filter(status__in=[Post.Status.DA_DUYET, Post.Status.DA_XUAT_BAN])
        active_filter_name = "Tổng Số Đã Duyệt"
    elif status_filter == 'REJECTED_BY_ME':
        rejected_post_ids = Feedback.objects.filter(editor=request.user, post__status=Post.Status.TU_CHOI).values_list('post_id', flat=True)
        posts_query = posts_query.filter(id__in=rejected_post_ids)
        active_filter_name = "Đã Từ Chối Bởi Bạn"
    # Thêm các trường hợp lọc khác nếu cần, ví dụ lọc theo một status cụ thể khác
    elif status_filter in [s[0] for s in Post.Status.choices]: # Nếu là một status hợp lệ
         posts_query = posts_query.filter(status=status_filter)
         try:
             active_filter_name = Post.Status(status_filter).label
         except ValueError:
             active_filter_name = status_filter.upper() # Fallback
    else: # Mặc định nếu status_filter không hợp lệ
        posts_query = posts_query.filter(status=Post.Status.CHO_DUYET)
        status_filter = Post.Status.CHO_DUYET
        active_filter_name = "Chờ Duyệt"
        
    posts_to_display = posts_query.order_by('-updated_at')

    # Counts cho sidebar
    sidebar_pending_count = Post.objects.filter(status=Post.Status.CHO_DUYET).count()
    sidebar_total_approved_count = Post.objects.filter(status__in=[Post.Status.DA_DUYET, Post.Status.DA_XUAT_BAN]).count()
    sidebar_btv_rejected_count = Feedback.objects.filter(editor=request.user, post__status=Post.Status.TU_CHOI).count()

    context = {
        'posts_to_display': posts_to_display,
        'page_title': f"{page_title_main} - {active_filter_name}",
        'active_filter_name': active_filter_name,
        'current_query': query,
        'current_status_filter': status_filter,
        'sidebar_counts': {
            'pending': sidebar_pending_count,
            'approved_total': sidebar_total_approved_count,
            'rejected_by_current_btv': sidebar_btv_rejected_count,
        },
        'post_statuses': Post.Status,
    }
    return render(request, 'blog/btv_manage_posts.html', context)


@login_required
@bientapvien_required
def btv_review_post_detail_view(request, slug):
    post_to_review = get_object_or_404(Post, slug=slug)
    feedback_form_initial = FeedbackForm()
    schedule_form_initial = SchedulePostForm(instance=post_to_review)

    current_feedback_form = feedback_form_initial
    current_schedule_form = schedule_form_initial
    show_feedback_form_js = False
    feedback_has_errors_js = False
    show_schedule_form_js = (post_to_review.status == Post.Status.DA_DUYET)

    if request.method == 'POST':
        if 'approve_post' in request.POST:
            if post_to_review.status == Post.Status.CHO_DUYET:
                post_to_review.status = Post.Status.DA_DUYET
                post_to_review.save()
                messages.success(request, f'Bài viết "{post_to_review.title}" đã được duyệt!')
                # Sau khi duyệt, chuyển đến trang chi tiết để có thể lên lịch
                return redirect('blog:btv_review_post_detail', slug=post_to_review.slug)
            else:
                messages.warning(request, "Bài viết này không ở trạng thái chờ duyệt.")
            return redirect('blog:btv_manage_posts') # Hoặc trang chi tiết bài này

        elif 'reject_post' in request.POST:
            if post_to_review.status == Post.Status.CHO_DUYET:
                # Gán lại current_feedback_form để xử lý lỗi
                current_feedback_form = FeedbackForm(request.POST)
                if current_feedback_form.is_valid():
                    feedback_instance = current_feedback_form.save(commit=False)
                    feedback_instance.post = post_to_review
                    feedback_instance.editor = request.user
                    feedback_instance.author = post_to_review.author
                    feedback_instance.status = Feedback.FeedbackStatus.DA_GUI
                    feedback_instance.save()

                    post_to_review.status = Post.Status.TU_CHOI
                    post_to_review.save()
                    messages.success(request, f'Bài viết "{post_to_review.title}" đã bị từ chối và phản hồi đã gửi.')
                    return redirect('blog:btv_manage_posts')
                else: # Feedback form không hợp lệ
                    messages.error(request, "Lỗi khi từ chối: Vui lòng cung cấp lý do.")
                    show_feedback_form_js = True
                    feedback_has_errors_js = True
            else:
                messages.warning(request, "Bài viết này không ở trạng thái chờ duyệt.")
                return redirect('blog:btv_manage_posts')
            
        elif 'schedule_post' in request.POST:
            if post_to_review.status == Post.Status.DA_DUYET:
                # Gán lại current_schedule_form để xử lý lỗi
                current_schedule_form = SchedulePostForm(request.POST, instance=post_to_review)
                if current_schedule_form.is_valid():
                    scheduled_post = current_schedule_form.save(commit=False)
                    scheduled_post.save() # Lưu publish_at
                    messages.success(request, f'Bài viết "{scheduled_post.title}" đã lên lịch đăng vào {scheduled_post.publish_at.strftime("%H:%M %d/%m/%Y")}.')
                    return redirect('blog:btv_scheduled_posts')
                else:
                    messages.error(request, "Lỗi khi lên lịch. Vui lòng kiểm tra lại thời gian.")
                    show_schedule_form_js = True # Để template biết mở form lịch
            else:
                messages.warning(request, "Chỉ có thể lên lịch cho bài viết đã được duyệt.")

        elif 'cancel_schedule' in request.POST:
            if post_to_review.status == Post.Status.DA_DUYET and post_to_review.publish_at and post_to_review.publish_at > timezone.now():
                post_to_review.publish_at = None
                post_to_review.save()
                messages.success(request, f'Lịch đăng cho bài viết "{post_to_review.title}" đã được hủy.')
            else:
                messages.warning(request, "Không thể hủy lịch cho bài viết này hoặc bài viết chưa được lên lịch.")
                return redirect('blog:btv_review_post_detail', slug=post_to_review.slug)
            
        elif 'unpublish_post' in request.POST:
            if post_to_review.status == Post.Status.DA_XUAT_BAN:
                post_to_review.status = Post.Status.DA_DUYET

                post_to_review.publish_at = None # Xóa lịch đăng cũ nếu có
                post_to_review.save()
                messages.success(request, f'Bài viết "{post_to_review.title}" đã được gỡ và chuyển về trạng thái "{post_to_review.get_status_display()}".')
            else:
                messages.warning(request, "Chỉ có thể gỡ bài viết đã được xuất bản.")
            return redirect('blog:btv_review_post_detail', slug=post_to_review.slug)
    
    context = {
        'post': post_to_review,
        'page_title': f"Xem Xét Bài: {post_to_review.title}",
        'feedback_form': current_feedback_form,
        'schedule_form': current_schedule_form,
        'post_statuses': Post.Status,
        'show_feedback_form_on_load': show_feedback_form_js,
        'feedback_form_has_errors_js': feedback_has_errors_js,
        'show_schedule_form_on_load': show_schedule_form_js,
        'is_scheduled_in_future': post_to_review.publish_at and post_to_review.publish_at > timezone.now(),
    }
    return render(request, 'blog/btv_review_post_detail.html', context)


@login_required
@bientapvien_required
def btv_scheduled_posts_view(request): # Trang quản lý lịch đăng
    now_time = timezone.now()

    # Bài viết đã duyệt
    schedulable_posts = Post.objects.filter(
        status=Post.Status.DA_DUYET
    ).filter(
        Q(publish_at__isnull=True) | Q(publish_at__lte=timezone.now())
    ).order_by('-updated_at')

    # Bài viết đã được lên lịch
    scheduled_posts = Post.objects.filter(
        status=Post.Status.DA_DUYET,
        publish_at__isnull=False,
        publish_at__gt=timezone.now()
    ).order_by('publish_at')

    # Bài viết đã xuất bản
    published_posts = Post.objects.filter(
        status=Post.Status.DA_XUAT_BAN
    ).order_by('-publish_at')

    sidebar_pending_count = Post.objects.filter(status=Post.Status.CHO_DUYET).count()
    sidebar_total_approved_count = Post.objects.filter(status__in=[Post.Status.DA_DUYET, Post.Status.DA_XUAT_BAN]).count()
    sidebar_btv_rejected_count = Feedback.objects.filter(editor=request.user, post__status=Post.Status.TU_CHOI).count()

    context = {
        'page_title': 'Quản Lý Lịch Đăng Bài',
        'schedulable_posts': schedulable_posts,
        'scheduled_posts': scheduled_posts,
        'published_posts': published_posts,
        'sidebar_counts': {
            'pending': sidebar_pending_count,
            'approved_total': sidebar_total_approved_count,
            'rejected_by_current_btv': sidebar_btv_rejected_count,
        },
        'active_sidebar_link': 'scheduled_posts',
        'post_statuses': Post.Status,
    }
    return render(request, 'blog/btv_scheduled_posts.html', context)


@login_required
@bientapvien_required
def btv_post_statistics_view(request):
    posts_with_stats = Post.objects.annotate(
        view_count=Count('views') 
    ).order_by('-view_count', '-publish_at')

    sidebar_pending_count = Post.objects.filter(status=Post.Status.CHO_DUYET).count()
    sidebar_total_approved_count = Post.objects.filter(status__in=[Post.Status.DA_DUYET, Post.Status.DA_XUAT_BAN]).count()
    sidebar_btv_rejected_count = Feedback.objects.filter(editor=request.user, post__status=Post.Status.TU_CHOI).count()


    context = {
        'posts_with_stats': posts_with_stats,
        'page_title': 'Thống Kê Lượt Xem Bài Viết',
        'sidebar_counts': {
            'pending': sidebar_pending_count,
            'approved_total': sidebar_total_approved_count,
            'rejected_by_current_btv': sidebar_btv_rejected_count,
        },
        'active_sidebar_link': 'post_statistics',
    }
    return render(request, 'blog/btv_post_statistics.html', context)

