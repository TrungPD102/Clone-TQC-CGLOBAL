from django.contrib import admin
from .models import Tag, Post, PostView, Feedback, Category

@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('ten_tag', 'slug')
    search_fields = ('ten_tag',)
    prepopulated_fields = {'slug': ('ten_tag',)}

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('ten_de_tai', 'slug')
    search_fields = ('ten_de_tai',)
    prepopulated_fields = {'slug': ('ten_de_tai',)}

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'status', 'category', 'publish_at', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at', 'publish_at', 'author', 'tags', 'category')
    search_fields = ('title', 'content', 'author__email', 'author__ho_ten') 
    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ('author',)
    date_hierarchy = 'publish_at'
    ordering = ('-status', '-publish_at')
    filter_horizontal = ('tags',)
    # Hoặc filter_vertical = ('tags',)

    fieldsets = (
        ('Thông tin chung', {
            'fields': ('title', 'slug', 'author', 'image', 'content')
        }),
        ('Trạng thái & Xuất bản', {
            'fields': ('status', 'publish_at')
        }),
        ('Phân loại', {
            'fields': ('category', 'tags',)
        }),
    )
    # readonly_fields = ('created_at', 'updated_at')

@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'ip_address', 'session_key', 'viewed_at')
    list_filter = ('viewed_at', 'post__title')
    search_fields = ('post__title', 'ip_address', 'session_key')
    readonly_fields = ('post', 'ip_address', 'session_key', 'viewed_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('post', 'editor_email', 'author_email', 'status', 'created_at')
    list_filter = ('status', 'created_at', 'editor', 'author')
    search_fields = ('post__title', 'editor__email', 'author__email', 'reason')
    raw_id_fields = ('post', 'editor', 'author')
    readonly_fields = ('created_at',)

    def editor_email(self, obj):
        return obj.editor.email if obj.editor else None
    editor_email.short_description = 'Biên tập viên'

    def author_email(self, obj):
        return obj.author.email if obj.author else None
    author_email.short_description = 'Tác giả nhận'

    fieldsets = (
        ('Thông tin Phản hồi', {
            'fields': ('post', 'editor', 'author', 'status')
        }),
        ('Nội dung', {
            'fields': ('reason', 'suggestion')
        }),
        ('Thời gian', {
            'fields': ('created_at',)
        }),
    )