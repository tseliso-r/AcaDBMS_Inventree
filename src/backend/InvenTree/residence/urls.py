"""
URL Configuration for Residence Inventory API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from residence import views

router = DefaultRouter()
router.register(r'houses', views.HouseViewSet)
router.register(r'blocks', views.BlockViewSet)
router.register(r'units', views.UnitViewSet)
router.register(r'inventory', views.UnitInventorySetViewSet)
router.register(r'maintenance-logs', views.MaintenanceLogViewSet)
router.register(r'staff-assignments', views.StaffBlockAssignmentViewSet)
router.register(r'admin-dashboard', views.AdminDashboardViewSet, basename='admin-dashboard')
router.register(r'employee-dashboard', views.EmployeeDashboardViewSet, basename='employee-dashboard')

app_name = 'residence'

urlpatterns = [
    path('api/residence/', include(router.urls)),
]
