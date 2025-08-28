import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bricklink_api import BrickLinkAPI
import json

def test_inventory():
    print("=== Testing Inventory Fetch ===\n")
    
    # Load credentials
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
    
    print("Fetching inventory summary...")
    success, summary = api.get_inventory_summary()
    
    if success:
        print("[SUCCESS] Inventory fetched!")
        print(f"Total items: {summary['total_items']}")
        print(f"Items with locations: {summary['items_with_locations']}")
        print(f"Items without locations: {summary['items_without_locations']}")
        print(f"Unique storage locations: {summary['unique_locations']}")
        
        print("\nItems by type:")
        for item_type, count in summary['items_by_type'].items():
            print(f"  {item_type}: {count}")
            
        if summary['top_locations']:
            print("\nTop 5 storage locations:")
            for location, count in list(summary['top_locations'].items())[:5]:
                if location.strip():  # Only show non-empty locations
                    print(f"  '{location}': {count} items")
    else:
        print(f"[FAILED] {summary}")

if __name__ == "__main__":
    test_inventory()