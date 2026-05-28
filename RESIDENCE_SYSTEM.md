# Academia Residence Inventory Management System – Complete Documentation

## 🏠 Overview

This is a complete, production-ready inventory management system for Academia student residence accommodation. Built on **InvenTree**, it tracks equipment across 28 blocks organized into 4 houses, supporting both single units and shared (A/B) units with shared kitchens.

**Repository Structure:**
```
InvenTree/
├── src/backend/InvenTree/residence/          # 👈 New residence app
│   ├── models.py                             # Data models
│   ├── views.py                              # API endpoints
│   ├── serializers.py                        # Data serialization
│   ├── urls.py                               # URL routing
│   ├── admin.py                              # Django admin
│   ├── signals.py                            # Event handlers
│   ├── validation.py                         # CSV validation
│   └── management/commands/
│       └── populate_residence.py             # CSV import
├── frontend/
│   └── EmployeeDashboard.vue                 # Example staff UI
├── data/
│   └── residence_inventory.csv               # Your inventory data
├── README.md                                 # Original InvenTree README
├── QUICK_START.md                            # 👈 Start here
├── RESIDENCE_INVENTORY_DESIGN.md             # Domain model
├── SETUP_DEPLOYMENT_GUIDE.md                 # Full setup
└── IMPLEMENTATION_SUMMARY.md                 # System overview
```

---

## 📖 Documentation Index

| Document | Purpose |
|----------|---------|
| **QUICK_START.md** | ⭐ 5-minute setup guide – START HERE |
| **RESIDENCE_INVENTORY_DESIGN.md** | Architecture, domain model, data relationships |
| **SETUP_DEPLOYMENT_GUIDE.md** | Complete installation & production deployment |
| **IMPLEMENTATION_SUMMARY.md** | Workflows, endpoints, extension points |

---

## ✨ Key Highlights

### ✅ Implemented Features
- Complete Django app with 9 custom models
- Full REST API (8 viewsets, 15+ endpoints)
- Role-based access control (Managers vs Staff)
- Automatic Stock Location hierarchy creation
- Flexible inventory item management
- Full audit trail (maintenance logs)
- Vue.js employee dashboard template
- CSV data population script
- Comprehensive documentation & guides

### 📋 Model Capabilities
- **House**: 4 residences (Saxenhof, Mostertsdrift, Boschendal, Weltevreden)
- **Block**: 28 buildings (1-28)
- **Unit**: Single or Shared A/B
- **Room**: Bedroom A, B, or single
- **SharedKitchen**: For shared units
- **UnitInventorySet**: Item tracking with status
- **MaintenanceLog**: Full audit trail
- **StaffBlockAssignment**: Staff-to-block mapping

### 🔌 API Endpoints
- 8 RESTful viewsets
- 15+ specific actions
- Full CRUD operations
- Role-based filtering
- Token authentication
- Comprehensive serializers

### 🎨 Frontend Assets
- Vue.js employee dashboard (650+ lines)
- Responsive design
- Real-time inventory management
- Action buttons (OK, Missing, Repair, Remove)
- Add item form
- Maintenance history view

### 📊 CSV Support
- Automatic format validation
- Smart unit type detection
- Hierarchical location creation
- Batch data population
- CSV validation script

---

## 🚀 Getting Started (3 Steps)

### Step 1: Setup Backend
```bash
cd InvenTree
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt djangorestframework django-filter
python src/backend/InvenTree/manage.py migrate
```

### Step 2: Initialize System
```bash
cd src/backend/InvenTree
python manage.py shell
>>> from residence import initialize_residence_system
>>> initialize_residence_system()
>>> exit()
```

### Step 3: Load Data
```bash
python manage.py populate_residence --csv-file ../../data/residence_inventory.csv
python manage.py runserver
```

**Access System:**
- Admin: http://localhost:8000/admin/
- API: http://localhost:8000/api/residence/

