from django.contrib import admin
from .models import Category, Product, Order, OrderItem

@admin.action(description="Mark selected products as available if in stock")
def make_available_if_in_stock(modeladmin, request, queryset):
    queryset.filter(stock__gt=0).update(available=True)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'product_count', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['product_count']

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'price', 'stock', 'available', 'featured', 'created_at']
    list_filter = ['available', 'featured', 'created_at', 'category']
    list_editable = ['price', 'stock', 'available', 'featured']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    actions = [make_available_if_in_stock]

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'address', 'total', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['user__username', 'address__street_address']

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product', 'quantity', 'price']
    search_fields = ['order__id', 'product__name']
