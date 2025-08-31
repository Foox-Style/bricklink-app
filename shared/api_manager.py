import customtkinter as ctk
import tkinter as tk
from typing import Optional, Callable
import threading
import logging
from bricklink_api import BrickLinkAPI

class APIManager:
    """Manages BrickLink API connection for the entire application"""
    
    def __init__(self, on_connection_change: Optional[Callable] = None):
        self.api: Optional[BrickLinkAPI] = None
        self.is_connected = False
        self.on_connection_change = on_connection_change
        self.logger = logging.getLogger(__name__)
    
    def connect(self, consumer_key: str, consumer_secret: str, token: str, token_secret: str) -> None:
        """Connect to BrickLink API in a separate thread"""
        def connect_thread():
            try:
                # Create API client
                self.api = BrickLinkAPI(
                    consumer_key.strip(),
                    consumer_secret.strip(),
                    token.strip(),
                    token_secret.strip()
                )
                
                # Test connection
                success, message = self.api.test_connection()
                
                if success:
                    self.is_connected = True
                    if self.on_connection_change:
                        self.on_connection_change(True, message)
                else:
                    self.is_connected = False
                    if self.on_connection_change:
                        self.on_connection_change(False, message)
                    
            except Exception as e:
                self.is_connected = False
                if self.on_connection_change:
                    self.on_connection_change(False, f"Connection error: {str(e)}")
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def get_api(self) -> Optional[BrickLinkAPI]:
        """Get the API instance if connected"""
        return self.api if self.is_connected else None
    
    def disconnect(self):
        """Disconnect from the API"""
        self.api = None
        self.is_connected = False
        if self.on_connection_change:
            self.on_connection_change(False, "Disconnected")