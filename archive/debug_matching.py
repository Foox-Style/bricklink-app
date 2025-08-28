import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bricklink_api import BrickLinkAPI
from bsx_handler import BSXHandler
import json

def debug_item_matching():
    print("=== DEBUG: Item ID Matching ===\n")
    
    # Load API credentials
    with open('config.json', 'r') as f:
        config = json.load(f)
    credentials = config['api_credentials']
    
    # Create API client
    api = BrickLinkAPI(
        credentials['consumer_key'],
        credentials['consumer_secret'],
        credentials['token'],
        credentials['token_secret']
    )
    
    print("1. Fetching BrickLink inventory sample...")
    success, inventory_data = api.get_inventory()
    
    if success:
        # Show first few inventory items to see structure
        print(f"Total inventory items: {len(inventory_data)}")
        print("\nFirst 3 inventory items structure:")
        for i, item in enumerate(inventory_data[:3]):
            print(f"\n--- Item {i+1} ---")
            print(f"Full item data: {json.dumps(item, indent=2)}")
            
            # Extract key fields
            item_info = item.get('item', {})
            item_id = item_info.get('no', '')  # This is what we're using
            remarks = item.get('remarks', '').strip()
            
            print(f"Extracted Item ID: '{item_id}'")
            print(f"Extracted Remarks: '{remarks}'")
    
    # Load BSX file (look for any BSX files in directory)
    print(f"\n2. Looking for BSX files...")
    bsx_files = [f for f in os.listdir('.') if f.endswith('.bsx')]
    
    if bsx_files:
        bsx_file = bsx_files[0]  # Use first BSX file found
        print(f"Loading BSX file: {bsx_file}")
        
        bsx_handler = BSXHandler()
        success, message = bsx_handler.load_bsx_file(bsx_file)
        
        if success:
            print(f"BSX loaded: {message}")
            
            # Show first few BSX items
            print(f"\nFirst 5 BSX items:")
            for i, item in enumerate(bsx_handler.items[:5]):
                print(f"\n--- BSX Item {i+1} ---")
                print(f"Item ID: '{item.item_id}'")
                print(f"Item Name: '{item.item_name}'")
                print(f"Color: '{item.color_name}' (ID: {item.color_id})")
                print(f"Type: '{item.item_type}'")
                print(f"Current Remarks: '{item.remarks}'")
            
            # Look for potential matches manually
            print(f"\n3. Manual matching test...")
            print("Looking for BSX items that should match inventory...")
            
            # Get items without locations from BSX
            items_without_locations = bsx_handler.get_items_without_locations()
            print(f"BSX items without locations: {len(items_without_locations)}")
            
            if items_without_locations:
                test_item = items_without_locations[0]
                print(f"\nTesting item: {test_item.item_name} (ID: '{test_item.item_id}')")
                
                # Look for this item in inventory
                matches = []
                for inv_item in inventory_data:
                    inv_item_info = inv_item.get('item', {})
                    inv_item_id = inv_item_info.get('no', '')
                    
                    if inv_item_id == test_item.item_id:
                        matches.append({
                            'item_id': inv_item_id,
                            'remarks': inv_item.get('remarks', ''),
                            'color': inv_item_info.get('color_id', ''),
                            'condition': inv_item.get('condition', '')
                        })
                
                print(f"Found {len(matches)} matches in inventory:")
                for match in matches[:3]:  # Show first 3
                    print(f"  - Remarks: '{match['remarks']}', Color: {match['color']}, Condition: {match['condition']}")
        
    else:
        print("No BSX files found in current directory")

if __name__ == "__main__":
    debug_item_matching()