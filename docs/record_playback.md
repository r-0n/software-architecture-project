# Record/Playback Testing

This document describes the automated record/playback testing system for deterministic behavior verification.

## Overview

The record/playback system captures HTTP requests and responses during testing, then replays them to verify deterministic behavior. This ensures that the same inputs always produce the same outputs, which is crucial for reliable testing.

## How It Works

### Recording Phase
- **Middleware**: `RequestRecordingMiddleware` captures all HTTP requests/responses
- **Automatic**: Only runs when `DEBUG=True` (disabled in production)
- **Selective**: Skips admin, static, and media files
- **Secure**: Automatically redacts sensitive data (passwords, card numbers, CSRF tokens)

### Replay Phase
- **Management Command**: `replay_requests` replays recorded requests
- **Comparison**: Can compare responses to detect regressions
- **Flexible**: Supports filtering, glob patterns, and fail-fast options

## Configuration

### Settings
```python
# In settings.py
REQUEST_RECORD_DIR = 'recorded_requests'  # Directory to store recordings
```

### Middleware
```python
# In settings.py MIDDLEWARE
'retail.middleware.RequestRecordingMiddleware',
```

## Usage

### Recording Requests
Recording happens automatically when `DEBUG=True`:

```bash
# Start Django development server
python src/manage.py runserver

# Make requests to your application
curl http://localhost:8000/products/
curl http://localhost:8000/cart/add/1/ -d "quantity=2"
```

### Replaying Requests
```bash
# Replay all recorded requests
python src/manage.py replay_requests

# Replay with comparison
python src/manage.py replay_requests --compare

# Replay specific files
python src/manage.py replay_requests --file specific_request.json

# Replay with filtering
python src/manage.py replay_requests --filter "path=/cart/flash-checkout"

# Replay with glob pattern
python src/manage.py replay_requests --glob "*.json"

# Fail fast on first mismatch
python src/manage.py replay_requests --compare --fail-fast
```

## File Structure

### Recorded Files
```
recorded_requests/
├── 20241201_143022_POST_cart_add_1.json
├── 20241201_143025_GET_products_.json
└── 20241201_143030_POST_cart_checkout_.json
```

### File Format
```json
{
  "request": {
    "method": "POST",
    "path": "/cart/add/1/",
    "query_params": {},
    "headers": {
      "HTTP_HOST": "localhost:8000",
      "CONTENT_TYPE": "application/x-www-form-urlencoded"
    },
    "post_data": {
      "quantity": "2",
      "csrfmiddlewaretoken": "[REDACTED]"
    },
    "timestamp": "2024-12-01T14:30:22.123456",
    "user_authenticated": true
  },
  "response": {
    "status_code": 302,
    "headers": {
      "Location": "/cart/"
    },
    "content_type": "text/html; charset=utf-8"
  },
  "recorded_at": "2024-12-01T14:30:22.123456"
}
```

## Security & Privacy

### Automatic Redaction
The system automatically redacts sensitive fields:
- `password`
- `card_number`
- `csrfmiddlewaretoken`
- Any field containing "secret", "key", "token"

### PII Protection
- User authentication status is recorded (boolean)
- No actual user credentials are stored
- Sensitive form data is replaced with `[REDACTED]`

## CI/CD Integration

### Automated Testing
```bash
# In CI pipeline
python src/manage.py replay_requests --compare --fail-fast
if [ $? -ne 0 ]; then
    echo "Regression detected!"
    exit 1
fi
```

### Exit Codes
- `0`: All replays successful, no regressions
- `1`: Mismatch detected or replay failed

## Troubleshooting

### No Recordings Created
- Check that `DEBUG=True` in settings
- Verify middleware is enabled
- Check file permissions for `REQUEST_RECORD_DIR`

### Replay Failures
- Ensure test database is set up
- Check that required users/products exist
- Verify CSRF tokens are handled correctly

### Authentication Issues
- Use `--create-user` flag to create test users
- Ensure user permissions match original requests
- Check session handling in replay

### Performance Considerations
- Recording adds minimal overhead (<1ms per request)
- Large numbers of recordings may impact disk space
- Consider cleanup scripts for old recordings

## Best Practices

### Recording
- Record representative user workflows
- Include both success and error scenarios
- Test with different user roles and permissions

### Replay
- Run replays in isolated test environments
- Use deterministic test data
- Clean up between replay runs

### Maintenance
- Regularly clean up old recordings
- Update recordings when UI/API changes
- Monitor replay success rates

## Examples

### Flash Sale Workflow
```bash
# Record flash sale checkout
curl -X POST http://localhost:8000/cart/flash-checkout/ \
  -d "product_id=1&quantity=1&address=123 Test St&payment_method=CARD"

# Replay with comparison
python src/manage.py replay_requests --filter "path=/cart/flash-checkout" --compare
```

### Product Catalog Testing
```bash
# Record product listing and search
curl http://localhost:8000/products/
curl http://localhost:8000/products/?search=test

# Replay all product-related requests
python src/manage.py replay_requests --glob "*products*" --compare
```

This system provides a robust foundation for deterministic testing and regression detection in your Django application.