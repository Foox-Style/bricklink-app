import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bricklink_api import BrickLinkAPI
from bsx_handler import BSXHandler
from location_matcher import LocationMatcher
import json

def test_full_workflow():
    print("=== Testing Full Workflow ===\n")
    
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
    
    # Test with real file
    original_file = "C:/Users/mikev/Desktop/Import 25082401.bsx"
    
    print("1. Loading BSX file...")
    bsx_handler = BSXHandler()
    success, message = bsx_handler.load_bsx_file(original_file)
    
    if not success:
        print(f"Failed: {message}")
        return
    
    print(f"[OK] {message}")
    
    # Check items without locations
    items_without_locations = bsx_handler.get_items_without_locations()
    print(f"Items without locations: {len(items_without_locations)}")
    
    if len(items_without_locations) > 0:
        print(f"First few items needing locations:")
        for i, item in enumerate(items_without_locations[:5]):
            print(f"  {i+1}. {item.item_name} ({item.item_id})")
    
    print(f"\n2. Creating location matcher and loading inventory...")
    location_matcher = LocationMatcher(api)
    success, message = location_matcher.load_inventory_locations()
    
    if not success:
        print(f"Failed: {message}")
        return
    
    print(f"[OK] {message}")
    
    print(f"\n3. Processing items (preview mode)...")
    success, results = location_matcher.process_bsx_file(bsx_handler, preview_only=True)
    
    if success:
        print(f"[SUCCESS] Processing complete!")
        print(f"  Items processed: {results['total_items_processed']}")
        print(f"  Locations assigned: {results['locations_assigned']}")
        print(f"  No matches found: {results['no_location_found']}")
        print(f"  Success rate: {results['success_rate']}%")
        
        if results['assignment_details']:
            print(f"\nFirst 5 assignments:")
            for i, detail in enumerate(results['assignment_details'][:5]):
                print(f"  {i+1}. {detail['item_name']} -> '{detail['assigned_location']}'")
        
        if results['success_rate'] > 0:
            print(f"\n4. Applying changes and saving...")
            # Apply changes for real
            success, results = location_matcher.process_bsx_file(bsx_handler, preview_only=False)
            
            if success:
                # Save file
                output_file = "C:/Users/mikev/Desktop/BL App/test_full_output.bsx"
                success, save_msg = bsx_handler.save_bsx_file(output_file)
                
                if success:
                    print(f"[OK] {save_msg}")
                    print(f"\n5. Verifying saved file structure...")
                    
                    # Load the saved file to verify
                    verify_handler = BSXHandler()
                    success, verify_msg = verify_handler.load_bsx_file(output_file)
                    
                    if success:
                        print(f"[OK] Saved file loads correctly: {verify_msg}")
                        
                        # Check if locations were saved
                        items_with_locations = verify_handler.get_items_with_locations()
                        print(f"Items with locations in saved file: {len(items_with_locations)}")
                        
                        if len(items_with_locations) > 0:
                            print("First few items with locations:")
                            for i, item in enumerate(items_with_locations[:3]):
                                print(f"  {i+1}. {item.item_name} -> '{item.remarks}'")
                        
                    else:
                        print(f"[ERROR] Saved file verification failed: {verify_msg}")
                else:
                    print(f"[ERROR] Save failed: {save_msg}")
        else:
            print("No matches found - nothing to save")
    else:
        print(f"[ERROR] Processing failed: {results}")

if __name__ == "__main__":
    test_full_workflow()