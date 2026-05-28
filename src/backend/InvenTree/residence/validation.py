"""
CSV Validation & Preview Script

Validates the residence inventory CSV before importing:
- Checks structure (headers, delimiters)
- Validates block numbers
- Validates room identifiers
- Shows preview of what will be created
- Reports any issues
"""

import csv
import sys
from pathlib import Path


def validate_csv(csv_file):
    """Validate and preview CSV file."""
    
    if not Path(csv_file).exists():
        print(f"❌ File not found: {csv_file}")
        return False
    
    # Expected headers
    EXPECTED_HEADERS = ['BLOCK', 'ROOM', 'FRIDGE', 'MICRO', 'SNAPPY', 'HEATER', 'BED', 'MATTRESS']
    
    # Block assignments
    BLOCKS_PER_HOUSE = {
        'Saxenhof': [1, 2, 3, 4, 5, 6, 7, 23],
        'Mostertsdrift': [8, 9, 10, 11, 12, 24, 27],
        'Boschendal': [18, 19, 20, 21, 22, 25, 28],
        'Weltevreden': [13, 14, 15, 16, 17, 26],
    }
    
    ALL_BLOCKS = []
    for blocks in BLOCKS_PER_HOUSE.values():
        ALL_BLOCKS.extend(blocks)
    
    print("=" * 80)
    print("CSV VALIDATION REPORT")
    print("=" * 80)
    
    issues = []
    warnings = []
    units_dict = {}
    row_count = 0
    
    try:
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, delimiter=';')
            
            # Validate headers
            if not reader.fieldnames or reader.fieldnames != EXPECTED_HEADERS:
                print(f"❌ Invalid headers: {reader.fieldnames}")
                print(f"   Expected: {EXPECTED_HEADERS}")
                return False
            
            print(f"✓ Headers valid: {', '.join(reader.fieldnames)}\n")
            
            # Validate rows
            for idx, row in enumerate(reader, start=2):  # Start at 2 (skip header)
                row_count += 1
                
                block_str = row['BLOCK'].strip()
                room_str = row['ROOM'].strip()
                
                # Validate BLOCK
                try:
                    block_num = int(block_str)
                    if block_num not in ALL_BLOCKS:
                        issues.append(f"  Line {idx}: Invalid BLOCK {block_num} (not in any house)")
                    else:
                        # Find house
                        for house, blocks in BLOCKS_PER_HOUSE.items():
                            if block_num in blocks:
                                block_house = house
                                break
                except ValueError:
                    issues.append(f"  Line {idx}: BLOCK '{block_str}' is not a number")
                    continue
                
                # Validate ROOM
                if not room_str:
                    issues.append(f"  Line {idx}: ROOM is empty")
                    continue
                
                # Parse room identifier
                if room_str.endswith('A') or room_str.endswith('B'):
                    try:
                        unit_num = int(room_str[:-1])
                        suffix = room_str[-1]
                    except ValueError:
                        issues.append(f"  Line {idx}: ROOM '{room_str}' is invalid (expected format: 101A, 101B, or 101)")
                        continue
                else:
                    try:
                        unit_num = int(room_str)
                        suffix = None
                    except ValueError:
                        issues.append(f"  Line {idx}: ROOM '{room_str}' is not valid")
                        continue
                
                # Track units
                key = (block_num, unit_num)
                if key not in units_dict:
                    units_dict[key] = {}
                
                if suffix:
                    if suffix in units_dict[key]:
                        warnings.append(f"  Line {idx}: Duplicate entry for {block_num}-{room_str}")
                    units_dict[key][suffix] = row
                else:
                    if None in units_dict[key]:
                        warnings.append(f"  Line {idx}: Duplicate entry for {block_num}-{room_str}")
                    units_dict[key][None] = row
                
                # Validate item columns (should be 0 or 1)
                for col in ['FRIDGE', 'MICRO', 'SNAPPY', 'HEATER', 'BED', 'MATTRESS']:
                    val = row[col].strip()
                    if val and val != '1':
                        warnings.append(f"  Line {idx}: {col}='{val}' (expected 1 or empty)")
        
        # Print summary
        print(f"Total rows: {row_count}")
        print(f"Total units: {len(units_dict)}\n")
        
        # Analyze units
        single_units = []
        shared_units = []
        
        for (block_num, unit_num), suffixes in sorted(units_dict.items()):
            if None in suffixes:
                single_units.append((block_num, unit_num))
            elif 'A' in suffixes and 'B' in suffixes:
                shared_units.append((block_num, unit_num))
            else:
                issues.append(f"Inconsistent unit: Block {block_num} Unit {unit_num} has only {list(suffixes.keys())}")
        
        print(f"Single units: {len(single_units)}")
        print(f"Shared units (A/B): {len(shared_units)}")
        print()
        
        # Print issues
        if issues:
            print("⚠️  ISSUES FOUND:")
            for issue in issues:
                print(f"  {issue}")
            print()
        
        # Print warnings
        if warnings:
            print("⚠️  WARNINGS:")
            for warning in warnings[:10]:  # Show first 10
                print(f"  {warning}")
            if len(warnings) > 10:
                print(f"  ... and {len(warnings) - 10} more")
            print()
        
        # Print preview
        print("PREVIEW OF UNITS TO CREATE:")
        print("-" * 80)
        
        # Single units sample
        if single_units:
            print("\nSingle Units (sample - first 5):")
            for block_num, unit_num in single_units[:5]:
                house = next(h for h, b in BLOCKS_PER_HOUSE.items() if block_num in b)
                row = units_dict[(block_num, unit_num)][None]
                items = [col for col in ['FRIDGE', 'MICRO', 'SNAPPY', 'HEATER', 'BED', 'MATTRESS']
                        if row[col].strip() == '1']
                print(f"  {house} Block {block_num} Unit {unit_num}")
                print(f"    Items: {', '.join(items) if items else 'NONE'}")
            if len(single_units) > 5:
                print(f"  ... and {len(single_units) - 5} more")
        
        # Shared units sample
        if shared_units:
            print("\nShared Units (sample - first 5):")
            for block_num, unit_num in shared_units[:5]:
                house = next(h for h, b in BLOCKS_PER_HOUSE.items() if block_num in b)
                row_a = units_dict[(block_num, unit_num)].get('A', {})
                row_b = units_dict[(block_num, unit_num)].get('B', {})
                
                items_a = [col for col in ['HEATER', 'BED', 'MATTRESS']
                          if row_a.get(col, '').strip() == '1']
                items_b = [col for col in ['HEATER', 'BED', 'MATTRESS']
                          if row_b.get(col, '').strip() == '1']
                items_k = [col for col in ['FRIDGE', 'MICRO', 'SNAPPY']
                          if row_a.get(col, '').strip() == '1']
                
                print(f"  {house} Block {block_num} Unit {unit_num} (Shared)")
                print(f"    Room A: {', '.join(items_a) if items_a else 'NONE'}")
                print(f"    Room B: {', '.join(items_b) if items_b else 'NONE'}")
                print(f"    Kitchen: {', '.join(items_k) if items_k else 'NONE'}")
            if len(shared_units) > 5:
                print(f"  ... and {len(shared_units) - 5} more")
        
        print()
        print("=" * 80)
        
        if issues:
            print("❌ VALIDATION FAILED - Fix issues before importing")
            return False
        else:
            print("✅ VALIDATION PASSED - Ready to import")
            return True
    
    except Exception as e:
        print(f"❌ Error reading CSV: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    csv_file = sys.argv[1] if len(sys.argv) > 1 else 'data/residence_inventory.csv'
    
    success = validate_csv(csv_file)
    sys.exit(0 if success else 1)
