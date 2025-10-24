# Retail Management System - Operational Runbook

## System Overview
- **Framework**: Django 5.2.6 with Python 3.13.3
- **Database**: SQLite3 (file-based)
- **Architecture**: 2-tier (Client + Database)
- **Key URLs**: http://127.0.0.1:8000/ (Main), http://127.0.0.1:8000/admin/ (Admin)

---

## Setup & Installation

### Prerequisites
- Python 3.10+, Git, pip
- 2GB RAM, 500MB storage

### Installation
```bash
# Clone and setup
git clone <repository-url>
cd software-architecture-project
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # macOS/Linux

# Install and configure
pip install -r requirements.txt
cd src
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser
python manage.py create_sample_data

# Verify
cd ..
python run_tests.py
```

---

## Development Operations

### Starting Services
```bash
cd src
python manage.py runserver  # http://127.0.0.1:8000/
python manage.py run_queue  # Background worker (optional)
```

### Common Tasks
```bash
# Database
python manage.py makemigrations
python manage.py migrate
rm db.sqlite3 && python manage.py migrate && python manage.py create_sample_data  # Reset

# Management
python manage.py createsuperuser
python manage.py create_sample_data
# Admin: http://127.0.0.1:8000/admin/
```

---

## Testing

### Test Suite (64 total tests)
- **Business Logic (9)**: Payment processing, cart rules, stock validation
- **Database Integration (15)**: CartItem operations, checkout flow, atomic transactions
- **Order Robustness (16)**: Resilience patterns, circuit breakers, retry policies
- **Record/Playback (5)**: Automated regression testing
- **Quality Scenarios (19)**: Comprehensive quality attribute testing

### Running Tests
```bash
# All tests
python run_tests.py

# Specific categories
cd src
python manage.py test tests.test_business_logic --verbosity=2
python manage.py test tests.test_database_integration --verbosity=2
python manage.py test tests.test_order_processing_robustness --verbosity=2
python manage.py test tests.test_record_playback --verbosity=2
python manage.py test tests.test_quality_scenarios --verbosity=2

# Record/playback testing
python manage.py replay_requests --dir recorded_requests
python manage.py replay_requests --file specific_file.json --compare --fail-fast

# Partner feed testing
python test_partner_ingestion.py
```