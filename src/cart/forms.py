from django import forms
from orders.models import Order, OrderItem

class CheckoutForm(forms.Form):
    address = forms.CharField(max_length=255, widget=forms.TextInput(attrs={"class": "form-control"}))
    payment_method = forms.ChoiceField(choices=Order.PAYMENT_METHODS, widget=forms.Select(attrs={"class": "form-select"}))
