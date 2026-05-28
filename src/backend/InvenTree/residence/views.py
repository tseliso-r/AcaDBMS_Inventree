"""
REST API Views for Residence Inventory System

Provides endpoints for both admins and maintenance staff.
Implements role-based access control and audit logging.
"""

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.db.models import Q, Count
from django_filters.rest_framework import DjangoFilterBackend

from residence.models import (
    House, Block, Unit, UnitInventorySet, MaintenanceLog, StaffBlockAssignment, Room, SharedKitchen
)
from residence.serializers import (
    HouseSerializer, BlockSerializer, UnitSerializer, UnitInventorySetSerializer,
    MaintenanceLogSerializer, StaffBlockAssignmentSerializer, PartSerializer, AdminDashboardSerializer
)
from part.models import Part


class IsManagerOrReadOnly(IsAuthenticated):
    """Permission class: Managers can edit, staff can view assigned blocks only."""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return True
    
    def is_manager(self, request):
        return request.user.groups.filter(name='Managers').exists() or request.user.is_staff


class IsStaffOrManager(IsAuthenticated):
    """Permission class: Staff and managers can access; staff limited to assigned blocks."""
    
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.groups.filter(name__in=['Managers', 'Maintenance Staff']).exists()


def get_staff_assigned_blocks(user):
    """Get all blocks assigned to a staff member."""
    assignments = StaffBlockAssignment.objects.filter(staff_member=user)
    return [a.block for a in assignments]


class HouseViewSet(viewsets.ReadOnlyModelViewSet):
    """Admin-only view of houses."""
    
    queryset = House.objects.all()
    serializer_class = HouseSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Managers see all houses; staff see houses with their assigned blocks
        if self.request.user.groups.filter(name='Managers').exists():
            return House.objects.all()
        
        # For staff: find houses containing their blocks
        assigned_blocks = get_staff_assigned_blocks(self.request.user)
        house_ids = set(block.house_id for block in assigned_blocks)
        return House.objects.filter(id__in=house_ids)


