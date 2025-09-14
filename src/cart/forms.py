# src/cart/forms.py
from django import forms
from orders.models import Payment

class CheckoutForm(forms.Form):
    address = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={"class": "form-control"})
    )
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHODS,
        widget=forms.Select(attrs={"class": "form-select", "id": "payment-method"})
    )
    card_number = forms.CharField(
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter card number"})
    )
