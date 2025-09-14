# Retail Management System

## Project Description

A retail management system with user authentication and product management capabilities. This project implements a 2-tier architecture with a web client and SQLite database for local persistence.

**Current Status**: User authentication, product management, shopping cart, and order management systems are fully implemented. The system now supports complete e-commerce functionality with payment processing.

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
  - Session-based cart management
  - Add/remove/update cart items
  - Stock validation before adding items
  - Real-time cart updates
  - Cart persistence across sessions

- **Order Management System**
  - Complete order processing workflow
  - Order history and tracking
  - Order detail views
  - Integration with cart system
  - Automatic stock decrementation

- **Payment Processing System**
  - Mock payment processing service
  - Support for cash and card payments
  - Payment validation and reference generation
  - Transaction management for data integrity

- **Checkout Process**
  - Secure checkout form with address collection
  - Payment method selection
  - Order confirmation and processing
  - Stock validation during checkout

### In Progress
- **Sales Reporting System**
  - Sales analytics and reporting
  - Inventory management reports
  - Customer order history analysis

## Technology Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite3
- **Frontend**: HTML, CSS, Bootstrap 5
- **Python**: 3.13.3
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
    │   ├── models.py        # Order and OrderItem models
    │   ├── views.py         # Order management views
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
    │       └── order_detail.html # Order details
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

#### **Administration**
- **Admin Panel**: http://127.0.0.1:8000/admin/


## Next Steps

1. Create sales reporting and analytics features
2. Add unit tests for all functionality
3. Create UML diagrams
4. Write Architectural Decision Records (ADRs)
5. Add email notifications for order confirmations
6. Implement inventory alerts for low stock
7. Add customer order tracking system
