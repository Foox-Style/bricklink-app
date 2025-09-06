import logging
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict
import time

from bricklink_api import BrickLinkAPI
from bsx_handler import BSXHandler, BSXItem


@dataclass
class BuildableMinifigure:
    """Represents a minifigure that can be built from current inventory"""
    minifig_id: str
    minifig_name: str
    max_buildable_quantity: int
    required_parts: List[Dict]
    available_parts: Dict[str, int]  # part_key -> available_quantity
    limiting_part: Dict  # The part that limits how many can be built


class MinifigureAnalyzer:
    """Analyzes inventory to find buildable minifigures"""
    
    def __init__(self, api: BrickLinkAPI):
        self.api = api
        self.logger = logging.getLogger(__name__)
        self.inventory_items = []
        self.inventory_by_part = defaultdict(dict)  # item_id -> color_id -> total_quantity
        
    def load_inventory(self) -> Tuple[bool, str]:
        """Load and index current inventory for fast lookups"""
        try:
            self.logger.info("Loading inventory for minifigure analysis...")
            success, items = self.api.get_inventory()
            
            if not success:
                return False, f"Failed to load inventory: {items}"
            
            self.inventory_items = items
            self.inventory_by_part = defaultdict(dict)
            
            # Index inventory by item_id and color_id for fast lookups
            for item in items:
                item_info = item.get('item', {})
                item_id = item_info.get('no', '')
                color_id = str(item_info.get('color_id', '0'))
                quantity = item.get('quantity', 0)
                
                # Only index parts (not sets, minifigures, etc.)
                if item_info.get('type') == 'PART':
                    if color_id in self.inventory_by_part[item_id]:
                        self.inventory_by_part[item_id][color_id] += quantity
                    else:
                        self.inventory_by_part[item_id][color_id] = quantity
            
            total_parts = sum(len(colors) for colors in self.inventory_by_part.values())
            self.logger.info(f"Indexed {total_parts} unique part/color combinations")
            return True, f"Loaded {len(items)} inventory items, indexed {total_parts} part/color combinations"
            
        except Exception as e:
            self.logger.error(f"Error loading inventory: {e}")
            return False, f"Error loading inventory: {e}"
    
    def find_torsos_in_inventory(self) -> List[Tuple[str, str]]:
        """Find all torso parts in current inventory
        
        Returns:
            List of (item_id, color_id) tuples for torsos
        """
        torsos = []
        
        # Common torso part numbers - this is a simplified list
        # In a full implementation, you might want to query BrickLink for all torso parts
        common_torso_ids = [
            '973', '973pb', '973c01', '973c02', '973c03', '973c04', '973c05',
            '973c06', '973c07', '973c08', '973c09', '973c10'
        ]
        
        for item_id in self.inventory_by_part:
            # Check if this looks like a torso (simplified check)
            if (item_id.startswith('973') or 
                'torso' in item_id.lower() or
                any(torso_id in item_id for torso_id in common_torso_ids)):
                
                for color_id in self.inventory_by_part[item_id]:
                    torsos.append((item_id, color_id))
        
        self.logger.info(f"Found {len(torsos)} torso parts in inventory")
        return torsos
    
    def find_minifigures_with_torso(self, torso_id: str, color_id: str) -> Tuple[bool, List[Dict]]:
        """Find all minifigures that use a specific torso
        
        NOTE: BrickLink's superset API doesn't seem to link parts directly to minifigures,
        only to sets. This method currently returns empty results because the superset 
        data only contains SETS that include the torso, not individual MINIFIGURES.
        
        This is a known limitation of the BrickLink API structure.
        
        Args:
            torso_id: The torso part ID
            color_id: The color ID of the torso
            
        Returns:
            Tuple of (success, empty list) - API limitation
        """
        try:
            self.logger.info(f"Searching for minifigures with torso: {torso_id}")
            
            # Don't filter by color initially as BrickLink seems to have issues with color_id=0
            success, supersets = self.api.get_superset_items('P', torso_id, None)
            
            if success:
                self.logger.info(f"API returned {len(supersets)} supersets for torso {torso_id}")
                
                # Check what types we get back
                types_found = {}
                all_entries = []
                for superset in supersets:
                    for entry in superset.get('entries', []):
                        all_entries.append(entry)
                        item_type = entry.get('item', {}).get('type', 'UNKNOWN')
                        types_found[item_type] = types_found.get(item_type, 0) + 1
                
                self.logger.info(f"Superset entry types found: {types_found}")
                
                # Look for minifigures in the entries
                minifigures = []
                for superset in supersets:
                    superset_color = superset.get('color_id', 0)
                    for entry in superset.get('entries', []):
                        item = entry.get('item', {})
                        if item.get('type') == 'MINIFIG':
                            minifigures.append({
                                'item': item,
                                'torso_color_id': superset_color,  # Color of the torso in this context
                                'quantity': entry.get('quantity', 1)
                            })
                
                self.logger.info(f"Found {len(minifigures)} minifigures using torso {torso_id}")
                if minifigures:
                    for i, minifig in enumerate(minifigures[:5]):  # Show first 5
                        name = minifig['item'].get('name', 'Unknown')
                        minifig_id = minifig['item'].get('no', 'Unknown ID')
                        torso_color = minifig.get('torso_color_id', 'Unknown')
                        self.logger.info(f"  Minifig {i+1}: {name} (ID: {minifig_id}, torso color: {torso_color})")
                
                return True, minifigures
            else:
                self.logger.warning(f"API call failed for torso {torso_id}: {supersets}")
                return False, []
            
        except Exception as e:
            self.logger.error(f"Error finding minifigures with torso {torso_id}/{color_id}: {e}")
            return False, []
    
    def get_minifigure_parts(self, minifig_id: str) -> Tuple[bool, List[Dict]]:
        """Get the complete parts list for a minifigure
        
        Args:
            minifig_id: The minifigure ID
            
        Returns:
            Tuple of (success, list of required parts)
        """
        try:
            success, subsets = self.api.get_item_subsets('M', minifig_id)
            
            if not success:
                return False, []
            
            # Extract the parts from the subset data
            parts = []
            for subset in subsets:
                subset_entries = subset.get('entries', [])
                for entry in subset_entries:
                    part_data = {
                        'item_id': entry.get('item', {}).get('no', ''),
                        'color_id': str(entry.get('color_id', '0')),
                        'quantity': entry.get('quantity', 1),
                        'item_type': entry.get('item', {}).get('type', 'PART'),
                        'item_name': entry.get('item', {}).get('name', 'Unknown')
                    }
                    parts.append(part_data)
            
            return True, parts
            
        except Exception as e:
            self.logger.error(f"Error getting parts for minifigure {minifig_id}: {e}")
            return False, []
    
    def find_available_quantity(self, item_id: str, required_color_id: str) -> int:
        """Find available quantity for a part with reasonable color matching
        
        Args:
            item_id: The part ID
            required_color_id: The required color ID
            
        Returns:
            Available quantity (0 if not found)
        """
        if item_id not in self.inventory_by_part:
            return 0
        
        available_colors = self.inventory_by_part[item_id]
        
        # Try exact color match first
        if required_color_id in available_colors:
            return available_colors[required_color_id]
        
        # Fallback for color "0" (no color/any color) - can use any available color
        if required_color_id == "0" and available_colors:
            # For "no color" parts, any color should work
            return max(available_colors.values())
        
        # Limited fallback: if we have color "0" and need a specific color
        # This handles decorated parts that might be listed as color 0 in inventory
        if "0" in available_colors:
            self.logger.debug(f"Using color 0 fallback for part {item_id} (required color {required_color_id})")
            return available_colors["0"]
        
        # No match found
        return 0

    def check_minifigure_buildability(self, minifig_id: str, minifig_name: str) -> Optional[BuildableMinifigure]:
        """Check if a minifigure can be built and how many
        
        Args:
            minifig_id: The minifigure ID
            minifig_name: The minifigure name
            
        Returns:
            BuildableMinifigure if buildable, None if not buildable
        """
        try:
            # Get required parts for this minifigure
            success, required_parts = self.get_minifigure_parts(minifig_id)
            
            if not success or not required_parts:
                return None
            
            available_parts = {}
            max_buildable = float('inf')
            limiting_part = None
            
            # Check availability of each required part
            for part in required_parts:
                item_id = part['item_id']
                color_id = part['color_id']
                required_qty = part['quantity']
                part_key = f"{item_id}_{color_id}"
                
                # Use strict color matching
                available_qty = self.find_available_quantity(item_id, color_id)
                available_parts[part_key] = available_qty
                
                if available_qty == 0:
                    # Missing part - can't build any
                    # Show what colors we DO have for this part to help debugging
                    if item_id in self.inventory_by_part:
                        available_colors = list(self.inventory_by_part[item_id].keys())
                        self.logger.debug(f"Missing part for {minifig_name}: {part['item_name']} ({item_id}) - need color {color_id}, have colors {available_colors}")
                    else:
                        self.logger.debug(f"Missing part for {minifig_name}: {part['item_name']} ({item_id}) - part not in inventory at all")
                    return None
                
                # Calculate how many complete minifigures this part allows
                possible_builds = available_qty // required_qty
                
                if possible_builds < max_buildable:
                    max_buildable = possible_builds
                    limiting_part = part
            
            if max_buildable == 0 or max_buildable == float('inf'):
                return None
            
            return BuildableMinifigure(
                minifig_id=minifig_id,
                minifig_name=minifig_name,
                max_buildable_quantity=int(max_buildable),
                required_parts=required_parts,
                available_parts=available_parts,
                limiting_part=limiting_part
            )
            
        except Exception as e:
            self.logger.error(f"Error checking buildability for {minifig_id}: {e}")
            return None
    
    def analyze_buildable_minifigures(self, progress_callback=None) -> Tuple[bool, Dict]:
        """Analyze inventory to find all buildable minifigures
        
        Args:
            progress_callback: Optional callback function for progress updates
            
        Returns:
            Tuple of (success, results dict)
        """
        try:
            self.logger.info("Starting buildable minifigures analysis...")
            
            # Load inventory first
            if progress_callback:
                progress_callback("Loading inventory...")
            
            success, message = self.load_inventory()
            if not success:
                return False, {"error": message}
            
            # Find torsos in inventory
            if progress_callback:
                progress_callback("Finding torsos in inventory...")
            
            torsos = self.find_torsos_in_inventory()
            if not torsos:
                return True, {
                    "buildable_minifigures": [],
                    "total_checked": 0,
                    "summary": "No torso parts found in inventory"
                }
            
            buildable_minifigures = []
            total_minifigures_checked = 0
            processed_minifigs = set()  # Avoid duplicates
            
            # Process each torso
            for i, (torso_id, color_id) in enumerate(torsos):
                if progress_callback:
                    progress_callback(f"Processing torso {i+1}/{len(torsos)}: {torso_id} (color {color_id})")
                
                # Find minifigures using this torso
                success, minifigures = self.find_minifigures_with_torso(torso_id, color_id)
                
                if not success:
                    continue
                
                # Check buildability for each minifigure
                for minifig in minifigures:
                    minifig_info = minifig.get('item', {})
                    minifig_id = minifig_info.get('no', '')
                    minifig_name = minifig_info.get('name', 'Unknown Minifigure')
                    
                    # Skip if already processed
                    if minifig_id in processed_minifigs:
                        continue
                    
                    processed_minifigs.add(minifig_id)
                    total_minifigures_checked += 1
                    
                    if progress_callback:
                        progress_callback(f"Checking buildability: {minifig_name}")
                    
                    buildable = self.check_minifigure_buildability(minifig_id, minifig_name)
                    
                    if buildable:
                        buildable_minifigures.append(buildable)
                        self.logger.info(f"Found buildable: {minifig_name} (can build {buildable.max_buildable_quantity})")
                    
                    # Small delay to respect rate limits
                    time.sleep(0.1)
            
            results = {
                "buildable_minifigures": buildable_minifigures,
                "total_torsos_processed": len(torsos),
                "total_minifigures_checked": total_minifigures_checked,
                "buildable_count": len(buildable_minifigures),
                "summary": f"Found {len(buildable_minifigures)} buildable minifigures from {total_minifigures_checked} checked"
            }
            
            self.logger.info(f"Analysis complete: {results['summary']}")
            return True, results
            
        except Exception as e:
            self.logger.error(f"Error in minifigure analysis: {e}")
            return False, {"error": f"Analysis failed: {e}"}
    
    def create_minifigures_bsx(self, buildable_minifigures: List[BuildableMinifigure], output_filename: str = None) -> Tuple[bool, str]:
        """Create a BSX file with buildable minifigures
        
        Args:
            buildable_minifigures: List of buildable minifigures
            output_filename: Optional output filename
            
        Returns:
            Tuple of (success, message/filename)
        """
        try:
            if not buildable_minifigures:
                return False, "No buildable minifigures to export"
            
            # Create BSX handler and build XML structure
            bsx_handler = BSXHandler()
            
            # Create the XML root structure
            from xml.etree.ElementTree import Element, SubElement
            
            root = Element("BrickStoreXML")
            inventory = SubElement(root, "Inventory")
            
            for minifig in buildable_minifigures:
                item_elem = SubElement(inventory, "Item")
                
                # Create minifigure entry (ItemTypeID = "M")
                SubElement(item_elem, "ItemID").text = minifig.minifig_id
                SubElement(item_elem, "ItemTypeID").text = "M"
                SubElement(item_elem, "ColorID").text = "0"  # Minifigures typically don't have color variants
                SubElement(item_elem, "ColorName").text = "Not Applicable"
                SubElement(item_elem, "CategoryID").text = "273"  # Minifigure category
                SubElement(item_elem, "CategoryName").text = "Minifigures"
                SubElement(item_elem, "ItemName").text = minifig.minifig_name
                SubElement(item_elem, "Qty").text = str(minifig.max_buildable_quantity)
                SubElement(item_elem, "Price").text = "0.00"
                SubElement(item_elem, "Condition").text = "N"
                
                # Add remarks with limiting part info
                limiting_part_info = f"Limited by: {minifig.limiting_part.get('item_name', 'Unknown')} ({minifig.limiting_part.get('item_id', '')})"
                SubElement(item_elem, "Remarks").text = limiting_part_info
            
            # Set up BSX handler with our created structure
            bsx_handler.root = root
            bsx_handler.items = []  # We're creating minifigures, not parsing existing items
            
            # Generate filename if not provided
            if not output_filename:
                from datetime import datetime
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_filename = f"buildable_minifigures_{timestamp}.bsx"
            
            # Save the file
            success, message = bsx_handler.save_bsx_file(output_filename)
            
            if success:
                return True, output_filename
            else:
                return False, f"Failed to save BSX file: {message}"
            
        except Exception as e:
            self.logger.error(f"Error creating minifigures BSX: {e}")
            return False, f"Error creating BSX file: {e}"


