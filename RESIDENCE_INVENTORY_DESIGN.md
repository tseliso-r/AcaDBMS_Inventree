# Residence Inventory Management System – Design Document

## Overview
This document outlines the domain model and implementation strategy for an inventory management system built on InvenTree for Academia residence accommodation (maintenance department).

---

## Property Structure

### Geographic Hierarchy
```
House (4)
├── Block (Variable per house)
│   ├── Unit (Single or Shared)
│   │   ├── Room A (Shared units only)
│   │   ├── Room B (Shared units only)
│   │   └── SharedKitchen (Shared units only)
```

### Houses
1. **Saxenhof** – Blocks 1, 2, 3, 4, 5, 6, 7, 23
2. **Mostertsdrift** – Blocks 8, 9, 10, 11, 12, 24, 27
3. **Boschendal** – Blocks 18, 19, 20, 21, 22, 25, 28
4. **Weltevreden** – Blocks 13, 14, 15, 16, 17, 26

### Unit Types

#### Single Units
- Example: Block 28, Room 305
- One person occupies both bedroom and kitchenette
- Assets: fridge, microwave, panel heater, bed, mattress

#### Shared Units (A/B)
- Example: Block 5, Unit 101 (Rooms 101A & 101B)
- Two separate bedrooms sharing one kitchen
- **Shared Assets** (kitchen): fridge, microwave, snappy chef
- **Individual Assets** (per room): panel heater, bed, mattress

---

## Data Model – InvenTree Mapping

### Stock Locations Hierarchy
```
Stock Location Hierarchy:
├── [STRUCTURAL] Academia
│   ├── [STRUCTURAL] Saxenhof
│   │   ├── [STRUCTURAL] Block 1
│   │   │   ├── [LEAF] Block1-Unit101A (Room 101A, Single or Shared)
│   │   │   ├── [LEAF] Block1-Unit101B (Room 101B, Shared only)
│   │   │   ├── [LEAF] Block1-Unit101K (Shared Kitchen, if shared unit)
│   │   │   ├── [LEAF] Block1-Unit102 (Room 102, Single)
│   │   │   └── ...
│   │   ├── [STRUCTURAL] Block 2
│   │   │   └── ...
│   ├── [STRUCTURAL] Mostertsdrift
│   │   └── ...
```

**Location Name Convention:**
- Single unit: `BlockX-UnitYYY` (e.g., `Block5-Unit305`)
- Shared room A: `BlockX-UnitYYYA` (e.g., `Block5-Unit101A`)
- Shared room B: `BlockX-UnitYYYB` (e.g., `Block5-Unit101B`)
- Shared kitchen: `BlockX-UnitYYYK` (e.g., `Block5-Unit101K`)

### Part Categories
```
Parts Hierarchy:
├── Appliances
│   ├── Fridge (can be single or multi-unit)
│   ├── Microwave (can be single or multi-unit)
│   ├── Snappy Chef (shared kitchens only)
├── Heating
│   ├── Panel Heater (individual units only)
├── Furniture
│   ├── Bed Frame
│   ├── Mattress
├── Maintenance & Spares
│   ├── Replacement Components (e.g., oven burner)
```

### Stock Items (Inventory Instances)
Each part deployed to a unit gets a `Stock` entry with:
- **Part** – The item type (e.g., Fridge)
- **Location** – Where it's stored (e.g., `Block5-Unit101K` for shared kitchen)
- **Serial Number** – Unique ID for tracked assets (e.g., `FRIDGE-001`)
- **Quantity** – Number of items (typically 1 for appliances/furniture)
- **Status** – `OK`, `Needs Repair`, `Missing`, `Replaced`
- **Custom Fields** – Condition, last maintenance date, notes

---

## Relationships: Custom Model Layer

### Django Custom Models (Wrapper)

#### `House`
```python
- name (Saxenhof, Mostertsdrift, etc.)
- code (SH, MD, BD, WV)
- manager (FK to User/Staff)
```

#### `Block`
```python
- house (FK to House)
- block_number (1-28)
- location (FK to InvenTree StockLocation – STRUCTURAL)
```

#### `Unit`
```python
- block (FK to Block)
- unit_number (e.g., 101, 305)
- unit_type (SINGLE, SHARED_AB)
- location_single_or_a (FK to InvenTree StockLocation – LEAF, single or room A)
- location_b (FK to InvenTree StockLocation – LEAF, room B only if SHARED_AB)
- location_kitchen (FK to InvenTree StockLocation – LEAF, kitchen only if SHARED_AB)
```

#### `UnitInventorySet`
```python
- unit (FK to Unit)
- item (FK to InvenTree Part)
- stock_location (FK to InvenTree StockLocation)
- serial_number (optional, for tracked items)
- quantity (default 1)
- status (OK, Needs Repair, Missing, Replaced)
- added_date
- last_checked
```

#### `MaintenanceLog`
```python
- unit (FK to Unit)
- inventory_item (FK to UnitInventorySet)
- action (ADDED, MOVED, REPAIRED, REPLACED, REMOVED)
- employee (FK to Staff)
- timestamp
- notes
```

---

## Permission Model

### User Groups

#### **Admin / Manager**
- Full access to all units, items, and reports
- Can manage users and assign blocks to staff
- Can run stocktakes and generate reports
- Dashboard: overview of all properties, maintenance history, asset status

