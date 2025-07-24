from django.urls import path
from . import views
from django.views.generic import TemplateView

app_name = 'blog'

urlpatterns = [
    # Public & Tác giả URLs
    path('', views.home_page, name='home'),
    path('dashboard/', views.user_dashboard, name='dashboard'),
    path('posts/new/', views.create_post_view, name='create_post'),
    path('my-posts/', views.author_posts_list_view, name='author_posts_list'),
    path('post/<slug:slug>/', views.post_detail_view, name='post_detail'),
    path('post/<slug:slug>/edit/', views.edit_post_view, name='edit_post'),
    path('post/<slug:slug>/delete/', views.delete_post_view, name='delete_post'),
    path('category/<slug:category_slug>/', views.posts_by_category_view, name='posts_by_category'),
    path('search/', views.search_results_view, name='search_results'),

    # Biên Tập Viên URL
    path('editor/manage-posts/', views.btv_manage_posts_view, name='btv_manage_posts'),
    path('editor/review/<slug:slug>/', views.btv_review_post_detail_view, name='btv_review_post_detail'),
    path('editor/scheduled-posts/', views.btv_scheduled_posts_view, name='btv_scheduled_posts'),
    path('editor/statistics/views/', views.btv_post_statistics_view, name='btv_post_statistics'),

    # --- THÊM URL CHO CÁC TRANG TĨNH ---
    path('gioi-thieu/', TemplateView.as_view(template_name="blog/Gioithieu.html"), name='gioi_thieu_page'),
    path('tuyen-dung/', TemplateView.as_view(template_name="blog/Tuyendung.html"), name='tuyen_dung_page'),
]