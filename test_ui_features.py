import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_ui_features():
    print("=== Checking UI Features ===\n")
    
    # Try importing the main app
    try:
        from main_app_expandable import LocationAssignmentModule, APISetupModule
        print("[OK] Main modules can be imported")
    except Exception as e:
        print(f"[ERROR] Import failed: {e}")
        return
    
    # Check if LocationAssignmentModule has required methods
    location_methods = [
        'get_name', 'get_icon', 'create_ui', 'setup_file_tab', 
        'setup_process_tab', 'setup_results_tab', 'browse_file',
        'save_results', 'export_log', 'update_process_requirements'
    ]
    
    print("LocationAssignmentModule methods:")
    for method in location_methods:
        if hasattr(LocationAssignmentModule, method):
            print(f"  ✓ {method}")
        else:
            print(f"  ❌ MISSING: {method}")
    
    # Check API module
    api_methods = ['get_name', 'get_icon', 'create_ui', 'load_config', 'save_config']
    
    print("\nAPISetupModule methods:")
    for method in api_methods:
        if hasattr(APISetupModule, method):
            print(f"  ✓ {method}")
        else:
            print(f"  ❌ MISSING: {method}")

if __name__ == "__main__":
    check_ui_features()