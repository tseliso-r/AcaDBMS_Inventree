"""
Data Population Script

Parses the CSV inventory file and populates InvenTree with:
1. Stock Locations (hierarchical: House -> Block -> Unit/Room/Kitchen)
2. Part Master data (Appliances, Heating, Furniture)
3. Stock records (inventory instances)
4. Custom residence models
"""

import csv
import os
from django.core.management.base import BaseCommand
from django.utils import timezone

from stock.models import StockLocation, Stock
from part.models import Part, PartCategory
from residence.models import House, Block, Unit, Room, SharedKitchen, ItemCategory, UnitInventorySet


class Command(BaseCommand):
    help = 'Populate residence inventory from CSV file'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--csv-file',
            type=str,
            default='attendance/data/residence_inventory.csv',
            help='Path to CSV file'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before populating'
        )
    
    def handle(self, *args, **options):
        csv_file = options['csv_file']
        
        if not os.path.exists(csv_file):
            self.stdout.write(self.style.ERROR(f'CSV file not found: {csv_file}'))
            return
        
        if options['clear']:
            self.clear_data()
        
        # Step 1: Create houses
        self.create_houses()
        
        # Step 2: Create item categories and parts
        self.create_parts()
        
        # Step 3: Parse CSV and create locations, blocks, units
        self.populate_from_csv(csv_file)
        
        self.stdout.write(self.style.SUCCESS('✓ Data population complete!'))
    
    def clear_data(self):
        """Clear all custom residence data (caution: destructive)."""
        self.stdout.write('Clearing existing data...')
        House.objects.all().delete()
        Block.objects.all().delete()
        Unit.objects.all().delete()
        Room.objects.all().delete()
        SharedKitchen.objects.all().delete()
        UnitInventorySet.objects.all().delete()
        self.stdout.write('✓ Data cleared')
    
    def create_houses(self):
        """Create the four main houses."""
        houses_data = [
            {'name': 'Saxenhof', 'code': 'SH', 'blocks': [1, 2, 3, 4, 5, 6, 7, 23]},
            {'name': 'Mostertsdrift', 'code': 'MD', 'blocks': [8, 9, 10, 11, 12, 24, 27]},
            {'name': 'Boschendal', 'code': 'BD', 'blocks': [18, 19, 20, 21, 22, 25, 28]},
            {'name': 'Weltevreden', 'code': 'WV', 'blocks': [13, 14, 15, 16, 17, 26]},
        ]
        
        self.stdout.write('Creating houses and blocks...')
        
        for house_data in houses_data:
            house, created = House.objects.get_or_create(
                name=house_data['name'],
                defaults={'code': house_data['code']}
            )
            
            if created:
                self.stdout.write(f'  ✓ Created house: {house.name}')
            
            # Create STRUCTURAL location for house
            house_location, _ = StockLocation.objects.get_or_create(
                name=f'{house.code}-House',
                defaults={
                    'description': f'{house.name} House',
                    'structural': True,
                }
            )
            
            # Create blocks
            for block_num in house_data['blocks']:
                block, created = Block.objects.get_or_create(
                    house=house,
                    block_number=block_num
                )
                
                # Create STRUCTURAL location for block
                block_location, _ = StockLocation.objects.get_or_create(
                    name=f'{house.code}-Block{block_num}',
                    defaults={
                        'description': f'{house.name} Block {block_num}',
                        'parent': house_location,
                        'structural': True,
                    }
                )
                block.location = block_location
                block.save()
                
                if created:
                    self.stdout.write(f'    ✓ Created block: {block}')
    
    def create_parts(self):
        """Create item categories and part master data."""
        self.stdout.write('Creating item categories and parts...')
        
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
            # Create PartCategory (InvenTree)
            part_cat, _ = PartCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'{category_name} items'}
            )
            
            # Create ItemCategory (custom)
            item_cat, _ = ItemCategory.objects.get_or_create(
                name=category_name,
                defaults={'description': f'{category_name} items'}
            )
            
            # Create parts
            for part_name, description in parts:
                part, created = Part.objects.get_or_create(
                    name=part_name,
                    defaults={
                        'description': description,
                        'category': part_cat,
                        'purchaseable': True,
                        'trackable': True,
                    }
                )
                if created:
                    self.stdout.write(f'  ✓ Created part: {part_name}')
    
    def populate_from_csv(self, csv_file):
        """Parse CSV and create units and inventory."""
        self.stdout.write(f'Parsing CSV: {csv_file}')
        
        # Map block number to house
        block_to_house = {}
        for house in House.objects.all():
            for block in house.blocks.all():
                block_to_house[block.block_number] = house
        
        # Parse CSV
        units_dict = {}  # Key: (block, unit_base), Value: {'A': row, 'B': row}
        
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            for row in reader:
                block_num = int(row['BLOCK'])
                room = row['ROOM'].strip()
                
                # Separate unit number and suffix (A/B)
                if room.endswith('A') or room.endswith('B'):
                    unit_num = int(room[:-1])
                    suffix = room[-1]
                else:
                    unit_num = int(room)
                    suffix = None
                
                key = (block_num, unit_num)
                if key not in units_dict:
                    units_dict[key] = {}
                
                if suffix:
                    units_dict[key][suffix] = row
                else:
                    units_dict[key][None] = row
        
        # Create units and inventory
        self.stdout.write('Creating units and inventory...')
        
        for (block_num, unit_num), room_rows in sorted(units_dict.items()):
            house = block_to_house.get(block_num)
            if not house:
                self.stdout.write(self.style.WARNING(f'  ⚠ House not found for block {block_num}'))
                continue
            
            block = Block.objects.get(house=house, block_number=block_num)
            
            # Determine unit type
            is_shared = 'A' in room_rows and 'B' in room_rows
            unit_type = 'SHARED_AB' if is_shared else 'SINGLE'
            
            # Create unit
            unit, created = Unit.objects.get_or_create(
                block=block,
                unit_number=unit_num,
                defaults={'unit_type': unit_type}
            )
            
            if created:
                self.stdout.write(f'  ✓ Created {unit_type} unit: {unit}')
            
            # Create locations and rooms
            if is_shared:
                self._create_shared_unit_locations(unit, block)
            else:
                self._create_single_unit_location(unit, block)
            
            # Add inventory based on CSV
            self._add_inventory_from_rows(unit, room_rows)
    
    def _create_single_unit_location(self, unit, block):
        """Create location for a single unit."""
        location_name = f'{block.house.code}B{block.block_number}U{unit.unit_number}'
        
        location, created = StockLocation.objects.get_or_create(
            name=location_name,
            defaults={
                'description': f'{block.house.name} Block {block.block_number} Unit {unit.unit_number}',
                'parent': block.location,
                'structural': False,
            }
        )
        
        unit.location_a = location
        unit.save()
        
        if created:
            self.stdout.write(f'    ✓ Created location: {location_name}')
        
        # Create Room
        Room.objects.get_or_create(
            unit=unit,
            room_type='SINGLE_BEDROOM',
            defaults={'location': location}
        )
    
    def _create_shared_unit_locations(self, unit, block):
        """Create locations for a shared (A/B) unit."""
        base_name = f'{block.house.code}B{block.block_number}U{unit.unit_number}'
        
        # Room A
        location_a, created_a = StockLocation.objects.get_or_create(
            name=f'{base_name}A',
            defaults={
                'description': f'{block.house.name} Block {block.block_number} Unit {unit.unit_number} - Room A',
                'parent': block.location,
                'structural': False,
            }
        )
        unit.location_a = location_a
        
        if created_a:
            self.stdout.write(f'    ✓ Created location: {base_name}A')
        
        # Room B
        location_b, created_b = StockLocation.objects.get_or_create(
            name=f'{base_name}B',
            defaults={
                'description': f'{block.house.name} Block {block.block_number} Unit {unit.unit_number} - Room B',
                'parent': block.location,
                'structural': False,
            }
        )
        unit.location_b = location_b
        
        if created_b:
            self.stdout.write(f'    ✓ Created location: {base_name}B')
        
        # Shared Kitchen
        location_k, created_k = StockLocation.objects.get_or_create(
            name=f'{base_name}K',
            defaults={
                'description': f'{block.house.name} Block {block.block_number} Unit {unit.unit_number} - Shared Kitchen',
                'parent': block.location,
                'structural': False,
            }
        )
        unit.location_kitchen = location_k
        
        if created_k:
            self.stdout.write(f'    ✓ Created location: {base_name}K')
        
        unit.save()
        
        # Create Rooms
        Room.objects.get_or_create(
            unit=unit,
            room_type='BEDROOM_A',
            defaults={'location': location_a}
        )
        Room.objects.get_or_create(
            unit=unit,
            room_type='BEDROOM_B',
            defaults={'location': location_b}
        )
        
        # Create SharedKitchen
        SharedKitchen.objects.get_or_create(
            unit=unit,
            defaults={'location': location_k}
        )
    
    def _add_inventory_from_rows(self, unit, room_rows):
        """Add inventory items based on CSV rows."""
        # Map CSV column to part and location(s)
        # For shared units: FRIDGE, MICRO, SNAPPY go to kitchen; HEATER, BED, MATTRESS per room
        # For single units: all items go to the single location
        
        item_mapping = {
            'FRIDGE': {'part_name': 'Fridge', 'location_type': 'kitchen'},
            'MICRO': {'part_name': 'Microwave', 'location_type': 'kitchen'},
            'SNAPPY': {'part_name': 'Snappy Chef', 'location_type': 'kitchen'},
            'HEATER': {'part_name': 'Panel Heater', 'location_type': 'room'},
            'BED': {'part_name': 'Bed Frame', 'location_type': 'room'},
            'MATTRESS': {'part_name': 'Mattress', 'location_type': 'room'},
        }
        
        # Get parts
        parts = {}
        for csv_col, mapping in item_mapping.items():
            try:
                parts[csv_col] = Part.objects.get(name=mapping['part_name'])
            except Part.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  ⚠ Part not found: {mapping["part_name"]}'))
                continue
        
        # Process each room (single unit has None key, shared has A and B)
        for suffix, row in room_rows.items():
            if not row:
                continue
            
            # Determine location(s) for this room
            if unit.unit_type == 'SINGLE':
                locations_for_room = {'bedroom': unit.location_a, 'kitchen': unit.location_a}
            else:
                if suffix == 'A':
                    locations_for_room = {
                        'bedroom': unit.location_a,
                        'kitchen': unit.location_kitchen,
                    }
                elif suffix == 'B':
                    locations_for_room = {
                        'bedroom': unit.location_b,
                        'kitchen': unit.location_kitchen,
                    }
                else:
                    continue
            
            # Add items
            for csv_col, mapping in item_mapping.items():
                if csv_col not in parts:
                    continue
                
                if row.get(csv_col, '').strip() == '1':
                    location_type = mapping['location_type']
                    if location_type == 'kitchen':
                        location = locations_for_room['kitchen']
                    else:
                        location = locations_for_room['bedroom']
                    
                    # For shared kitchen, only add once (check if already exists)
                    if location_type == 'kitchen' and unit.unit_type == 'SHARED_AB':
                        existing = UnitInventorySet.objects.filter(
                            unit=unit,
                            part=parts[csv_col],
                            location=location
                        ).exists()
                        if existing:
                            continue
                    
                    # Create or get Stock record
                    stock, _ = Stock.objects.get_or_create(
                        part=parts[csv_col],
                        location=location,
                        defaults={
                            'quantity': 1,
                        }
                    )
                    
                    # Create UnitInventorySet
                    inventory, created = UnitInventorySet.objects.get_or_create(
                        unit=unit,
                        part=parts[csv_col],
                        location=location,
                        defaults={
                            'stock': stock,
                            'quantity': 1,
                            'status': 'OK',
                        }
                    )
                    
                    if created:
                        self.stdout.write(f'      ✓ Added {parts[csv_col].name} to {unit}')
