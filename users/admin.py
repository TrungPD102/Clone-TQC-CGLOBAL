from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User
from .forms import CustomAdminUserCreationForm, CustomAdminUserChangeForm

@admin.register(User)
class UserAdmin(BaseUserAdmin):
    form = CustomAdminUserChangeForm
    add_form = CustomAdminUserCreationForm

    list_display = ('email', 'ho_ten', 'role', 'is_staff', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active', 'is_staff')
    search_fields = ('email', 'ho_ten')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Thông tin cá nhân', {'fields': ('ho_ten', 'avatar', 'mo_ta')}),
        ('Phân quyền & Trạng thái', {'fields': ('role', 'nguoi_tao', 'is_active', 'is_staff', 'is_superuser',
                                             'groups', 'user_permissions')}),
        ('Thời gian quan trọng', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'ho_ten', 'role', 'password1', 'password2'),
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change and not obj.nguoi_tao:
            obj.nguoi_tao = request.user
        super().save_model(request, obj, form, change)