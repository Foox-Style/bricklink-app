import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
import threading
from bricklink_api import BrickLinkAPI

ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class APITestApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("BrickLink API Connection Tester")
        self.root.geometry("600x700")
        self.root.minsize(500, 600)
        
        # Variables
        self.consumer_key = tk.StringVar()
        self.consumer_secret = tk.StringVar()
        self.token = tk.StringVar()
        self.token_secret = tk.StringVar()
        
        self.api = None
        
        self.setup_ui()
        self.load_config()
        
    def setup_ui(self):
        # Main container
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="BrickLink API Connection Tester",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Instructions
        instructions = ctk.CTkLabel(
            main_frame,
            text="Enter your BrickLink API credentials below.\nYou can get these from your BrickLink Developer Console.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        instructions.pack(pady=(0, 20))
        
        # Credentials frame
        creds_frame = ctk.CTkFrame(main_frame)
        creds_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(creds_frame, text="API Credentials", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 20))
        
        # Consumer Key
        ctk.CTkLabel(creds_frame, text="Consumer Key:", anchor="w").pack(fill="x", padx=20, pady=(5, 0))
        self.consumer_key_entry = ctk.CTkEntry(creds_frame, textvariable=self.consumer_key, width=400)
        self.consumer_key_entry.pack(padx=20, pady=(0, 10))
        
        # Consumer Secret
        ctk.CTkLabel(creds_frame, text="Consumer Secret:", anchor="w").pack(fill="x", padx=20, pady=(5, 0))
        self.consumer_secret_entry = ctk.CTkEntry(creds_frame, textvariable=self.consumer_secret, 
                                                 show="*", width=400)
        self.consumer_secret_entry.pack(padx=20, pady=(0, 10))
        
        # Token
        ctk.CTkLabel(creds_frame, text="Token:", anchor="w").pack(fill="x", padx=20, pady=(5, 0))
        self.token_entry = ctk.CTkEntry(creds_frame, textvariable=self.token, width=400)
        self.token_entry.pack(padx=20, pady=(0, 10))
        
        # Token Secret
        ctk.CTkLabel(creds_frame, text="Token Secret:", anchor="w").pack(fill="x", padx=20, pady=(5, 0))
        self.token_secret_entry = ctk.CTkEntry(creds_frame, textvariable=self.token_secret, 
                                              show="*", width=400)
        self.token_secret_entry.pack(padx=20, pady=(0, 15))
        
        # Buttons frame
        buttons_frame = ctk.CTkFrame(creds_frame, fg_color="transparent")
        buttons_frame.pack(fill="x", padx=20, pady=10)
        
        self.save_btn = ctk.CTkButton(buttons_frame, text="Save Config", 
                                     command=self.save_config, width=120)
        self.save_btn.pack(side="left", padx=(0, 10))
        
        self.load_btn = ctk.CTkButton(buttons_frame, text="Load Config", 
                                     command=self.load_config, width=120)
        self.load_btn.pack(side="left")
        
        # Test frame
        test_frame = ctk.CTkFrame(main_frame)
        test_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(test_frame, text="Connection Test", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Test button
        self.test_btn = ctk.CTkButton(
            test_frame,
            text="Test Connection",
            command=self.test_connection_threaded,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.test_btn.pack(pady=10)
        
        # Status label
        self.status_label = ctk.CTkLabel(test_frame, text="Ready to test connection")
        self.status_label.pack(pady=5)
        
        # Results frame
        results_frame = ctk.CTkFrame(main_frame)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(results_frame, text="Test Results", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Results text area
        self.results_text = ctk.CTkTextbox(results_frame, width=500, height=200)
        self.results_text.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Inventory test button
        self.inventory_btn = ctk.CTkButton(
            results_frame,
            text="Test Inventory Fetch",
            command=self.test_inventory_threaded,
            width=180,
            state="disabled"
        )
        self.inventory_btn.pack(pady=10)
        
    def load_config(self):
        """Load configuration from file"""
        try:
            if os.path.exists('config.json'):
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                credentials = config.get('api_credentials', {})
                
                # Only load if not placeholder values
                if credentials.get('consumer_key', '') != 'YOUR_CONSUMER_KEY':
                    self.consumer_key.set(credentials.get('consumer_key', ''))
                    self.consumer_secret.set(credentials.get('consumer_secret', ''))
                    self.token.set(credentials.get('token', ''))
                    self.token_secret.set(credentials.get('token_secret', ''))
                    
                    self.results_text.insert("1.0", "✓ Configuration loaded from config.json\n\n")
            else:
                self.results_text.insert("1.0", "No config.json found. Enter credentials manually.\n\n")
                
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load config: {str(e)}")
    
    def save_config(self):
        """Save configuration to file"""
        try:
            config = {
                "api_credentials": {
                    "consumer_key": self.consumer_key.get(),
                    "consumer_secret": self.consumer_secret.get(),
                    "token": self.token.get(),
                    "token_secret": self.token_secret.get()
                },
                "settings": {
                    "rate_limit_seconds": 1.0,
                    "cache_inventory": True,
                    "cache_duration_hours": 24
                }
            }
            
            with open('config.json', 'w') as f:
                json.dump(config, f, indent=2)
            
            self.results_text.insert("1.0", "✓ Configuration saved to config.json\n\n")
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
    
    def validate_credentials(self):
        """Validate that all credentials are provided"""
        if not all([
            self.consumer_key.get().strip(),
            self.consumer_secret.get().strip(),
            self.token.get().strip(),
            self.token_secret.get().strip()
        ]):
            messagebox.showerror("Error", "Please fill in all API credentials")
            return False
        return True
    
    def test_connection_threaded(self):
        """Test connection in a separate thread"""
        if not self.validate_credentials():
            return
            
        # Clear previous results and add initial message
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", "Starting connection test...\n")
        
        # Disable button and show loading
        self.test_btn.configure(state="disabled", text="Testing...")
        self.status_label.configure(text="Testing connection...", text_color="orange")
        
        def test_thread():
            try:
                # Add step-by-step feedback
                self.root.after(0, lambda: self.results_text.insert(tk.END, "Creating API client...\n"))
                
                # Create API instance
                self.api = BrickLinkAPI(
                    self.consumer_key.get().strip(),
                    self.consumer_secret.get().strip(),
                    self.token.get().strip(),
                    self.token_secret.get().strip()
                )
                
                self.root.after(0, lambda: self.results_text.insert(tk.END, "Sending test request to BrickLink API...\n"))
                
                # Test connection
                success, message = self.api.test_connection()
                
                # Update UI in main thread
                self.root.after(0, lambda: self.connection_test_complete(success, message))
                
            except Exception as e:
                error_msg = f"Exception occurred: {str(e)}"
                self.root.after(0, lambda: self.results_text.insert(tk.END, f"ERROR: {error_msg}\n"))
                self.root.after(0, lambda: self.connection_test_complete(False, error_msg))
        
        threading.Thread(target=test_thread, daemon=True).start()
    
    def connection_test_complete(self, success, message):
        """Handle connection test completion"""
        self.test_btn.configure(state="normal", text="Test Connection")
        
        if success:
            self.status_label.configure(text="✓ Connection successful", text_color="green")
            self.inventory_btn.configure(state="normal")
            result_text = f"\n=== CONNECTION SUCCESS! ===\n{message}\n\n"
            self.results_text.insert(tk.END, result_text)
        else:
            self.status_label.configure(text="✗ Connection failed", text_color="red")
            self.inventory_btn.configure(state="disabled")
            result_text = f"\n=== CONNECTION FAILED! ===\n{message}\n\n"
            self.results_text.insert(tk.END, result_text)
    
    def test_inventory_threaded(self):
        """Test inventory fetch in a separate thread"""
        if not self.api:
            messagebox.showerror("Error", "Please test connection first")
            return
            
        self.inventory_btn.configure(state="disabled", text="Fetching...")
        self.status_label.configure(text="Fetching inventory summary...", text_color="orange")
        
        def inventory_thread():
            try:
                success, summary = self.api.get_inventory_summary()
                self.root.after(0, lambda: self.inventory_test_complete(success, summary))
                
            except Exception as e:
                self.root.after(0, lambda: self.inventory_test_complete(False, f"Error: {str(e)}"))
        
        threading.Thread(target=inventory_thread, daemon=True).start()
    
    def inventory_test_complete(self, success, data):
        """Handle inventory test completion"""
        self.inventory_btn.configure(state="normal", text="Test Inventory Fetch")
        
        if success:
            self.status_label.configure(text="✓ Inventory fetched successfully", text_color="green")
            
            result_text = f"""INVENTORY FETCH SUCCESS!

Summary:
• Total items: {data['total_items']}
• Items with storage locations: {data['items_with_locations']}
• Items without locations: {data['items_without_locations']}
• Unique storage locations: {data['unique_locations']}

Items by type:
"""
            for item_type, count in data['items_by_type'].items():
                result_text += f"• {item_type}: {count}\n"
            
            if data['top_locations']:
                result_text += "\nMost used storage locations:\n"
                for location, count in list(data['top_locations'].items())[:5]:
                    result_text += f"• {location}: {count} items\n"
            
            result_text += "\n"
            
        else:
            self.status_label.configure(text="✗ Inventory fetch failed", text_color="red")
            result_text = f"INVENTORY FETCH FAILED!\n{data}\n\n"
        
        self.results_text.insert("1.0", result_text)
    
    def run(self):
        self.root.mainloop()

if __name__ == "__main__":
    app = APITestApp()
    app.run()