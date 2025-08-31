import customtkinter as ctk
from abc import ABC, abstractmethod
from typing import Optional
from bricklink_api import BrickLinkAPI

class BaseTool(ABC):
    """Base class for all BrickLink tools"""
    
    def __init__(self, parent_frame: ctk.CTkFrame, api: Optional[BrickLinkAPI] = None):
        self.parent_frame = parent_frame
        self.api = api
        self.main_frame = None
        self.setup_ui()
    
    @abstractmethod
    def setup_ui(self):
        """Setup the tool's user interface"""
        pass
    
    @abstractmethod
    def get_tool_name(self) -> str:
        """Return the display name of the tool"""
        pass
    
    @abstractmethod
    def get_tool_icon(self) -> str:
        """Return the icon for the tool (emoji or text)"""
        pass
    
    def set_api(self, api: BrickLinkAPI):
        """Update the API connection for this tool"""
        self.api = api
        self.on_api_connected()
    
    def on_api_connected(self):
        """Called when API connection is established"""
        pass
    
    def show(self):
        """Show this tool's interface"""
        if self.main_frame:
            self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)
    
    def hide(self):
        """Hide this tool's interface"""
        if self.main_frame:
            self.main_frame.pack_forget()
    
    def destroy(self):
        """Clean up the tool"""
        if self.main_frame:
            self.main_frame.destroy()