👉 **Detailed guide**: See [QUICK_START.md](QUICK_START.md)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────┐
│  Frontend Dashboards                │
│  (Admin Dashboard + Employee UI)    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  REST API (Django REST Framework)   │
│  - Token Authentication             │
│  - Role-Based Permissions           │
│  - Comprehensive Filtering          │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Django Backend with Residence App  │
│  ├─ 9 Custom Models                 │
│  ├─ 8 ViewSets                      │
│  ├─ Permission Classes              │
│  └─ Signal Handlers                 │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  InvenTree Core                     │
│  ├─ Stock Locations                 │
│  ├─ Parts Master                    │
│  ├─ Stock Management                │
│  └─ Database ORM                    │
└──────────────┬──────────────────────┘
               │
┌──────────────▼──────────────────────┐
│  Database (PostgreSQL/SQLite)       │
└─────────────────────────────────────┘
```

---

## 📊 Data Model Example

### Single Unit (Block 5, Unit 305)
```
Block5-Unit305
├─ Fridge (serial: FRIDGE-001, OK)
├─ Microwave (serial: MW-001, OK)
├─ Panel Heater (serial: HEATER-001, Needs Repair)
├─ Bed Frame (OK)
└─ Mattress (OK)
```

### Shared Unit (Block 5, Unit 101)
```
Block5-Unit101A (Room A)
├─ Panel Heater (serial: HEATER-A-001, OK)
├─ Bed Frame (OK)
└─ Mattress (OK)

Block5-Unit101B (Room B)
├─ Panel Heater (serial: HEATER-B-001, OK)
├─ Bed Frame (OK)
└─ Mattress (OK)

Block5-Unit101K (Shared Kitchen)
├─ Fridge (serial: FRIDGE-101K, OK)
├─ Microwave (serial: MW-101K, OK)
└─ Snappy Chef (serial: SC-101K, Missing)
```

---

## 🔐 Access Control

### Managers (Admin)
- Full access to all houses, blocks, units
- Add/edit/delete operations
- View all staff assignments
- Access admin dashboard
- Generate reports
- Manage users and permissions

### Maintenance Staff (6 employees)
- View only assigned blocks
- View inventory in those blocks
- Mark items (OK, Missing, Needs Repair)
- Add new items flexibly
- Remove items with audit trail
- View maintenance history
- Cannot modify master data or other blocks

---

## 📡 API Examples

### Authenticate
```bash
curl -X POST http://localhost:8000/api-token-auth/ \
  -H "Content-Type: application/json" \
  -d '{"username":"staff1","password":"password123"}'
# Returns: {"token": "abc123..."}
```

### View Dashboard
```bash
TOKEN="abc123..."
curl http://localhost:8000/api/residence/employee-dashboard/my_assignments/ \
  -H "Authorization: Token $TOKEN"
```

### Mark Item as OK
```bash
curl -X POST http://localhost:8000/api/residence/inventory/1/mark_as_ok/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

### Add Item
```bash
curl -X POST http://localhost:8000/api/residence/units/1/add_item/ \
  -H "Authorization: Token $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "part_id": 1,
    "location_id": 5,
    "serial_number": "FRIDGE-NEW",
    "notes": "Replacement unit"
  }'
```

---

## 📋 Workflows

### Daily Maintenance
1. Staff logs in → sees assigned blocks
2. Selects unit → views inventory
3. For each item: marks OK, missing, or repair needed
4. System logs with timestamp, employee, action

### Adding Equipment
1. Staff identifies need (e.g., new heater)
2. Uses "Add Item" form
3. System creates Stock + UnitInventorySet records
4. Audit trail logged automatically

### Monthly Stocktake
1. Manager generates report
2. Staff verify physical vs system records
3. Discrepancies flagged automatically
4. Manager reconciles differences

---

## 🧪 Testing

### Validate CSV
```bash
python src/backend/InvenTree/residence/validation.py \
  data/residence_inventory.csv
```

### Sample API Calls
```bash
# List all units
curl http://localhost:8000/api/residence/units/ -H "Authorization: Token $TOKEN"

# Get unit details with inventory
curl http://localhost:8000/api/residence/units/1/ -H "Authorization: Token $TOKEN"

# View maintenance logs
curl http://localhost:8000/api/residence/maintenance-logs/ -H "Authorization: Token $TOKEN"
```

---

## 🚢 Deployment

### Development
```bash
python manage.py runserver
# Access: http://localhost:8000/
```

