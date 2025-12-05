# Retail Management System

## Project Description

A comprehensive retail management system built with Django that provides user authentication, product catalog management, shopping cart functionality, order processing, and payment handling. The system implements a 2-tier architecture with a web client and SQLite database for local persistence.

## Team Members

- Aaron Wajah
- Kyrie Park

## Features

- **User Authentication**: Registration, login/logout, profile management, secure sessions
- **Product Management**: Full CRUD operations, categories, search/filtering, stock tracking
- **Shopping Cart**: Session/database storage, real-time validation, stock protection
- **Order Processing**: Complete workflow, order history, PDF receipts, status tracking
- **Payment System**: Mock processing for cash/card payments with validation
- **Checkout Flow**: Secure forms, address collection, payment method selection
- **Concurrency Control**: Atomic transactions, row-level locking, error handling
- **Flash Sale Orders**: High-concurrency checkout with throttling and idempotency
- **Partner Catalog Ingest**: Automated product feed processing with validation
- **Order Processing Robustness**: Retry policies, circuit breakers, atomic rollbacks
- **Record/Playback Testing**: Automated regression testing through interface testing

## New Features – Checkpoint 4

### 2.1 Order History Filtering & Search (Customer Side)

A comprehensive filtering and search system has been added to the Order History screen, allowing customers to efficiently find and filter their past orders.

**Features:**
- **Filter by Order Status**: Filter orders by status categories:
  - **Completed**: Paid orders that had return history (excludes clean orders with no returns)
  - **Pending**: Orders with RMA status in requested, under_review, validated, or in_transit
  - **Returned**: Orders with RMA status in received, under_inspection, or approved
  - **Refunded**: Orders with RMA status "refunded" or closed with resolution="refund"
- **Keyword Search**: Search by order ID (numeric) or product names within order items
- **Date Range Filter**: Filter orders by creation date using start date and end date inputs
- **No Return Requests Filter**: Checkbox option to show only orders that never had any return request (orthogonal to status filter)

**Implementation Details:**
- New `OrderHistoryFilterForm` in `src/orders/forms.py` with fields: search, status, start_date, end_date, only_no_returns
- Enhanced `order_history` view in `src/orders/views.py` with:
  - Dynamic status filtering based on RMA status and resolution
  - Keyword search across order ID and product names via related SaleItem relationships
  - Date range filtering on `Sale.created_at`
  - `overall_status` computation that maps RMA states to high-level status categories
- Filter UI matches the existing product search form design for consistency
- All filters work in combination and preserve state in URL parameters

### 2.2 Configurable Low-Stock Alerts (Admin Side)

Admin users now have access to configurable low-stock threshold controls in the product management interface.

**Features:**
- **Dynamic Threshold Input**: Admin users see a number input field to set a custom low-stock threshold per request
- **Low-Stock Filter Checkbox**: "Only show low-stock products (≤ threshold)" checkbox to filter products where `0 < stock_quantity <= threshold`
- **Default Threshold**: Configurable via `LOW_STOCK_THRESHOLD_DEFAULT` setting (default: 10, can be overridden via environment variable)
- **Admin-Only UI**: Low-stock controls are only visible to users with admin role (via `UserProfile.role == 'admin'` or superuser status)

