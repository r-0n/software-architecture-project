"""
Request recording middleware for interface testing and replay.
Captures HTTP requests/responses for deterministic testing.
"""
import json
import os
from datetime import datetime
from django.conf import settings
from django.http import JsonResponse


class RequestRecordingMiddleware:
    """Middleware to record HTTP requests and responses for replay testing"""
    
    def __init__(self, get_response):
        self.get_response = get_response
        self.record_dir = getattr(settings, 'REQUEST_RECORD_DIR', 'recorded_requests')
        
    def __call__(self, request):
        # Only record in test/development mode
        if not settings.DEBUG:
            return self.get_response(request)
            
        # Skip recording for certain paths
        skip_paths = ['/admin/', '/static/', '/media/', '/favicon.ico']
        if any(request.path.startswith(path) for path in skip_paths):
            return self.get_response(request)
        
        # Record request metadata
        request_data = {
            'method': request.method,
            'path': request.path,
            'query_params': dict(request.GET),
            'headers': {
                key: value for key, value in request.META.items() 
                if key.startswith('HTTP_') or key in ['CONTENT_TYPE', 'CONTENT_LENGTH']
            },
            'timestamp': datetime.now().isoformat(),
            'user_authenticated': request.user.is_authenticated if hasattr(request, 'user') else False,
        }
        
        # Record POST data (excluding sensitive fields)
        if request.method == 'POST':
            sensitive_fields = ['password', 'card_number', 'csrfmiddlewaretoken']
            post_data = {}
            for key, value in request.POST.items():
                if key not in sensitive_fields:
                    post_data[key] = value
                else:
                    post_data[key] = '[REDACTED]'
            request_data['post_data'] = post_data
        
        # Get response
        response = self.get_response(request)
        
        # Record response metadata
        response_data = {
            'status_code': response.status_code,
            'headers': dict(response.items()),
            'content_type': response.get('Content-Type', ''),
        }
        
        # Record response content (for JSON responses only)
        if response.get('Content-Type', '').startswith('application/json'):
            try:
                if hasattr(response, 'content'):
                    response_data['content'] = json.loads(response.content.decode())
            except (json.JSONDecodeError, UnicodeDecodeError):
                response_data['content'] = '[BINARY_CONTENT]'
        
        # Combine request and response
        record_entry = {
            'request': request_data,
            'response': response_data,
            'recorded_at': datetime.now().isoformat()
        }
        
        # Save to file
        self._save_record(record_entry)
        
        return response
    
    def _save_record(self, record_entry):
        """Save request/response record to file"""
        os.makedirs(self.record_dir, exist_ok=True)
        
        # Create filename based on timestamp and path
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        safe_path = record_entry['request']['path'].replace('/', '_').replace('?', '_').replace('=', '_')
        filename = f"{timestamp}_{record_entry['request']['method']}_{safe_path}.json"
        
        filepath = os.path.join(self.record_dir, filename)
        
        try:
            with open(filepath, 'w') as f:
                json.dump(record_entry, f, indent=2)
        except Exception as e:
            # Silently fail to avoid breaking the application
            pass
