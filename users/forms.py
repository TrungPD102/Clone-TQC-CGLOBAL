from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from .models import User

class UserRegisterForm(UserCreationForm):
    ho_ten = forms.CharField(label='Họ và tên', max_length=255, required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'ho_ten')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'email' in self.fields:
            self.fields['email'].label = "Địa chỉ Email"
            self.fields['email'].widget.attrs.update({'placeholder': 'vidu@email.com', 'autofocus': True})
        if 'ho_ten' in self.fields:
            self.fields['ho_ten'].widget.attrs.update({'placeholder': 'Nguyễn Văn A'})

# --- THÊM FORM MỚI CHO CẬP NHẬT PROFILE ---
class UserProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['ho_ten', 'mo_ta', 'avatar']
        widgets = {
            'ho_ten': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Họ tên đầy đủ của bạn'}),
            'mo_ta': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Một vài dòng giới thiệu về bạn...'}),
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

        labels = {
            'ho_ten': 'Họ và tên',
            'mo_ta': 'Mô tả bản thân',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


# --- FORM CHO ADMIN KHI TẠO USER MỚI ---
class CustomAdminUserCreationForm(UserCreationForm):
    ho_ten = forms.CharField(label='Họ và tên', required=True) # Bắt buộc
    role = forms.ChoiceField(label='Vai trò', choices=User.Role.choices, initial=User.Role.TAC_GIA)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('email', 'ho_ten', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if 'email' in self.fields:
            self.fields['email'].label = "Địa chỉ Email"

# --- FORM CHO ADMIN KHI SỬA USER ---
class CustomAdminUserChangeForm(UserChangeForm):
    class Meta(UserChangeForm.Meta):
        model = User
        fields = ('email', 'ho_ten', 'avatar', 'mo_ta', 'role', 'nguoi_tao',
                  'is_active', 'is_staff', 'is_superuser',
                  'groups', 'user_permissions')