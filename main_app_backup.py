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
        
        # Create tabview
        self.tabview = ctk.CTkTabview(main_frame, width=850, height=580)
        self.tabview.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Setup tabs
        self.setup_file_tab()
        self.setup_api_tab()
        self.setup_process_tab()
        self.setup_results_tab()
        
    def setup_file_tab(self):
        tab = self.tabview.add("1. Select File")
        
        # File selection section
        file_frame = ctk.CTkFrame(tab)
        file_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(file_frame, text="BSX File Selection", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Instructions
        instructions = ctk.CTkLabel(
            file_frame,
            text="Select a BSX (BrickStore XML) file containing items that need storage locations.\nThe app will match items with your existing BrickLink inventory locations.",
            font=ctk.CTkFont(size=12),
            justify="center"
        )
        instructions.pack(pady=(0, 15))
        
        # File drop area
        self.file_drop_frame = ctk.CTkFrame(file_frame, height=120, fg_color=("gray90", "gray20"))
        self.file_drop_frame.pack(fill="x", padx=20, pady=10)
        
        self.file_label = ctk.CTkLabel(
            self.file_drop_frame,
            text="No file selected\nClick Browse to select a BSX file",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.file_label.pack(expand=True)
        
        # Browse button
        browse_btn = ctk.CTkButton(
            file_frame,
            text="Browse BSX Files",
            command=self.browse_file,
            width=160,
            height=35,
            font=ctk.CTkFont(size=14)
        )
        browse_btn.pack(pady=15)
        
        # File info display
        self.file_info_frame = ctk.CTkFrame(tab)
        self.file_info_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(self.file_info_frame, text="File Information", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.file_info_text = ctk.CTkTextbox(self.file_info_frame, height=150)
        self.file_info_text.pack(padx=20, pady=(0, 15), fill="x")
        
        # Output options
        options_frame = ctk.CTkFrame(tab)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(options_frame, text="Output Options", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Radio buttons for output mode
        output_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        output_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkRadioButton(output_frame, text="Create new file (recommended)", 
                          variable=self.output_mode, value="new").pack(anchor="w", pady=3)
        ctk.CTkRadioButton(output_frame, text="Overwrite original file", 
                          variable=self.output_mode, value="overwrite").pack(anchor="w", pady=3)
        
        # Preview checkbox
        ctk.CTkCheckBox(options_frame, text="Preview changes before saving", 
                       variable=self.preview_enabled).pack(padx=20, pady=(5, 15), anchor="w")
        
    def setup_api_tab(self):
        tab = self.tabview.add("2. API Setup")
        
        # Status indicator
        self.api_status_frame = ctk.CTkFrame(tab)
        self.api_status_frame.pack(fill="x", padx=20, pady=(20, 10))
        
        self.api_status_label = ctk.CTkLabel(
            self.api_status_frame,
            text="API Status: Not Connected",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="red"
        )
        self.api_status_label.pack(pady=10)
        
        # Credentials frame
        creds_frame = ctk.CTkFrame(tab)
        creds_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(creds_frame, text="BrickLink API Credentials", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 20))
        
        # Grid for credentials
        cred_grid = ctk.CTkFrame(creds_frame, fg_color="transparent")
        cred_grid.pack(fill="x", padx=20)
        
        # Consumer Key
        ctk.CTkLabel(cred_grid, text="Consumer Key:").grid(row=0, column=0, sticky="w", pady=5)
        self.consumer_key_entry = ctk.CTkEntry(cred_grid, textvariable=self.consumer_key, width=300)
        self.consumer_key_entry.grid(row=0, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        # Consumer Secret
        ctk.CTkLabel(cred_grid, text="Consumer Secret:").grid(row=1, column=0, sticky="w", pady=5)
        self.consumer_secret_entry = ctk.CTkEntry(cred_grid, textvariable=self.consumer_secret, 
                                                 show="*", width=300)
        self.consumer_secret_entry.grid(row=1, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        # Token
        ctk.CTkLabel(cred_grid, text="Token:").grid(row=2, column=0, sticky="w", pady=5)
        self.token_entry = ctk.CTkEntry(cred_grid, textvariable=self.token, width=300)
        self.token_entry.grid(row=2, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        # Token Secret
        ctk.CTkLabel(cred_grid, text="Token Secret:").grid(row=3, column=0, sticky="w", pady=5)
        self.token_secret_entry = ctk.CTkEntry(cred_grid, textvariable=self.token_secret, 
                                              show="*", width=300)
        self.token_secret_entry.grid(row=3, column=1, padx=(10, 0), pady=5, sticky="ew")
        
        cred_grid.columnconfigure(1, weight=1)
        
        # Buttons
        button_frame = ctk.CTkFrame(creds_frame, fg_color="transparent")
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
        info_frame = ctk.CTkFrame(tab)
        info_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(info_frame, text="Connection Information", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.api_info_text = ctk.CTkTextbox(info_frame, height=200)
        self.api_info_text.pack(padx=20, pady=(0, 15), fill="both", expand=True)
        
    def setup_process_tab(self):
        tab = self.tabview.add("3. Process")
        
        # Requirements check
        req_frame = ctk.CTkFrame(tab)
        req_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(req_frame, text="Ready to Process?", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.req_file_label = ctk.CTkLabel(req_frame, text="❌ No BSX file selected")
        self.req_file_label.pack(pady=2, anchor="w", padx=20)
        
        self.req_api_label = ctk.CTkLabel(req_frame, text="❌ API not connected")
        self.req_api_label.pack(pady=2, anchor="w", padx=20)
        
        # Process button
        self.process_btn = ctk.CTkButton(
            req_frame,
            text="Start Processing",
            command=self.start_processing_threaded,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold"),
            state="disabled"
        )
        self.process_btn.pack(pady=20)
        
        # Progress section
        progress_frame = ctk.CTkFrame(tab)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(progress_frame, text="Processing Progress", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=500)
        self.progress_bar.pack(padx=20, pady=10)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(progress_frame, text="Ready to start")
        self.progress_status.pack(pady=5)
        
        # Log section
        log_frame = ctk.CTkFrame(tab)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="Processing Log", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.log_text = ctk.CTkTextbox(log_frame, height=200)
        self.log_text.pack(padx=20, pady=(0, 15), fill="both", expand=True)
        
    def setup_results_tab(self):
        tab = self.tabview.add("4. Results")
        
        # Summary section
        summary_frame = ctk.CTkFrame(tab)
        summary_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(summary_frame, text="Processing Summary", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.summary_text = ctk.CTkTextbox(summary_frame, height=150)
        self.summary_text.pack(padx=20, pady=(0, 15), fill="x")
        
        # Details section
        details_frame = ctk.CTkFrame(tab)
        details_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(details_frame, text="Detailed Results", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        self.results_text = ctk.CTkTextbox(details_frame, height=250)
        self.results_text.pack(padx=20, pady=(0, 10), fill="both", expand=True)
        
        # Action buttons
        button_frame = ctk.CTkFrame(details_frame, fg_color="transparent")
        button_frame.pack(pady=(0, 15))
        
        self.save_results_btn = ctk.CTkButton(
            button_frame,
            text="Save Updated File",
            command=self.save_results,
            width=150,
            height=35,
            state="disabled"
        )
        self.save_results_btn.pack(side="left", padx=5)
        
        self.export_log_btn = ctk.CTkButton(
            button_frame,
            text="Export Log",
            command=self.export_log,
            width=150,
            height=35,
            state="disabled"
        )
        self.export_log_btn.pack(side="left", padx=5)
        
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
                # Update file label
                filename = os.path.basename(file_path)
                self.file_label.configure(text=f"✓ {filename}\nClick to select a different file")
                
                # Show file information
                summary = self.bsx_handler.get_file_summary()
                
                info_text = f"""File: {filename}
Path: {file_path}

Summary:
• Total items: {summary['total_items']}
• Total quantity: {summary['total_quantity']}
• Items with locations: {summary['items_with_locations']}
• Items needing locations: {summary['items_without_locations']}

Items by type:
"""
                for item_type, count in summary['by_type'].items():
                    info_text += f"• {item_type}: {count}\n"
                
                info_text += f"\nBy condition:\n"
                for condition, count in summary['by_condition'].items():
                    cond_name = "New" if condition == "N" else "Used"
                    info_text += f"• {cond_name}: {count}\n"
                
                self.file_info_text.delete("1.0", tk.END)
                self.file_info_text.insert("1.0", info_text)
                
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
        self.connect_btn.configure(state="normal", text="Connect & Test")
        
        if success:
            self.api_status_label.configure(text="API Status: Connected ✓", text_color="green")
            self.api_info_text.insert(tk.END, f"\n[SUCCESS] {message}")
        else:
            self.api_status_label.configure(text="API Status: Connection Failed", text_color="red")
            self.api_info_text.insert(tk.END, f"\n[FAILED] {message}")
            self.api_connected = False
        
        self.update_process_requirements()
    
    def update_process_requirements(self):
        """Update the process requirements display"""
        file_ready = bool(self.bsx_handler and self.selected_file.get())
        api_ready = self.api_connected
        
        if file_ready:
            filename = os.path.basename(self.selected_file.get())
            self.req_file_label.configure(text=f"✓ BSX file loaded: {filename}")
        else:
            self.req_file_label.configure(text="❌ No BSX file selected")
        
        if api_ready:
            self.req_api_label.configure(text="✓ API connected and inventory loaded")
        else:
            self.req_api_label.configure(text="❌ API not connected")
        
        # Enable process button if both requirements are met
        if file_ready and api_ready:
            self.process_btn.configure(state="normal")
        else:
            self.process_btn.configure(state="disabled")
    
    def start_processing_threaded(self):
        """Start the location matching process in a separate thread"""
        if not (self.bsx_handler and self.location_matcher):
            messagebox.showerror("Error", "Missing required components")
            return
        
        # Switch to process tab
        self.tabview.set("3. Process")
        
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
            
            # Store results but don't switch tabs - let user choose
            self.processing_results = results
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
    
    def run(self):
        """Start the application"""
        self.root.mainloop()

if __name__ == "__main__":
    app = BrickLinkStorageApp()
    app.run()