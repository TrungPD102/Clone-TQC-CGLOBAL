from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from .forms import UserRegisterForm, UserProfileUpdateForm 
from django.contrib.auth.decorators import login_required
from .decorators import admin_required
# from .models import User # Không cần User ở đây nữa
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.contrib.auth.forms import AuthenticationForm

@login_required
@admin_required
def admin_only_view(request):
    return render(request, 'users/admin_page.html')

def register_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()

            login(request, user)    # Tự động đăng nhập sau khi đăng ký thành công
            
            # username = form.cleaned_data.get('email') # Lấy email
            
            if is_ajax:
                return JsonResponse({
                    'success': True,
                    'message': f'Tài khoản cho {user.email} đã được tạo thành công! Vui lòng đóng popup này và đăng nhập.',
                    'auto_logged_in': True,
                })
            else:
                messages.success(request, f'Tài khoản cho {user.email} đã được tạo thành công!')
                return redirect('login')
        else:
            if is_ajax:
                return JsonResponse({'success': False, 'errors': form.errors.get_json_data()}, status=400)
            else:
                messages.error(request, "Đăng ký không thành công. Vui lòng kiểm tra lại thông tin.")
                context = {
                    'form': form,
                    'page_title': 'Đăng Ký Tài Khoản'
                }
                return render(request, 'users/register.html', context)
    else: # GET request
        form = UserRegisterForm()
    
    context = {
        'form': form,
        'page_title': 'Đăng Ký Tài Khoản'
    }
    return render(request, 'users/register.html', context)

@require_POST
def login_ajax_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not is_ajax:
        return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ.'}, status=400)

    form = AuthenticationForm(data=request.POST)
    if form.is_valid():
        user = form.get_user()
        login(request, user)
        return JsonResponse({
            'success': True,
            'message': 'Đăng nhập thành công!',
            'user': {
                'ho_ten': user.ho_ten,
                'email': user.email,
                'role': user.get_role_display()
            }
        })
    else:
        error_messages = []
        for field, errors in form.errors.items():
            for error in errors:
                error_messages.append(str(error))
        
        return JsonResponse({
            'success': False,
            'message': " ".join(error_messages) if error_messages else 'Email hoặc mật khẩu không đúng.',
            'errors': form.errors.get_json_data()
        }, status=400)

@require_POST
def logout_ajax_view(request):
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    if not is_ajax:
        return JsonResponse({'success': False, 'message': 'Yêu cầu không hợp lệ.'}, status=400)
    
    logout(request)
    return JsonResponse({'success': True, 'message': 'Bạn đã đăng xuất thành công.'})


@login_required
def profile_view(request):
    if request.method == 'POST':
        form = UserProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thông tin tài khoản của bạn đã được cập nhật thành công!')
            return redirect('users:profile')
    else:
        form = UserProfileUpdateForm(instance=request.user)

    context = {
        'form': form,
        'page_title': 'Thông Tin Tài Khoản',
        'current_user': request.user
    }
    return render(request, 'users/profile.html', context)