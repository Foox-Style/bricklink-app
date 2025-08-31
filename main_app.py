import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import threading
from typing import Optional
import logging

from bricklink_api import BrickLinkAPI
from bsx_handler import BSXHandler
from location_matcher import LocationMatcher

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

class BrickLinkStorageApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("BrickLink Storage Location Auto-Populator")
        self.root.geometry("900x700")
        self.root.minsize(700, 600)
        
        # Core components
        self.api: Optional[BrickLinkAPI] = None
        self.bsx_handler: Optional[BSXHandler] = None
        self.location_matcher: Optional[LocationMatcher] = None
        
        # State variables
        self.selected_file = tk.StringVar()
        self.api_connected = False
        self.processing_results = None
        
        # UI Variables
        self.consumer_key = tk.StringVar()
        self.consumer_secret = tk.StringVar()
        self.token = tk.StringVar()
        self.token_secret = tk.StringVar()
        self.output_mode = tk.StringVar(value="new")
        self.preview_enabled = tk.BooleanVar(value=True)
        
        self.setup_ui()
        self.load_config()
        
        # Auto-connect if credentials are available
        self.auto_connect_if_ready()
        
        self.logger = logging.getLogger(__name__)
        
    def setup_ui(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=15, pady=15)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="BrickLink Storage Location Auto-Populator",
            font=ctk.CTkFont(size=22, weight="bold")
        )
        title_label.pack(pady=(15, 25))
        
        # Content container - single page layout
        content_container = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_container.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Connection status at top
        self.setup_connection_status(content_container)
        
        # Setup single page content
        self.setup_main_content(content_container)
        
    def setup_connection_status(self, parent):
        """Setup connection status indicator"""
        self.connection_frame = ctk.CTkFrame(parent, height=50, corner_radius=6)
        self.connection_frame.pack(fill="x", padx=20, pady=(0, 10))
        self.connection_frame.pack_propagate(False)
        
        self.connection_dot = ctk.CTkLabel(
            self.connection_frame,
            text="●",
            font=ctk.CTkFont(size=20),
            text_color="red",
            cursor="hand2"
        )
        self.connection_dot.pack(side="left", padx=(15, 5), pady=15)
        
        self.connection_text = ctk.CTkLabel(
            self.connection_frame,
            text="Not Connected - Click to configure API settings",
            font=ctk.CTkFont(size=12),
            cursor="hand2"
        )
        self.connection_text.pack(side="left", pady=15)
        
        # Make connection indicator clickable
        self.connection_dot.bind("<Button-1>", lambda e: self.show_api_settings())
        self.connection_text.bind("<Button-1>", lambda e: self.show_api_settings())
        self.connection_frame.bind("<Button-1>", lambda e: self.show_api_settings())
    
    def setup_main_content(self, parent):
        """Setup the main content area with all functionality on one page"""
        # File selection section
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(file_frame, text="📁 BSX File Selection", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # File drop area
        self.file_drop_frame = ctk.CTkFrame(file_frame, height=100, fg_color=("gray90", "gray20"))
        self.file_drop_frame.pack(fill="x", padx=20, pady=10)
        
        self.file_label = ctk.CTkLabel(
            self.file_drop_frame,
            text="No file selected - Click Browse to select a BSX file",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.file_label.pack(expand=True)
        
        # Browse and process buttons
        button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        button_frame.pack(pady=15)
        
        browse_btn = ctk.CTkButton(
            button_frame,
            text="Browse BSX Files",
            command=self.browse_file,
            width=160,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        browse_btn.pack(side="left", padx=5)
        
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="⚙️ Process Locations",
            command=self.start_processing_threaded,
            width=160,
            height=35,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.process_btn.pack(side="left", padx=5)
        
        self.save_results_btn = ctk.CTkButton(
            button_frame,
            text="💾 Save File",
            command=self.save_results,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            state="disabled"
        )
        self.save_results_btn.pack(side="left", padx=5)
        
        # Processing log section
        log_frame = ctk.CTkFrame(parent)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="📋 Processing Log & Results", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(log_frame, width=500)
        self.progress_bar.pack(padx=20, pady=10)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(log_frame, text="Ready to start")
        self.progress_status.pack(pady=5)
        
        # Combined log and results text area
        self.log_text = ctk.CTkTextbox(log_frame, height=300)
        self.log_text.pack(padx=20, pady=(0, 15), fill="both", expand=True)
        
        # Output options
        options_frame = ctk.CTkFrame(parent)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(options_frame, text="⚙️ Output Options", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        output_controls = ctk.CTkFrame(options_frame, fg_color="transparent")
        output_controls.pack(fill="x", padx=20, pady=(0, 15))
        
        ctk.CTkRadioButton(output_controls, text="Create new file (recommended)", 
                          variable=self.output_mode, value="new").pack(anchor="w", pady=3)
        ctk.CTkRadioButton(output_controls, text="Overwrite original file", 
                          variable=self.output_mode, value="overwrite").pack(anchor="w", pady=3)
        
        ctk.CTkCheckBox(output_controls, text="Preview changes before saving", 
                       variable=self.preview_enabled).pack(anchor="w", pady=5)
        
        
    def show_api_settings(self):
        """Show API settings in a popup window"""
        # Check if window already exists
        if hasattr(self, 'api_window') and self.api_window.winfo_exists():
            self.api_window.lift()
            self.api_window.focus()
            return
        
        # Create popup window
        self.api_window = ctk.CTkToplevel(self.root)
        self.api_window.title("BrickLink API Settings")
        self.api_window.geometry("550x650")
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
        self.consumer_key_entry = ctk.CTkEntry(cred_grid, textvariable=self.consumer_key, width=300)
        self.consumer_key_entry.grid(row=0, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        # Consumer Secret
        ctk.CTkLabel(cred_grid, text="Consumer Secret:").grid(row=1, column=0, sticky="w", pady=8)
        self.consumer_secret_entry = ctk.CTkEntry(cred_grid, textvariable=self.consumer_secret, 
                                                 show="*", width=300)
        self.consumer_secret_entry.grid(row=1, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        # Token
        ctk.CTkLabel(cred_grid, text="Token:").grid(row=2, column=0, sticky="w", pady=8)
        self.token_entry = ctk.CTkEntry(cred_grid, textvariable=self.token, width=300)
        self.token_entry.grid(row=2, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        # Token Secret
        ctk.CTkLabel(cred_grid, text="Token Secret:").grid(row=3, column=0, sticky="w", pady=8)
        self.token_secret_entry = ctk.CTkEntry(cred_grid, textvariable=self.token_secret, 
                                              show="*", width=300)
        self.token_secret_entry.grid(row=3, column=1, padx=(10, 0), pady=8, sticky="ew")
        
        cred_grid.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=20)
        
        self.connect_btn = ctk.CTkButton(
            button_frame,
            text="Connect & Test",
            command=self.connect_api_threaded,
            width=140,
            height=35
        )
        self.connect_btn.pack(side="left", padx=5)
        
        save_btn = ctk.CTkButton(
            button_frame,
            text="Save Config",
            command=self.save_config,
            width=140,
            height=35
        )
        save_btn.pack(side="left", padx=5)
        
        load_btn = ctk.CTkButton(
            button_frame,
            text="Load Config",
            command=self.load_config,
            width=140,
            height=35
        )
        load_btn.pack(side="left", padx=5)
        
        # Connection info
        info_frame = ctk.CTkFrame(main_frame)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, text="Connection Information", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.api_info_text = ctk.CTkTextbox(info_frame, height=200)
        self.api_info_text.pack(padx=20, pady=(0, 15), fill="both", expand=True)
        
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
        
        
        
    def browse_file(self):
        """Browse and select a BSX file"""
        file_path = filedialog.askopenfilename(
            title="Select BSX File",
            filetypes=[
                ("BSX files", "*.bsx"),
                ("XML files", "*.xml"),
                ("All files", "*.*")
            ]
        )
        
        if file_path:
            self.selected_file.set(file_path)
            self.load_bsx_file(file_path)
            self.update_ui_status()
    
    def load_bsx_file(self, file_path: str):
        """Load and analyze the BSX file"""
        try:
            self.bsx_handler = BSXHandler()
            success, message = self.bsx_handler.load_bsx_file(file_path)
            
            if success:
                # Update file label
                filename = os.path.basename(file_path)
                self.file_label.configure(text=f"✓ {filename} - Ready to process")
                
                # Show file information in log
                summary = self.bsx_handler.get_file_summary()
                
                info_text = f"File loaded: {filename}\n"
                info_text += f"• Total items: {summary['total_items']}\n"
                info_text += f"• Items needing locations: {summary['items_without_locations']}\n"
                info_text += f"• Items with locations: {summary['items_with_locations']}\n\n"
                
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert("1.0", info_text)
                
            else:
                messagebox.showerror("Error Loading File", message)
                self.file_label.configure(text="Error loading file\nClick Browse to try again")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
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
    
    def auto_connect_if_ready(self):
        """Automatically connect if all credentials are available"""
        # Check if all credentials are filled and valid (not default values)
        if (self.consumer_key.get().strip() and 
            self.consumer_secret.get().strip() and 
            self.token.get().strip() and 
            self.token_secret.get().strip() and
            self.consumer_key.get() != 'YOUR_CONSUMER_KEY' and
            not self.api_connected):  # Don't reconnect if already connected
            
            # Auto-connect
            self.connect_api_threaded()
    
    def save_config(self):
        """Save API configuration to file"""
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
            
            messagebox.showinfo("Success", "Configuration saved successfully!")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save config: {str(e)}")
    
    def connect_api_threaded(self):
        """Connect to BrickLink API in a separate thread"""
        if not all([
            self.consumer_key.get().strip(),
            self.consumer_secret.get().strip(),
            self.token.get().strip(),
            self.token_secret.get().strip()
        ]):
            messagebox.showerror("Error", "Please fill in all API credentials")
            return
        
        # Update UI (only if elements exist)
        if hasattr(self, 'connect_btn'):
            self.connect_btn.configure(state="disabled", text="Connecting...")
        if hasattr(self, 'api_info_text'):
            self.api_info_text.delete("1.0", tk.END)
            self.api_info_text.insert("1.0", "Connecting to BrickLink API...\n")
        # Update connection indicator to show connecting status
        self.connection_dot.configure(text_color="orange")
        self.connection_text.configure(text="Connecting...")
        
        def connect_thread():
            try:
                # Create API client
                self.api = BrickLinkAPI(
                    self.consumer_key.get().strip(),
                    self.consumer_secret.get().strip(),
                    self.token.get().strip(),
                    self.token_secret.get().strip()
                )
                
                # Test connection
                success, message = self.api.test_connection()
                
                if success:
                    # Create location matcher and load inventory
                    self.location_matcher = LocationMatcher(self.api)
                    if hasattr(self, 'api_info_text'):
                        self.root.after(0, lambda: self.api_info_text.insert(tk.END, "Loading inventory locations...\n"))
                    
                    inv_success, inv_message = self.location_matcher.load_inventory_locations()
                    
                    if inv_success:
                        self.api_connected = True
                        stats = self.location_matcher.get_location_statistics()
                        
                        final_message = f"{message}\n\nInventory loaded:\n{inv_message}\n\nLocation Statistics:\n"
                        final_message += f"• Items with locations: {stats['unique_items_with_locations']}\n"
                        final_message += f"• Unique storage locations: {stats['unique_locations']}\n"
                        
                        if stats['most_used_locations']:
                            final_message += "\nMost used locations:\n"
                            for location, count in list(stats['most_used_locations'].items())[:5]:
                                final_message += f"  '{location}': {count} items\n"
                        
                        self.root.after(0, lambda: self.connection_complete(True, final_message))
                    else:
                        self.root.after(0, lambda: self.connection_complete(False, f"Connection successful but failed to load inventory: {inv_message}"))
                else:
                    self.root.after(0, lambda: self.connection_complete(False, message))
                    
            except Exception as e:
                self.root.after(0, lambda: self.connection_complete(False, f"Connection error: {str(e)}"))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def connection_complete(self, success: bool, message: str):
        """Handle API connection completion"""
        if hasattr(self, 'connect_btn'):
            self.connect_btn.configure(state="normal", text="Connect & Test")
        
        if success:
            if hasattr(self, 'api_info_text'):
                self.api_info_text.insert(tk.END, f"\n[SUCCESS] {message}")
            # Update connection indicator
            self.connection_dot.configure(text_color="green")
            self.connection_text.configure(text="Connected - API ready")
        else:
            if hasattr(self, 'api_info_text'):
                self.api_info_text.insert(tk.END, f"\n[FAILED] {message}")
            self.api_connected = False
            # Update connection indicator
            self.connection_dot.configure(text_color="red")
            self.connection_text.configure(text="Failed - Click to retry")
        
        self.update_ui_status()
    
    def update_ui_status(self):
        """Update UI status and button states"""
        file_ready = bool(self.bsx_handler and self.selected_file.get())
        api_ready = self.api_connected
        
        # Update progress status
        if file_ready and api_ready:
            self.progress_status.configure(text="Ready to process - Click Process Locations")
            self.process_btn.configure(state="normal")
        elif file_ready:
            self.progress_status.configure(text="File ready - Connect API to enable processing")
            self.process_btn.configure(state="disabled")
        elif api_ready:
            self.progress_status.configure(text="API ready - Select a BSX file to continue")
            self.process_btn.configure(state="disabled")
        else:
            self.progress_status.configure(text="Select file and connect API to begin")
            self.process_btn.configure(state="disabled")
    
    def start_processing_threaded(self):
        """Start the location matching process in a separate thread"""
        if not (self.bsx_handler and self.location_matcher):
            messagebox.showerror("Error", "Missing required components")
            return
        
        # Update UI
        self.process_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        self.progress_status.configure(text="Starting processing...")
        self.log_text.delete("1.0", tk.END)
        
        def process_thread():
            try:
                # Log start
                self.root.after(0, lambda: self.log_text.insert(tk.END, "Starting location matching process...\n"))
                self.root.after(0, lambda: self.progress_bar.set(0.2))
                
                # Process in preview mode first if enabled
                preview_mode = self.preview_enabled.get()
                
                self.root.after(0, lambda: self.log_text.insert(tk.END, f"Processing in {'preview' if preview_mode else 'final'} mode...\n"))
                self.root.after(0, lambda: self.progress_bar.set(0.4))
                
                success, results = self.location_matcher.process_bsx_file(self.bsx_handler, preview_only=preview_mode)
                
                if success:
                    self.processing_results = results
                    self.root.after(0, lambda: self.progress_bar.set(1.0))
                    self.root.after(0, lambda: self.processing_complete(True, results))
                else:
                    self.root.after(0, lambda: self.processing_complete(False, results.get('error', 'Unknown error')))
                    
            except Exception as e:
                self.root.after(0, lambda: self.processing_complete(False, f"Processing error: {str(e)}"))
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def processing_complete(self, success: bool, results):
        """Handle processing completion"""
        self.process_btn.configure(state="normal", text="Start Processing")
        
        if success:
            self.progress_status.configure(text="Processing completed successfully! Check Results tab for details.")
            self.log_text.insert(tk.END, "Processing completed!\n")
            self.log_text.insert(tk.END, f"Items processed: {results['total_items_processed']}\n")
            self.log_text.insert(tk.END, f"Locations assigned: {results['locations_assigned']}\n")
            self.log_text.insert(tk.END, f"Success rate: {results['success_rate']}%\n")
            self.log_text.insert(tk.END, "\nSwitch to the Results tab to view detailed results and save the file.\n")
            
            # Store results and display them
            self.processing_results = results
            self.display_results_in_log(results)
            
            # Enable save button
            self.save_results_btn.configure(state="normal")
            
        else:
            self.progress_status.configure(text="Processing failed")
            self.log_text.insert(tk.END, f"ERROR: {results}\n")
            messagebox.showerror("Processing Error", f"Processing failed: {results}")
    
    def display_results_in_log(self, results):
        """Display processing results in the log area"""
        # Summary
        summary_text = f"\n=== PROCESSING COMPLETE ===\n\n"
        summary_text += f"• Items processed: {results['total_items_processed']}\n"
        summary_text += f"• Locations assigned: {results['locations_assigned']}\n"
        summary_text += f"• Items without matches: {results['no_location_found']}\n"
        summary_text += f"• Success rate: {results['success_rate']}%\n"
        summary_text += f"• Mode: {'Preview (changes not saved)' if self.preview_enabled.get() else 'Final (changes applied)'}\n\n"
        
        # Detailed results
        if results['assignment_details']:
            summary_text += "=== LOCATION ASSIGNMENTS ===\n\n"
            for detail in results['assignment_details']:
                summary_text += f"✓ {detail['item_name']} ({detail['item_id']})\n"
                summary_text += f"  Color: {detail['color_name']}, Qty: {detail['quantity']}\n"
                summary_text += f"  -> Location: '{detail['assigned_location']}'\n\n"
        
        if results['items_without_matches']:
            summary_text += "=== ITEMS WITHOUT MATCHES ===\n\n"
            for item in results['items_without_matches']:
                summary_text += f"❌ {item['item_name']} ({item['item_id']})\n"
                summary_text += f"  Color: {item['color_name']}, Qty: {item['quantity']}\n"
                summary_text += f"  Reason: No existing inventory found\n\n"
        
        self.log_text.insert(tk.END, summary_text)
    
    def save_results(self):
        """Save the processed BSX file"""
        if not self.bsx_handler:
            messagebox.showerror("Error", "No BSX file loaded")
            return
        
        try:
            # If we were in preview mode, process again for real
            if self.preview_enabled.get():
                if messagebox.askyesno("Confirm Save", "This will apply the location changes to your BSX file. Continue?"):
                    # Process for real this time
                    success, results = self.location_matcher.process_bsx_file(self.bsx_handler, preview_only=False)
                    if not success:
                        messagebox.showerror("Error", f"Failed to apply changes: {results}")
                        return
            
            # Save the file
            overwrite = self.output_mode.get() == "overwrite"
            
            if overwrite:
                success, message = self.bsx_handler.save_bsx_file(overwrite_original=True)
            else:
                # Generate new filename
                original_path = self.selected_file.get()
                base, ext = os.path.splitext(original_path)
                new_path = f"{base}_with_locations{ext}"
                success, message = self.bsx_handler.save_bsx_file(new_path)
            
            if success:
                messagebox.showinfo("Success", f"File saved successfully!\n{message}")
            else:
                messagebox.showerror("Error", f"Failed to save file: {message}")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error while saving: {str(e)}")
    
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BrickLinkStorageApp()
    app.run()