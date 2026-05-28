"""
Residence Inventory Management System - Initialization & Setup

This module provides setup utilities for the residence inventory system.
"""

from django.core.management import call_command
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


def setup_user_groups():
    """
    Create user groups and assign permissions for:
    - Managers (full access)
    - Maintenance Staff (limited to assigned blocks)
    """
    
    # Get or create groups
    managers_group, _ = Group.objects.get_or_create(name='Managers')
    staff_group, _ = Group.objects.get_or_create(name='Maintenance Staff')
    
    # Get content types
    from residence.models import Unit, UnitInventorySet, MaintenanceLog, StaffBlockAssignment
    
    unit_ct = ContentType.objects.get_for_model(Unit)
    inventory_ct = ContentType.objects.get_for_model(UnitInventorySet)
    log_ct = ContentType.objects.get_for_model(MaintenanceLog)
    assignment_ct = ContentType.objects.get_for_model(StaffBlockAssignment)
    
    # Manager permissions: full access
    manager_perms = Permission.objects.filter(
        content_type__in=[unit_ct, inventory_ct, log_ct, assignment_ct]
    )
    managers_group.permissions.set(manager_perms)
    
    # Staff permissions: limited view/add/change (see/add/modify their own)
    staff_perms = Permission.objects.filter(
        content_type__in=[unit_ct, inventory_ct, log_ct],
        codename__in=['view_unit', 'add_unit', 'change_unit',
                      'view_unitinventoryset', 'add_unitinventoryset', 'change_unitinventoryset',
                      'view_maintenancelog', 'add_maintenancelog']
    )
    staff_group.permissions.set(staff_perms)
    
    return managers_group, staff_group


def create_initial_parts():
    """Create initial part master data if not exists."""
    from part.models import Part, PartCategory
    
    categories_parts = {
        'Appliances': [
            ('Fridge', 'Refrigerator for single or shared kitchen'),
            ('Microwave', 'Microwave oven'),
            ('Snappy Chef', 'Compact electric cooking device'),
        ],
        'Heating': [
            ('Panel Heater', 'Wall-mounted electric panel heater'),
        ],
        'Furniture': [
            ('Bed Frame', 'Single bed frame'),
            ('Mattress', 'Single mattress'),
        ],
        'Maintenance & Spares': [
            ('Oven Burner', 'Replacement oven burner'),
            ('Door Handle', 'Generic door handle'),
        ],
    }
    
    for category_name, parts in categories_parts.items():
        part_cat, _ = PartCategory.objects.get_or_create(
            name=category_name,
            defaults={'description': f'{category_name} items'}
        )
        
        for part_name, description in parts:
            Part.objects.get_or_create(
                name=part_name,
                defaults={
                    'description': description,
                    'category': part_cat,
                    'purchaseable': True,
                    'trackable': True,
                }
            )


def initialize_residence_system():
    """
    Full initialization routine:
    1. Create user groups and permissions
    2. Create initial parts master data
    """
    print('Initializing Residence Inventory System...')
    
    try:
        setup_user_groups()
        print('✓ User groups and permissions created')
    except Exception as e:
        print(f'✗ Error creating user groups: {e}')
    
    try:
        create_initial_parts()
        print('✓ Initial parts master data created')
    except Exception as e:
        print(f'✗ Error creating parts: {e}')
    
    print('✓ Residence system initialized')
