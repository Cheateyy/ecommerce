from .models import Category

def navbar_categories(request):
    return {'navbar_categories': Category.objects.all()} 