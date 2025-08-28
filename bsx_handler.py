import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
import os
from dataclasses import dataclass
import logging

@dataclass
class BSXItem:
    """Represents a single item in a BSX file"""
    item_id: str
    item_type: str
    color_id: str
    category_id: str
    color_name: str
    category_name: str
    item_name: str
    qty: int
    price: float
    condition: str
    remarks: str
    
    # XML element reference for modification
    xml_element: ET.Element = None

class BSXHandler:
    """Handler for BSX (BrickStore XML) files"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.root = None
        self.items = []
        self.file_path = None
    
    def load_bsx_file(self, file_path: str) -> Tuple[bool, str]:
        """Load and parse a BSX file"""
        try:
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            if not file_path.lower().endswith(('.bsx', '.xml')):
                return False, "File must be a BSX or XML file"
            
            # Parse the XML
            tree = ET.parse(file_path)
            self.root = tree.getroot()
            self.file_path = file_path
            
            # Validate it's a BrickStore file
            if self.root.tag != 'BrickStoreXML':
                return False, "Not a valid BrickStore XML file"
            
            # Parse all items
            self.items = []
            item_elements = self.root.findall('.//Item')
            
            for item_elem in item_elements:
                try:
                    item = self._parse_item_element(item_elem)
                    if item:
                        self.items.append(item)
                except Exception as e:
                    self.logger.warning(f"Failed to parse item: {e}")
                    continue
            
            self.logger.info(f"Loaded {len(self.items)} items from {file_path}")
            return True, f"Successfully loaded {len(self.items)} items"
            
        except ET.ParseError as e:
            return False, f"XML parsing error: {e}"
        except Exception as e:
            return False, f"Error loading file: {e}"
    
    def _parse_item_element(self, item_elem: ET.Element) -> Optional[BSXItem]:
        """Parse a single Item XML element into a BSXItem - preserve all original elements"""
        try:
            # Get only the essential fields we need for matching
            item_id = self._get_element_text(item_elem, 'ItemID', '')
            item_type = self._get_element_text(item_elem, 'ItemTypeID', 'P')  # Default to Part
            color_id = self._get_element_text(item_elem, 'ColorID', '0')
            category_id = self._get_element_text(item_elem, 'CategoryID', '0')
            
            # Get text content with defaults
            color_name = self._get_element_text(item_elem, 'ColorName', 'Unknown')
            category_name = self._get_element_text(item_elem, 'CategoryName', 'Unknown')
            item_name = self._get_element_text(item_elem, 'ItemName', 'Unknown Item')
            
            # Get numeric values
            qty_text = self._get_element_text(item_elem, 'Qty', '1')
            price_text = self._get_element_text(item_elem, 'Price', '0.00')
            
            try:
                qty = int(qty_text)
            except (ValueError, TypeError):
                qty = 1
                
            try:
                price = float(price_text)
            except (ValueError, TypeError):
                price = 0.0
            
            condition = self._get_element_text(item_elem, 'Condition', 'N')
            remarks = self._get_element_text(item_elem, 'Remarks', '')
            
            # IMPORTANT: Store the original XML element to preserve ALL fields
            # We don't parse every field - we preserve the original structure
            
            return BSXItem(
                item_id=item_id,
                item_type=item_type,
                color_id=color_id,
                category_id=category_id,
                color_name=color_name,
                category_name=category_name,
                item_name=item_name,
                qty=qty,
                price=price,
                condition=condition,
                remarks=remarks,
                xml_element=item_elem  # This preserves ALL original XML structure
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing item element: {e}")
            return None
    
    def _get_element_text(self, parent: ET.Element, tag_name: str, default: str = '') -> str:
        """Safely get text content from an XML element"""
        element = parent.find(tag_name)
        if element is not None and element.text is not None:
            return element.text.strip()
        return default
    
    def get_items_without_locations(self) -> List[BSXItem]:
        """Get all items that don't have location information in remarks"""
        return [item for item in self.items if not item.remarks.strip()]
    
    def get_items_with_locations(self) -> List[BSXItem]:
        """Get all items that have location information in remarks"""
        return [item for item in self.items if item.remarks.strip()]
    
    def update_item_location(self, item: BSXItem, location: str) -> bool:
        """Update an item's location in the remarks field"""
        try:
            if item.xml_element is None:
                return False
            
            # Find or create the Remarks element
            remarks_elem = item.xml_element.find('Remarks')
            if remarks_elem is None:
                remarks_elem = ET.SubElement(item.xml_element, 'Remarks')
            
            # Update the text content
            remarks_elem.text = location
            item.remarks = location
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating item location: {e}")
            return False
    
    def save_bsx_file(self, output_path: str = None, overwrite_original: bool = False) -> Tuple[bool, str]:
        """Save the BSX file with modifications"""
        try:
            if self.root is None:
                return False, "No BSX file loaded"
            
            # Determine output path
            if overwrite_original:
                save_path = self.file_path
            elif output_path:
                save_path = output_path
            else:
                # Generate new filename
                base, ext = os.path.splitext(self.file_path)
                save_path = f"{base}_updated{ext}"
            
            # Create the tree and save
            tree = ET.ElementTree(self.root)
            
            # Pretty print the XML
            self._indent_xml(self.root)
            
            # Write with exact BrickStore-compatible format
            with open(save_path, 'wb') as f:
                f.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
                tree.write(f, encoding='UTF-8', xml_declaration=False)
            
            self.logger.info(f"Saved BSX file to: {save_path}")
            return True, f"File saved successfully to: {save_path}"
            
        except Exception as e:
            return False, f"Error saving file: {e}"
    
    def _indent_xml(self, elem: ET.Element, level: int = 0):
        """Add pretty-print indentation to XML"""
        indent = "\n" + level * "  "
        if len(elem):
            if not elem.text or not elem.text.strip():
                elem.text = indent + "  "
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
            for elem in elem:
                self._indent_xml(elem, level + 1)
            if not elem.tail or not elem.tail.strip():
                elem.tail = indent
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = indent
    
    def get_file_summary(self) -> Dict:
        """Get summary statistics of the loaded BSX file"""
        if not self.items:
            return {}
        
        total_items = len(self.items)
        items_with_locations = len(self.get_items_with_locations())
        items_without_locations = len(self.get_items_without_locations())
        
        # Count by item type
        type_counts = {}
        condition_counts = {}
        
        for item in self.items:
            # Item type counts
            type_name = self._get_item_type_name(item.item_type)
            type_counts[type_name] = type_counts.get(type_name, 0) + item.qty
            
            # Condition counts
            condition_counts[item.condition] = condition_counts.get(item.condition, 0) + item.qty
        
        return {
            'total_items': total_items,
            'total_quantity': sum(item.qty for item in self.items),
            'items_with_locations': items_with_locations,
            'items_without_locations': items_without_locations,
            'by_type': type_counts,
            'by_condition': condition_counts,
            'file_path': self.file_path
        }
    
    def _get_item_type_name(self, type_id: str) -> str:
        """Convert item type ID to readable name"""
        type_map = {
            'P': 'Parts',
            'M': 'Minifigures',
            'S': 'Sets', 
            'B': 'Books',
            'I': 'Instructions',
            'O': 'Original Boxes',
            'G': 'Gear'
        }
        return type_map.get(type_id, f'Type_{type_id}')

