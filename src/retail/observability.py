"""
Structured logging and metrics collection for observability.
Includes request ID tracking, structured logging, and metrics aggregation.
"""
import logging
import uuid
import time
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Count, Avg, Q, Sum
from decimal import Decimal
import json
import logging


# Request ID context storage (thread-local)
import threading
_context = threading.local()


class RequestIDFilter(logging.Filter):
    """Logging filter to add request ID to log records"""
    
    def filter(self, record):
        from retail.observability import get_request_id
        record.request_id = get_request_id() or 'no-request-id'
        
        # Format extra data as JSON string
        if hasattr(record, 'extra'):
            try:
                record.extra = json.dumps(record.extra)
            except:
                record.extra = '{}'
        else:
            record.extra = '{}'
        
        return True


def get_request_id():
    """Get current request ID from context"""
    return getattr(_context, 'request_id', None)


def set_request_id(request_id):
    """Set request ID in context"""
    _context.request_id = request_id


class StructuredLogger:
    """Structured logger with request ID and consistent format"""
    
    def __init__(self, name):
        self.logger = logging.getLogger(name)
    
    def _get_extra(self, **kwargs):
        """Build structured log entry with request ID"""
        extra = {
            'timestamp': timezone.now().isoformat(),
            'request_id': get_request_id(),
        }
        extra.update(kwargs)
        return extra
    
    def info(self, event, **kwargs):
        """Log info level event"""
        self.logger.info(f"event={event}", extra=self._get_extra(event=event, level='INFO', **kwargs))
    
    def warning(self, event, **kwargs):
        """Log warning level event"""
        self.logger.warning(f"event={event}", extra=self._get_extra(event=event, level='WARNING', **kwargs))
    
    def error(self, event, **kwargs):
        """Log error level event"""
        self.logger.error(f"event={event}", extra=self._get_extra(event=event, level='ERROR', **kwargs))
    
    def debug(self, event, **kwargs):
        """Log debug level event"""
        self.logger.debug(f"event={event}", extra=self._get_extra(event=event, level='DEBUG', **kwargs))


# Global structured logger instance
structured_logger = StructuredLogger('retail.observability')




def record_metric(metric_type: str, value: float, metadata: dict = None):
    """Record a metric value"""
    try:
        from retail.models import Metric
        Metric.objects.create(
            metric_type=metric_type,
            value=Decimal(str(value)),
            metadata=metadata or {}
        )
    except Exception as e:
        structured_logger.error('metric.record_failed', error=str(e), metric_type=metric_type)


def get_metrics_summary(days: int = 7) -> dict:
    """Get metrics summary for the last N days"""
    from orders.models import Sale, Payment
    from retail.models import Metric
    from datetime import timedelta
    
    start_date = timezone.now() - timedelta(days=days)
    
    # Orders per day
    from django.db import connection
    is_sqlite = 'sqlite' in connection.vendor
    
    if is_sqlite:
        orders_today = Sale.objects.filter(
            created_at__date=timezone.now().date()
        ).count()
        # For SQLite, calculate average manually
        daily_counts = Sale.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': "date(created_at)"}
        ).values('day').annotate(count=Count('id'))
        orders_per_day_avg = sum(d['count'] for d in daily_counts) / len(daily_counts) if daily_counts else 0
    else:
        # PostgreSQL
        orders_today = Sale.objects.filter(created_at__date=timezone.now().date()).count()
        orders_per_day_avg = Sale.objects.filter(
            created_at__gte=start_date
        ).extra(
            select={'day': "date(created_at)"}
        ).values('day').annotate(count=Count('id')).aggregate(
            avg=Avg('count')
        )['avg'] or 0
    
    # Error rate (from logs - simplified, would need log parsing in production)
    total_requests = Metric.objects.filter(
        metric_type='error_rate',
        recorded_at__gte=start_date
    ).count()
    errors = Metric.objects.filter(
        metric_type='error_rate',
        value__gt=0,
        recorded_at__gte=start_date
    ).count()
    error_rate = (errors / total_requests * 100) if total_requests > 0 else 0
    
    # Refunds per day
    refunds_today = 0  # Would need Refund model
    refunds_per_day_avg = 0  # Would need Refund model
    
    # Payment success rate
    payments = Payment.objects.filter(processed_at__gte=start_date)
    total_payments = payments.count()
    successful_payments = payments.filter(status='COMPLETED').count()
    payment_success_rate = (successful_payments / total_payments * 100) if total_payments > 0 else 0
    
    # Average response time
    response_times = Metric.objects.filter(
        metric_type='avg_response_time',
        recorded_at__gte=start_date
    ).aggregate(avg=Avg('value'))['avg'] or 0
    
    # Circuit breaker state
    latest_cb_metric = Metric.objects.filter(
        metric_type='circuit_breaker_state'
    ).order_by('-recorded_at').first()
    circuit_breaker_state = latest_cb_metric.metadata.get('state', 'CLOSED') if latest_cb_metric else 'CLOSED'
    
    # Stock conflicts
    stock_conflicts = Metric.objects.filter(
        metric_type='stock_conflicts',
        recorded_at__gte=start_date
    ).count()
    
    # Throttled requests
    throttled_requests = Metric.objects.filter(
        metric_type='throttled_requests',
        recorded_at__gte=start_date
    ).count()
    
    return {
        'orders_today': orders_today,
        'orders_per_day_avg': float(orders_per_day_avg),
        'error_rate': float(error_rate),
        'refunds_today': refunds_today,
        'refunds_per_day_avg': refunds_per_day_avg,
        'payment_success_rate': float(payment_success_rate),
        'avg_response_time_ms': float(response_times),
        'circuit_breaker_state': circuit_breaker_state,
        'stock_conflicts': stock_conflicts,
        'throttled_requests': throttled_requests,
        'period_days': days,
    }