### Production (Gunicorn + Nginx)
```bash
# See SETUP_DEPLOYMENT_GUIDE.md for full instructions
pip install gunicorn
gunicorn --workers 4 --bind 127.0.0.1:8000 src.backend.InvenTree.wsgi:application
```

---

## 🛠️ Customization Points

### Add More Item Types
Edit `residence/__init__.py` → `create_initial_parts()`:
```python
'New Category': [
    ('New Item', 'Description'),
]
```

### Add More Houses/Blocks
Edit CSV file with new rows, re-run population script.

### Customize Permissions
Edit `residence/views.py` permission classes to restrict further.

### Add Custom Workflows
Create new viewset actions in `residence/views.py`.

### Extend Frontend
Modify `frontend/EmployeeDashboard.vue` or create new components.

---

## 📚 File Descriptions

### Core Models (`residence/models.py`)
- `House`: 4 residences
- `Block`: Buildings (1-28)
- `Unit`: Single or Shared A/B
- `Room`: Bedrooms
- `SharedKitchen`: Shared spaces
- `ItemCategory`: Custom grouping
- `UnitInventorySet`: Item tracking
- `MaintenanceLog`: Audit trail
- `StaffBlockAssignment`: Staff mapping

### API Views (`residence/views.py`)
- `HouseViewSet`: Read-only houses
- `BlockViewSet`: Blocks with permissions
- `UnitViewSet`: Full CRUD + custom actions
- `UnitInventorySetViewSet`: Item management
- `MaintenanceLogViewSet`: Read-only logs
- `StaffBlockAssignmentViewSet`: Admin-only
- `AdminDashboardViewSet`: Summary stats
- `EmployeeDashboardViewSet`: Staff overview

### Serializers (`residence/serializers.py`)
- Data serialization for all models
- Nested relationships
- Read-only computed fields
- Custom field displays

### Utilities
- `validation.py`: CSV validation before import
- `signals.py`: Auto-create rooms/kitchens
- `admin.py`: Django admin interface
- `populate_residence.py`: CSV import command

---

## ⚙️ Configuration

### Settings to Update (`InvenTree/settings.py`)
```python
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'django_filters',
    'residence',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'PAGE_SIZE': 50,
}
```

### URLs (`InvenTree/urls.py`)
```python
urlpatterns = [
    # ...
    path('', include('residence.urls')),
]
```

---

## 🐛 Common Issues

| Issue | Fix |
|-------|-----|
| ModuleNotFoundError: residence | Add to INSTALLED_APPS |
| Permission denied on API | Check user group & block assignment |
| CSV import fails | Run validation.py to diagnose |
| Location not found | Ensure Stock Locations created first |

---

## 🔮 Future Enhancements

### Phase 2
- QR code scanning
- Mobile app (React Native)
- Email notifications
- Advanced reporting

### Phase 3
- Resident portal
- IoT sensors
- ML predictions
- Multi-property support

### Phase 4
- Computer vision
- Offline mobile mode
- SMS notifications

---

## 📞 Support

- **API Documentation**: http://localhost:8000/api/residence/
- **Django Admin**: http://localhost:8000/admin/
- **Design Document**: RESIDENCE_INVENTORY_DESIGN.md
- **Setup Guide**: SETUP_DEPLOYMENT_GUIDE.md
- **Quick Start**: QUICK_START.md

---

## ✅ Deployment Checklist

- [ ] Read QUICK_START.md
- [ ] Setup virtual environment
- [ ] Install dependencies
- [ ] Add residence to INSTALLED_APPS
- [ ] Run migrations
- [ ] Initialize system
- [ ] Create superuser
- [ ] Validate CSV
- [ ] Load data
- [ ] Create test staff users
- [ ] Test API endpoints
- [ ] Build frontend dashboards
- [ ] Deploy to production
- [ ] Train staff

---

## 🎉 Ready to Deploy

All core functionality is implemented and production-ready. Start with [QUICK_START.md](QUICK_START.md) and follow the documentation. The system can be deployed immediately.

**Questions?** Refer to the comprehensive documentation or check the code comments.

**Let's go!** 🚀

