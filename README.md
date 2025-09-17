# Retail Management System

## Project Description

A retail management system with user authentication and product management capabilities. This project implements a 2-tier architecture with a web client and SQLite database for local persistence.

## Team Members

- Aaron Wajah
- Kyrie Park

## Features

### Implemented
- **User Authentication System**
  - User registration with extended profile fields (phone, address)
  - User login/logout functionality
  - User profile management
  - Secure password handling
  - Session management
  - Dashboard for authenticated users

- **Product Management System**
  - Product catalog with full CRUD operations
  - Category management system
  - Product search and filtering
  - Stock quantity tracking
  - Product status management (active/inactive)
  - Admin interface integration
  - Responsive web interface

- **Shopping Cart System**
  - Session-based cart management for anonymous users
  - Database-based cart management for authenticated users
  - Add/remove/update cart items with real-time validation
  - Proactive stock validation preventing overselling
  - Real-time cart updates and persistence across sessions
  - Comprehensive error handling for invalid operations

- **Order Management System**
  - Complete order processing workflow with Sale/SaleItem models
  - Order history and tracking with detailed views
  - PDF receipt generation and download
  - Integration with cart system and payment processing
  - Atomic stock decrementation with concurrency protection
  - Comprehensive order status management

- **Payment Processing System**
  - Mock payment processing service with detailed validation
  - Support for cash and card payments with comprehensive error handling
  - Payment validation, reference generation, and failure scenarios
  - Transaction management with atomic operations for data integrity
  - Payment voiding and rollback capabilities for concurrency conflicts

- **Checkout Process**
  - Secure checkout form with address collection and validation
  - Dynamic payment method selection with card input fields
  - Order confirmation and processing with comprehensive error handling
  - Real-time stock validation during checkout with concurrency protection
  - Cart clearing and user notification for all scenarios

- **Concurrency & Error Handling**
  - Atomic transactions with row-level locking (select_for_update)
  - Comprehensive concurrency conflict detection and handling
  - Payment voiding and cart clearing for failed transactions
  - User-friendly error messages for all failure scenarios
  - Robust handling of alternative scenarios (A1-A6)


## Technology Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite3 (with atomic transactions and row-level locking)
- **Frontend**: HTML, CSS, Bootstrap 5, JavaScript
- **Python**: 3.13.3
- **PDF Generation**: reportlab
- **Testing**: pytest, pytest-django
- **Development Tools**: django-extensions

## Project Structure

```
software-architecture-project/
├── .git/                    # Git repository
├── .venv/                   # Virtual environment
├── db/                      # Database files
├── docs/                    # Documentation
│   ├── ADR/                 # Architectural Decision Records
│   └── UML/                 # UML diagrams
├── tests/                   # Unit tests
├── README.md                # This file
├── requirements.txt         # Dependencies
└── src/                     # Source code
    ├── manage.py            # Django management script
    ├── accounts/            # Authentication app
    │   ├── models.py        # User and UserProfile models
    │   ├── views.py         # Authentication views
    │   ├── forms.py         # Registration and login forms
    │   ├── urls.py          # Account URLs
    │   └── admin.py         # Admin configuration
    ├── products/            # Product management app
    │   ├── models.py        # Product and Category models
    │   ├── views.py         # Product management views
    │   ├── forms.py         # Product forms
    │   ├── urls.py          # Product URLs
    │   ├── admin.py         # Product admin configuration
    │   └── management/      # Management commands
    │       └── commands/    # Custom Django commands
    ├── cart/                # Shopping cart app
    │   ├── models.py        # CartItem model and Cart utility class
    │   ├── views.py         # Cart management views
    │   ├── forms.py         # Checkout form
    │   ├── urls.py          # Cart URLs
    │   └── admin.py         # Cart admin configuration
    ├── orders/              # Order management app
    │   ├── models.py        # Sale, SaleItem, and Payment models
    │   ├── views.py         # Order management views with PDF generation
    │   ├── urls.py          # Order URLs
    │   └── admin.py         # Order admin configuration
    ├── retail/              # Main Django project
    │   ├── settings.py      # Django settings
    │   ├── urls.py          # Main URLs
    │   ├── views.py         # Main views
    │   └── payment.py       # Payment processing service
    ├── templates/           # HTML templates
    │   ├── accounts/        # Account templates
    │   │   ├── base.html    # Base template
    │   │   ├── login.html   # Login page
    │   │   ├── register.html # Registration page
    │   │   ├── profile.html # Profile page
    │   │   └── dashboard.html # Dashboard
    │   ├── products/        # Product templates
    │   │   ├── product_list.html # Product listing
    │   │   ├── product_detail.html # Product details
    │   │   ├── product_form.html # Product forms
    │   │   ├── category_list.html # Category listing
    │   │   └── category_form.html # Category forms
    │   ├── cart/            # Cart templates
    │   │   ├── cart.html    # Shopping cart view
    │   │   └── checkout.html # Checkout process
    │   └── orders/          # Order templates
    │       ├── order_history.html # Order history
    │       └── order_detail.html # Order details with PDF download
    └── db.sqlite3           # SQLite database
```

## Setup Instructions

### Prerequisites

- Python 3.10+ installed on your system
- Git (for version control)

### 1. Clone the Repository

```bash
git clone <your-repository-url>
cd software-architecture-project
```

### 2. Create Virtual Environment

```bash
python -m venv .venv
```

### 3. Activate Virtual Environment

**Windows:**
```bash
.venv\Scripts\Activate
```

**macOS/Linux:**
```bash
source .venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

### 5. Navigate to Source Directory

```bash
cd src
```

### 6. Create Database Migrations

```bash
python manage.py makemigrations
```

### 7. Apply Database Migrations

```bash
python manage.py migrate
```

## Run Instructions

### 1. Start the Development Server

```bash
python manage.py runserver
```

### 2. Access the Application

Open your web browser and navigate to:
- **Main Application**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

### 3. Available URLs

#### **Authentication**
- **Home/Login**: http://127.0.0.1:8000/
- **User Registration**: http://127.0.0.1:8000/accounts/register/
- **User Login**: http://127.0.0.1:8000/accounts/login/
- **User Profile**: http://127.0.0.1:8000/accounts/profile/
- **Dashboard**: http://127.0.0.1:8000/dashboard/

#### **Product Management**
- **Product List**: http://127.0.0.1:8000/products/
- **Add Product**: http://127.0.0.1:8000/products/create/
- **Categories**: http://127.0.0.1:8000/products/categories/
- **Add Category**: http://127.0.0.1:8000/products/categories/create/

#### **Shopping Cart**
- **Cart View**: http://127.0.0.1:8000/cart/
- **Add to Cart**: http://127.0.0.1:8000/cart/add/{product_id}/
- **Remove from Cart**: http://127.0.0.1:8000/cart/remove/{product_id}/
- **Update Cart**: http://127.0.0.1:8000/cart/update/{product_id}/
- **Clear Cart**: http://127.0.0.1:8000/cart/clear/
- **Checkout**: http://127.0.0.1:8000/cart/checkout/

#### **Order Management**
- **Order History**: http://127.0.0.1:8000/orders/
- **Order Detail**: http://127.0.0.1:8000/orders/{order_id}/
- **Download Receipt**: http://127.0.0.1:8000/orders/{order_id}/download/

#### **Administration**
- **Admin Panel**: http://127.0.0.1:8000/admin/
