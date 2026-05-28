"""
REST API Serializers for Residence Inventory System
"""

from rest_framework import serializers
from residence.models import (
    House, Block, Unit, Room, SharedKitchen, UnitInventorySet, MaintenanceLog, StaffBlockAssignment
)
from stock.models import StockLocation, Stock
from part.models import Part
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']


class HouseSerializer(serializers.ModelSerializer):
    manager_name = serializers.CharField(source='manager.get_full_name', read_only=True)
    block_count = serializers.SerializerMethodField()
    
    class Meta:
        model = House
        fields = ['id', 'name', 'code', 'manager', 'manager_name', 'block_count']
    
    def get_block_count(self, obj):
        return obj.blocks.count()


class BlockSerializer(serializers.ModelSerializer):
    house_name = serializers.CharField(source='house.name', read_only=True)
    unit_count = serializers.SerializerMethodField()
    assigned_staff = serializers.SerializerMethodField()
    
    class Meta:
        model = Block
        fields = ['id', 'house', 'house_name', 'block_number', 'location', 'unit_count', 'assigned_staff']
    
    def get_unit_count(self):
        return self.object.units.count()
    
    def get_assigned_staff(self, obj):
        staff = obj.assigned_staff.all()
        return UserSerializer(many=True, read_only=True).to_representation([s.staff_member for s in staff])


class PartSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Part
        fields = ['id', 'name', 'description', 'category', 'category_name']


class RoomSerializer(serializers.ModelSerializer):
    room_type_display = serializers.CharField(source='get_room_type_display', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = Room
        fields = ['id', 'unit', 'room_type', 'room_type_display', 'location', 'location_name']


class SharedKitchenSerializer(serializers.ModelSerializer):
    unit_display = serializers.CharField(source='unit.__str__', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    
    class Meta:
        model = SharedKitchen
        fields = ['id', 'unit', 'unit_display', 'location', 'location_name']


class UnitInventorySetSerializer(serializers.ModelSerializer):
    part_name = serializers.CharField(source='part.name', read_only=True)
    location_name = serializers.CharField(source='location.name', read_only=True)
    last_checked_by_name = serializers.CharField(source='last_checked_by.get_full_name', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = UnitInventorySet
        fields = [
            'id', 'unit', 'part', 'part_name', 'stock', 'location', 'location_name',
            'serial_number', 'quantity', 'status', 'status_display', 'notes',
            'added_date', 'last_checked', 'last_checked_by', 'last_checked_by_name'
        ]


class MaintenanceLogSerializer(serializers.ModelSerializer):
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    employee_name = serializers.CharField(source='employee.get_full_name', read_only=True)
    part_name = serializers.CharField(source='inventory_item.part.name', read_only=True)
    moved_from_name = serializers.CharField(source='moved_from_location.name', read_only=True)
    moved_to_name = serializers.CharField(source='moved_to_location.name', read_only=True)
    
    class Meta:
        model = MaintenanceLog
        fields = [
            'id', 'unit', 'inventory_item', 'part_name', 'action', 'action_display',
            'employee', 'employee_name', 'timestamp', 'notes',
            'moved_from_location', 'moved_from_name', 'moved_to_location', 'moved_to_name'
        ]


class UnitSerializer(serializers.ModelSerializer):
    """Full unit details with inventory and rooms."""
    
    block_display = serializers.CharField(source='block.__str__', read_only=True)
    house_name = serializers.CharField(source='block.house.name', read_only=True)
    unit_type_display = serializers.CharField(source='get_unit_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    location_a_name = serializers.CharField(source='location_a.name', read_only=True)
    location_b_name = serializers.CharField(source='location_b.name', read_only=True)
    location_kitchen_name = serializers.CharField(source='location_kitchen.name', read_only=True)
    
    rooms = RoomSerializer(many=True, read_only=True)
    shared_kitchen = SharedKitchenSerializer(read_only=True)
    inventory_items = UnitInventorySetSerializer(many=True, read_only=True)
    
    class Meta:
        model = Unit
        fields = [
            'id', 'block', 'block_display', 'house_name', 'unit_number', 'unit_type', 'unit_type_display',
            'status', 'status_display', 'location_a', 'location_a_name', 'location_b', 'location_b_name',
            'location_kitchen', 'location_kitchen_name', 'rooms', 'shared_kitchen', 'inventory_items'
        ]


class StaffBlockAssignmentSerializer(serializers.ModelSerializer):
    staff_name = serializers.CharField(source='staff_member.get_full_name', read_only=True)
    block_display = serializers.CharField(source='block.__str__', read_only=True)
    
    class Meta:
        model = StaffBlockAssignment
        fields = ['id', 'staff_member', 'staff_name', 'block', 'block_display', 'assigned_date']


class AdminDashboardSerializer(serializers.Serializer):
    """Summary data for admin dashboard."""
    
    total_units = serializers.IntegerField()
    total_inventory_items = serializers.IntegerField()
    items_needing_repair = serializers.IntegerField()
    missing_items = serializers.IntegerField()
    recent_maintenance = MaintenanceLogSerializer(many=True, read_only=True)


class EmployeeDashboardSerializer(serializers.Serializer):
    """Summary data for employee dashboard."""
    
    assigned_blocks = BlockSerializer(many=True, read_only=True)
    units_in_blocks = UnitSerializer(many=True, read_only=True)
    pending_actions = MaintenanceLogSerializer(many=True, read_only=True)
