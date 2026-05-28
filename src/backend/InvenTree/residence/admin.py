"""
Django Admin Configuration for Residence Models
"""

from django.contrib import admin
from django.utils.html import format_html
from residence.models import (
    House, Block, Unit, Room, SharedKitchen, ItemCategory, UnitInventorySet, MaintenanceLog, StaffBlockAssignment
)


@admin.register(House)
class HouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'manager', 'block_count', 'created_at']
    list_filter = ['code', 'created_at']
    search_fields = ['name', 'code']
    readonly_fields = ['created_at', 'updated_at']
    
    def block_count(self, obj):
        return obj.blocks.count()
    block_count.short_description = 'Number of Blocks'


@admin.register(Block)
class BlockAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'house', 'block_number', 'unit_count', 'created_at']
    list_filter = ['house', 'created_at']
    search_fields = ['house__name', 'block_number']
    readonly_fields = ['created_at', 'updated_at']
    
    def unit_count(self, obj):
        return obj.units.count()
    unit_count.short_description = 'Units'


@admin.register(Unit)
class UnitAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'block', 'unit_number', 'unit_type', 'status', 'inventory_count', 'created_at']
    list_filter = ['block__house', 'block', 'unit_type', 'status', 'created_at']
    search_fields = ['block__house__name', 'block__block_number', 'unit_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Identification', {
            'fields': ('block', 'unit_number', 'unit_type', 'status')
        }),
        ('Locations', {
            'fields': ('location_a', 'location_b', 'location_kitchen'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def inventory_count(self, obj):
        return obj.inventory_items.count()
    inventory_count.short_description = 'Items'


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ['unit', 'room_type', 'location', 'created_at']
    list_filter = ['unit__block__house', 'unit__block', 'room_type', 'created_at']
    search_fields = ['unit__unit_number', 'room_type']
    readonly_fields = ['created_at']


@admin.register(SharedKitchen)
class SharedKitchenAdmin(admin.ModelAdmin):
    list_display = ['unit', 'location', 'created_at']
    list_filter = ['unit__block__house', 'unit__block', 'created_at']
    search_fields = ['unit__unit_number']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(ItemCategory)
class ItemCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at']
    search_fields = ['name']
    readonly_fields = ['created_at']


@admin.register(UnitInventorySet)
class UnitInventorySetAdmin(admin.ModelAdmin):
    list_display = ['unit', 'part', 'status_badge', 'serial_number', 'location', 'last_checked', 'added_date']
    list_filter = ['unit__block__house', 'unit__block', 'status', 'part__category', 'added_date']
    search_fields = ['unit__unit_number', 'part__name', 'serial_number']
    readonly_fields = ['created_at', 'updated_at', 'added_date']
    fieldsets = (
        ('Item Information', {
            'fields': ('unit', 'part', 'serial_number', 'quantity', 'status', 'location')
        }),
        ('Maintenance', {
            'fields': ('notes', 'last_checked', 'last_checked_by'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('added_date', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def status_badge(self, obj):
        color_map = {
            'OK': 'green',
            'NEEDS_REPAIR': 'orange',
            'MISSING': 'red',
            'REPLACED': 'blue',
        }
        color = color_map.get(obj.status, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'


@admin.register(MaintenanceLog)
class MaintenanceLogAdmin(admin.ModelAdmin):
    list_display = ['timestamp', 'unit', 'action_badge', 'employee', 'inventory_item', 'notes_preview']
    list_filter = ['action', 'timestamp', 'employee', 'unit__block__house']
    search_fields = ['unit__unit_number', 'employee__username', 'notes']
    readonly_fields = ['timestamp']
    date_hierarchy = 'timestamp'
    ordering = ['-timestamp']
    
    def action_badge(self, obj):
        color_map = {
            'ADDED': 'green',
            'MOVED': 'blue',
            'REPAIRED': 'orange',
            'REPLACED': 'purple',
            'REMOVED': 'red',
            'CHECKED': 'gray',
        }
        color = color_map.get(obj.action, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 3px 8px; border-radius: 3px;">{}</span>',
            color,
            obj.get_action_display()
        )
    action_badge.short_description = 'Action'
    
    def notes_preview(self, obj):
        return obj.notes[:50] + '...' if len(obj.notes) > 50 else obj.notes
    notes_preview.short_description = 'Notes'


@admin.register(StaffBlockAssignment)
class StaffBlockAssignmentAdmin(admin.ModelAdmin):
    list_display = ['staff_member', 'block', 'assigned_date']
    list_filter = ['block__house', 'block', 'assigned_date']
    search_fields = ['staff_member__username', 'staff_member__first_name', 'block__house__name']
    readonly_fields = ['assigned_date']
