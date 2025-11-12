# Deployment & Reliability Guide

This document describes the containerization, observability, and quality scenario verification features.

## A. Containerization

### Docker Setup

The application is containerized using Docker and Docker Compose.

#### One-Command Startup

```bash
docker compose up -d
```

This starts:
- **PostgreSQL database** (port 5432)
- **Django web application** (port 8000)
- **Background worker** (for async job processing)

## Quick Start Guide

### 1. Start the Application

```bash
docker compose up -d
```

This starts all services in the background:
- PostgreSQL database (port 5432)
- Django web application (port 8000)
- Background worker

### 2. Run Database Migrations

Migrations run automatically on startup, but you can run them manually:

```bash
docker compose exec web python manage.py migrate
```

### 3. Create Admin User

```bash
docker compose exec web python manage.py create_admin
```

Default credentials:
- Username: `admin`
- Password: `admin123`

### 4. Populate Sample Data

```bash
docker compose exec web python manage.py populate_products
```

### 5. Access the Application

- **Main Application**: http://localhost:8000
- **Admin Panel**: http://localhost:8000/admin/
- **Products**: http://localhost:8000/products/
- **Metrics Dashboard**: http://localhost:8000/metrics/dashboard/ (admin only)
- **Quality Scenarios**: http://localhost:8000/metrics/quality-scenarios/ (admin only)
- **Metrics API**: http://localhost:8000/metrics/api/?days=7

## Daily Operations

**View Application Logs:**
```bash
docker compose logs web -f
```

**Stop Containers:**
```bash
docker compose down
```

**Restart Containers:**
```bash
docker compose restart
```

**Rebuild After Code Changes:**
```bash
docker compose up --build
```

**Access Django Shell:**
```bash
docker compose exec web python manage.py shell
```

**Run Management Commands:**
```bash
# Create admin user
docker compose exec web python manage.py create_admin

# Populate products
docker compose exec web python manage.py populate_products

# Create superuser (interactive)
docker compose exec -it web python manage.py createsuperuser
```

#### Files

- `Dockerfile`: Defines the Django application container
- `docker-compose.yml`: Orchestrates all services
- `.dockerignore`: Excludes unnecessary files from build context

#### Environment Variables

Create a `.env` file (see `.env.example`):

```env
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://retail_user:retail_password@db:5432/retail_db
```

#### Database Migrations

Migrations run automatically on container startup. To run manually:

```bash
docker compose exec web python manage.py migrate
```

## B. Observability

### Structured Logging

All logs include:
- **Request ID**: Unique identifier for each request (UUID)
- **Timestamp**: ISO 8601 format
- **Error Level**: INFO, WARNING, ERROR, DEBUG
- **Structured JSON**: Machine-readable format

#### Log Format

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
    "user_id": "1"
  }
}
```

#### Log Locations

- **Console**: Structured JSON output
- **File**: `logs/application.log` (created automatically)

### Metrics Collection

The system tracks the following metrics:

- **orders_per_day**: Daily order count
- **error_rate**: HTTP error rate percentage
- **refunds_per_day**: Daily refund count
- **payment_success_rate**: Payment success percentage
- **avg_response_time**: Average HTTP response time (ms)
- **circuit_breaker_state**: Payment circuit breaker state (CLOSED/OPEN/HALF_OPEN)
- **stock_conflicts**: Stock concurrency conflicts
- **throttled_requests**: Rate-limited requests

#### Metrics Dashboard

Access the admin metrics dashboard at:

```
/metrics/dashboard/
```

Features:
- Key metrics cards (orders, error rate, payment success, response time)
- System health indicators
- Daily orders trend
- Payment status breakdown
- Recent error metrics

#### Metrics API

JSON API endpoint:

```
/metrics/api/?days=7
```

Returns metrics summary as JSON.

## D. Quality Scenario Verification

### Runtime Verification

The system verifies quality scenarios from `QS-Catalog.md` using runtime metrics.

Access at:

```
/metrics/quality-scenarios/
```

### Verified Scenarios

#### Scenario A1: Flash Sale Concurrency Control

**Response Measure**: 0 oversell incidents; stock consistency maintained

**Verification**:
- Tracks `stock_conflicts` metric
- Verifies stock conflicts = 0
- Monitors concurrent checkout operations

**Status**: PASS if stock_conflicts = 0

#### Scenario A2: Payment Service Resilience

**Response Measure**: ≥95% successful payments; <100ms fast-fail when circuit open

**Verification**:
- Calculates payment success rate from Payment model
- Tracks circuit breaker state transitions
- Monitors fast-fail latency when circuit is OPEN

**Status**: PASS if success_rate ≥ 95% AND fast_fail < 100ms

### Metrics Used for Verification

- **Stock Conflicts**: Recorded when `IntegrityError` occurs during checkout
- **Payment Success Rate**: Calculated from `Payment` model status
- **Circuit Breaker State**: Recorded on each payment attempt
- **Fast-Fail Latency**: Response time when circuit breaker is OPEN

## Implementation Details

### Request ID Middleware

`ObservabilityMiddleware`:
- Generates UUID for each request
- Adds `X-Request-ID` header to responses
- Logs request/response with timing
- Records error metrics for 4xx/5xx responses

### Metrics Recording

Metrics are recorded via `record_metric()` function:

```python
from retail.observability import record_metric

