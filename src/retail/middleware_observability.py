"""
Observability middleware for structured logging with request IDs.
Tracks request/response metrics and logs structured events.
"""
import time
import uuid
from django.utils import timezone
from retail.observability import structured_logger, set_request_id, record_metric


class ObservabilityMiddleware:
    """Middleware for request ID tracking and structured logging"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Generate request ID
        request_id = str(uuid.uuid4())
        set_request_id(request_id)
        request.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Log request
        user_id = 'anonymous'
        if hasattr(request, 'user') and request.user.is_authenticated:
            user_id = str(request.user.id)
        
        structured_logger.info(
            'http.request',
            method=request.method,
            path=request.path,
            user_id=user_id,
            ip_address=self._get_client_ip(request),
        )
        
        # Process request
        try:
            response = self.get_response(request)
            status_code = response.status_code
            
            # Determine log level based on status code
            if status_code >= 500:
                log_level = 'error'
            elif status_code >= 400:
                log_level = 'warning'
            else:
                log_level = 'info'
            
            # Calculate response time
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            user_id = 'anonymous'
            if hasattr(request, 'user') and request.user.is_authenticated:
                user_id = str(request.user.id)
            
            getattr(structured_logger, log_level)(
                'http.response',
                method=request.method,
                path=request.path,
                status_code=status_code,
                duration_ms=round(duration_ms, 2),
                user_id=user_id,
            )
            
            # Record response time metric
            record_metric('avg_response_time', duration_ms, {
                'path': request.path,
                'method': request.method,
                'status_code': status_code,
            })
            
            # Record error if applicable
            if status_code >= 400:
                record_metric('error_rate', 1 if status_code >= 500 else 0.5, {
                    'path': request.path,
                    'method': request.method,
                    'status_code': status_code,
                })
            
            # Add request ID to response header
            response['X-Request-ID'] = request_id
            
            return response
            
        except Exception as e:
            # Log exception
            duration_ms = (time.time() - start_time) * 1000
            structured_logger.error(
                'http.exception',
                method=request.method,
                path=request.path,
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=round(duration_ms, 2),
            )
            
            # Record error metric
            record_metric('error_rate', 1, {
                'path': request.path,
                'method': request.method,
                'error': str(e),
                'error_type': type(e).__name__,
            })
            
            raise
    
    def _get_client_ip(self, request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

