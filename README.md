# Retail Management System

## Project Description

A retail management system with user authentication and product management capabilities. This project implements a 2-tier architecture with a web client and SQLite database for local persistence.

**Current Status**: User authentication and product management systems are fully implemented. Sales management features are planned for future development.

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

### In Progress
- **Sales Management System**
  - Sales transaction processing
  - Payment processing
  - Inventory management
  - Sales reporting

## Technology Stack

- **Backend**: Django 5.2.6
- **Database**: SQLite3
- **Frontend**: HTML, CSS, Bootstrap 5
- **Python**: 3.13.3
- **Testing**: pytest, pytest-django

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
    ├── retail/              # Main Django project
    │   ├── settings.py      # Django settings
    │   ├── urls.py          # Main URLs
    │   └── views.py         # Main views
    ├── templates/           # HTML templates
    │   ├── accounts/        # Account templates
    │   │   ├── base.html    # Base template
    │   │   ├── login.html   # Login page
    │   │   ├── register.html # Registration page
    │   │   ├── profile.html # Profile page
    │   │   └── dashboard.html # Dashboard
    │   └── products/        # Product templates
    │       ├── product_list.html # Product listing
    │       ├── product_detail.html # Product details
    │       ├── product_form.html # Product forms
    │       ├── category_list.html # Category listing
    │       └── category_form.html # Category forms
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

#### **Administration**
- **Admin Panel**: http://127.0.0.1:8000/admin/


## Next Steps

1. Build sales transaction system
2. Add payment processing
3. Create sales reporting features
4. Add unit tests for all functionality
5. Create UML diagrams
6. Write Architectural Decision Records (ADRs)
