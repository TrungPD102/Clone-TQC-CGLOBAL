from .models import Category

def blog_categories_processor(request):
    all_categories = Category.objects.all().order_by('ten_de_tai') # Lấy tất cả Category, sắp xếp theo tên
    return {'all_blog_categories': all_categories}