#### **Maintenance Staff (6 employees)**
- Assigned to 1–2 blocks
- Can view unit inventory within their assigned blocks
- Can add new items to units
- Can record maintenance actions (repair, replacement, removal)
- Can move items between units (with audit trail)
- Cannot delete or modify master data
- Cannot view other blocks' inventory
- Dashboard: simplified interface showing assigned blocks, pending tasks

---

## Operational Workflows

### 1. **Onboarding / Initial Inventory**
1. Create Stock Location hierarchy (House → Block → Unit/Room/Kitchen)
2. Create Part Master data (Fridge, Microwave, Snappy Chef, Heater, Bed, Mattress)
3. Import CSV data to populate Stock Locations
4. Assign initial inventory (stock records) to each unit location
5. Assign staff members to blocks

### 2. **Daily Maintenance Workflow**
1. Employee logs into the system and sees their assigned blocks
2. Employee selects a unit to inspect
3. Views current inventory for the unit (including shared kitchen if applicable)
4. Can perform actions:
   - **Check item** – Confirm item is present and OK
   - **Mark item as missing** – Flag for investigation
   - **Record repair** – Document maintenance work
   - **Add item** – Add new equipment to unit (e.g., new fridge)
   - **Remove item** – Log item removal or disposal
   - **Move item** – Transfer item between units (e.g., relocate a heater)
5. All actions logged with timestamp, employee name, and notes

### 3. **Monthly / Quarterly Stocktake**
1. Manager initiates stocktake report
2. System generates checklist of all units and their expected inventory
3. Employees verify physical inventory against system records
4. System auto-flags discrepancies
5. Manager reviews and reconciles

### 4. **Repair / Replacement Workflow**
1. Employee reports item as needing repair
2. Manager reviews queue
3. Manager marks item status as `Needs Repair` or schedules replacement
4. Once repaired/replaced, employee confirms and updates status to `OK` or `Replaced`

---

## Technical Architecture

### Backend (InvenTree + Custom Django App)
- **InvenTree Core** – Stock locations, parts, stock tracking, API
- **Custom App** – Units, rooms, kitchens, custom workflows
- **Permissions** – Role-based via groups and API token scoping
- **API** – REST endpoints for admin and employee interfaces

### Frontend

#### Admin Dashboard
- React/Vue-based
- Overview of all properties, units, and inventory
- User/staff management
- Report generation
- Configuration (add units, edit part master)

#### Employee Interface
- Lightweight, mobile-friendly
- Assign to specific blocks
- Simple action buttons: Check, Report Missing, Record Repair, Add Item, Remove Item
- Minimal cognitive load

### Database
- InvenTree's default (Django ORM) – PostgreSQL or SQLite
- Custom tables for Unit, Room, SharedKitchen, MaintenanceLog

---

## CSV Parsing & Data Population

### CSV Structure (from attachment)
```
BLOCK;ROOM;FRIDGE;MICRO;SNAPPY;HEATER;BED;MATTRESS
1;101A;1;1;1;1;1;1
1;101B;;;;1;1;1
...
```

### Interpretation
- `BLOCK` – Block number
- `ROOM` – Unit/Room identifier (with A/B suffix for shared units)
- `FRIDGE` / `MICRO` / `SNAPPY` / `HEATER` / `BED` / `MATTRESS` – Presence indicator (1 = present, blank = not present)

### Population Logic
1. Group rows by (BLOCK, ROOM_BASE) to identify unit type:
   - If two rows exist for (1, 101) with suffixes A and B → SHARED unit
   - If one row for (1, 102) with no suffix → SINGLE unit
2. For each unit:
   - Create Stock Locations (A, B, Kitchen as applicable)
   - Create Stock records for each present item
3. Assign to appropriate house based on block number

---

## Implementation Phases

### Phase 1: Setup & Data Model
- [ ] Create Django custom models (Unit, Room, Block, House, MaintenanceLog)
- [ ] Design and document location hierarchy convention
- [ ] Create data population script

### Phase 2: InvenTree Integration
- [ ] Seed Stock Locations (hierarchical)
- [ ] Seed Part Master data
- [ ] Import CSV to populate initial Stock records
- [ ] Test location and part queries via API

### Phase 3: API Layer
- [ ] Create REST endpoints for employees (list units, view inventory, record actions)
- [ ] Implement permission checking (staff can only see assigned blocks)
- [ ] Create endpoints for admins (full CRUD, reports, user management)

### Phase 4: Frontend
- [ ] Admin dashboard (overview, user management, reports)
- [ ] Employee dashboard (assigned blocks, unit inventory, action buttons)

### Phase 5: Testing & Deployment
- [ ] End-to-end testing
- [ ] Staff training
- [ ] Go-live and monitoring

---

## Key Considerations

1. **Shared Kitchen Logic** – Ensure items in `BlockX-UnitYYYK` are visible to both room A and room B staff without duplication.
2. **Extra Items** – Staff can add items outside the predefined set; the system must allow flexible part assignment.
3. **Audit Trail** – Every action (add, move, repair, remove) must be logged with employee, timestamp, and rationale.
4. **Permissions** – Staff must only see/modify their assigned blocks; prevent accidental cross-block visibility.
5. **Barcode/Serial Integration** – Future: generate barcodes for assets and enable scanning workflows.
6. **Offline Mode** – If field staff don't always have network, consider offline-first or mobile app caching.

