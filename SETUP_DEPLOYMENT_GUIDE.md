# Residence Inventory Management System – Setup & Deployment Guide

## Overview
This guide walks through setting up and deploying the Residence Inventory Management System built on InvenTree for Academia residence accommodation.

---

## Prerequisites
- Python 3.9+
- PostgreSQL or SQLite (development)
- Node.js 16+ (for frontend, optional)
- Git
- Virtual environment tool (venv, conda)

---

## Phase 1: Backend Setup (InvenTree + Residence App)

### 1.1 Clone & Setup InvenTree
```bash
# Clone InvenTree repository (if not already done)
git clone https://github.com/inventree/InvenTree.git
cd InvenTree

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install Django REST framework and dependencies (if not already installed)
pip install djangorestframework django-filter
```

### 1.2 Add the Residence App to InvenTree

The residence app should be located at:
```
src/backend/InvenTree/residence/
├── __init__.py
├── models.py
├── views.py
├── serializers.py
├── urls.py
├── admin.py
├── apps.py
├── signals.py
├── management/
│   └── commands/
│       └── populate_residence.py
```

Add `residence` to `INSTALLED_APPS` in Django settings:

**File:** `src/backend/InvenTree/InvenTree/settings.py`
```python
INSTALLED_APPS = [
    # ... other apps ...
    'rest_framework',
    'django_filters',
    'residence',
]

# Rest framework configuration
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
}
```

### 1.3 Run Database Migrations

```bash
# Create migrations for residence app
python src/backend/InvenTree/manage.py makemigrations residence

# Apply migrations
python src/backend/InvenTree/manage.py migrate
```

### 1.4 Initialize System

```bash
# Create user groups and permissions
python src/backend/InvenTree/manage.py shell
>>> from residence import initialize_residence_system
>>> initialize_residence_system()
>>> exit()
```

### 1.5 Populate Data from CSV

Place your CSV file at:
```
src/backend/InvenTree/data/residence_inventory.csv
```

Then run:
```bash
python src/backend/InvenTree/manage.py populate_residence --csv-file data/residence_inventory.csv
```

Expected output:
```
Creating houses and blocks...
  ✓ Created house: Saxenhof
    ✓ Created block: SH Block 1
    ✓ Created block: SH Block 2
    ...
Creating item categories and parts...
  ✓ Created part: Fridge
  ✓ Created part: Microwave
  ...
Creating units and inventory...
  ✓ Created SHARED unit: SH Block 5 Unit 101
    ✓ Created location: SHB5U101A
    ✓ Created location: SHB5U101B
    ✓ Created location: SHB5U101K
      ✓ Added Fridge to SH Block 5 Unit 101
      ✓ Added Microwave to SH Block 5 Unit 101
      ...
✓ Data population complete!
```

### 1.6 Add Residence URLs to Main URLconf

**File:** `src/backend/InvenTree/InvenTree/urls.py`
```python
# Add to urlpatterns
urlpatterns = [
    # ... existing urls ...
    path('', include('residence.urls')),
]
```

### 1.7 Create Superuser & Setup Groups

```bash
# Create superuser
python src/backend/InvenTree/manage.py createsuperuser

# Then in Django shell, add user to group
python src/backend/InvenTree/manage.py shell
>>> from django.contrib.auth.models import User, Group
>>> admin = User.objects.get(username='admin')
>>> managers = Group.objects.get(name='Managers')
>>> admin.groups.add(managers)
>>> 
>>> # Create maintenance staff
>>> staff1 = User.objects.create_user('john_maint', 'john@example.com', 'password123')
>>> staff_group = Group.objects.get(name='Maintenance Staff')
>>> staff1.groups.add(staff_group)
>>>
>>> # Assign blocks to staff
>>> from residence.models import Block, StaffBlockAssignment
>>> block1 = Block.objects.get(house__code='SH', block_number=1)
>>> StaffBlockAssignment.objects.create(staff_member=staff1, block=block1)
>>> exit()
```

### 1.8 Run Development Server

```bash
cd src/backend/InvenTree
python manage.py runserver 0.0.0.0:8000
```

Access:
- Admin dashboard: http://localhost:8000/admin
- API browser: http://localhost:8000/api/residence/

---

## Phase 2: API Testing

### 2.1 Obtain Authentication Token

```bash
# Create token for a user
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "john_maint",
    "password": "password123"
  }'

# Response:
# {"token": "abc123xyz..."}
```

### 2.2 Test Employee Endpoints

**Get assigned blocks:**
```bash
curl -X GET http://localhost:8000/api/residence/employee-dashboard/my_assignments/ \
  -H "Authorization: Token abc123xyz..."
```

**Get units in a block:**
```bash
curl -X GET http://localhost:8000/api/residence/units/?block=1 \
  -H "Authorization: Token abc123xyz..."
```

**Get inventory for a unit:**
```bash
curl -X GET http://localhost:8000/api/residence/units/1/inventory/ \
  -H "Authorization: Token abc123xyz..."
```

**Mark item as OK:**
```bash
curl -X POST http://localhost:8000/api/residence/inventory/1/mark_as_ok/ \
  -H "Authorization: Token abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Mark item as missing:**
```bash
curl -X POST http://localhost:8000/api/residence/inventory/1/mark_as_missing/ \
  -H "Authorization: Token abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{}'
