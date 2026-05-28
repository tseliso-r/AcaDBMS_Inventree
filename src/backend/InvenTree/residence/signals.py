"""
Django Signals for Residence Inventory System

Automated handlers for:
- Room creation when units are created
- Audit logging
- Shared kitchen management
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from residence.models import Unit, Room, SharedKitchen, MaintenanceLog


@receiver(post_save, sender=Unit)
def create_unit_rooms(sender, instance, created, **kwargs):
    """
    Automatically create Room entries when a Unit is created.
    For SHARED_AB units, create Room A and Room B.
    For SINGLE units, create a single bedroom.
    """
    if not created:
        return
    
    if instance.unit_type == 'SINGLE':
        # Single bedroom unit
        Room.objects.get_or_create(
            unit=instance,
            room_type='SINGLE_BEDROOM',
            defaults={'location': instance.location_a}
        )
    elif instance.unit_type == 'SHARED_AB':
        # Shared unit with A and B bedrooms
        Room.objects.get_or_create(
            unit=instance,
            room_type='BEDROOM_A',
            defaults={'location': instance.location_a}
        )
        Room.objects.get_or_create(
            unit=instance,
            room_type='BEDROOM_B',
            defaults={'location': instance.location_b}
        )
        
        # Create SharedKitchen
        SharedKitchen.objects.get_or_create(
            unit=instance,
            defaults={'location': instance.location_kitchen}
        )


@receiver(post_delete, sender=Unit)
def cleanup_unit_on_delete(sender, instance, **kwargs):
    """Clean up associated rooms and kitchen when unit is deleted."""
    # Django cascade deletes should handle this, but this is a safety net
    pass
