from typing import Dict, List, Tuple, Optional
from collections import Counter
import logging
from bsx_handler import BSXHandler, BSXItem
from bricklink_api import BrickLinkAPI

class LocationMatcher:
    """Matches BSX items with existing inventory locations from BrickLink"""
    
    def __init__(self, api: BrickLinkAPI):
        self.api = api
        self.logger = logging.getLogger(__name__)
        self.inventory_locations = {}  # item_id -> list of locations with counts
        self.inventory_loaded = False
    
    def _get_location_priority(self, location: str) -> int:
        """Get priority for location based on leading character. R=0 (highest), S=1, others=2 (lowest)"""
        if not location:
            return 2
        first_char = location[0].upper()
        if first_char == 'R':
            return 0
        elif first_char == 'S':
            return 1
        else:
            return 2
    
    def load_inventory_locations(self) -> Tuple[bool, str]:
        """Load and process inventory data from BrickLink API"""
        try:
            self.logger.info("Fetching inventory from BrickLink...")
            success, inventory_data = self.api.get_inventory()
            
            if not success:
                return False, f"Failed to fetch inventory: {inventory_data}"
            
            # Process inventory to extract location data
            self.inventory_locations = {}
            
            for item in inventory_data:
                item_info = item.get('item', {})
                item_id = item_info.get('no', '')  # BrickLink uses 'no' for item ID
                remarks = item.get('remarks', '').strip()
                
                if item_id and remarks:
                    if item_id not in self.inventory_locations:
                        self.inventory_locations[item_id] = []
                    
                    # Store location with quantity (for frequency analysis)
                    quantity = item.get('quantity', 1)
                    self.inventory_locations[item_id].append({
                        'location': remarks,
                        'quantity': quantity,
                        'condition': item.get('condition', 'N'),
                        'color_id': item_info.get('color_id', '0')
                    })
            
            self.inventory_loaded = True
            
            total_items = len(inventory_data)
            items_with_locations = len(self.inventory_locations)
            
            self.logger.info(f"Processed {total_items} inventory items")
            self.logger.info(f"Found {items_with_locations} unique item IDs with locations")
            
            return True, f"Loaded locations for {items_with_locations} unique items from {total_items} inventory entries"
            
        except Exception as e:
            return False, f"Error loading inventory: {e}"
    
    def find_best_location_for_item(self, bsx_item: BSXItem) -> Optional[str]:
        """Find the best storage location for a BSX item based on color-aware logic with R -> S -> Remainder prioritization"""
        if not self.inventory_loaded:
            return None
        
        item_id = bsx_item.item_id
        item_color_id = str(bsx_item.color_id) if hasattr(bsx_item, 'color_id') else '0'
        
        if item_id not in self.inventory_locations:
            return None
        
        locations = self.inventory_locations[item_id]
        
        if not locations:
            return None
        
        # Analyze existing locations for this item
        location_analysis = {}
        
        for entry in locations:
            location = entry['location']
            entry_color_id = str(entry['color_id'])
            quantity = entry['quantity']
            
            if location not in location_analysis:
                location_analysis[location] = {
                    'colors': set(),
                    'total_quantity': 0,
                    'color_quantities': {}
                }
            
            location_analysis[location]['colors'].add(entry_color_id)
            location_analysis[location]['total_quantity'] += quantity
            location_analysis[location]['color_quantities'][entry_color_id] = location_analysis[location]['color_quantities'].get(entry_color_id, 0) + quantity
        
        # Apply color-based location assignment logic
        
        # Step 1: Check if a dedicated location exists for this color
        for location, analysis in location_analysis.items():
            if len(analysis['colors']) == 1 and item_color_id in analysis['colors']:
                self.logger.debug(f"Item {item_id} color {item_color_id}: Found dedicated color location '{location}'")
                return location
        
        # Step 2: Check if only one location exists for this item
        if len(location_analysis) == 1:
            location = list(location_analysis.keys())[0]
            self.logger.debug(f"Item {item_id} color {item_color_id}: Only one location exists '{location}', assigning there")
            return location
        
        # Step 3: Check if multiple single-color locations exist
        single_color_locations = []
        mixed_color_locations = []
        
        for location, analysis in location_analysis.items():
            if len(analysis['colors']) == 1:
                single_color_locations.append((location, analysis['total_quantity']))
            else:
                mixed_color_locations.append((location, analysis['total_quantity']))
        
        # If we have multiple single-color locations, prioritize R -> S -> others, then by quantity
        if len(single_color_locations) >= 2:
            single_color_locations.sort(key=lambda x: (self._get_location_priority(x[0]), x[1]))  # Sort by priority first, then quantity
            best_location = single_color_locations[0][0]
            self.logger.debug(f"Item {item_id} color {item_color_id}: Multiple single-color locations found, assigning to priority location '{best_location}'")
            return best_location
        
        # Step 4: If dedicated color location exists for different color, assign to mixed location
        dedicated_locations_exist = len(single_color_locations) > 0
        if dedicated_locations_exist and mixed_color_locations:
            # Prioritize R -> S -> others, then by quantity (descending)
            mixed_color_locations.sort(key=lambda x: (self._get_location_priority(x[0]), -x[1]))  # Priority first, then quantity descending
            best_location = mixed_color_locations[0][0]
            self.logger.debug(f"Item {item_id} color {item_color_id}: Dedicated locations exist for other colors, assigning to priority mixed location '{best_location}'")
            return best_location
        
        # Step 5: Fallback to most frequently used location with R -> S -> others priority
        location_counts = Counter()
        
        for entry in locations:
            location = entry['location']
            quantity = entry['quantity']
            location_counts[location] += quantity
        
        # Sort by priority first, then by quantity descending
        sorted_locations = sorted(location_counts.items(), key=lambda x: (self._get_location_priority(x[0]), -x[1]))
        if sorted_locations:
            best_location = sorted_locations[0][0]
            self.logger.debug(f"Item {item_id} color {item_color_id}: Fallback to priority location '{best_location}'")
            return best_location
        
        return None
    
    def process_bsx_file(self, bsx_handler: BSXHandler, preview_only: bool = False) -> Tuple[bool, Dict]:
        """Process all items in a BSX file and assign locations"""
        if not self.inventory_loaded:
            return False, {"error": "Inventory not loaded. Call load_inventory_locations() first."}
        
        items_without_locations = bsx_handler.get_items_without_locations()
        
        results = {
            'total_items_processed': len(items_without_locations),
            'locations_assigned': 0,
            'no_location_found': 0,
            'assignment_details': [],
            'items_without_matches': []
        }
        
        for item in items_without_locations:
            best_location = self.find_best_location_for_item(item)
            
            if best_location:
                assignment_info = {
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'color_name': item.color_name,
                    'condition': item.condition,
                    'quantity': item.qty,
                    'assigned_location': best_location
                }
                
                if not preview_only:
                    # Actually update the item
                    success = bsx_handler.update_item_location(item, best_location)
                    if success:
                        results['locations_assigned'] += 1
                        results['assignment_details'].append(assignment_info)
                    else:
                        self.logger.error(f"Failed to update location for item {item.item_id}")
                else:
                    # Preview mode - just record what would be done
                    results['locations_assigned'] += 1
                    results['assignment_details'].append(assignment_info)
            else:
                # No location found
                no_match_info = {
                    'item_id': item.item_id,
                    'item_name': item.item_name,
                    'color_name': item.color_name,
                    'condition': item.condition,
                    'quantity': item.qty
                }
                
                results['no_location_found'] += 1
                results['items_without_matches'].append(no_match_info)
        
        success_rate = (results['locations_assigned'] / results['total_items_processed'] * 100) if results['total_items_processed'] > 0 else 0
        results['success_rate'] = round(success_rate, 1)
        
        return True, results
    
    def get_location_statistics(self) -> Dict:
        """Get statistics about the loaded inventory locations"""
        if not self.inventory_loaded:
            return {"error": "Inventory not loaded"}
        
        total_unique_items = len(self.inventory_locations)
        all_locations = []
        
        for item_id, locations in self.inventory_locations.items():
            for entry in locations:
                all_locations.append(entry['location'])
        
        location_frequency = Counter(all_locations)
        
        return {
            'unique_items_with_locations': total_unique_items,
            'total_location_entries': len(all_locations),
            'unique_locations': len(location_frequency),
            'most_used_locations': dict(location_frequency.most_common(10)),
            'sample_items': dict(list(self.inventory_locations.items())[:5])  # Show first 5 for debugging
        }

