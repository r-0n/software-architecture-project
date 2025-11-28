from django.contrib import admin
from .models import RMA, RMAItem, RMAEvent, RMANotification


@admin.register(RMA)
class RMAAdmin(admin.ModelAdmin):
    list_display = ['id', 'sale', 'customer', 'status', 'reason', 'opened_at', 'closed_at']
    list_filter = ['status', 'reason', 'opened_at']
    search_fields = ['id', 'sale__id', 'customer__username', 'tracking_number']
    readonly_fields = ['opened_at', 'closed_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('sale', 'customer', 'status', 'reason')
        }),
        ('Details', {
            'fields': ('notes', 'tracking_number', 'restocking_fee', 'shipping_refund')
        }),
        ('Timestamps', {
            'fields': ('opened_at', 'closed_at')
        }),
    )


@admin.register(RMAItem)
class RMAItemAdmin(admin.ModelAdmin):
    list_display = ['id', 'rma', 'sale_item', 'requested_quantity', 'approved_quantity']
    list_filter = ['rma__status']
    search_fields = ['rma__id', 'sale_item__product__name']


@admin.register(RMAEvent)
class RMAEventAdmin(admin.ModelAdmin):
    list_display = ['id', 'rma', 'from_status', 'to_status', 'actor', 'timestamp']
    list_filter = ['to_status', 'timestamp']
    search_fields = ['rma__id', 'actor__username', 'notes']
    readonly_fields = ['timestamp']


@admin.register(RMANotification)
class RMANotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'rma', 'status', 'is_read', 'created_at']
    list_filter = ['status', 'is_read', 'created_at']
    search_fields = ['user__username', 'rma__id', 'message']
    readonly_fields = ['created_at']
    list_editable = ['is_read']

