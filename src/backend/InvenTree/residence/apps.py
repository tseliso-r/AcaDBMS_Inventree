"""
Django App Configuration for Residence Inventory System
"""

from django.apps import AppConfig


class ResidenceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'residence'
    verbose_name = 'Residence Inventory Management'
    
    def ready(self):
        """Initialize app signals and setup."""
        import residence.signals  # noqa
