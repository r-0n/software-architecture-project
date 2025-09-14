# src/cart/forms.py
from django import forms
from orders.models import Payment

class CheckoutForm(forms.Form):
    address = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter delivery address"})
    )
    payment_method = forms.ChoiceField(
        choices=Payment.PAYMENT_METHODS,
        required=True,
        widget=forms.Select(attrs={"class": "form-select", "id": "payment-method"})
    )
    card_number = forms.CharField(
        max_length=16,
        required=False,
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter 16-digit card number", "maxlength": "16"})
    )

    def clean(self):
        cleaned_data = super().clean()
        payment_method = cleaned_data.get('payment_method')
        address = cleaned_data.get('address')
        card_number = cleaned_data.get('card_number')

        # A4. Payment Failure/Decline validation
        if not address or address.strip() == "":
            raise forms.ValidationError("Address is required for delivery.")
        
        if payment_method == "CARD":
            if not card_number or card_number.strip() == "":
                raise forms.ValidationError("Card number is required for Credit/Debit Card payment method.")
            elif len(card_number.strip()) != 16:
                raise forms.ValidationError("Card number must be exactly 16 digits long.")
            elif not card_number.strip().isdigit():
                raise forms.ValidationError("Card number must contain only numeric digits.")

        return cleaned_data
