import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os
import threading
from typing import Optional
from shared.base_tool import BaseTool
from bsx_handler import BSXHandler
from location_matcher import LocationMatcher

class LocationAssignmentTool(BaseTool):
    """Location Assignment Tool"""
    
    def __init__(self, parent_frame: ctk.CTkFrame, api=None):
        self.bsx_handler: Optional[BSXHandler] = None
        self.location_matcher: Optional[LocationMatcher] = None
        self.selected_file = tk.StringVar()
        self.output_mode = tk.StringVar(value="new")
        self.preview_enabled = tk.BooleanVar(value=True)
        self.processing_results = None
        super().__init__(parent_frame, api)
    
    def get_tool_name(self) -> str:
        return "Location Assignment"
    
    def get_tool_icon(self) -> str:
        return "📦"
    
    def setup_ui(self):
        """Setup the location assignment interface"""
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"{self.get_tool_icon()} {self.get_tool_name()}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(15, 20))
        
        # File selection section
        file_frame = ctk.CTkFrame(self.main_frame)
        file_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(file_frame, text="BSX File Selection", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        # File drop area
        self.file_drop_frame = ctk.CTkFrame(file_frame, height=80, fg_color=("gray90", "gray20"))
        self.file_drop_frame.pack(fill="x", padx=15, pady=10)
        
        self.file_label = ctk.CTkLabel(
            self.file_drop_frame,
            text="No file selected - Click Browse",
            font=ctk.CTkFont(size=12)
        )
        self.file_label.pack(expand=True)
        
        # Buttons
        button_frame = ctk.CTkFrame(file_frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        browse_btn = ctk.CTkButton(
            button_frame,
            text="Browse BSX Files",
            command=self.browse_file,
            width=140,
            height=30
        )
        browse_btn.pack(side="left", padx=5)
        
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="Process Locations",
            command=self.start_processing,
            width=140,
            height=30,
            state="disabled"
        )
        self.process_btn.pack(side="left", padx=5)
        
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save File",
            command=self.save_results,
            width=100,
            height=30,
            state="disabled"
        )
        self.save_btn.pack(side="left", padx=5)
        
        # Progress section
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(progress_frame, text="Select a BSX file to begin")
        self.progress_status.pack(pady=5)
        
        # Log area
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="Processing Log", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(log_frame, height=250)
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        
        # Options
        options_frame = ctk.CTkFrame(self.main_frame)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(options_frame, text="Output Options", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        opt_controls = ctk.CTkFrame(options_frame, fg_color="transparent")
        opt_controls.pack(padx=15, pady=(0, 10))
        
        ctk.CTkRadioButton(opt_controls, text="Create new file", variable=self.output_mode, value="new").pack(anchor="w", pady=2)
        ctk.CTkRadioButton(opt_controls, text="Overwrite original", variable=self.output_mode, value="overwrite").pack(anchor="w", pady=2)
        ctk.CTkCheckBox(opt_controls, text="Preview changes first", variable=self.preview_enabled).pack(anchor="w", pady=2)
    
    def browse_file(self):
        """Browse and select a BSX file"""
        file_path = filedialog.askopenfilename(
            title="Select BSX File",
            filetypes=[("BSX files", "*.bsx"), ("XML files", "*.xml"), ("All files", "*.*")]
        )
        
        if file_path:
            self.selected_file.set(file_path)
            self.load_bsx_file(file_path)
    
    def load_bsx_file(self, file_path: str):
        """Load and analyze the BSX file"""
        try:
            self.bsx_handler = BSXHandler()
            success, message = self.bsx_handler.load_bsx_file(file_path)
            
            if success:
                filename = os.path.basename(file_path)
                self.file_label.configure(text=f"✓ {filename}")
                
                summary = self.bsx_handler.get_file_summary()
                info_text = f"File loaded: {filename}\n"
                info_text += f"• Total items: {summary['total_items']}\n"
                info_text += f"• Items needing locations: {summary['items_without_locations']}\n\n"
                
                self.log_text.delete("1.0", tk.END)
                self.log_text.insert("1.0", info_text)
                self.update_ui_status()
            else:
                messagebox.showerror("Error", message)
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
    
    def start_processing(self):
        """Start location processing"""
        if not (self.bsx_handler and self.location_matcher):
            messagebox.showerror("Error", "Missing components")
            return
        
        self.process_btn.configure(state="disabled", text="Processing...")
        self.progress_bar.set(0)
        
        def process_thread():
            try:
                self.progress_bar.set(0.3)
                success, results = self.location_matcher.process_bsx_file(
                    self.bsx_handler, 
                    preview_only=self.preview_enabled.get()
                )
                
                if success:
                    self.processing_results = results
                    self.progress_bar.set(1.0)
                    self.display_results(results)
                    self.save_btn.configure(state="normal")
                    self.process_btn.configure(state="normal", text="Process Locations")
                else:
                    self.log_text.insert(tk.END, f"ERROR: {results}\n")
                    self.process_btn.configure(state="normal", text="Process Locations")
            except Exception as e:
                self.log_text.insert(tk.END, f"ERROR: {str(e)}\n")
                self.process_btn.configure(state="normal", text="Process Locations")
        
        threading.Thread(target=process_thread, daemon=True).start()
    
    def display_results(self, results):
        """Display processing results"""
        summary = f"\n=== PROCESSING COMPLETE ===\n"
        summary += f"• Items processed: {results['total_items_processed']}\n"
        summary += f"• Locations assigned: {results['locations_assigned']}\n"
        summary += f"• Success rate: {results['success_rate']}%\n\n"
        
        if results['assignment_details']:
            summary += "=== ASSIGNMENTS ===\n"
            for detail in results['assignment_details'][:10]:  # Show first 10
                summary += f"✓ {detail['item_name']} -> '{detail['assigned_location']}'\n"
            if len(results['assignment_details']) > 10:
                summary += f"... and {len(results['assignment_details']) - 10} more\n"
        
        self.log_text.insert(tk.END, summary)
    
    def save_results(self):
        """Save the processed file"""
        if not self.bsx_handler:
            return
        
        try:
            if self.preview_enabled.get():
                success, results = self.location_matcher.process_bsx_file(self.bsx_handler, preview_only=False)
                if not success:
                    messagebox.showerror("Error", f"Failed: {results}")
                    return
            
            if self.output_mode.get() == "overwrite":
                success, message = self.bsx_handler.save_bsx_file(overwrite_original=True)
            else:
                original_path = self.selected_file.get()
                base, ext = os.path.splitext(original_path)
                new_path = f"{base}_with_locations{ext}"
                success, message = self.bsx_handler.save_bsx_file(new_path)
            
            if success:
                messagebox.showinfo("Success", f"File saved!\n{message}")
            else:
                messagebox.showerror("Error", f"Save failed: {message}")
        except Exception as e:
            messagebox.showerror("Error", f"Error: {str(e)}")
    
    def update_ui_status(self):
        """Update UI status"""
        file_ready = bool(self.bsx_handler)
        api_ready = bool(self.api)
        
        if file_ready and api_ready:
            self.progress_status.configure(text="Ready to process")
            self.process_btn.configure(state="normal")
        elif file_ready:
            self.progress_status.configure(text="File ready - API needed")
            self.process_btn.configure(state="disabled")
        elif api_ready:
            self.progress_status.configure(text="API ready - Select file")
            self.process_btn.configure(state="disabled")
        else:
            self.progress_status.configure(text="Select file and connect API")
            self.process_btn.configure(state="disabled")
    
    def on_api_connected(self):
        """Called when API connection is established"""
        if self.api:
            self.location_matcher = LocationMatcher(self.api)
            self.log_text.insert(tk.END, "API connected! Loading inventory...\n")
            
            def load_inventory():
                success, message = self.location_matcher.load_inventory_locations()
                if success:
                    self.log_text.insert(tk.END, f"Inventory loaded: {message}\n\n")
                else:
                    self.log_text.insert(tk.END, f"Inventory load failed: {message}\n\n")
                self.update_ui_status()
            
            threading.Thread(target=load_inventory, daemon=True).start()