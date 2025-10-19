from django import forms
from django.core.exceptions import ValidationError
from .models import Product, Category


class ProductForm(forms.ModelForm):
    """Form for creating and updating products with flash sale configuration"""
    
    class Meta:
        model = Product
        fields = [
            'name', 'description', 'sku', 'price', 'category', 'stock_quantity', 'is_active',
            'flash_sale_enabled', 'flash_sale_price', 'flash_sale_starts_at', 'flash_sale_ends_at'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'stock_quantity': forms.NumberInput(attrs={'min': '0'}),
            'flash_sale_price': forms.NumberInput(attrs={'step': '0.01', 'min': '0.01'}),
            'flash_sale_starts_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'flash_sale_ends_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if field_name in ['is_active', 'flash_sale_enabled']:
                field.widget.attrs['class'] = 'form-check-input'
        
        # Add help text for flash sale fields
        self.fields['flash_sale_enabled'].help_text = "Enable flash sale pricing for this product"
        self.fields['flash_sale_price'].help_text = "Special price during flash sale period"
        self.fields['flash_sale_starts_at'].help_text = "When the flash sale begins"
        self.fields['flash_sale_ends_at'].help_text = "When the flash sale ends"
        
        # Format datetime fields for datetime-local widget
        if self.instance and self.instance.pk:
            if self.instance.flash_sale_starts_at:
                self.fields['flash_sale_starts_at'].initial = self.instance.flash_sale_starts_at.strftime('%Y-%m-%dT%H:%M')
            if self.instance.flash_sale_ends_at:
                self.fields['flash_sale_ends_at'].initial = self.instance.flash_sale_ends_at.strftime('%Y-%m-%dT%H:%M')
    
    def clean(self):
        cleaned_data = super().clean()
        flash_sale_enabled = cleaned_data.get('flash_sale_enabled')
        
        # Only validate flash sale fields if flash sale is enabled
        if flash_sale_enabled:
            flash_sale_price = cleaned_data.get('flash_sale_price')
            flash_sale_starts_at = cleaned_data.get('flash_sale_starts_at')
            flash_sale_ends_at = cleaned_data.get('flash_sale_ends_at')
            
            if not flash_sale_price:
                raise forms.ValidationError("Flash sale price is required when flash sale is enabled")
            if not flash_sale_starts_at:
                raise forms.ValidationError("Flash sale start time is required when flash sale is enabled")
            if not flash_sale_ends_at:
                raise forms.ValidationError("Flash sale end time is required when flash sale is enabled")
            if flash_sale_starts_at and flash_sale_ends_at and flash_sale_starts_at >= flash_sale_ends_at:
                raise forms.ValidationError("Flash sale start time must be before end time")
        
        return cleaned_data
    
    def save(self, commit=True):
        """Override save to avoid model clean validation issues"""
        instance = super().save(commit=False)
        
        # Only call model clean if commit is True
        if commit:
            try:
                instance.full_clean()
            except ValidationError as e:
                # Convert model validation errors to form errors
                for field, errors in e.message_dict.items():
                    if field in self.fields:
                        for error in errors:
                            self.add_error(field, error)
                return None
        
        if commit:
            instance.save()
        
        return instance


class ProductSearchForm(forms.Form):
    """Form for searching products"""
    search = forms.CharField(
        max_length=200,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search products by name, SKU, or description...'
        })
    )
    category = forms.ModelChoiceField(
        queryset=Category.objects.all(),
        required=False,
        empty_label="All Categories",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    stock_status = forms.ChoiceField(
        choices=[
            ('', 'All Stock Status'),
            ('in_stock', 'In Stock'),
            ('low_stock', 'Low Stock'),
            ('out_of_stock', 'Out of Stock'),
            ('flash_sale', 'Flash Sale Items'),
        ],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )


class CategoryForm(forms.ModelForm):
    """Form for creating and updating categories"""
    
    class Meta:
        model = Category
        fields = ['name', 'description']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