def main():
    """Test the location matcher"""
    import json
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    # Load API credentials
    if not os.path.exists('config.json'):
        print("Error: config.json not found. Please run the API test first.")
        return
    
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
    
    # Create location matcher
    matcher = LocationMatcher(api)
    
    print("=== Testing Location Matcher ===\n")
    
    # Load inventory
    print("Loading inventory locations...")
    success, message = matcher.load_inventory_locations()
    if not success:
        print(f"Failed to load inventory: {message}")
        return
    
    print(f"[OK] {message}\n")
    
    # Show statistics
    stats = matcher.get_location_statistics()
    print("Location Statistics:")
    print(f"- Items with locations: {stats['unique_items_with_locations']}")
    print(f"- Total location entries: {stats['total_location_entries']}")
    print(f"- Unique storage locations: {stats['unique_locations']}")
    print(f"\nMost used locations:")
    for location, count in list(stats['most_used_locations'].items())[:5]:
        print(f"  '{location}': {count} items")
    
    # Test with sample BSX file
    if os.path.exists('sample_inventory.bsx'):
        print(f"\n--- Testing with Sample BSX File ---")
        
        bsx_handler = BSXHandler()
        success, message = bsx_handler.load_bsx_file('sample_inventory.bsx')
        
        if success:
            print(f"[OK] Loaded BSX file: {message}")
            
            # Preview mode first
            success, results = matcher.process_bsx_file(bsx_handler, preview_only=True)
            
            if success:
                print(f"\nPreview Results:")
                print(f"- Items to process: {results['total_items_processed']}")
                print(f"- Locations that would be assigned: {results['locations_assigned']}")
                print(f"- Items without matches: {results['no_location_found']}")
                print(f"- Success rate: {results['success_rate']}%")
                
                if results['assignment_details']:
                    print(f"\nWould assign locations:")
                    for detail in results['assignment_details']:
                        print(f"  {detail['item_name']} -> '{detail['assigned_location']}'")
                
                if results['items_without_matches']:
                    print(f"\nItems without matches:")
                    for item in results['items_without_matches']:
                        print(f"  {item['item_name']} ({item['item_id']})")
            
        else:
            print(f"Failed to load BSX file: {message}")
    else:
        print("\nNo sample BSX file found. Run bsx_handler.py first to create one.")

if __name__ == "__main__":
    main()