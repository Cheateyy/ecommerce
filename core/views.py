from django.shortcuts import render
from django.contrib import messages
from products.models import Category, Product
from django.http import JsonResponse
from django.conf import settings

# Create your views here.
def home(request):
    """Home page with featured products and categories"""
    featured_products = Product.objects.filter(featured=True, available=True)[:6]
    categories = Category.objects.all()
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, "core/home.html", context)

def about(request):
    """About page with company information"""
    return render(request, "core/about.html")

def contact(request):
    """Contact page with contact form"""
    if request.method == 'POST':
        # TODO: Implement contact form processing
        messages.success(request, 'Thank you for your message! We will get back to you soon.')
        return render(request, "core/contact.html")
    
    return render(request, "core/contact.html")

def shop(request):
    """Shop page - will redirect to products listing"""
    # TODO: Redirect to products app when created
    return render(request, "core/shop.html")

def debug_db(request):
    return JsonResponse(settings.DATABASES)