def create_sample_bsx():
    """Create a sample BSX file for testing"""
    sample_xml = '''<?xml version="1.0" encoding="UTF-8"?>
<BrickStoreXML>
  <Inventory>
    <Item>
      <ItemID>3001</ItemID>
      <ItemTypeID>P</ItemTypeID>
      <ColorID>4</ColorID>
      <ColorName>Red</ColorName>
      <CategoryID>5</CategoryID>
      <CategoryName>Bricks</CategoryName>
      <ItemName>Brick 2 x 4</ItemName>
      <Qty>10</Qty>
      <Price>0.50</Price>
      <Condition>N</Condition>
      <Remarks></Remarks>
    </Item>
    <Item>
      <ItemID>3024</ItemID>
      <ItemTypeID>P</ItemTypeID>
      <ColorID>1</ColorID>
      <ColorName>White</ColorName>
      <CategoryID>26</CategoryID>
      <CategoryName>Plates</CategoryName>
      <ItemName>Plate 1 x 1</ItemName>
      <Qty>25</Qty>
      <Price>0.10</Price>
      <Condition>N</Condition>
      <Remarks></Remarks>
    </Item>
    <Item>
      <ItemID>973</ItemID>
      <ItemTypeID>P</ItemTypeID>
      <ColorID>2</ColorID>
      <ColorName>Tan</ColorName>
      <CategoryID>271</CategoryID>
      <CategoryName>Minifigure, Body Part</CategoryName>
      <ItemName>Torso Plain</ItemName>
      <Qty>5</Qty>
      <Price>1.25</Price>
      <Condition>U</Condition>
      <Remarks>A1-B2</Remarks>
    </Item>
  </Inventory>
</BrickStoreXML>'''
    
    with open('sample_inventory.bsx', 'w', encoding='utf-8') as f:
        f.write(sample_xml)
    
    print("Created sample BSX file: sample_inventory.bsx")

if __name__ == "__main__":
    # Test the BSX handler
    logging.basicConfig(level=logging.INFO)
    
    # Create sample file if it doesn't exist
    if not os.path.exists('sample_inventory.bsx'):
        create_sample_bsx()
    
    # Test loading and parsing
    handler = BSXHandler()
    success, message = handler.load_bsx_file('sample_inventory.bsx')
    
    if success:
        print(f"[SUCCESS] {message}")
        
        summary = handler.get_file_summary()
        print(f"\nFile Summary:")
        print(f"Total items: {summary['total_items']}")
        print(f"Total quantity: {summary['total_quantity']}")
        print(f"Items with locations: {summary['items_with_locations']}")
        print(f"Items without locations: {summary['items_without_locations']}")
        
        print(f"\nBy type: {summary['by_type']}")
        print(f"By condition: {summary['by_condition']}")
        
        # Test updating locations
        items_without_locations = handler.get_items_without_locations()
        print(f"\nItems needing locations: {len(items_without_locations)}")
        
        for item in items_without_locations[:2]:  # Test first 2
            print(f"- {item.item_name} ({item.item_id})")
            handler.update_item_location(item, f"TEST-LOC-{item.item_id}")
        
        # Save test
        success, save_msg = handler.save_bsx_file()
        print(f"\nSave result: {save_msg}")
        
    else:
        print(f"[ERROR] {message}")