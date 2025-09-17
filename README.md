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
├── docs/                    # Documentation (ADR, UML)
├── tests/                   # Unit tests (business logic + database integration)
├── README.md                # This file
├── requirements.txt         # Dependencies
├── run_tests.py             # Test runner script
└── src/                     # Django project
    ├── manage.py            # Django management script
    ├── db.sqlite3           # SQLite database
    ├── accounts/            # Authentication (models, views, forms, urls)
    ├── products/            # Product management (CRUD, categories, admin)
    ├── cart/                # Shopping cart (models, business_rules, checkout)
    ├── orders/              # Order processing (sales, payments, PDF receipts)
    ├── retail/              # Main project (settings, urls, payment service)
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

### Sample Data
```bash
python manage.py create_sample_data
```

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

### Test Coverage (24 total tests)
- **Business Logic Tests (9)**: Payment processing, cart rules, stock validation
- **Database Integration Tests (15)**: CartItem operations, checkout flow, atomic transactions

### Test Output
- Verbose execution details
- Clear "BUSINESS LOGIC" vs "DATABASE INTEGRATION" categorization
- Summary statistics with pass/fail counts and success rate
