# Quick Start Guide – Residence Inventory Management System

## 5-Minute Setup (Development)

### 1. Clone InvenTree & Enter Directory
```bash
git clone https://github.com/inventree/InvenTree.git
cd InvenTree
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
pip install djangorestframework django-filter
```

### 4. Copy Residence App
Ensure the `residence` folder exists at:
```
src/backend/InvenTree/residence/
```

### 5. Update Django Settings
Edit `src/backend/InvenTree/InvenTree/settings.py`:

```python
# Add to INSTALLED_APPS
INSTALLED_APPS = [
    # ...existing apps...
    'rest_framework',
    'django_filters',
    'residence',
]

# Add REST configuration
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'PAGE_SIZE': 50,
}
```

Edit `src/backend/InvenTree/InvenTree/urls.py`:
```python
urlpatterns = [
    # ...existing urls...
    path('', include('residence.urls')),
]
```

### 6. Run Migrations
```bash
cd src/backend/InvenTree
python manage.py makemigrations residence
python manage.py migrate
```

### 7. Initialize System
```bash
python manage.py shell
>>> from residence import initialize_residence_system
>>> initialize_residence_system()
>>> exit()
```

### 8. Create Superuser
```bash
python manage.py createsuperuser
# Follow prompts: username, email, password
```

### 9. Populate Data
```bash
# Copy your CSV to:
# src/backend/InvenTree/data/residence_inventory.csv

python manage.py populate_residence --csv-file data/residence_inventory.csv
```

### 10. Create Staff Users
```bash
python manage.py shell
>>> from django.contrib.auth.models import User, Group
>>> from residence.models import Block, StaffBlockAssignment
>>>
>>> # Create manager
>>> admin = User.objects.get(username='admin')
>>> managers = Group.objects.get(name='Managers')
>>> admin.groups.add(managers)
>>>
>>> # Create staff members
>>> for i in range(1, 7):
...     staff = User.objects.create_user(f'staff{i}', f'staff{i}@example.com', 'password123')
...     staff_group = Group.objects.get(name='Maintenance Staff')
...     staff.groups.add(staff_group)
...     # Assign to blocks 1-2 (round-robin)
...     block = Block.objects.get(house__code='SH', block_number=1 + (i % 2))
...     StaffBlockAssignment.objects.create(staff_member=staff, block=block)
>>>
>>> exit()
```

### 11. Run Server
```bash
python manage.py runserver
```

### 12. Access System
- **Admin Dashboard**: http://localhost:8000/admin/
- **API Browser**: http://localhost:8000/api/residence/
- **Login**: 
  - Admin: `admin` / `<your_password>`
  - Staff: `staff1` / `password123`

---

## Testing the API

### Get Authentication Token
```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username": "staff1", "password": "password123"}'

# Returns:
# {"token": "abc123xyz..."}
```

### View Employee Dashboard
```bash
TOKEN="abc123xyz..."

curl -X GET http://localhost:8000/api/residence/employee-dashboard/my_assignments/ \
  -H "Authorization: Token $TOKEN"
```

### List Units in Block
```bash
curl -X GET http://localhost:8000/api/residence/units/?block=1 \
  -H "Authorization: Token $TOKEN"
```

### Get Unit Inventory
```bash
curl -X GET http://localhost:8000/api/residence/units/1/inventory/ \
  -H "Authorization: Token $TOKEN"
```

### Mark Item as OK
```bash
curl -X POST http://localhost:8000/api/residence/inventory/1/mark_as_ok/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Add New Item
```bash
curl -X POST http://localhost:8000/api/residence/units/1/add_item/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "part_id": 1,
    "location_id": 5,
    "serial_number": "FRIDGE-NEW-001",
    "notes": "Replacement for damaged unit"
  }'
```

---

## Common Tasks

### Add a New Unit
```bash
# Via API
curl -X POST http://localhost:8000/api/residence/units/ \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "block": 1,
    "unit_number": 105,
    "unit_type": "SHARED_AB",
    "status": "VACANT"
  }'

# Via Admin: http://localhost:8000/admin/residence/unit/add/
```

### Assign Staff to Block
```bash
# Via API
curl -X POST http://localhost:8000/api/residence/staff-assignments/ \
  -H "Authorization: Token $ADMIN_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "staff_member": 2,
    "block": 1
  }'

# Via Admin: http://localhost:8000/admin/residence/staffblockassignment/add/
```

### View Maintenance Logs
```bash
curl -X GET http://localhost:8000/api/residence/maintenance-logs/ \
  -H "Authorization: Token $TOKEN"
```

### Get Admin Dashboard Summary
```bash
curl -X GET http://localhost:8000/api/residence/admin-dashboard/summary/ \
  -H "Authorization: Token $ADMIN_TOKEN"

# Returns:
# {
#   "total_units": 28,
#   "total_inventory_items": 156,
#   "items_needing_repair": 2,
#   "missing_items": 1,
#   "recent_maintenance": [...]
# }
```

---

## File Structure

```
InvenTree/
├── src/backend/InvenTree/
│   ├── residence/
│   │   ├── __init__.py                 # Initialization & setup
│   │   ├── models.py                   # Data models
│   │   ├── views.py                    # API views
│   │   ├── serializers.py              # Data serialization
│   │   ├── urls.py                     # URL routing
│   │   ├── admin.py                    # Django admin
│   │   ├── apps.py                     # App config
│   │   ├── signals.py                  # Event handlers
│   │   └── management/commands/
│   │       └── populate_residence.py   # CSV import script
│   ├── InvenTree/
│   │   ├── settings.py                 # Django settings (add residence app)
│   │   └── urls.py                     # Add residence.urls
│   └── manage.py
├── data/
│   └── residence_inventory.csv         # Your inventory data
├── RESIDENCE_INVENTORY_DESIGN.md       # Domain model documentation
├── SETUP_DEPLOYMENT_GUIDE.md           # Full setup guide
├── IMPLEMENTATION_SUMMARY.md           # System overview
└── QUICK_START.md                      # This file
```

---

## Troubleshooting

### ModuleNotFoundError: No module named 'residence'
- Ensure `residence` folder exists in `src/backend/InvenTree/`
- Add `'residence'` to `INSTALLED_APPS` in settings.py

### Migration fails
```bash
cd src/backend/InvenTree
python manage.py migrate residence zero
python manage.py migrate
```

### CSV import fails
- Check delimiter is `;` (semicolon)
- Verify block numbers match configured houses
- Ensure room format: `101A`, `101B`, or `102` (no spaces)

### Permission denied accessing API
- Ensure user is in `Managers` or `Maintenance Staff` group
- Check staff block assignment exists
- Verify token is valid

### Port 8000 already in use
```bash
python manage.py runserver 8080
```

---

## Next Steps

1. ✅ **Backend running** – Navigate to http://localhost:8000/admin/
2. ⏭️ **Create Employee Dashboard** – Use provided Vue template in `frontend/EmployeeDashboard.vue`
3. ⏭️ **Create Admin Dashboard** – Similar React/Vue component
4. ⏭️ **Mobile App** (optional) – Build React Native interface
5. ⏭️ **Deploy** – Follow `SETUP_DEPLOYMENT_GUIDE.md` for production

---

## Support

**API Documentation**: http://localhost:8000/api/residence/
**Django Admin**: http://localhost:8000/admin/
**InvenTree Docs**: https://docs.inventree.org/
**System Design**: See `RESIDENCE_INVENTORY_DESIGN.md`

