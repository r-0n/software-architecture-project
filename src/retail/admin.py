from django.contrib import admin
from .models import Metric


@admin.register(Metric)
class MetricAdmin(admin.ModelAdmin):
    list_display = ('metric_type', 'value', 'recorded_at')
    list_filter = ('metric_type', 'recorded_at')
    search_fields = ('metric_type',)
    readonly_fields = ('recorded_at',)
    date_hierarchy = 'recorded_at'
    
    def has_add_permission(self, request):
        # Metrics are created programmatically, not manually
        return False

