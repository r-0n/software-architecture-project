# Observability and Resilience Architectural Decision

## Status
**Accepted**

## Context

The retail management system requires comprehensive observability and resilience capabilities to:
- **Debug Production Issues**: Trace requests across the system using unique identifiers
- **Monitor System Health**: Track key performance indicators (KPIs) and business metrics
- **Verify Quality Scenarios**: Demonstrate runtime satisfaction of architectural quality attributes (availability, performance)
- **Detect Anomalies**: Identify errors, performance degradation, and system failures early
- **Support Operations**: Provide administrators with actionable insights through dashboards
- **Ensure Resilience**: Monitor circuit breaker states, stock conflicts, and payment success rates
- **Compliance and Auditing**: Maintain request traces for security and compliance requirements

Key requirements include:
- **Structured Logging**: Machine-readable logs with request IDs, timestamps, and error levels
- **Metrics Collection**: Track business metrics (orders/day, refunds/day) and system metrics (error rate, response time)
- **Admin Dashboard**: Visual representation of system health and performance
- **Quality Scenario Verification**: Runtime verification of quality attributes (A1: Concurrency Control, A2: Payment Resilience)
- **Request Tracing**: Unique request IDs for correlating logs across services
- **Error Tracking**: Automatic error detection and classification
- **Performance Monitoring**: Response time tracking and performance degradation detection

## Decision

We implemented a **comprehensive observability and resilience system** using:
1. **Structured Logging** with request ID tracking via Django middleware
2. **Metrics Collection** using a dedicated `Metric` model with database storage
3. **Admin Dashboard** with visual metrics display and quality scenario verification
4. **Resilience Monitoring** for circuit breakers, stock conflicts, and payment success rates

### Technical Implementation

**1. Structured Logging Architecture:**

- **Request ID Generation**: UUID-based request IDs generated per HTTP request
- **Thread-Local Storage**: Request IDs stored in thread-local context for log correlation
- **Middleware Integration**: `ObservabilityMiddleware` intercepts all requests/responses
- **JSON Format**: Structured logs in JSON format for machine parsing
- **Dual Output**: Logs written to both console (stdout) and file (`logs/application.log`)
- **Request ID Header**: `X-Request-ID` header added to all HTTP responses

**Key Components:**
- `ObservabilityMiddleware`: Generates request IDs, logs requests/responses, records metrics
- `RequestIDFilter`: Injects request IDs into all log records
- `StructuredLogger`: Wrapper for consistent structured logging with event types

**2. Metrics Collection System:**

- **Metric Model**: Database-backed metrics storage with type, value, metadata, and timestamp
- **Metric Types**:
  - `orders_per_day`: Daily order count
  - `error_rate`: HTTP error rate percentage
  - `refunds_per_day`: Daily refund count
  - `payment_success_rate`: Payment success percentage
  - `avg_response_time`: Average HTTP response time (ms)
  - `circuit_breaker_state`: Payment circuit breaker state (CLOSED/OPEN/HALF_OPEN)
  - `stock_conflicts`: Stock concurrency conflicts
  - `throttled_requests`: Rate-limited requests

- **Automatic Recording**: Metrics recorded automatically via middleware and business logic hooks
- **Metadata Support**: JSON metadata field for additional context (path, method, status_code, etc.)
- **Database Indexing**: Optimized queries with indexes on `metric_type` and `recorded_at`

**3. Admin Dashboard:**

- **Metrics Dashboard** (`/metrics/dashboard/`): Admin-only view showing:
  - Key metrics cards (orders, error rate, payment success, response time)
  - System health indicators
  - Daily orders trend
  - Payment status breakdown
  - Recent error metrics
  - Response time statistics

- **Quality Scenario Verification** (`/metrics/quality-scenarios/`): Runtime verification of:
  - **Scenario A1**: Flash Sale Concurrency Control (stock conflicts = 0)
  - **Scenario A2**: Payment Service Resilience (≥95% success rate, <100ms fast-fail)

- **Metrics API** (`/metrics/api/?days=7`): JSON API for programmatic access

**4. Resilience Monitoring:**

- **Circuit Breaker Tracking**: State changes recorded as metrics with metadata
- **Stock Conflict Detection**: Integrity errors during checkout recorded as metrics
- **Payment Success Rate**: Calculated from `Payment` model status
- **Error Classification**: Automatic error classification (4xx vs 5xx) with appropriate log levels

