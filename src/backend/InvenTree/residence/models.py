"""
Residence Inventory Management Models

Extends InvenTree with custom models for residence accommodation:
- House, Block, Unit, Room, SharedKitchen
- MaintenanceLog for audit trail
"""

from django.db import models
from django.contrib.auth.models import User
from stock.models import StockLocation, Stock
from part.models import Part


class House(models.Model):
    """Represents a house in the residence complex (e.g., Saxenhof, Mostertsdrift)."""
    
    HOUSE_CHOICES = [
        ('SH', 'Saxenhof'),
        ('MD', 'Mostertsdrift'),
        ('BD', 'Boschendal'),
        ('WV', 'Weltevreden'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=10, choices=HOUSE_CHOICES, unique=True)
    manager = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='managed_houses')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
        verbose_name_plural = "Houses"
    
    def __str__(self):
        return f"{self.name} ({self.code})"


class Block(models.Model):
    """Represents a block (building) within a house."""
    
    house = models.ForeignKey(House, on_delete=models.CASCADE, related_name='blocks')
    block_number = models.IntegerField()
    
    # Reference to InvenTree Stock Location (STRUCTURAL)
    location = models.OneToOneField(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='block'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('house', 'block_number')
        ordering = ['house', 'block_number']
    
    def __str__(self):
        return f"{self.house.code} Block {self.block_number}"


class Unit(models.Model):
    """
    Represents a unit within a block.
    
    Unit types:
    - SINGLE: One person, one bedroom, one kitchenette
    - SHARED_AB: Two bedrooms (A & B) sharing one kitchen
    """
    
    UNIT_TYPE_CHOICES = [
        ('SINGLE', 'Single Unit'),
        ('SHARED_AB', 'Shared Unit (A & B)'),
    ]
    
    STATUS_CHOICES = [
        ('OCCUPIED', 'Occupied'),
        ('VACANT', 'Vacant'),
        ('MAINTENANCE', 'Under Maintenance'),
    ]
    
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='units')
    unit_number = models.IntegerField()  # e.g., 101, 305
    unit_type = models.CharField(max_length=20, choices=UNIT_TYPE_CHOICES, default='SINGLE')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='VACANT')
    
    # InvenTree Stock Locations
    # For SINGLE units: location_a is the only location; location_b and location_kitchen are NULL
    # For SHARED_AB units: location_a (room A), location_b (room B), location_kitchen (shared kitchen)
    location_a = models.OneToOneField(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unit_location_a'
    )
    location_b = models.OneToOneField(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unit_location_b'
    )
    location_kitchen = models.OneToOneField(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='unit_location_kitchen'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('block', 'unit_number')
        ordering = ['block', 'unit_number']
    
    def __str__(self):
        suffix = "A/B" if self.unit_type == 'SHARED_AB' else ""
        return f"{self.block} Unit {self.unit_number}{suffix}"
    
    def get_all_locations(self):
        """Return all active locations for this unit."""
        locations = [self.location_a]
        if self.unit_type == 'SHARED_AB':
            locations.extend([self.location_b, self.location_kitchen])
        return [loc for loc in locations if loc]


class Room(models.Model):
    """
    Represents a room (bedroom) within a unit.
    For SINGLE units, there's one Room.
    For SHARED_AB units, there are two Rooms (A and B).
    """
    
    ROOM_TYPE_CHOICES = [
        ('BEDROOM_A', 'Bedroom A'),
        ('BEDROOM_B', 'Bedroom B'),
        ('SINGLE_BEDROOM', 'Single Bedroom'),
    ]
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='rooms')
    room_type = models.CharField(max_length=20, choices=ROOM_TYPE_CHOICES)
    location = models.OneToOneField(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='room'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['unit', 'room_type']
    
    def __str__(self):
        return f"{self.unit} - {self.get_room_type_display()}"


class SharedKitchen(models.Model):
    """
    Represents a shared kitchen within a SHARED_AB unit.
    Only applicable to SHARED_AB units.
    """
    
    unit = models.OneToOneField(Unit, on_delete=models.CASCADE, related_name='shared_kitchen')
    location = models.OneToOneField(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='shared_kitchen'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Shared Kitchens"
    
    def __str__(self):
        return f"Shared Kitchen - {self.unit}"


class ItemCategory(models.Model):
    """
    Custom categorization of items in the residence.
    E.g., Appliances, Heating, Furniture, Maintenance & Spares
    """
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural = "Item Categories"
        ordering = ['name']
    
    def __str__(self):
        return self.name


class UnitInventorySet(models.Model):
    """
    Custom tracking for inventory items assigned to units.
    Links Unit -> StockLocation -> Stock -> Part
    """
    
    STATUS_CHOICES = [
        ('OK', 'OK'),
        ('NEEDS_REPAIR', 'Needs Repair'),
        ('MISSING', 'Missing'),
        ('REPLACED', 'Replaced'),
    ]
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='inventory_items')
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='unit_inventory')
    stock = models.ForeignKey(Stock, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Which location within the unit (A, B, or Kitchen)
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        related_name='unit_inventory_items'
    )
    
    serial_number = models.CharField(max_length=100, blank=True, null=True)
    quantity = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='OK')
    
    notes = models.TextField(blank=True)
    added_date = models.DateTimeField(auto_now_add=True)
    last_checked = models.DateTimeField(auto_now=True)
    last_checked_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='checked_inventory_items'
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('unit', 'part', 'location', 'serial_number')
        ordering = ['-added_date']
    
    def __str__(self):
        return f"{self.unit} - {self.part.name} ({self.status})"


class MaintenanceLog(models.Model):
    """
    Audit trail for all maintenance actions on inventory items.
    """
    
    ACTION_CHOICES = [
        ('ADDED', 'Item Added'),
        ('MOVED', 'Item Moved'),
        ('REPAIRED', 'Item Repaired'),
        ('REPLACED', 'Item Replaced'),
        ('REMOVED', 'Item Removed'),
        ('CHECKED', 'Item Checked'),
    ]
    
    unit = models.ForeignKey(Unit, on_delete=models.CASCADE, related_name='maintenance_logs')
    inventory_item = models.ForeignKey(
        UnitInventorySet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs'
    )
    
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    employee = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='maintenance_actions'
    )
    
    timestamp = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    # Optional: track movement details
    moved_from_location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs_from'
    )
    moved_to_location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='maintenance_logs_to'
    )
    
    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['employee']),
            models.Index(fields=['unit']),
        ]
    
    def __str__(self):
        return f"{self.get_action_display()} - {self.unit} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"


class StaffBlockAssignment(models.Model):
    """
    Maps maintenance staff to blocks they're responsible for.
    A staff member can be assigned to multiple blocks.
    """
    
    staff_member = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='assigned_blocks'
    )
    block = models.ForeignKey(Block, on_delete=models.CASCADE, related_name='assigned_staff')
    assigned_date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('staff_member', 'block')
        ordering = ['staff_member', 'block']
    
    def __str__(self):
        return f"{self.staff_member.username} - {self.block}"
