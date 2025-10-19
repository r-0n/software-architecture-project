from django.contrib import admin
from django.core.exceptions import ValidationError
from .models import Product, Category


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'description', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'description']
    ordering = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'sku', 'category', 'price', 'stock_quantity', 'stock_status', 'is_active', 'flash_sale_enabled', 'created_at']
    list_filter = ['category', 'is_active', 'flash_sale_enabled', 'created_at']
    search_fields = ['name', 'sku', 'description']
    list_editable = ['price', 'stock_quantity', 'is_active', 'flash_sale_enabled']
    ordering = ['name']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'sku', 'category')
        }),
        ('Pricing & Inventory', {
            'fields': ('price', 'stock_quantity', 'is_active')
        }),
        ('Flash Sale Configuration', {
            'fields': ('flash_sale_enabled', 'flash_sale_price', 'flash_sale_starts_at', 'flash_sale_ends_at'),
            'description': 'Configure flash sale pricing and timing. All fields are required when flash sale is enabled.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        def clean(self):
            cleaned_data = super().clean()
            flash_sale_enabled = cleaned_data.get('flash_sale_enabled')
            
            if flash_sale_enabled:
                flash_sale_price = cleaned_data.get('flash_sale_price')
                flash_sale_starts_at = cleaned_data.get('flash_sale_starts_at')
                flash_sale_ends_at = cleaned_data.get('flash_sale_ends_at')
                
                if not flash_sale_price:
                    raise ValidationError("Flash sale price is required when flash sale is enabled")
                if not flash_sale_starts_at:
                    raise ValidationError("Flash sale start time is required when flash sale is enabled")
                if not flash_sale_ends_at:
                    raise ValidationError("Flash sale end time is required when flash sale is enabled")
                if flash_sale_starts_at and flash_sale_ends_at and flash_sale_starts_at >= flash_sale_ends_at:
                    raise ValidationError("Flash sale start time must be before end time")
            
            return cleaned_data
        
        form.clean = clean
        return form