## Consequences

### Positive Consequences

- **Request Traceability**: Every request has a unique ID for end-to-end tracing
- **Structured Data**: Machine-readable logs enable automated analysis and alerting
- **Performance Visibility**: Response time tracking identifies slow endpoints
- **Error Detection**: Automatic error classification and tracking
- **Quality Assurance**: Runtime verification of architectural quality attributes
- **Operational Insights**: Admin dashboard provides actionable system health information
- **Debugging Efficiency**: Request IDs enable quick log correlation and issue diagnosis
- **Compliance Support**: Audit trail with request IDs and timestamps
- **Proactive Monitoring**: Early detection of performance degradation and errors
- **Resilience Verification**: Circuit breaker and stock conflict monitoring ensures system reliability
- **Business Intelligence**: Orders/day and refunds/day metrics support business decisions
- **Database-Backed Metrics**: Persistent metrics enable historical analysis and trending

### Negative Consequences

- **Performance Overhead**: Middleware adds latency to every request (minimal but measurable)
- **Storage Growth**: Metrics and logs accumulate over time, requiring retention policies
- **Database Load**: Additional writes for metrics may impact database performance
- **Complexity**: Additional code complexity for logging and metrics collection
- **Maintenance**: Requires ongoing monitoring of log file sizes and metric retention
- **Learning Curve**: Team members need to understand structured logging and metrics
- **Debugging Complexity**: JSON logs may be harder to read for developers used to plain text
- **Resource Usage**: Log files and metrics consume disk space and database storage

### Trade-offs

- **Performance vs. Observability**: Accept minimal performance overhead for comprehensive observability
- **Storage vs. Retention**: Balance between keeping historical data and storage costs
- **Simplicity vs. Features**: Chose comprehensive solution over minimal logging
- **Database vs. External Service**: Use database for metrics instead of external services (simpler, but less scalable)
- **Automatic vs. Manual**: Automatic metric recording vs. manual instrumentation (chose automatic for consistency)

## Alternatives Considered

### External APM Tools (New Relic, Datadog, AppDynamics)
- **Pros**: Enterprise-grade features, advanced analytics, alerting, distributed tracing
- **Cons**: Cost (significant for small projects), vendor lock-in, external dependency, complexity
- **Decision**: Rejected due to cost and complexity for current project scale

### ELK Stack (Elasticsearch, Logstash, Kibana)
- **Pros**: Powerful log aggregation, search, visualization, open-source
- **Cons**: Complex setup, resource-intensive, requires separate infrastructure, operational overhead
- **Decision**: Rejected due to infrastructure complexity and operational overhead

### Prometheus + Grafana
- **Pros**: Industry-standard metrics, powerful visualization, alerting, time-series database
- **Cons**: Requires separate infrastructure, learning curve, configuration complexity
- **Decision**: Rejected due to infrastructure requirements and complexity for current needs

### Cloud Logging Services (AWS CloudWatch, Google Cloud Logging)
- **Pros**: Managed service, automatic scaling, integration with cloud services
- **Cons**: Vendor lock-in, cost at scale, internet dependency
- **Decision**: Rejected due to vendor lock-in and cost considerations

### Simple File-Based Logging
- **Pros**: Zero configuration, no dependencies, simple to implement
- **Cons**: No structured format, difficult to query, no metrics, no request tracing
- **Decision**: Rejected due to lack of structured data and metrics capabilities

### No Observability
- **Pros**: Zero overhead, no complexity, no maintenance
- **Cons**: No debugging capability, no performance monitoring, no quality verification
- **Decision**: Rejected as observability is essential for production systems

### Log Aggregation Only (No Metrics)
- **Pros**: Simpler implementation, lower database load
- **Cons**: No business metrics, no dashboard, limited operational insights
- **Decision**: Rejected as metrics are essential for business and operational monitoring

## Implementation Notes

### Logging Configuration

**Django Settings (`settings.py`):**
```python
LOGGING = {
    'version': 1,
    'formatters': {
        'structured': {
            'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s", "request_id": "%(request_id)s", "extra": %(extra)s}',
        },
    },
    'filters': {
        'request_id': {
            '()': 'retail.observability.RequestIDFilter',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'structured',
            'filters': ['request_id'],
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'logs/application.log',
            'formatter': 'structured',
            'filters': ['request_id'],
        },
    },
}
```

