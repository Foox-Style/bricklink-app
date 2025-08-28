import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bsx_handler import BSXHandler
import xml.etree.ElementTree as ET

def test_bsx_preservation():
    print("=== Testing BSX Structure Preservation ===\n")
    
    # Load the original file
    original_file = "C:/Users/mikev/Desktop/Import 25082401.bsx"
    
    print(f"1. Loading original file: {original_file}")
    handler = BSXHandler()
    success, message = handler.load_bsx_file(original_file)
    
    if not success:
        print(f"Failed to load: {message}")
        return
    
    print(f"[OK] {message}")
    
    # Check first item structure
    if handler.items:
        first_item = handler.items[0]
        print(f"\nFirst item: {first_item.item_name} ({first_item.item_id})")
        print(f"Original XML element children:")
        
        for child in first_item.xml_element:
            print(f"  {child.tag}: {child.text}")
        
        # Check for attributes in the original
        print(f"\nOriginal XML element attributes: {first_item.xml_element.attrib}")
        
        # Check if DifferenceBaseValues exists
        diff_elem = first_item.xml_element.find('DifferenceBaseValues')
        if diff_elem is not None:
            print(f"DifferenceBaseValues attributes: {diff_elem.attrib}")
    
    # Save to a test file
    test_file = "test_preservation.bsx"
    print(f"\n2. Saving to test file: {test_file}")
    success, message = handler.save_bsx_file(test_file)
    
    if success:
        print(f"[OK] {message}")
        
        # Compare structure
        print(f"\n3. Comparing structures...")
        
        # Parse both files and compare
        original_tree = ET.parse(original_file)
        test_tree = ET.parse(test_file)
        
        original_root = original_tree.getroot()
        test_root = test_tree.getroot()
        
        # Compare inventory attributes
        orig_inv = original_root.find('Inventory')
        test_inv = test_root.find('Inventory')
        
        print(f"Original Inventory attributes: {orig_inv.attrib if orig_inv is not None else 'None'}")
        print(f"Test Inventory attributes: {test_inv.attrib if test_inv is not None else 'None'}")
        
        # Compare first item
        orig_items = original_root.findall('.//Item')
        test_items = test_root.findall('.//Item')
        
        if orig_items and test_items:
            orig_first = orig_items[0]
            test_first = test_items[0]
            
            print(f"\nOriginal first item children: {len(list(orig_first))}")
            print(f"Test first item children: {len(list(test_first))}")
            
            print(f"\nOriginal children:")
            for child in orig_first:
                attrs_str = f" (attrs: {child.attrib})" if child.attrib else ""
                print(f"  {child.tag}: '{child.text}'{attrs_str}")
            
            print(f"\nTest children:")
            for child in test_first:
                attrs_str = f" (attrs: {child.attrib})" if child.attrib else ""
                print(f"  {child.tag}: '{child.text}'{attrs_str}")
        
    else:
        print(f"Failed to save: {message}")

if __name__ == "__main__":
    test_bsx_preservation()