class BlockViewSet(viewsets.ReadOnlyModelViewSet):
    """View of blocks, with staff limited to assigned blocks."""
    
    queryset = Block.objects.all()
    serializer_class = BlockSerializer
    permission_classes = [IsStaffOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['house', 'block_number']
    search_fields = ['house__name', 'block_number']
    
    def get_queryset(self):
        # Managers see all blocks; staff see only assigned blocks
        if self.request.user.groups.filter(name='Managers').exists():
            return Block.objects.all()
        
        assigned_blocks = get_staff_assigned_blocks(self.request.user)
        return Block.objects.filter(id__in=[b.id for b in assigned_blocks])


class UnitViewSet(viewsets.ModelViewSet):
    """CRUD operations on units (create, read, update, delete)."""
    
    queryset = Unit.objects.all()
    serializer_class = UnitSerializer
    permission_classes = [IsStaffOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['block', 'unit_type', 'status']
    search_fields = ['block__house__name', 'block__block_number', 'unit_number']
    
    def get_queryset(self):
        # Managers see all units; staff see only units in assigned blocks
        if self.request.user.groups.filter(name='Managers').exists():
            return Unit.objects.all()
        
        assigned_blocks = get_staff_assigned_blocks(self.request.user)
        return Unit.objects.filter(block__in=assigned_blocks)
    
    @action(detail=True, methods=['get'])
    def inventory(self, request, pk=None):
        """Get all inventory items for a unit."""
        unit = self.get_object()
        items = unit.inventory_items.all()
        serializer = UnitInventorySetSerializer(items, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add a new item to a unit."""
        unit = self.get_object()
        
        # Check permission
        if not self._user_can_modify_unit(request.user, unit):
            return Response(
                {'error': 'You do not have permission to modify this unit.'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        part_id = request.data.get('part_id')
        location_id = request.data.get('location_id')
        serial_number = request.data.get('serial_number', '')
        notes = request.data.get('notes', '')
        
        if not part_id or not location_id:
            return Response(
                {'error': 'part_id and location_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            part = Part.objects.get(id=part_id)
            from stock.models import StockLocation
            location = StockLocation.objects.get(id=location_id)
        except (Part.DoesNotExist, StockLocation.DoesNotExist):
            return Response(
                {'error': 'Invalid part or location'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create or update Stock
        from stock.models import Stock
        stock, _ = Stock.objects.get_or_create(
            part=part,
            location=location,
            defaults={'quantity': 1}
        )
        
        # Create UnitInventorySet
        inventory = UnitInventorySet.objects.create(
            unit=unit,
            part=part,
            stock=stock,
            location=location,
            serial_number=serial_number,
            quantity=1,
            status='OK',
            notes=notes,
            last_checked_by=request.user
        )
        
        # Log action
        MaintenanceLog.objects.create(
            unit=unit,
            inventory_item=inventory,
            action='ADDED',
            employee=request.user,
            notes=f'{part.name} added to {location.name}. {notes}'
        )
        
        serializer = UnitInventorySetSerializer(inventory)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'])
    def maintenance_history(self, request, pk=None):
        """Get maintenance history for a unit."""
        unit = self.get_object()
        logs = unit.maintenance_logs.all().order_by('-timestamp')
        
        limit = request.query_params.get('limit', 50)
        try:
            logs = logs[:int(limit)]
        except (ValueError, TypeError):
            pass
        
        serializer = MaintenanceLogSerializer(logs, many=True)
        return Response(serializer.data)
    
    def _user_can_modify_unit(self, user, unit):
        """Check if user has permission to modify this unit."""
        if user.groups.filter(name='Managers').exists():
            return True
        
        assigned_blocks = get_staff_assigned_blocks(user)
        return unit.block in assigned_blocks


class UnitInventorySetViewSet(viewsets.ModelViewSet):
    """CRUD operations on inventory items."""
    
    queryset = UnitInventorySet.objects.all()
    serializer_class = UnitInventorySetSerializer
    permission_classes = [IsStaffOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['unit', 'status', 'location']
    search_fields = ['part__name', 'serial_number']
    
    def get_queryset(self):
        # Managers see all inventory; staff see only items in assigned blocks
        if self.request.user.groups.filter(name='Managers').exists():
            return UnitInventorySet.objects.all()
        
        assigned_blocks = get_staff_assigned_blocks(self.request.user)
        return UnitInventorySet.objects.filter(unit__block__in=assigned_blocks)
    
    @action(detail=True, methods=['post'])
    def mark_as_missing(self, request, pk=None):
        """Mark an item as missing."""
        item = self.get_object()
        
        if not self._user_can_modify_item(request.user, item):
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        item.status = 'MISSING'
        item.save()
        
        MaintenanceLog.objects.create(
            unit=item.unit,
            inventory_item=item,
            action='CHECKED',
            employee=request.user,
            notes=f'{item.part.name} marked as MISSING'
        )
        
        serializer = UnitInventorySetSerializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_as_ok(self, request, pk=None):
        """Mark an item as OK."""
        item = self.get_object()
        
        if not self._user_can_modify_item(request.user, item):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        item.status = 'OK'
        item.last_checked = timezone.now()
        item.last_checked_by = request.user
        item.save()
        
        MaintenanceLog.objects.create(
            unit=item.unit,
            inventory_item=item,
            action='CHECKED',
            employee=request.user,
            notes=f'{item.part.name} checked and OK'
        )
        
        serializer = UnitInventorySetSerializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def mark_for_repair(self, request, pk=None):
        """Mark an item as needing repair."""
        item = self.get_object()
        
        if not self._user_can_modify_item(request.user, item):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        item.status = 'NEEDS_REPAIR'
        notes = request.data.get('notes', 'Needs repair')
        item.notes = notes
        item.save()
        
        MaintenanceLog.objects.create(
            unit=item.unit,
            inventory_item=item,
            action='REPAIRED',
            employee=request.user,
            notes=notes
        )
        
        serializer = UnitInventorySetSerializer(item)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def remove_item(self, request, pk=None):
        """Remove an item from inventory."""
        item = self.get_object()
        
        if not self._user_can_modify_item(request.user, item):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        unit = item.unit
        part_name = item.part.name
        notes = request.data.get('notes', 'Item removed')
        
        MaintenanceLog.objects.create(
            unit=unit,
            inventory_item=item,
            action='REMOVED',
            employee=request.user,
            notes=notes
        )
        
        item.delete()
        
        return Response(
            {'message': f'{part_name} removed from {unit}'},
            status=status.HTTP_204_NO_CONTENT
        )
    
    def _user_can_modify_item(self, user, item):
        """Check if user has permission to modify this item."""
        if user.groups.filter(name='Managers').exists():
            return True
        
        assigned_blocks = get_staff_assigned_blocks(user)
        return item.unit.block in assigned_blocks


class MaintenanceLogViewSet(viewsets.ReadOnlyModelViewSet):
    """Read-only view of maintenance logs."""
    
    queryset = MaintenanceLog.objects.all()
    serializer_class = MaintenanceLogSerializer
    permission_classes = [IsStaffOrManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['unit', 'action', 'employee']
    search_fields = ['unit__unit_number', 'employee__username']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        # Managers see all logs; staff see only logs for their blocks
        if self.request.user.groups.filter(name='Managers').exists():
            return MaintenanceLog.objects.all()
        
        assigned_blocks = get_staff_assigned_blocks(self.request.user)
        return MaintenanceLog.objects.filter(unit__block__in=assigned_blocks)


class StaffBlockAssignmentViewSet(viewsets.ModelViewSet):
    """Manage staff-to-block assignments (admin only)."""
    
    queryset = StaffBlockAssignment.objects.all()
    serializer_class = StaffBlockAssignmentSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # Only managers can view/edit assignments
        if self.request.user.groups.filter(name='Managers').exists():
            return StaffBlockAssignment.objects.all()
        return StaffBlockAssignment.objects.none()


class AdminDashboardViewSet(viewsets.ViewSet):
    """Admin dashboard with summary statistics."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get dashboard summary for admins."""
        if not request.user.groups.filter(name='Managers').exists():
            return Response({'error': 'Admin access only'}, status=status.HTTP_403_FORBIDDEN)
        
        total_units = Unit.objects.count()
        total_items = UnitInventorySet.objects.count()
        items_needing_repair = UnitInventorySet.objects.filter(status='NEEDS_REPAIR').count()
        missing_items = UnitInventorySet.objects.filter(status='MISSING').count()
        
        recent_logs = MaintenanceLog.objects.all().order_by('-timestamp')[:10]
        
        data = {
            'total_units': total_units,
            'total_inventory_items': total_items,
            'items_needing_repair': items_needing_repair,
            'missing_items': missing_items,
            'recent_maintenance': MaintenanceLogSerializer(recent_logs, many=True).data
        }
        
        return Response(data)


class EmployeeDashboardViewSet(viewsets.ViewSet):
    """Employee dashboard with simplified view of assigned blocks."""
    
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def my_assignments(self, request):
        """Get blocks and units assigned to current staff member."""
        assigned_blocks = get_staff_assigned_blocks(request.user)
        units = Unit.objects.filter(block__in=assigned_blocks)
        
        data = {
            'assigned_blocks': BlockSerializer(assigned_blocks, many=True).data,
            'units': UnitSerializer(units, many=True).data,
            'total_units': units.count(),
        }
        
        return Response(data)
