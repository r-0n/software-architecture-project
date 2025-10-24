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
- **Record/Playback Testing**: Automated regression testing with PII scrubbing


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
├── docs/                    # Documentation (ADR, UML, QS-Catalog, Record/Playback)
├── tests/                   # Unit tests (business logic + database integration + robustness + record/playback)
├── README.md                # This file
├── requirements.txt         # Dependencies
├── run_tests.py             # Test runner script
└── src/                     # Django project
    ├── manage.py            # Django management script
    ├── db.sqlite3           # SQLite database
    ├── accounts/            # Authentication (models, views, forms, urls)
    ├── products/            # Product management (CRUD, categories, admin)
    ├── cart/                # Shopping cart (models, business_rules, checkout, robustness)
    ├── orders/              # Order processing (sales, payments, PDF receipts)
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
