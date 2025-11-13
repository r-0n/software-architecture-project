"""
Observability models for metrics collection.
"""
from django.db import models
from decimal import Decimal


class Metric(models.Model):
    """Store system metrics for observability"""
    
    METRIC_TYPES = [
        ('orders_per_day', 'Orders Per Day'),
        ('error_rate', 'Error Rate'),
        ('refunds_per_day', 'Refunds Per Day'),
        ('payment_success_rate', 'Payment Success Rate'),
        ('avg_response_time', 'Average Response Time'),
        ('circuit_breaker_state', 'Circuit Breaker State'),
        ('stock_conflicts', 'Stock Conflicts'),
        ('throttled_requests', 'Throttled Requests'),
    ]
    
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)
    value = models.DecimalField(max_digits=15, decimal_places=4)
    metadata = models.JSONField(default=dict, blank=True)
    recorded_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['metric_type', '-recorded_at']),
            models.Index(fields=['-recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.value} at {self.recorded_at}"

