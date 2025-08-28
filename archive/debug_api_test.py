import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bricklink_api import BrickLinkAPI
import json

def mask_secret(secret, show_chars=4):
    """Mask a secret string, showing only first few characters"""
    if len(secret) <= show_chars:
        return "*" * len(secret)
    return secret[:show_chars] + "*" * (len(secret) - show_chars)

def test_api_connection():
    print("=== BrickLink API Debug Test ===\n")
    
    # Try to load from config first
    config_file = 'config.json'
    credentials = None
    
    if os.path.exists(config_file):
        print(f"Loading credentials from {config_file}")
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
            credentials = config.get('api_credentials', {})
            print("[OK] Config file loaded successfully")
        except Exception as e:
            print(f"[ERROR] Error loading config: {e}")
    else:
        print(f"[ERROR] Config file {config_file} not found")
        print("Please create it by running the UI and saving your credentials")
        return
    
    # Check credentials
    required_keys = ['consumer_key', 'consumer_secret', 'token', 'token_secret']
    missing_keys = []
    
    for key in required_keys:
        value = credentials.get(key, '')
        if not value or value == f'YOUR_{key.upper()}':
            missing_keys.append(key)
        else:
            print(f"[OK] {key}: {mask_secret(value)}")
    
    if missing_keys:
        print(f"\n[ERROR] Missing credentials: {', '.join(missing_keys)}")
        print("Please fill in all credentials in the UI and save them.")
        return
    
    print(f"\n--- Testing API Connection ---")
    
    try:
        # Create API client
        api = BrickLinkAPI(
            credentials['consumer_key'],
            credentials['consumer_secret'],
            credentials['token'],
            credentials['token_secret']
        )
        
        print("[OK] API client created")
        
        # Test connection
        print("Making test request...")
        success, message = api.test_connection()
        
        if success:
            print(f"[SUCCESS] {message}")
        else:
            print(f"[FAILED] {message}")
            
    except Exception as e:
        print(f"[EXCEPTION] {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api_connection()