**Implementation Details:**
- New setting `LOW_STOCK_THRESHOLD_DEFAULT` in `src/retail/settings.py`
- Enhanced `product_list` view in `src/products/views.py` with:
  - Runtime threshold calculation from request parameters or default
  - Admin-only filter application when checkbox is checked
  - Uses custom `user_is_admin` logic (not Django's `is_staff`)
- Admin controls added to `src/templates/products/product_list.html`:
  - Threshold input field pre-filled with current threshold value
  - Checkbox to toggle low-stock-only filtering
  - Only visible when `user_is_admin` is True (same condition as "Add New Product" button)
- Regular customers see no changes to the UI

### 2.3 RMA Status Notifications

RMA status changes are now surfaced to users through lightweight front-end notifications and badges.

**Features:**
- **Status Display**: RMA status progression displayed as badges:
  - Submitted → Received → Under Inspection → Approved → Refunded
- **UI Notifications**: Simple front-end notifications for status changes (no email/SMS)
- **Integration**: Fully integrated with existing Returns & Refunds workflow
- **User Experience**: Clear visual indicators for RMA status at each stage of the return process

**Implementation Details:**
- Status badges and notifications integrated into RMA detail and list views
- Uses existing Bootstrap badge components for consistent styling
- No backend notification service required — lightweight front-end implementation only

## Observability & Monitoring (Checkpoint 3)

The system includes comprehensive observability features to support debugging and production monitoring:

### Structured Logging
- **JSON Format**: All logs output in structured JSON with timestamp, level, logger, message, and request_id
- **X-Request-ID Tracing**: UUID-based request IDs generated per HTTP request for correlating logs across the system
- **ObservabilityMiddleware**: Automatically injects request IDs into log records and response headers
- **Logging Configuration**: `src/retail/logging.py` with console and file handlers

### Metrics Collection
- **Metric Model**: Database-backed metrics storage (`src/retail/models.py`)
- **Metric Types**: orders_per_day, error_rate, payment_success_rate, avg_response_time, circuit_breaker_state, stock_conflicts, throttled_requests
- **Recording**: `record_metric()` function for capturing key system events
- **Aggregation**: `get_metrics_summary(days=7)` for time-based analytics

### Dashboards
- **Metrics Dashboard** (`/metrics/dashboard/`): Admin-only view showing:
  - Key metrics cards (orders, error rate, payment success, response time)
  - System health indicators
  - Daily trends and payment status breakdown
- **Quality Scenarios Dashboard** (`/metrics/quality-scenarios/`): Runtime verification of quality attributes:
  - A1: Flash Sale Concurrency Control (stock conflicts = 0)
  - A2: Payment Service Resilience (≥95% success, <100ms fast-fail)

### Debugging Support
- **Request Tracing**: X-Request-ID headers enable end-to-end request tracking across logs
- **Error Metrics**: Automatic recording of 4xx/5xx responses with metadata
- **Circuit Breaker Monitoring**: Real-time circuit breaker state tracking for payment service health
- **Structured Search**: JSON logs enable efficient searching by request_id, user_id, or error type

## Technology Stack

- **Backend**: Django 5.2.6, Python 3.13.3
- **Database**: SQLite3 with atomic transactions
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **PDF Generation**: reportlab
- **Testing**: Django Test Framework

## Project Structure

```
software-architecture-project/
├── db/                      # Database schema documentation
│   └── init.sql             # Complete database schema (Django-generated)
├── docs/                    # Documentation
│   ├── ADR/                 # Architectural Decision Records
│   │   ├── CP4_ADR.md       # CP4 features (Order History, Low-Stock Alerts, RMA Notifications)
│   │   └── ...              # Other ADRs (persistence, observability, returns, etc.)
│   ├── UML/                 # UML diagrams for all checkpoints (CP1-CP4)
│   │   └── UMLdiagrams.md   # Complete 4+1 view diagrams for CP1-CP4
│   ├── CP4_Design_Reflection.md  # CP4 design decisions reflection & analysis
│   ├── QS-Catalog.md        # Quality Scenario Catalog
│   ├── record_playback.md   # Record/Playback testing documentation
│   └── RUNBOOK.md           # Operational runbook
├── tests/                   # Unit tests (business logic + database integration + robustness + record/playback)
├── README.md                # This file
├── requirements.txt         # Dependencies
├── run_tests.py             # Test runner script
└── src/                     # Django project
    ├── manage.py            # Django management script
    ├── db.sqlite3           # SQLite database
    ├── accounts/            # Authentication (models, views, forms, urls)
    ├── products/            # Product management (CRUD, categories, admin, low-stock filtering)
    ├── cart/                # Shopping cart (models, business_rules, checkout, robustness)
    ├── orders/              # Order processing (sales, payments, PDF receipts, history filtering)
    ├── partner_feeds/       # Partner catalog ingestion (adapters, validators, services)
    ├── payments/            # Payment resilience (client, policy, service)
    ├── retail/              # Main project (settings, urls, middleware, logging)
    └── templates/           # HTML templates (accounts, products, cart, orders)
```

## Setup Instructions

### Prerequisites
- Python 3.10+
- Git

### Quick Setup
```bash
# Clone repository
git clone <this-repository-url>
cd software-architecture-project

# Create and activate virtual environment
python -m venv .venv
# Windows: .venv\Scripts\Activate
# macOS/Linux: source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Setup database
cd src
python manage.py makemigrations
python manage.py migrate
```
### Sample Data
```bash
python manage.py create_sample_data
```

## Run Instructions

### Start Development Server
```bash
python manage.py runserver
```

### Access Application
- **Main App**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

### Key URLs
- **Authentication**: `/accounts/login/`, `/accounts/register/`, `/accounts/profile/`
- **Products**: `/products/`, `/products/create/`, `/products/categories/`
- **Cart**: `/cart/`, `/cart/checkout/`
- **Orders**: `/orders/`, `/orders/{id}/download/`

## Database Setup

### Automatic Setup
Database is created automatically during migration. SQLite file: `src/db.sqlite3`

### Models
- **User & UserProfile**: Authentication and profiles with role-based access
- **Category & Product**: Catalog with stock management and SKU tracking
- **CartItem**: Shopping cart items
- **Sale & SaleItem**: Order records and items with atomic transactions
- **Payment**: Transaction records with multiple payment methods



### Reset Database
```bash
rm src/db.sqlite3
python manage.py migrate
```

### Create Admin User
```bash
python manage.py createsuperuser
```

## Test Instructions

### Run Tests
```bash
python run_tests.py
```
### Test Partner Ingest with sample Data

```bash
cd software-architecture-project/src
python test_partner_ingestion.py
```


### Test Coverage (64 total tests)
- **Business Logic Tests (9)**: Payment processing, cart rules, stock validation
- **Database Integration Tests (15)**: CartItem operations, checkout flow, atomic transactions
- **Order Robustness Tests (16)**: 
  - Happy path (success)
  - Retry then success (transient failure recovery)
  - Total failure → atomic rollback
  - Circuit breaker opens (fail fast)
  - Breaker recovery (half-open → closed)
  - Timeout bound (bounded latency)
  - Invariant validation (paid requires provider_ref)
  - Stock conflict rollback
  - Comprehensive resilience scenarios
  - No retry on non-transient errors (4xx)
  - Circuit breaker short-circuit (fast-fail)
  - Breaker time window semantics
  - Bounded latency when OPEN
  - Isolation across orders (global protection)
  - Logging/observability verification
  - CSRF protection on flash checkout
- **Record/Playback Tests (5)**: Automated regression testing, PII scrubbing, flash sale workload testing
- **Quality Scenario Tests (19)**: Comprehensive testing of all quality scenarios
  - **Core Quality Scenarios (14)**: From QS-Catalog.md
    - Availability (A1, A2): Concurrency control, payment resilience
    - Security (S1, S2): CSRF protection, RBAC authorization
    - Modifiability (M1, M2): Adapter pattern, business rules isolation
    - Performance (P1, P2): Throttling, async queue split
    - Integrability (I1, I2): Validate-transform-upsert pipeline, bulk operations
    - Testability (T1, T2): Dependency injection, deterministic environment
    - Usability (U1, U2): Error messages, payment unavailable UX
  - **Release Resilience Scenarios (5)**: For "Faster Releases with Fewer Outages"
    - R1: Zero downtime deployment
    - R2: Feature flag safety
    - R3: Database migration safety
    - R4: Monitoring early detection
    - R5: Graceful degradation

### Record/Replay Testing
The system includes automated record/playback testing for regression detection:

```bash
# Run all tests including record/playback
python run_tests.py
```

**Features:**
- Automatic recording of POST requests when `DEBUG=True`
- PII scrubbing (passwords, tokens redacted)
- Automated regression detection in test suite
- Flash sale workload testing
- 5 comprehensive record/playback tests


### Test Output
- Verbose execution details for all test categories
- Clear "BUSINESS LOGIC" vs "DATABASE INTEGRATION" vs "ORDER ROBUSTNESS" vs "RECORD/PLAYBACK" vs "QUALITY SCENARIO" categorization
- Summary statistics with pass/fail counts and success rate
- Feature 3 implementation validation
- Comprehensive quality scenario validation
- 100% success rate (64/64 tests passing)


