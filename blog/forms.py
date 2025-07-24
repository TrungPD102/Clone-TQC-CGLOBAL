from django import forms
from .models import Post, Tag, Feedback, Category
from ckeditor_uploader.widgets import CKEditorUploadingWidget

class PostForm(forms.ModelForm): # Dùng cho Tác giả tạo/sửa bài
    tags_input = forms.CharField(
        label="Tags (cách nhau bằng dấu phẩy)",
        required=False, # Cho phép không nhập tag
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ví dụ: công nghệ, AI, django tips'}),
        help_text="Nhập các tags, cách nhau bằng dấu phẩy. Ví dụ: #django, #python, #webdev"
    )

    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=True, 
        label="Chọn Đề Tài",
        empty_label="-- Chọn một đề tài --",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    content = forms.CharField(
        label="Nội dung chi tiết",
        widget=CKEditorUploadingWidget(config_name='default')
    )

    class Meta:
        model = Post
        fields = ['title', 'category' ,'content', 'image']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nhập tiêu đề bài viết'}),
            #'content': forms.Textarea(attrs={'class': 'form-control', 'rows': 10, 'placeholder': 'Soạn nội dung bài viết của bạn...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }
        labels = {
            'title': 'Tiêu đề bài viết',
            #'content': 'Nội dung chi tiết',
            'image': 'Ảnh đại diện cho bài viết (tùy chọn)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            current_tags = self.instance.tags.all()
            if current_tags:
                self.fields['tags_input'].initial = ', '.join(tag.ten_tag for tag in current_tags)
                
        if 'category' in self.fields:
            self.fields['category'].widget.attrs.update({'class': 'form-control'})


class FeedbackForm(forms.ModelForm): # Dùng cho BTV khi từ chối bài
    class Meta:
        model = Feedback
        fields = ['reason', 'suggestion']
        widgets = {
            'reason': forms.Textarea(attrs={
                'class': 'form-control reason-textarea', # Class này sẽ được dùng trong btv_review_post_detail.html
                'rows': 3,
                'placeholder': 'Nhập lý do từ chối bài viết...'
            }),
            'suggestion': forms.Textarea(attrs={
                'class': 'form-control suggestion-textarea', # Class này sẽ được dùng trong btv_review_post_detail.html
                'rows': 3,
                'placeholder': 'Gợi ý chỉnh sửa cho tác giả (tùy chọn)...' # Sửa lại placeholder
            }),
        }
        labels = {
            'reason': 'Lý do từ chối (bắt buộc)', # Sửa lại label
            'suggestion': 'Gợi ý chỉnh sửa (tùy chọn)',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['reason'].required = True
        self.fields['suggestion'].required = False


class SchedulePostForm(forms.ModelForm): # Dùng cho BTV lên lịch bài viết
    publish_at = forms.DateTimeField(
        label='Thời điểm xuất bản',
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local', 'class': 'form-control'}),
        required=True, # Bắt buộc khi BTV chủ động lên lịch
    )

    class Meta:
        model = Post
        fields = ['publish_at'] # BTV chỉ set thời gian đăng