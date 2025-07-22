from django.contrib import admin
from .models import Address

# Register your models here.
@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'first_name', 'last_name', 'city', 'is_default', 'is_shipping', 'is_billing']
    list_filter = ['is_default', 'is_shipping', 'is_billing']
    search_fields = ['user__username', 'first_name', 'last_name', 'street_address', 'city']
    list_editable = ['is_default', 'is_shipping', 'is_billing']