**Middleware Registration:**
```python
MIDDLEWARE = [
    # ... other middleware
    'retail.middleware_observability.ObservabilityMiddleware',
    # ... other middleware
]
```

### Metrics Recording

**Automatic Recording (Middleware):**
- Response time: Recorded for every request
- Error rate: Recorded for 4xx/5xx responses

**Business Logic Recording:**
- Stock conflicts: Recorded in `cart/views.py` when `IntegrityError` occurs
- Throttled requests: Recorded in `cart/views.py` when rate limiting triggers
- Circuit breaker state: Recorded in `payments/service.py` on state changes

**Example Usage:**
```python
from retail.observability import record_metric

record_metric('stock_conflicts', 1, {
    'product_id': 123,
    'product_name': 'Product Name',
})
```

### Metrics Aggregation

**Summary Function:**
- `get_metrics_summary(days=7)`: Aggregates metrics over specified period
- Calculates averages, totals, and percentages
- Supports both SQLite and PostgreSQL

**Quality Scenario Verification:**
- Scenario A1: Checks `stock_conflicts` metric count (should be 0)
- Scenario A2: Calculates payment success rate (should be ≥95%) and fast-fail latency (should be <100ms)

### Dashboard Implementation

**Views:**
- `metrics_dashboard`: Admin-only dashboard with visual metrics
- `quality_scenarios_verification`: Runtime quality scenario verification
- `metrics_api`: JSON API for programmatic access

**Templates:**
- `retail/metrics_dashboard.html`: Bootstrap-based dashboard with charts and cards
- `retail/quality_scenarios.html`: Quality scenario verification display

### Request ID Flow

1. **Request Arrives**: `ObservabilityMiddleware` generates UUID
2. **Context Storage**: Request ID stored in thread-local context
3. **Logging**: All logs include request ID via `RequestIDFilter`
4. **Response**: Request ID added to `X-Request-ID` header
5. **Correlation**: Request ID enables log correlation across services

### Log Format Example

```json
{
  "timestamp": "2024-01-15T10:30:45+00:00",
  "level": "INFO",
  "logger": "retail.observability",
  "message": "event=http.request",
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "extra": {
    "method": "GET",
    "path": "/products/",
    "user_id": "1",
    "ip_address": "127.0.0.1"
  }
}
```

## Quality Scenario Verification

### Scenario A1: Flash Sale Concurrency Control

**Response Measure**: 0 oversell incidents; stock consistency maintained

**Verification:**
- Tracks `stock_conflicts` metric
- Verifies `stock_conflicts = 0` over monitoring period
- Monitors concurrent checkout operations

**Status**: PASS if `stock_conflicts = 0`

### Scenario A2: Payment Service Resilience

**Response Measure**: ≥95% successful payments; <100ms fast-fail when circuit open

**Verification:**
- Calculates payment success rate from `Payment` model
- Tracks circuit breaker state transitions
- Monitors fast-fail latency when circuit is OPEN

**Status**: PASS if `success_rate ≥ 95%` AND `fast_fail < 100ms`

## Future Considerations

1. **Log Rotation**: Implement automatic log rotation to manage file sizes
2. **Metrics Retention**: Add cleanup job for old metrics (e.g., keep last 90 days)
3. **Alerting**: Integrate with alerting systems (email, Slack, PagerDuty) for critical metrics
4. **Distributed Tracing**: Extend request IDs across microservices if architecture evolves
5. **Advanced Analytics**: Add percentile calculations (p95, p99) for response times
6. **Real-time Dashboards**: Consider WebSocket-based real-time metric updates
7. **External Integration**: Export metrics to Prometheus or other time-series databases
8. **Anomaly Detection**: Implement automated anomaly detection for metrics
9. **Cost Optimization**: Archive old metrics to cold storage (S3, etc.)
10. **Performance Optimization**: Consider async metric recording to reduce request latency

## Related Decisions

- **Docker ADR**: Containerization supports structured logging and metrics collection
- **Database ADR**: Database choice affects metrics storage and query performance
- **Persistence ADR**: Metrics persistence strategy and retention policies

This observability and resilience approach provides comprehensive system visibility, enables quality scenario verification, and supports operational excellence while maintaining reasonable complexity and resource usage for the current project scope.

