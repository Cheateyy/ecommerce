from django import forms
from .models import Order

class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['address']      # Add more fields if needed (e.g., 'notes', 'phone') 
        
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['address'].required = True
        if user is not None:
            self.fields['address'].queryset = user.addresses.all()
        