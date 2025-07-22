from django.urls import path
from . import views

urlpatterns =[
    path("", views.product_list, name= "product_list"), # /products/
    path("<int:pk>/", views.product_detail, name="product_detail"), # /products/1/
    path("category/<slug:slug>/", views.category_detail, name="category_detail"), # /products/category/electronics/
    path("search/", views.search_products, name="search_products"), # /products/search/
    path("cart/", views.cart_detail, name="cart_detail"), # /products/cart/
    path("cart/add/<int:product_id>/", views.cart_add, name="cart_add"), # /products/cart/add/1/
    path("cart/remove/<int:product_id>/", views.cart_remove, name="cart_remove"), # /products/cart/remove/1/
    path("cart/clear/", views.cart_clear, name="cart_clear"), # /products/cart/clear/
    path("cart/checkout/", views.checkout, name="checkout"), # /products/cart/checkout/
    path("checkout/success/<int:order_id>/", views.checkout_success, name="checkout_success"), # /products/checkout/success/1/
    path("orders/history/", views.order_history, name="order_history")
]