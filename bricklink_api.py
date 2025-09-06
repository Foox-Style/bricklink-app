import requests
import json
from requests_oauthlib import OAuth1
import time
from typing import Dict, List, Optional, Tuple
import logging

class BrickLinkAPI:
    """BrickLink API client with OAuth1 authentication"""
    
    def __init__(self, consumer_key: str, consumer_secret: str, token: str, token_secret: str):
        self.base_url = "https://api.bricklink.com/api/store/v1"
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.token = token
        self.token_secret = token_secret
        
        # OAuth1 authentication
        self.auth = OAuth1(
            client_key=consumer_key,
            client_secret=consumer_secret,
            resource_owner_key=token,
            resource_owner_secret=token_secret,
            signature_method='HMAC-SHA1',
            signature_type='AUTH_HEADER'
        )
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1.0  # 1 second between requests
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
    
    def _rate_limit(self):
        """Enforce rate limiting between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, endpoint: str, method: str = 'GET', params: Dict = None) -> Tuple[bool, Dict]:
        """Make authenticated request to BrickLink API"""
        self._rate_limit()
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            self.logger.info(f"Making {method} request to {endpoint}")
            
            if method == 'GET':
                response = requests.get(url, auth=self.auth, params=params, timeout=30)
            else:
                response = requests.request(method, url, auth=self.auth, json=params, timeout=30)
            
            # Log response status
            self.logger.info(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                return True, response.json()
            elif response.status_code == 401:
                return False, {"error": "Authentication failed. Check your API credentials."}
            elif response.status_code == 429:
                return False, {"error": "Rate limit exceeded. Please wait and try again."}
            else:
                return False, {"error": f"API error: {response.status_code} - {response.text}"}
                
        except requests.exceptions.Timeout:
            return False, {"error": "Request timeout. Please check your internet connection."}
        except requests.exceptions.ConnectionError:
            return False, {"error": "Connection error. Please check your internet connection."}
        except Exception as e:
            return False, {"error": f"Unexpected error: {str(e)}"}
    
    def test_connection(self) -> Tuple[bool, str]:
        """Test API connection by getting store info"""
        print(f"Testing connection to {self.base_url}/orders")
        success, data = self._make_request("/orders", params={"direction": "in", "status": "COMPLETED"})
        
        if success:
            orders = data.get('data', [])
            return True, f"Connected successfully!\nAPI is responding. Found {len(orders)} completed orders."
        else:
            error_msg = data.get('error', 'Unknown error')
            print(f"Connection failed: {error_msg}")
            return False, f"Connection failed: {error_msg}"
    
    def get_inventory(self) -> Tuple[bool, List[Dict]]:
        """Get all inventory items from the store"""
        all_items = []
        page = 1
        
        while True:
            success, data = self._make_request("/inventories", params={"page": page})
            
            if not success:
                return False, data.get('error', 'Failed to fetch inventory')
            
            items = data.get('data', [])
            if not items:
                break
                
            all_items.extend(items)
            self.logger.info(f"Fetched page {page}, total items so far: {len(all_items)}")
            
            # Check if there are more pages
            meta = data.get('meta', {})
            current_page = meta.get('current_page', page)
            total_pages = meta.get('total_pages', page)
            
            if current_page >= total_pages:
                break
                
            page += 1
        
        self.logger.info(f"Total inventory items fetched: {len(all_items)}")
        return True, all_items
    
    def get_inventory_summary(self) -> Tuple[bool, Dict]:
        """Get inventory summary statistics"""
        success, items = self.get_inventory()
        
        if not success:
            return False, {"error": items}
        
        # Process items to extract location data
        location_counts = {}
        items_by_type = {}
        total_items = len(items)
        items_with_locations = 0
        
        for item in items:
            # Get item type
            item_info = item.get('item', {})
            item_type = item_info.get('type', 'Unknown')
            items_by_type[item_type] = items_by_type.get(item_type, 0) + 1
            
            # Get location from remarks
            remarks = item.get('remarks', '').strip()
            if remarks:
                items_with_locations += 1
                location_counts[remarks] = location_counts.get(remarks, 0) + 1
        
        summary = {
            'total_items': total_items,
            'items_with_locations': items_with_locations,
            'items_without_locations': total_items - items_with_locations,
            'unique_locations': len(location_counts),
            'items_by_type': items_by_type,
            'top_locations': dict(sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10])
        }
        
        return True, summary
    
    def get_orders(self, direction: str = "out", status: str = "COMPLETED") -> Tuple[bool, List[Dict]]:
        """Get orders from the store
        
        Args:
            direction: "in" for purchases, "out" for sales
            status: Order status filter (PENDING, UPDATING, COMPLETED, etc.)
        """
        all_orders = []
        page = 1
        
        while True:
            params = {
                "direction": direction,
                "status": status,
                "page": page
            }
            
            success, data = self._make_request("/orders", params=params)
            
            if not success:
                return False, data.get('error', 'Failed to fetch orders')
            
            orders = data.get('data', [])
            if not orders:
                break
                
            all_orders.extend(orders)
            self.logger.info(f"Fetched orders page {page}, total orders so far: {len(all_orders)}")
            
            # Check if there are more pages
            meta = data.get('meta', {})
            current_page = meta.get('current_page', page)
            total_pages = meta.get('total_pages', page)
            
            if current_page >= total_pages:
                break
                
            page += 1
        
        self.logger.info(f"Total orders fetched: {len(all_orders)}")
        return True, all_orders
    
    def get_order_items(self, order_id: str) -> Tuple[bool, List[Dict]]:
        """Get items for a specific order"""
        success, data = self._make_request(f"/orders/{order_id}/items")
        
        if success:
            return True, data.get('data', [])
        else:
            return False, data.get('error', 'Failed to fetch order items')
    
    def get_item_subsets(self, item_type: str, item_id: str) -> Tuple[bool, List[Dict]]:
        """Get subsets (part lists) for an item - used for minifigure parts
        
        Args:
            item_type: Item type ('MINIFIG', 'SET', etc. or short codes like 'M', 'S')
            item_id: Item ID to get subsets for
        """
        # Convert short codes to full type names for the API
        type_mapping = {
            'P': 'PART',
            'M': 'MINIFIG', 
            'S': 'SET',
            'B': 'BOOK',
            'G': 'GEAR',
            'I': 'INSTRUCTION',
            'O': 'ORIGINAL_BOX'
        }
        
        api_type = type_mapping.get(item_type, item_type).lower()
        endpoint = f"/items/{api_type}/{item_id}/subsets"
        success, data = self._make_request(endpoint)
        
        if success:
            return True, data.get('data', [])
        else:
            return False, data.get('error', f'Failed to fetch subsets for {api_type}/{item_id}')
    
    def get_superset_items(self, item_type: str, item_id: str, color_id: str = None) -> Tuple[bool, List[Dict]]:
        """Get supersets - items that contain this part (used to find minifigures containing a torso)
        
        Args:
            item_type: Item type of the part ('PART', 'MINIFIG', 'SET', etc.)
            item_id: Part ID to search for
            color_id: Optional color filter
        """
        # Convert short codes to full type names for the API
        type_mapping = {
            'P': 'PART',
            'M': 'MINIFIG', 
            'S': 'SET',
            'B': 'BOOK',
            'G': 'GEAR',
            'I': 'INSTRUCTION',
            'O': 'ORIGINAL_BOX'
        }
        
        api_type = type_mapping.get(item_type, item_type).lower()
        endpoint = f"/items/{api_type}/{item_id}/supersets"
        
        params = {}
        if color_id:
            params['color_id'] = color_id
        
        success, data = self._make_request(endpoint, params=params)
        
        if success:
            return True, data.get('data', [])
        else:
            return False, data.get('error', f'Failed to fetch supersets for {api_type}/{item_id}')
    
    def get_item_info(self, item_type: str, item_id: str) -> Tuple[bool, Dict]:
        """Get information about a specific item
        
        Args:
            item_type: Item type ('PART', 'MINIFIG', etc. or short codes like 'P', 'M')
            item_id: Item ID
        """
        # Convert short codes to full type names for the API
        type_mapping = {
            'P': 'PART',
            'M': 'MINIFIG', 
            'S': 'SET',
            'B': 'BOOK',
            'G': 'GEAR',
            'I': 'INSTRUCTION',
            'O': 'ORIGINAL_BOX'
        }
        
        api_type = type_mapping.get(item_type, item_type).lower()
        endpoint = f"/items/{api_type}/{item_id}"
        success, data = self._make_request(endpoint)
        
        if success:
            return True, data.get('data', {})
        else:
            return False, data.get('error', f'Failed to fetch info for {api_type}/{item_id}')

def create_sample_config():
    """Create a sample configuration file"""
    config = {
        "api_credentials": {
            "consumer_key": "YOUR_CONSUMER_KEY",
            "consumer_secret": "YOUR_CONSUMER_SECRET", 
            "token": "YOUR_TOKEN",
            "token_secret": "YOUR_TOKEN_SECRET"
        },
        "settings": {
            "rate_limit_seconds": 1.0,
            "cache_inventory": True,
            "cache_duration_hours": 24
        }
    }
    
    with open('config.json', 'w') as f:
        json.dump(config, f, indent=2)
    
    print("Sample config.json created. Please fill in your BrickLink API credentials.")

if __name__ == "__main__":
    # Create sample config if it doesn't exist
    import os
    if not os.path.exists('config.json'):
        create_sample_config()
    else:
        print("Testing BrickLink API connection...")
        
        # Load config
        with open('config.json', 'r') as f:
            config = json.load(f)
        
        credentials = config['api_credentials']
        
        # Check if credentials are filled in
        if credentials['consumer_key'] == 'YOUR_CONSUMER_KEY':
            print("Please fill in your API credentials in config.json first!")
        else:
            # Test connection
            api = BrickLinkAPI(
                credentials['consumer_key'],
                credentials['consumer_secret'],
                credentials['token'],
                credentials['token_secret']
            )
            
            success, message = api.test_connection()
            print(f"Connection test: {message}")