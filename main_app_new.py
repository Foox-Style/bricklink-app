import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
from typing import Optional, Dict, Any
import logging

from shared.api_manager import APIManager
from tools.feature1 import LocationAssignmentTool
from tools.feature2 import Feature2Tool
from tools.feature3 import Feature3Tool

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('bricklink_app.log'),
        logging.StreamHandler()
    ]
)

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class BrickLinkToolsApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("BrickLink Tools Suite")
        self.root.geometry("1000x700")
        self.root.minsize(800, 600)
        
        # Core components
        self.api_manager = APIManager(on_connection_change=self.on_connection_change)
        self.current_tool = None
        self.tools: Dict[str, Any] = {}
        
        # UI Variables for API settings
        self.consumer_key = tk.StringVar()
        self.consumer_secret = tk.StringVar()
        self.token = tk.StringVar()
        self.token_secret = tk.StringVar()
        
        self.setup_ui()
        self.load_config()
        self.auto_connect_if_ready()
        
        self.logger = logging.getLogger(__name__)
    
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title and connection status
        header_frame = ctk.CTkFrame(main_frame)
        header_frame.pack(fill="x", padx=5, pady=(5, 10))
        
        title_label = ctk.CTkLabel(
            header_frame,
            text="BrickLink Tools Suite",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(side="left", padx=20, pady=15)
        
        # Connection status on the right
        self.connection_frame = ctk.CTkFrame(header_frame, corner_radius=6)
        self.connection_frame.pack(side="right", padx=20, pady=15)
        
        self.connection_dot = ctk.CTkLabel(
            self.connection_frame,
            text="●",
            font=ctk.CTkFont(size=16),
            text_color="red",
            cursor="hand2"
        )
        self.connection_dot.pack(side="left", padx=(15, 5), pady=10)
        
        self.connection_text = ctk.CTkLabel(
            self.connection_frame,
            text="Not Connected - Click to configure",
            font=ctk.CTkFont(size=12),
            cursor="hand2"
        )
        self.connection_text.pack(side="left", padx=(0, 15), pady=10)
        
        # Make connection status clickable
        self.connection_dot.bind("<Button-1>", lambda e: self.show_api_settings())
        self.connection_text.bind("<Button-1>", lambda e: self.show_api_settings())
        self.connection_frame.bind("<Button-1>", lambda e: self.show_api_settings())
        
        # Main content area
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Sidebar for tools
        self.sidebar = ctk.CTkFrame(content_frame, width=180, corner_radius=8)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10))
        self.sidebar.pack_propagate(False)
        
        # Sidebar title
        sidebar_title = ctk.CTkLabel(
            self.sidebar,
            text="Tools",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        sidebar_title.pack(pady=(20, 15))
        
        # Tool buttons
        self.tool_buttons = {}
        tools_info = [
            ("feature1", "📦 Location Assignment"),
            ("feature2", "📊 Feature 2"), 
            ("feature3", "⚡ Feature 3")
        ]
        
        for tool_id, tool_name in tools_info:
            btn = ctk.CTkButton(
                self.sidebar,
                text=tool_name,
                width=150,
                height=50,
                command=lambda tid=tool_id: self.switch_tool(tid),
                font=ctk.CTkFont(size=14),
                corner_radius=8,
                anchor="w"
            )
            btn.pack(pady=5, padx=15)
            self.tool_buttons[tool_id] = btn
        
        # Tool content area
        self.tool_area = ctk.CTkFrame(content_frame)
        self.tool_area.pack(side="right", fill="both", expand=True)
        
        # Initialize tools
        self.init_tools()
        
        # Show first tool by default
        self.switch_tool("feature1")
    
    def init_tools(self):
        """Initialize all tools"""
        self.tools["feature1"] = LocationAssignmentTool(self.tool_area, self.api_manager.get_api())
        self.tools["feature2"] = Feature2Tool(self.tool_area, self.api_manager.get_api())
        self.tools["feature3"] = Feature3Tool(self.tool_area, self.api_manager.get_api())
        
        # Hide all tools initially
        for tool in self.tools.values():
            tool.hide()
    
    def switch_tool(self, tool_id: str):
        """Switch to the specified tool"""
        # Hide current tool
        if self.current_tool and self.current_tool in self.tools:
            self.tools[self.current_tool].hide()
        
        # Show new tool
        if tool_id in self.tools:
            self.tools[tool_id].show()
            self.current_tool = tool_id
            
            # Update button appearance
            for tid, btn in self.tool_buttons.items():
                if tid == tool_id:
                    btn.configure(fg_color=("gray75", "gray25"))
                else:
                    btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
    
    def on_connection_change(self, connected: bool, message: str):
        """Handle API connection status changes"""
        if connected:
            self.connection_dot.configure(text_color="green")
            self.connection_text.configure(text="Connected - API Ready")
            
            # Update all tools with new API connection
            api = self.api_manager.get_api()
            for tool in self.tools.values():
                tool.set_api(api)
                
        else:
            self.connection_dot.configure(text_color="red")
            self.connection_text.configure(text="Not Connected - Click to configure")
    
    def show_api_settings(self):
        """Show API settings popup"""
        # Check if window already exists
        if hasattr(self, 'api_window') and self.api_window.winfo_exists():
            self.api_window.lift()
            self.api_window.focus()
            return
        
        # Create popup window
        self.api_window = ctk.CTkToplevel(self.root)
        self.api_window.title("BrickLink API Settings")
        self.api_window.geometry("500x500")
        self.api_window.resizable(False, False)
        
        # Make it modal
        self.api_window.transient(self.root)
        self.api_window.grab_set()
        
        # Center the window
        self.api_window.after(100, lambda: self.center_window(self.api_window))
        
        # Main frame
        main_frame = ctk.CTkFrame(self.api_window)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame,
            text="BrickLink API Credentials",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(15, 25))
        
        # Credentials frame
        creds_frame = ctk.CTkFrame(main_frame)
        creds_frame.pack(fill="x", padx=20, pady=10)
        
        # Grid for credentials
        cred_grid = ctk.CTkFrame(creds_frame, fg_color="transparent")
        cred_grid.pack(fill="x", padx=20, pady=20)
        
        # Consumer Key
        ctk.CTkLabel(cred_grid, text="Consumer Key:").grid(row=0, column=0, sticky="w", pady=8)
        self.consumer_key_entry = ctk.CTkEntry(cred_grid, textvariable=self.consumer_key, width=250)
        self.consumer_key_entry.grid(row=0, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        # Consumer Secret
        ctk.CTkLabel(cred_grid, text="Consumer Secret:").grid(row=1, column=0, sticky="w", pady=8)
        self.consumer_secret_entry = ctk.CTkEntry(cred_grid, textvariable=self.consumer_secret, show="*", width=250)
        self.consumer_secret_entry.grid(row=1, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        # Token
        ctk.CTkLabel(cred_grid, text="Token:").grid(row=2, column=0, sticky="w", pady=8)
        self.token_entry = ctk.CTkEntry(cred_grid, textvariable=self.token, width=250)
        self.token_entry.grid(row=2, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        # Token Secret
        ctk.CTkLabel(cred_grid, text="Token Secret:").grid(row=3, column=0, sticky="w", pady=8)
        self.token_secret_entry = ctk.CTkEntry(cred_grid, textvariable=self.token_secret, show="*", width=250)
        self.token_secret_entry.grid(row=3, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        cred_grid.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        connect_btn = ctk.CTkButton(
            button_frame,
            text="Connect & Test",
            command=self.connect_api,
            width=120,
            height=35
        )
        connect_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Config",
            command=self.save_config,
            width=120,
            height=35
        )
        save_btn.pack(side="left", padx=5)
        
        # Close button
        close_btn = ctk.CTkButton(
            main_frame,
            text="Close",
            command=self.api_window.destroy,
            width=100,
            height=35
        )
        close_btn.pack(pady=10)
    
    def center_window(self, window):
        """Center a window on the screen"""
        window.update_idletasks()
        width = window.winfo_width()
        height = window.winfo_height()
        x = (window.winfo_screenwidth() // 2) - (width // 2)
        y = (window.winfo_screenheight() // 2) - (height // 2)
        window.geometry(f'{width}x{height}+{x}+{y}')
    
    def connect_api(self):
        """Connect to BrickLink API"""
        if not all([
            self.consumer_key.get().strip(),
            self.consumer_secret.get().strip(),
            self.token.get().strip(),
            self.token_secret.get().strip()
        ]):
            messagebox.showerror("Error", "Please fill in all API credentials")
            return
        
        # Update connection indicator
        self.connection_dot.configure(text_color="orange")
        self.connection_text.configure(text="Connecting...")
        
        # Connect through API manager
        self.api_manager.connect(
            self.consumer_key.get(),
            self.consumer_secret.get(),
            self.token.get(),
            self.token_secret.get()
        )
    
    def load_config(self):
        """Load API configuration from file"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                credentials = config.get('api_credentials', {})
                
                if credentials.get('consumer_key', '') != 'YOUR_CONSUMER_KEY':
                    self.consumer_key.set(credentials.get('consumer_key', ''))
                    self.consumer_secret.set(credentials.get('consumer_secret', ''))
                    self.token.set(credentials.get('token', ''))
                    self.token_secret.set(credentials.get('token_secret', ''))
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
    
    def save_config(self):
        """Save API configuration to file"""
        try:
            config = {
                "api_credentials": {
                    "consumer_key": self.consumer_key.get(),
                    "consumer_secret": self.consumer_secret.get(),
                    "token": self.token.get(),
                    "token_secret": self.token_secret.get()
                }
            }
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
    
    def auto_connect_if_ready(self):
        """Automatically connect if all credentials are available"""
        if (self.consumer_key.get().strip() and 
            self.consumer_secret.get().strip() and 
            self.token.get().strip() and 
            self.token_secret.get().strip() and
            self.consumer_key.get() != 'YOUR_CONSUMER_KEY'):
            
            self.connect_api()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BrickLinkToolsApp()
    app.run()