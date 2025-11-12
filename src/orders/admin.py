from django.contrib import admin
from .models import Sale, SaleItem, Payment


class SaleItemInline(admin.TabularInline):
    """Inline admin for SaleItems"""
    model = SaleItem
    extra = 0
    readonly_fields = ('subtotal',)
    fields = ('product', 'quantity', 'unit_price', 'subtotal')


@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    """Admin interface for Sales"""
    list_display = ('id', 'user', 'total', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('id', 'user__username', 'user__email')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    inlines = [SaleItemInline]
    
    fieldsets = (
        ('Order Information', {
            'fields': ('user', 'status', 'total', 'created_at')
        }),
        ('Shipping', {
            'fields': ('address',)
        }),
    )


@admin.register(SaleItem)
class SaleItemAdmin(admin.ModelAdmin):
    """Admin interface for SaleItems"""
    list_display = ('id', 'sale', 'product', 'quantity', 'unit_price', 'subtotal')
    list_filter = ('sale__status', 'sale__created_at')
    search_fields = ('sale__id', 'product__name', 'product__sku')
    readonly_fields = ('subtotal',)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    """Admin interface for Payments"""
    list_display = ('id', 'sale', 'method', 'amount', 'status', 'processed_at')
    list_filter = ('status', 'method', 'processed_at')
    search_fields = ('sale__id', 'reference', 'sale__user__username')
    readonly_fields = ('processed_at',)
    date_hierarchy = 'processed_at'
    
    fieldsets = (
        ('Payment Information', {
            'fields': ('sale', 'method', 'amount', 'status')
        }),
        ('Transaction Details', {
            'fields': ('reference', 'processed_at')
        }),
    )

