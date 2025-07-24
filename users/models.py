from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _

class UserManager(BaseUserManager):

    def _create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError(_('The Email field must be set'))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('role', User.Role.ADMIN)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self._create_user(email, password, **extra_fields)

class User(AbstractUser):
    username = None
    email = models.EmailField(_('email address'), unique=True)

    class Role(models.TextChoices):
        ADMIN = 'ADMIN', _('Admin')
        BIEN_TAP_VIEN = 'BIENTAPVIEN', _('Biên tập viên')
        TAC_GIA = 'TACGIA', _('Tác giả')

    # Thông tin chung từ ERD
    ho_ten = models.CharField(_('họ tên'), max_length=255)
    mo_ta = models.TextField(_('mô tả'), blank=True, null=True)
    avatar = models.ImageField(_('ảnh đại diện'), upload_to='avatars/', blank=True, null=True)

    # Vai trò và trạng thái
    role = models.CharField(_('vai trò'), max_length=50, choices=Role.choices, default=Role.TAC_GIA)

    nguoi_tao = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='users_created',
        verbose_name=_('người tạo')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['ho_ten']

    objects = UserManager()

    def __str__(self):
        return self.email

    class Meta:
        verbose_name = _('Người dùng')
        verbose_name_plural = _('Người dùng')