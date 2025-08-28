import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import json
import os
import threading
from typing import Optional, Dict, Any
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

class ModuleBase:
    """Base class for application modules"""
    def __init__(self, parent, app_context):
        self.parent = parent
        self.app_context = app_context
        self.frame = None
        
    def create_ui(self):
        """Override in subclasses to create module UI"""
        pass
        
    def get_name(self):
        """Override in subclasses to return module name"""
        return "Base Module"
    
    def get_icon(self):
        """Override in subclasses to return module icon"""
        return "🔧"
    
    def on_activate(self):
        """Called when module becomes active"""
        pass
        
    def on_deactivate(self):
        """Called when module becomes inactive"""
        pass

class LocationAssignmentModule(ModuleBase):
    """Module for BSX location assignment functionality"""
    
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        
        # State variables
        self.selected_file = tk.StringVar()
        self.output_mode = tk.StringVar(value="new")
        self.preview_enabled = tk.BooleanVar(value=True)
        self.processing_results = None
        
    def get_name(self):
        return "Location Assignment"
    
    def get_icon(self):
        return "📍"
    
    def create_ui(self):
        """Create the location assignment UI"""
        self.frame = ctk.CTkFrame(self.parent)
        
        # Create sub-tabs for the workflow  
        self.tabview = ctk.CTkTabview(self.frame, width=850, height=580)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        self.setup_file_tab()
        self.setup_process_tab()
        self.setup_results_tab()
        
        return self.frame
    
    def setup_file_tab(self):
        tab = self.tabview.add("1. Select File")
        
        # Title with more space
        title_label = ctk.CTkLabel(tab, text="Select BSX File", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(30, 20))
        
        # File drop area - larger and more prominent
        self.file_drop_frame = ctk.CTkFrame(tab, height=120, 
                                           corner_radius=15,
                                           fg_color=("gray88", "gray22"),
                                           border_width=2,
                                           border_color=("gray70", "gray50"))
        self.file_drop_frame.pack(fill="x", padx=20, pady=30)
        
        self.file_label = ctk.CTkLabel(
            self.file_drop_frame,
            text="No file selected\nClick Browse to select a BSX file",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.file_label.pack(expand=True)
        
        # Browse button - larger and more prominent
        browse_btn = ctk.CTkButton(
            tab,
            text="Browse BSX Files",
            command=self.browse_file,
            width=220,
            height=50,
            font=ctk.CTkFont(size=16, weight="bold"),
            corner_radius=25
        )
        browse_btn.pack(pady=30)
        
        # File info - only show when file is selected
        self.file_info_text = ctk.CTkTextbox(tab, height=100, corner_radius=10)
        self.file_info_text.pack(fill="x", padx=40, pady=(20, 40))
        self.file_info_text.pack_forget()  # Hide initially
        
        # Output options - more spaced out
        options_container = ctk.CTkFrame(tab, fg_color="transparent")
        options_container.pack(pady=20)
        
        options_title = ctk.CTkLabel(options_container, text="Output Options", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        options_title.pack(pady=(0, 15))
        
        ctk.CTkRadioButton(options_container, text="Create new file (recommended)", 
                          variable=self.output_mode, value="new",
                          font=ctk.CTkFont(size=13)).pack(pady=8)
        ctk.CTkRadioButton(options_container, text="Overwrite original file", 
                          variable=self.output_mode, value="overwrite",
                          font=ctk.CTkFont(size=13)).pack(pady=8)
        
        ctk.CTkCheckBox(options_container, text="Preview changes before saving", 
                       variable=self.preview_enabled,
                       font=ctk.CTkFont(size=13)).pack(pady=15)
    
    def setup_process_tab(self):
        tab = self.tabview.add("2. Process")
        
        # More spacious layout
        title_label = ctk.CTkLabel(tab, text="Process BSX File", 
                                  font=ctk.CTkFont(size=20, weight="bold"))
        title_label.pack(pady=(40, 30))
        
        # Requirements in a clean container
        req_container = ctk.CTkFrame(tab, fg_color="transparent")
        req_container.pack(pady=20)
        
        self.req_file_label = ctk.CTkLabel(req_container, text="❌ No BSX file selected", 
                                          font=ctk.CTkFont(size=14))
        self.req_file_label.pack(pady=8)
        
        self.req_api_label = ctk.CTkLabel(req_container, text="❌ API not connected",
                                         font=ctk.CTkFont(size=14))
        self.req_api_label.pack(pady=8)
        
        # Large prominent process button
        self.process_btn = ctk.CTkButton(
            tab,
            text="🚀 Start Processing",
            command=self.start_processing_threaded,
            width=280,
            height=60,
            font=ctk.CTkFont(size=18, weight="bold"),
            state="disabled",
            corner_radius=30
        )
        self.process_btn.pack(pady=40)
        
        # Progress section
        self.progress_bar = ctk.CTkProgressBar(tab, width=600, height=12)
        self.progress_bar.pack(pady=20)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(tab, text="Ready to start", 
                                          text_color="gray",
                                          font=ctk.CTkFont(size=13))
        self.progress_status.pack(pady=(5, 30))
        
        # Log area - more compact
        self.log_text = ctk.CTkTextbox(tab, height=150, corner_radius=10)
        self.log_text.pack(fill="both", expand=True, padx=50, pady=(0, 30))
    
    def setup_results_tab(self):
        tab = self.tabview.add("3. Results")
        
        # Title
        title_label = ctk.CTkLabel(tab, text="Processing Results", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(20, 10))
        
        # Summary - direct in tab
        summary_label = ctk.CTkLabel(tab, text="Summary", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        summary_label.pack(pady=(10, 5))
        
        self.summary_text = ctk.CTkTextbox(tab, height=90)
        self.summary_text.pack(fill="x", padx=30, pady=(0, 15))
        
        # Details - direct in tab  
        details_label = ctk.CTkLabel(tab, text="Detailed Results", 
                                   font=ctk.CTkFont(size=16, weight="bold"))
        details_label.pack(pady=(10, 5))
        
        self.results_text = ctk.CTkTextbox(tab, height=200)
        self.results_text.pack(fill="both", expand=True, padx=30, pady=(0, 15))
        
        # Action buttons - clean layout
        self.save_results_btn = ctk.CTkButton(
            tab,
            text="💾 Save Updated File",
            command=self.save_results,
            width=200,
            height=45,
            state="disabled",
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.save_results_btn.pack(pady=10)
        
        self.export_log_btn = ctk.CTkButton(
            tab,
            text="📄 Export Log",
            command=self.export_log,
            width=150,
            height=35,
            state="disabled",
            fg_color="gray",
            hover_color="darkgray"
        )
        self.export_log_btn.pack(pady=(5, 20))
    
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
            self.update_process_requirements()
    
    def load_bsx_file(self, file_path: str):
        """Load and analyze the BSX file"""
        try:
            self.bsx_handler = BSXHandler()
            success, message = self.bsx_handler.load_bsx_file(file_path)
            
            if success:
                filename = os.path.basename(file_path)
                self.file_label.configure(text=f"✓ Selected: {filename}")
                
                summary = self.bsx_handler.get_file_summary()
                
                # Show the file info section
                self.file_info_text.pack(fill="x", padx=40, pady=(20, 40))
                
                # Simplified info display
                info_text = f"📁 {filename}\n"
                info_text += f"📊 {summary['total_items']} items total • {summary['items_without_locations']} need locations\n"
                
                # Show item types if multiple
                if len(summary['by_type']) > 1:
                    types = [f"{count} {type_name}" for type_name, count in summary['by_type'].items()]
                    info_text += f"🏷️ {' • '.join(types)}"
                
                self.file_info_text.delete("1.0", tk.END)
                self.file_info_text.insert("1.0", info_text)
                
            else:
                messagebox.showerror("Error Loading File", message)
                self.file_label.configure(text="Error loading file\nClick Browse to try again")
                
        except Exception as e:
            messagebox.showerror("Error", f"Unexpected error: {str(e)}")
    
    def update_process_requirements(self):
        """Update the process requirements display"""
        # Safety check - only update if UI elements exist
        if not (hasattr(self, 'req_file_label') and hasattr(self, 'req_api_label') and hasattr(self, 'process_btn')):
            return
            
        file_ready = hasattr(self, 'bsx_handler') and self.selected_file.get()
        api_ready = self.app_context.get('api_connected', False)
        
        if file_ready:
            filename = os.path.basename(self.selected_file.get())
            self.req_file_label.configure(text=f"✓ BSX file loaded: {filename}")
        else:
            self.req_file_label.configure(text="❌ No BSX file selected")
        
        if api_ready:
            self.req_api_label.configure(text="✓ API connected and inventory loaded")
        else:
            self.req_api_label.configure(text="❌ API not connected")
        
        if file_ready and api_ready:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")
    
    def start_processing_threaded(self):
        """Start the location matching process in a separate thread"""
        if not (hasattr(self, 'bsx_handler') and self.app_context.get('location_matcher')):
            messagebox.showerror("Error", "Missing required components")
            return
        
        # Update UI
        self.process_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        self.progress_status.configure(text="Starting processing...")
        self.log_text.delete("1.0", tk.END)
        
        def process_thread():
            try:
                location_matcher = self.app_context['location_matcher']
                
                # Log start
                self.app_context['main_window'].after(0, lambda: self.log_text.insert(tk.END, "Starting location matching process...\n"))
                self.app_context['main_window'].after(0, lambda: self.progress_bar.set(0.2))
                
                preview_mode = self.preview_enabled.get()
                
                self.app_context['main_window'].after(0, lambda: self.log_text.insert(tk.END, f"Processing in {'preview' if preview_mode else 'final'} mode...\n"))
                self.app_context['main_window'].after(0, lambda: self.progress_bar.set(0.4))
                
                success, results = location_matcher.process_bsx_file(self.bsx_handler, preview_only=preview_mode)
                
                if success:
                    self.processing_results = results
                    self.app_context['main_window'].after(0, lambda: self.progress_bar.set(1.0))
                    self.app_context['main_window'].after(0, lambda: self.processing_complete(True, results))
                else:
                    self.app_context['main_window'].after(0, lambda: self.processing_complete(False, results.get('error', 'Unknown error')))
                    
            except Exception as e:
                self.app_context['main_window'].after(0, lambda: self.processing_complete(False, f"Processing error: {str(e)}"))
        
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
            
            self.display_results(results)
            
            # Enable action buttons
            self.save_results_btn.configure(state="normal")
            self.export_log_btn.configure(state="normal")
            
        else:
            self.progress_status.configure(text="Processing failed")
            self.log_text.insert(tk.END, f"ERROR: {results}\n")
            messagebox.showerror("Processing Error", f"Processing failed: {results}")
    
    def display_results(self, results):
        """Display processing results in the results tab"""
        # Summary
        summary_text = f"""Processing Summary:

• Items processed: {results['total_items_processed']}
• Locations assigned: {results['locations_assigned']}
• Items without matches: {results['no_location_found']}
• Success rate: {results['success_rate']}%

Mode: {'Preview (changes not saved)' if self.preview_enabled.get() else 'Final (changes applied)'}
"""
        
        self.summary_text.delete("1.0", tk.END)
        self.summary_text.insert("1.0", summary_text)
        
        # Detailed results
        details_text = "=== LOCATION ASSIGNMENTS ===\n\n"
        
        if results['assignment_details']:
            for detail in results['assignment_details']:
                details_text += f"✓ {detail['item_name']} ({detail['item_id']})\n"
                details_text += f"  Color: {detail['color_name']}, Qty: {detail['quantity']}\n"
                details_text += f"  → Location: '{detail['assigned_location']}'\n\n"
        else:
            details_text += "No locations were assigned.\n\n"
        
        if results['items_without_matches']:
            details_text += "=== ITEMS WITHOUT MATCHES ===\n\n"
            for item in results['items_without_matches']:
                details_text += f"❌ {item['item_name']} ({item['item_id']})\n"
                details_text += f"  Color: {item['color_name']}, Qty: {item['quantity']}\n"
                details_text += f"  Reason: No existing inventory found for this item\n\n"
        
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", details_text)
    
    def save_results(self):
        """Save the processed BSX file"""
        if not hasattr(self, 'bsx_handler'):
            messagebox.showerror("Error", "No BSX file loaded")
            return
        
        try:
            # If we were in preview mode, process again for real
            if self.preview_enabled.get():
                if messagebox.askyesno("Confirm Save", "This will apply the location changes to your BSX file. Continue?"):
                    location_matcher = self.app_context['location_matcher']
                    success, results = location_matcher.process_bsx_file(self.bsx_handler, preview_only=False)
                    if not success:
                        messagebox.showerror("Error", f"Failed to apply changes: {results}")
                        return
            
            # Save the file
            overwrite = self.output_mode.get() == "overwrite"
            
            if overwrite:
                success, message = self.bsx_handler.save_bsx_file(overwrite_original=True)
            else:
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
    
    def export_log(self):
        """Export the processing log to a text file"""
        try:
            log_content = self.log_text.get("1.0", tk.END)
            results_content = self.results_text.get("1.0", tk.END)
            
            full_log = f"BrickLink Storage Location Auto-Populator - Processing Log\n"
            full_log += f"Generated: {tk.datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            full_log += f"{'='*60}\n\n"
            full_log += "PROCESSING LOG:\n"
            full_log += log_content
            full_log += "\n\nDETAILED RESULTS:\n"
            full_log += results_content
            
            # Save to file
            original_path = self.selected_file.get()
            base = os.path.splitext(original_path)[0]
            log_path = f"{base}_processing_log.txt"
            
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(full_log)
            
            messagebox.showinfo("Success", f"Processing log exported to:\n{log_path}")
            
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export log: {str(e)}")

class APISetupModule(ModuleBase):
    """Module for API configuration and connection"""
    
    def __init__(self, parent, app_context):
        super().__init__(parent, app_context)
        
        # Variables
        self.consumer_key = tk.StringVar()
        self.consumer_secret = tk.StringVar()
        self.token = tk.StringVar()
        self.token_secret = tk.StringVar()
        
    def get_name(self):
        return "API Setup"
    
    def get_icon(self):
        return "🔗"
    
    def create_ui(self):
        """Create the API setup UI"""
        self.frame = ctk.CTkFrame(self.parent)
        
        # Title
        title_label = ctk.CTkLabel(self.frame, text="BrickLink API Setup", 
                                  font=ctk.CTkFont(size=18, weight="bold"))
        title_label.pack(pady=(30, 10))
        
        # Status indicator
        self.api_status_label = ctk.CTkLabel(
            self.frame,
            text="API Status: Not Connected",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="red"
        )
        self.api_status_label.pack(pady=10)
        
        # Instructions
        instructions = ctk.CTkLabel(
            self.frame,
            text="Enter your BrickLink API credentials to connect to your store inventory.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        instructions.pack(pady=(0, 25))
        
        # Credentials - direct in frame
        cred_label = ctk.CTkLabel(self.frame, text="API Credentials", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        cred_label.pack(pady=(10, 15))
        
        # Consumer Key
        key_label = ctk.CTkLabel(self.frame, text="Consumer Key:")
        key_label.pack(pady=(5, 2))
        self.consumer_key_entry = ctk.CTkEntry(self.frame, textvariable=self.consumer_key, 
                                              width=400, height=35)
        self.consumer_key_entry.pack(pady=(0, 10))
        
        # Consumer Secret  
        secret_label = ctk.CTkLabel(self.frame, text="Consumer Secret:")
        secret_label.pack(pady=(5, 2))
        self.consumer_secret_entry = ctk.CTkEntry(self.frame, textvariable=self.consumer_secret, 
                                                 show="*", width=400, height=35)
        self.consumer_secret_entry.pack(pady=(0, 10))
        
        # Token
        token_label = ctk.CTkLabel(self.frame, text="Token:")
        token_label.pack(pady=(5, 2))
        self.token_entry = ctk.CTkEntry(self.frame, textvariable=self.token, 
                                       width=400, height=35)
        self.token_entry.pack(pady=(0, 10))
        
        # Token Secret
        token_secret_label = ctk.CTkLabel(self.frame, text="Token Secret:")
        token_secret_label.pack(pady=(5, 2))
        self.token_secret_entry = ctk.CTkEntry(self.frame, textvariable=self.token_secret, 
                                              show="*", width=400, height=35)
        self.token_secret_entry.pack(pady=(0, 20))
        
        # Buttons
        self.connect_btn = ctk.CTkButton(
            self.frame,
            text="🔗 Connect & Test",
            command=self.connect_api_threaded,
            width=180,
            height=45,
            font=ctk.CTkFont(size=15, weight="bold")
        )
        self.connect_btn.pack(pady=10)
        
        # Secondary buttons
        button_container = ctk.CTkFrame(self.frame, fg_color="transparent")
        button_container.pack(pady=10)
        
        save_btn = ctk.CTkButton(
            button_container,
            text="Save Config",
            command=self.save_config,
            width=120,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        )
        save_btn.pack(side="left", padx=5)
        
        load_btn = ctk.CTkButton(
            button_container,
            text="Load Config",
            command=self.load_config,
            width=120,
            height=35,
            fg_color="gray",
            hover_color="darkgray"
        )
        load_btn.pack(side="left", padx=5)
        
        # Connection info
        info_label = ctk.CTkLabel(self.frame, text="Connection Status", 
                                 font=ctk.CTkFont(size=16, weight="bold"))
        info_label.pack(pady=(25, 10))
        
        self.api_info_text = ctk.CTkTextbox(self.frame, height=150)
        self.api_info_text.pack(fill="both", expand=True, padx=30, pady=(0, 30))
        
        return self.frame
    
    def on_activate(self):
        """Load config when module becomes active"""
        self.load_config()
        # Auto-connect if credentials are available
        self.auto_connect_if_ready()
    
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
            self.app_context.get('logger', logging.getLogger()).error(f"Error loading config: {e}")
    
    def auto_connect_if_ready(self):
        """Automatically connect if all credentials are available"""
        # Check if all credentials are filled and valid (not default values)
        if (self.consumer_key.get().strip() and 
            self.consumer_secret.get().strip() and 
            self.token.get().strip() and 
            self.token_secret.get().strip() and
            self.consumer_key.get() != 'YOUR_CONSUMER_KEY' and
            not self.app_context.get('api_connected', False)):  # Don't reconnect if already connected
            
            # Show auto-connect status
            self.api_info_text.delete("1.0", tk.END)
            self.api_info_text.insert("1.0", "Found saved credentials. Auto-connecting to BrickLink API...\n")
            
            # Connect automatically
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
        
        # Update UI
        self.connect_btn.configure(state="disabled", text="Connecting...")
        self.api_info_text.delete("1.0", tk.END)
        self.api_info_text.insert("1.0", "Connecting to BrickLink API...\n")
        
        def connect_thread():
            try:
                # Create API client
                api = BrickLinkAPI(
                    self.consumer_key.get().strip(),
                    self.consumer_secret.get().strip(),
                    self.token.get().strip(),
                    self.token_secret.get().strip()
                )
                
                # Test connection
                success, message = api.test_connection()
                
                if success:
                    # Create location matcher and load inventory
                    location_matcher = LocationMatcher(api)
                    self.app_context['main_window'].after(0, lambda: self.api_info_text.insert(tk.END, "Loading inventory locations...\n"))
                    
                    inv_success, inv_message = location_matcher.load_inventory_locations()
                    
                    if inv_success:
                        # Store in app context
                        self.app_context['api'] = api
                        self.app_context['location_matcher'] = location_matcher
                        self.app_context['api_connected'] = True
                        
                        stats = location_matcher.get_location_statistics()
                        
                        final_message = f"{message}\n\nInventory loaded:\n{inv_message}\n\nLocation Statistics:\n"
                        final_message += f"• Items with locations: {stats['unique_items_with_locations']}\n"
                        final_message += f"• Unique storage locations: {stats['unique_locations']}\n"
                        
                        if stats['most_used_locations']:
                            final_message += "\nMost used locations:\n"
                            for location, count in list(stats['most_used_locations'].items())[:5]:
                                final_message += f"  '{location}': {count} items\n"
                        
                        self.app_context['main_window'].after(0, lambda: self.connection_complete(True, final_message))
                    else:
                        self.app_context['main_window'].after(0, lambda: self.connection_complete(False, f"Connection successful but failed to load inventory: {inv_message}"))
                else:
                    self.app_context['main_window'].after(0, lambda: self.connection_complete(False, message))
                    
            except Exception as e:
                self.app_context['main_window'].after(0, lambda: self.connection_complete(False, f"Connection error: {str(e)}"))
        
        threading.Thread(target=connect_thread, daemon=True).start()
    
    def connection_complete(self, success: bool, message: str):
        """Handle API connection completion"""
        self.connect_btn.configure(state="normal", text="Connect & Test")
        
        if success:
            self.api_status_label.configure(text="API Status: Connected ✓", text_color="green")
            self.api_info_text.insert(tk.END, f"\n[SUCCESS] {message}")
        else:
            self.api_status_label.configure(text="API Status: Connection Failed", text_color="red")
            self.api_info_text.insert(tk.END, f"\n[FAILED] {message}")
            self.app_context['api_connected'] = False
        
        # Update other modules
        self.app_context.get('update_callback', lambda: None)()

class ExpandableBrickLinkApp:
    """Main expandable application with module system"""
    
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("BrickLink Storage Manager")
        self.root.geometry("1100x800")
        self.root.minsize(1000, 700)
        
        # Application context for sharing data between modules
        self.app_context = {
            'main_window': self.root,
            'api_connected': False,
            'update_callback': self.update_modules,
            'logger': logging.getLogger(__name__)
        }
        
        # Module system
        self.modules = {}
        self.current_module = None
        
        self.setup_ui()
        self.register_modules()
        
        # Check if we should start with API setup or go directly to location assignment
        self.smart_startup()
    
    def create_module_command(self, module_id):
        """Create a command function for module activation (fixes lambda closure issue)"""
        return lambda: self.activate_module(module_id)
    
    def smart_startup(self):
        """Intelligently choose which module to start with based on saved config"""
        # Check if API credentials exist and are valid
        config_exists = os.path.exists('config.json')
        
        if config_exists:
            try:
                with open('config.json', 'r') as f:
                    config = json.load(f)
                
                credentials = config.get('api_credentials', {})
                
                # Check if we have valid credentials (not default placeholder values)
                has_credentials = (
                    credentials.get('consumer_key', '') and
                    credentials.get('consumer_secret', '') and
                    credentials.get('token', '') and
                    credentials.get('token_secret', '') and
                    credentials.get('consumer_key', '') != 'YOUR_CONSUMER_KEY'
                )
                
                if has_credentials:
                    # Start with API Setup for auto-connection, then will switch to Location Assignment
                    self.activate_module("api_setup")
                    
                    # Schedule switch to location assignment after API connects
                    def check_and_switch():
                        if self.app_context.get('api_connected', False):
                            self.activate_module("location_assignment")
                        else:
                            # Check again in 3 seconds if not connected yet
                            self.root.after(3000, check_and_switch)
                    
                    # Give API time to auto-connect, then switch
                    self.root.after(2000, check_and_switch)
                    return
                    
            except Exception as e:
                self.app_context.get('logger', logging.getLogger()).warning(f"Error reading config for smart startup: {e}")
        
        # Default: start with API setup
        self.activate_module("api_setup")
    
    def setup_ui(self):
        """Setup main UI structure"""
        # Main container
        main_container = ctk.CTkFrame(self.root)
        main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header with title
        header_frame = ctk.CTkFrame(main_container)
        header_frame.pack(fill="x", pady=(0, 10))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text="BrickLink Storage Manager",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=15)
        
        # Create content area with navigation
        content_container = ctk.CTkFrame(main_container)
        content_container.pack(fill="both", expand=True)
        
        # Sidebar for module navigation
        self.sidebar = ctk.CTkFrame(content_container, width=200)
        self.sidebar.pack(side="left", fill="y", padx=(0, 10), pady=10)
        self.sidebar.pack_propagate(False)  # Don't shrink sidebar
        
        # Module navigation title
        nav_title = ctk.CTkLabel(
            self.sidebar,
            text="Features",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        nav_title.pack(pady=(20, 10))
        
        # Content area for modules
        self.content_area = ctk.CTkFrame(content_container)
        self.content_area.pack(side="right", fill="both", expand=True, pady=10)
        
    def register_modules(self):
        """Register all available modules"""
        # API Setup Module
        api_module = APISetupModule(self.content_area, self.app_context)
        self.modules["api_setup"] = api_module
        
        # Location Assignment Module  
        location_module = LocationAssignmentModule(self.content_area, self.app_context)
        self.modules["location_assignment"] = location_module
        
        # Create navigation buttons for each module (fix lambda closure issue)
        self.nav_buttons = {}
        for module_id, module in self.modules.items():
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"{module.get_icon()} {module.get_name()}",
                command=self.create_module_command(module_id),  # Fix closure issue
                width=170,
                height=40,
                font=ctk.CTkFont(size=14),
                anchor="w"
            )
            btn.pack(pady=5, padx=10)
            self.nav_buttons[module_id] = btn
        
        # Add separator
        separator = ctk.CTkFrame(self.sidebar, height=2)
        separator.pack(fill="x", pady=20, padx=10)
        
        # Future modules placeholder
        future_label = ctk.CTkLabel(
            self.sidebar,
            text="Coming Soon:",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="gray"
        )
        future_label.pack(pady=(0, 5))
        
        future_features = [
            "📦 Location Allocation",
            "📊 Analytics Dashboard", 
            "🔄 Inventory Sync",
            "⚡ Optimization Tools"
        ]
        
        for feature in future_features:
            feature_label = ctk.CTkLabel(
                self.sidebar,
                text=feature,
                font=ctk.CTkFont(size=11),
                text_color="gray"
            )
            feature_label.pack(anchor="w", padx=20, pady=1)
    
    def activate_module(self, module_id: str):
        """Activate a specific module"""
        if module_id not in self.modules:
            return
        
        # Deactivate current module
        if self.current_module:
            self.current_module.on_deactivate()
            if self.current_module.frame:
                self.current_module.frame.pack_forget()
        
        # Activate new module
        module = self.modules[module_id]
        
        # Create UI if not exists
        if not module.frame:
            module.create_ui()
        
        # Show module UI
        module.frame.pack(fill="both", expand=True, padx=10, pady=10)
        module.on_activate()
        
        # Update navigation buttons
        for btn_id, btn in self.nav_buttons.items():
            if btn_id == module_id:
                btn.configure(fg_color=("gray75", "gray25"))  # Active color
            else:
                btn.configure(fg_color=ctk.ThemeManager.theme["CTkButton"]["fg_color"])  # Default color
        
        self.current_module = module
    
    def update_modules(self):
        """Update all modules with shared state changes"""
        for module in self.modules.values():
            if hasattr(module, 'update_process_requirements'):
                module.update_process_requirements()
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = ExpandableBrickLinkApp()
    app.run()