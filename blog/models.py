from django.db import models
from django.conf import settings # Để gọi AUTH_USER_MODEL
from django.utils.text import slugify
from django.utils.translation import gettext_lazy as _
from users.models import User

class Tag(models.Model):
    ten_tag = models.CharField(_('tên tag'), max_length=50, unique=True)
    slug = models.SlugField(_('slug'), max_length=60, unique=True, blank=True)

    def __str__(self):
        return self.ten_tag

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ten_tag)
            original_slug = self.slug
            queryset = Tag.objects.all().exclude(pk=self.pk) # loại trừ chính nó khi edit
            counter = 1

            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Tag')
        verbose_name_plural = _('Các Tags')
        ordering = ['ten_tag']

class Category(models.Model):
    ten_de_tai = models.CharField(_('tên đề tài'), max_length=100, unique=True)
    slug = models.SlugField(_('slug'), max_length=120, unique=True, blank=True, help_text=_('Để trống để tự động tạo slug từ tên đề tài.'))
    mo_ta = models.TextField(_('mô tả'), blank=True, null=True)

    class Meta:
        verbose_name = _('Đề tài')
        verbose_name_plural = _('Các Đề tài')
        ordering = ['ten_de_tai']

    def __str__(self):
        return self.ten_de_tai

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.ten_de_tai)
            original_slug = self.slug
            queryset = Category.objects.all().exclude(pk=self.pk)
            counter = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

class Post(models.Model):
    class Status(models.TextChoices):
        NHAP = 'NHAP', _('Nháp')
        CHO_DUYET = 'CHODUYET', _('Đang chờ duyệt')
        DA_DUYET = 'DADUYET', _('Đã duyệt')
        TU_CHOI = 'TUCHOI', _('Bị từ chối')
        DA_XUAT_BAN = 'DAXUATBAN', _('Đã xuất bản')

    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='posts',
        verbose_name=_('tác giả'),
        # giới hạn chỉ Tác giả mới được tạo bài viết:
        limit_choices_to={'role': 'TACGIA'}
    )

    title = models.CharField(_('tiêu đề'), max_length=255)
    slug = models.SlugField(max_length=255, unique=True, blank=True, help_text=_("Tự động tạo từ tiêu đề nếu để trống."))
    content = models.TextField(_('nội dung'))
    image = models.ImageField(_('ảnh đại diện bài viết'), upload_to='post_images/', blank=True, null=True)
    status = models.CharField(_('trạng thái'), max_length=20, choices=Status.choices, default=Status.NHAP)
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='posts',
        verbose_name=_('đề tài')
    )
    tags = models.ManyToManyField(Tag, blank=True, related_name='posts', verbose_name=_('tags'))
    
    created_at = models.DateTimeField(_('thời điểm tạo'), auto_now_add=True)
    updated_at = models.DateTimeField(_('thời điểm cập nhật'), auto_now=True)
    publish_at = models.DateTimeField(_('thời điểm xuất bản dự kiến'), null=True, blank=True,
                                      help_text=_("Nếu đặt, bài viết sẽ tự động công khai vào thời điểm này nếu trạng thái là 'Đã duyệt' hoặc 'Đã xuất bản'."))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Đảm bảo slug là duy nhất
            original_slug = self.slug
            queryset = Post.objects.all().exclude(id=self.id)
            counter = 1
            while queryset.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{counter}"
                counter += 1
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['-publish_at', '-created_at']
        verbose_name = _('Bài viết')
        verbose_name_plural = _('Bài viết')

class PostView(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='views', verbose_name=_('bài viết'))
    ip_address = models.GenericIPAddressField(_('địa chỉ IP'), null=True, blank=True)
    session_key = models.CharField(_('session key'), max_length=40, null=True, blank=True) # Để theo dõi lượt xem từ user chưa đăng nhập
    viewed_at = models.DateTimeField(_('thời điểm xem'), auto_now_add=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('người xem')
    )

    user_agent = models.TextField(_('user agent'), null=True, blank=True)
    viewed_at = models.DateTimeField(_('thời điểm xem'), auto_now_add=True)

    def __str__(self):
        return f"View for {self.post.title} at {self.viewed_at}"

    class Meta:
        ordering = ['-viewed_at']
        verbose_name = _('Lượt xem bài viết')
        verbose_name_plural = _('Lượt xem bài viết')

class Feedback(models.Model):
    class FeedbackStatus(models.TextChoices):
        DANG_GUI = 'DANGGUI', _('Đang gửi')
        DA_GUI = 'DAGUI', _('Đã gửi')
        DA_XEM = 'DAXEM', _('Tác giả đã xem')

    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='feedbacks', verbose_name=_('bài viết'))
    editor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='feedbacks_given',
        verbose_name=_('biên tập viên'),
        # Giới hạn chỉ Admin/BTV mới có thể tạo feedback:
        limit_choices_to={'role__in': [User.Role.ADMIN, User.Role.BIEN_TAP_VIEN]}
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks_received',
        verbose_name=_('tác giả nhận')
    )
    reason = models.TextField(_('lý do từ chối'))
    suggestion = models.TextField(_('gợi ý chỉnh sửa'), blank=True, null=True)
    status = models.CharField(_('trạng thái phản hồi'), max_length=20, choices=FeedbackStatus.choices, default=FeedbackStatus.DANG_GUI)
    created_at = models.DateTimeField(_('thời điểm tạo phản hồi'), auto_now_add=True)

    def __str__(self):
        return f"Feedback for {self.post.title} by {self.editor.email if self.editor else 'N/A'}"

    class Meta:
        ordering = ['-created_at']
        verbose_name = _('Phản hồi bài viết')
        verbose_name_plural = _('Phản hồi bài viết')