from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='core-home'),
    path('about/', views.about, name='core-about'),
    path('contact/', views.contact, name='core-contact'),
    path('shop/', views.shop, name='core-shop'),
    path('debug-db/', views.debug_db, name='debug-db'),
]