```

**Add new item to unit:**
```bash
curl -X POST http://localhost:8000/api/residence/units/1/add_item/ \
  -H "Authorization: Token abc123xyz..." \
  -H "Content-Type: application/json" \
  -d '{
    "part_id": 1,
    "location_id": 5,
    "serial_number": "NEW-FRIDGE-001",
    "notes": "Replacement for damaged unit"
  }'
```

**View maintenance history:**
```bash
curl -X GET http://localhost:8000/api/residence/maintenance-logs/?unit=1 \
  -H "Authorization: Token abc123xyz..."
```

### 2.3 Test Manager Endpoints

**Get all houses:**
```bash
curl -X GET http://localhost:8000/api/residence/houses/ \
  -H "Authorization: Token admin_token..."
```

**Get admin dashboard:**
```bash
curl -X GET http://localhost:8000/api/residence/admin-dashboard/summary/ \
  -H "Authorization: Token admin_token..."
```

---

## Phase 3: Frontend Setup (Optional)

### 3.1 Admin Dashboard (React)

Create `frontend/admin-dashboard/`:

```bash
cd frontend
npm create vite@latest admin-dashboard -- --template react
cd admin-dashboard
npm install axios react-router-dom
```

**File:** `frontend/admin-dashboard/src/api.js`
```javascript
import axios from 'axios';

const API_BASE = 'http://localhost:8000/api/residence/';

export const api = axios.create({
  baseURL: API_BASE,
  headers: {
    'Authorization': `Token ${localStorage.getItem('token')}`
  }
});

export const getHouses = () => api.get('houses/');
export const getUnits = () => api.get('units/');
export const getInventory = () => api.get('inventory/');
export const getMaintenanceLogs = () => api.get('maintenance-logs/');
export const getDashboardSummary = () => api.get('admin-dashboard/summary/');
```

### 3.2 Employee Dashboard (Vue/React)

Similar setup for simplified employee interface with limited options.

---

## Phase 4: Environment Configuration

### 4.1 Create `.env` file

**File:** `.env`
```
DEBUG=True
SECRET_KEY=your-secret-key-here
DATABASE_URL=postgresql://user:password@localhost:5432/residence_db
ALLOWED_HOSTS=localhost,127.0.0.1
REST_FRAMEWORK_TOKEN_EXPIRES_IN=86400
```

### 4.2 Update settings.py to use environment variables

```python
import os
from pathlib import Path

DEBUG = os.getenv('DEBUG', 'False') == 'True'
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-key-change-in-production')
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost').split(',')
```

---

## Phase 5: Production Deployment

### 5.1 PostgreSQL Setup

```bash
# Install PostgreSQL (Ubuntu)
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE residence_db;
CREATE USER residence_user WITH PASSWORD 'strong_password';
ALTER ROLE residence_user SET client_encoding TO 'utf8';
ALTER ROLE residence_user SET default_transaction_isolation TO 'read_committed';
ALTER ROLE residence_user SET default_transaction_deferrable TO on;
ALTER ROLE residence_user SET timezone TO 'UTC';
GRANT ALL PRIVILEGES ON DATABASE residence_db TO residence_user;
\q
```

### 5.2 Gunicorn Setup

```bash
pip install gunicorn

# Create systemd service file
sudo tee /etc/systemd/system/residence-api.service > /dev/null <<EOF
[Unit]
Description=Residence Inventory API
After=network.target

[Service]
Type=notify
User=www-data
WorkingDirectory=/var/www/inventree
ExecStart=/var/www/inventree/venv/bin/gunicorn \
  --workers 4 \
  --bind 127.0.0.1:8000 \
  --timeout 60 \
  src.backend.InvenTree.InvenTree.wsgi:application
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Start service
sudo systemctl daemon-reload
sudo systemctl start residence-api
sudo systemctl enable residence-api
```

### 5.3 Nginx Reverse Proxy

```nginx
server {
    listen 80;
    server_name residence.example.com;

    location /static/ {
        alias /var/www/inventree/static/;
    }

    location /media/ {
        alias /var/www/inventree/media/;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## Troubleshooting

### Migration Errors
```bash
# Reset migrations (development only)
python manage.py migrate residence zero
python manage.py migrate
```

### Permission Denied on API
- Ensure user is in correct group: `Managers` or `Maintenance Staff`
- Check staff block assignment: `StaffBlockAssignment`

### CSV Import Issues
- Verify CSV delimiter is `;`
- Check block numbers match configured houses
- Ensure room identifiers are consistent (e.g., `101A`, `101B`, `102`)

---

## Next Steps

1. **Customize Item Categories** – Add more part types as needed
2. **Setup Barcode/Serial Integration** – Print labels for assets
3. **Mobile App** – Build native mobile app using Expo/React Native
4. **Reporting** – Generate monthly/quarterly inventory reports
5. **Notifications** – Alert managers of missing/repair-needed items
6. **Integration** – Connect to maintenance request system, resident portal

---

## Support & Documentation

- InvenTree Docs: https://docs.inventree.org/
- API Reference: http://localhost:8000/api/residence/
- Django Admin: http://localhost:8000/admin/