# Test function
def test_minifigure_analyzer():
    """Test function for the minifigure analyzer"""
    import json
    import os
    
    # Load config
    if not os.path.exists('config.json'):
        print("config.json not found. Please create it with your BrickLink API credentials.")
        return
    
    with open('config.json', 'r') as f:
        config = json.load(f)
    
    credentials = config['api_credentials']
    
    if credentials['consumer_key'] == 'YOUR_CONSUMER_KEY':
        print("Please fill in your API credentials in config.json first!")
        return
    
    # Create API client
    api = BrickLinkAPI(
        credentials['consumer_key'],
        credentials['consumer_secret'],
        credentials['token'],
        credentials['token_secret']
    )
    
    # Test connection
    success, message = api.test_connection()
    if not success:
        print(f"API connection failed: {message}")
        return
    
    print(f"API connected: {message}")
    
    # Create analyzer and run test
    analyzer = MinifigureAnalyzer(api)
    
    def progress_callback(status):
        print(f"Progress: {status}")
    
    print("\nStarting minifigure analysis...")
    success, results = analyzer.analyze_buildable_minifigures(progress_callback)
    
    if success:
        print(f"\nAnalysis Results:")
        print(f"- Torsos processed: {results.get('total_torsos_processed', 0)}")
        print(f"- Minifigures checked: {results.get('total_minifigures_checked', 0)}")
        print(f"- Buildable minifigures: {results.get('buildable_count', 0)}")
        
        buildable = results.get('buildable_minifigures', [])
        if buildable:
            print(f"\nBuildable Minifigures:")
            for minifig in buildable[:5]:  # Show first 5
                limiting_part = minifig.limiting_part
                print(f"- {minifig.minifig_name} (can build {minifig.max_buildable_quantity})")
                print(f"  Limited by: {limiting_part.get('item_name', 'Unknown')}")
            
            # Test BSX creation
            print(f"\nCreating BSX file...")
            success, filename = analyzer.create_minifigures_bsx(buildable)
            if success:
                print(f"BSX file created: {filename}")
            else:
                print(f"Failed to create BSX file: {filename}")
    else:
        print(f"Analysis failed: {results.get('error', 'Unknown error')}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    test_minifigure_analyzer()