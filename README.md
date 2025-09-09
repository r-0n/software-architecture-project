# Retail Management System

## Project Description


## Team Members

- [Kyrie Park]
- [Aaron Wajah]

## Features

### Implemented
- **User Authentication System**
  - User registration with extended profile fields
  - User login/logout functionality
  - User profile management
  - Secure password handling
  - Session management

### In Progress
- **Sales Management System**
  - Product catalog management
  - Sales transaction processing
  - Inventory management
  - Payment processing

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
    ├── retail/              # Main Django project
    │   ├── settings.py      # Django settings
    │   ├── urls.py          # Main URLs
    │   └── views.py         # Main views
    └── templates/           # HTML templates
        └── accounts/        # Account templates
            ├── base.html    # Base template
            ├── login.html   # Login page
            ├── register.html # Registration page
            ├── profile.html # Profile page
            └── dashboard.html # Dashboard
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

- **Home/Login**: http://127.0.0.1:8000/
- **User Registration**: http://127.0.0.1:8000/accounts/register/
- **User Login**: http://127.0.0.1:8000/accounts/login/
- **User Profile**: http://127.0.0.1:8000/accounts/profile/
- **Dashboard**: http://127.0.0.1:8000/dashboard/
- **Admin Panel**: http://127.0.0.1:8000/admin/


## Next Steps

1. Implement product catalog management
2. Build sales transaction system
3. Add inventory management
4. Create reporting features
5. Add unit tests for all functionality
6. Create UML diagrams
7. Write Architectural Decision Records (ADRs)