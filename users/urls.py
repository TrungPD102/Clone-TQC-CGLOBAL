from django.urls import path
from . import views

app_name = 'users'

urlpatterns = [
    path('admin-page/', views.admin_only_view, name='admin_page'),
    path('register/', views.register_view, name='register'),
    path('ajax/login/', views.login_ajax_view, name='ajax_login'),
    path('ajax/logout/', views.logout_ajax_view, name='ajax_logout'),
    path('profile/', views.profile_view, name='profile'),
]