record_metric('stock_conflicts', 1, {
    'product_id': 123,
    'product_name': 'Product Name',
})
```

### Database Models

- `Metric`: Stores all system metrics with type, value, metadata, and timestamp

### Admin Interface

Metrics are visible in Django admin at `/admin/retail/metric/`

## Initial Setup

### Create Admin User

After starting the containers, create an admin user to access the admin panel:

```bash
docker compose exec web python manage.py create_admin
```

This creates a default admin user:
- **Username**: `admin`
- **Password**: `admin123`
- **Email**: `admin@example.com`

**Custom Admin User:**

To create an admin with custom credentials:

```bash
docker compose exec web python manage.py create_admin \
  --username myadmin \
  --email myadmin@example.com \
  --password mypassword123
```

**Access Admin Panel:**
- URL: http://localhost:8000/admin/
- Login with the credentials created above

### Populate Sample Products

The database starts empty. Populate it with sample products:

```bash
docker compose exec web python manage.py populate_products
```

This creates:
- **4 Categories**: Electronics, Clothing, Books, Home & Garden
- **10 Sample Products** across different categories with stock quantities

**Repopulate Products (Clear and Recreate):**

```bash
docker compose exec web python manage.py populate_products --clear
```

**View Products:**
- Web interface: http://localhost:8000/products/
- Admin panel: http://localhost:8000/admin/products/product/

### Admin Panel Features

The admin panel provides management interfaces for:

1. **Users & Authentication**
   - User management
   - Groups and permissions

2. **Products**
   - Categories management
   - Products with flash sale configuration
   - Stock management

3. **Orders**
   - Sales/Orders with inline items
   - Sale Items
   - Payment records

4. **Partner Feeds**
   - Partner management
   - Feed ingestion tracking

5. **Retail (Observability)**
   - System metrics viewing
   - Metrics are created programmatically (read-only in admin)

6. **Accounts**
   - User profiles

## Production Considerations

1. **Log Rotation**: Configure log rotation for `logs/application.log`
2. **Metrics Retention**: Implement cleanup for old metrics (e.g., keep last 90 days)
3. **Database**: Use PostgreSQL in production (configured in docker-compose)
4. **Monitoring**: Integrate with external monitoring (Prometheus, Grafana, etc.)
5. **Alerting**: Set up alerts for:
   - Error rate > 5%
   - Payment success rate < 95%
   - Stock conflicts > 0
   - Circuit breaker OPEN state
6. **Security**: Change default admin credentials in production
7. **Data Seeding**: Use fixtures or management commands for production data

## Troubleshooting

### Logs Not Appearing

- Check `logs/` directory exists and is writable
- Verify `LOGGING` configuration in `settings.py`

### Metrics Not Recording

- Ensure `Metric` model migrations are applied
- Check database connection
- Verify `record_metric()` calls are executing

### Docker Issues

- Check container logs: `docker compose logs web`
- Verify database connection: `docker compose exec web python manage.py dbshell`
- Rebuild containers: `docker compose up --build`

### No Products Available

- Run the populate command: `docker compose exec web python manage.py populate_products`
- Check products in admin: http://localhost:8000/admin/products/product/
- Verify database has data: `docker compose exec web python manage.py shell` then `from products.models import Product; print(Product.objects.count())`

### Admin Panel Access Issues

- Ensure superuser exists: `docker compose exec web python manage.py create_admin`
- Check user permissions in admin panel
- Verify Django admin is enabled in `INSTALLED_APPS`

