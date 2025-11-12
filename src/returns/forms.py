from django import forms
from orders.models import Sale, SaleItem
from .models import RMA, RMAItem


class CreateRMAForm(forms.ModelForm):
    """Form for creating a new RMA request"""
    
    reason = forms.ChoiceField(
        choices=RMA.REASON_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    notes = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 4,
            'placeholder': 'Please provide additional details about your return...'
        })
    )
    photo = forms.ImageField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/*'
        }),
        help_text="Upload photo(s) of the item(s) you're returning (optional)"
    )
    
    class Meta:
        model = RMA
        fields = ['reason', 'notes']
    
    def __init__(self, *args, **kwargs):
        self.sale = kwargs.pop('sale', None)
        super().__init__(*args, **kwargs)
        
        if self.sale:
            # Add dynamic fields for each sale item
            for sale_item in self.sale.items.all():
                field_name = f'quantity_{sale_item.id}'
                self.fields[field_name] = forms.IntegerField(
                    min_value=0,
                    max_value=sale_item.quantity,
                    required=False,
                    initial=0,
                    widget=forms.NumberInput(attrs={
                        'class': 'form-control',
                        'min': 0,
                        'max': sale_item.quantity
                    }),
                    label=f"Return quantity for {sale_item.product.name}"
                )


class RMAItemApprovalForm(forms.ModelForm):
    """Form for staff to approve RMA items"""
    
    class Meta:
        model = RMAItem
        fields = ['approved_quantity']
        widgets = {
            'approved_quantity': forms.NumberInput(attrs={'class': 'form-control'})
        }


class RMAUpdateForm(forms.ModelForm):
    """Form for updating RMA details (staff use)"""
    
    class Meta:
        model = RMA
        fields = ['status', 'notes', 'tracking_number', 'restocking_fee', 'shipping_refund']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'tracking_number': forms.TextInput(attrs={'class': 'form-control'}),
            'restocking_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'shipping_refund': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
        }

