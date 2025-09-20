import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
import json
import os
from typing import Dict, List, Set, Optional, Tuple
import threading
import logging
import datetime


class EmptyLocationAnalyzer:
    """Analyzes empty warehouse locations by comparing config with BrickLink inventory"""
    
    def __init__(self, api=None):
        self.api = api
        self.logger = logging.getLogger(__name__)
        self.warehouse_locations: List[str] = []
        self.used_locations: Set[str] = set()
        self.empty_locations: List[str] = []
        
    def load_warehouse_locations(self) -> Tuple[bool, str]:
        """Load warehouse locations from config file"""
        try:
            if not os.path.exists('config.json'):
                return False, "Config file not found"
                
            with open('config.json', 'r') as f:
                config = json.load(f)
            
            warehouse_config = config.get('warehouse_locations', {})
            self.warehouse_locations = warehouse_config.get('locations', [])
            
            if not self.warehouse_locations:
                return False, "No warehouse locations found in config"
                
            return True, f"Loaded {len(self.warehouse_locations)} warehouse locations from config"
            
        except Exception as e:
            return False, f"Error loading warehouse locations: {e}"
    
    def get_used_locations_from_inventory(self) -> Tuple[bool, str]:
        """Get all currently used locations from BrickLink inventory"""
        try:
            if not self.api:
                return False, "API connection not available"
                
            self.logger.info("Fetching inventory to analyze used locations...")
            success, inventory_data = self.api.get_inventory()
            
            if not success:
                return False, f"Failed to fetch inventory: {inventory_data}"
            
            self.used_locations = set()
            
            for item in inventory_data:
                remarks = item.get('remarks', '').strip()
                if remarks:
                    self.used_locations.add(remarks)
            
            self.logger.info(f"Found {len(self.used_locations)} unique used locations")
            return True, f"Found {len(self.used_locations)} unique locations currently in use"
            
        except Exception as e:
            return False, f"Error analyzing inventory locations: {e}"
    
    def find_empty_locations(self) -> Tuple[bool, str]:
        """Find empty locations by comparing warehouse config with used locations"""
        try:
            if not self.warehouse_locations:
                return False, "Warehouse locations not loaded"
                
            # Find locations that are in config but not in inventory
            warehouse_set = set(self.warehouse_locations)
            self.empty_locations = sorted(list(warehouse_set - self.used_locations))
            
            # Also find locations in inventory that are not in warehouse config (potential issues)
            unknown_locations = sorted(list(self.used_locations - warehouse_set))
            
            result_msg = f"Analysis complete:\n"
            result_msg += f"• Total warehouse locations: {len(self.warehouse_locations)}\n"
            result_msg += f"• Currently used locations: {len(self.used_locations)}\n"
            result_msg += f"• Empty locations: {len(self.empty_locations)}\n"
            
            if unknown_locations:
                result_msg += f"• Unknown locations (not in config): {len(unknown_locations)}\n"
                result_msg += f"  Unknown locations: {', '.join(unknown_locations[:10])}"
                if len(unknown_locations) > 10:
                    result_msg += f" ... and {len(unknown_locations) - 10} more"
            
            return True, result_msg
            
        except Exception as e:
            return False, f"Error finding empty locations: {e}"
    
    def get_location_statistics(self) -> Dict:
        """Get detailed statistics about location usage"""
        return {
            'total_warehouse_locations': len(self.warehouse_locations),
            'used_locations_count': len(self.used_locations),
            'empty_locations_count': len(self.empty_locations),
            'utilization_percentage': (len(self.used_locations) / len(self.warehouse_locations) * 100) if self.warehouse_locations else 0,
            'empty_locations': self.empty_locations,
            'used_locations': sorted(list(self.used_locations)),
            'unknown_locations': sorted(list(self.used_locations - set(self.warehouse_locations)))
        }


class Feature4Tool:
    """UI Tool for Empty Location Analysis"""
    
    def __init__(self, parent, api=None):
        self.parent = parent
        self.api = api
        self.analyzer = EmptyLocationAnalyzer(api)
        self.logger = logging.getLogger(__name__)
        
        # Create main frame
        self.frame = ctk.CTkFrame(parent)
        self.setup_ui()
        
    def setup_ui(self):
        """Setup the user interface"""
        # Title
        title_label = ctk.CTkLabel(
            self.frame,
            text="📦 Empty Location Analyzer",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            self.frame,
            text="Find empty warehouse locations by comparing your config with BrickLink inventory",
            font=ctk.CTkFont(size=14),
            text_color="gray"
        )
        desc_label.pack(pady=(0, 20))
        
        # Control buttons
        button_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        button_frame.pack(pady=10)
        
        self.analyze_btn = ctk.CTkButton(
            button_frame,
            text="🔍 Analyze Empty Locations",
            command=self.start_analysis_threaded,
            width=200,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.analyze_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="📄 Export Results",
            command=self.export_results,
            width=150,
            height=40,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(self.frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(self.frame, text="Ready to analyze")
        self.progress_status.pack(pady=5)
        
        # Results area
        results_frame = ctk.CTkFrame(self.frame)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        results_title = ctk.CTkLabel(
            results_frame,
            text="Analysis Results",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        results_title.pack(pady=(15, 10))
        
        # Create tabview for different result types
        self.results_tabview = ctk.CTkTabview(results_frame, width=600, height=400)
        self.results_tabview.pack(padx=20, pady=(0, 15), fill="both", expand=True)
        
        # Add tabs
        self.results_tabview.add("Summary")
        self.results_tabview.add("Empty Locations")
        self.results_tabview.add("Used Locations")
        self.results_tabview.add("Unknown Locations")
        
        # Summary tab
        self.summary_text = ctk.CTkTextbox(
            self.results_tabview.tab("Summary"),
            font=ctk.CTkFont(size=12, family="Courier")
        )
        self.summary_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Empty locations tab
        self.empty_text = ctk.CTkTextbox(
            self.results_tabview.tab("Empty Locations"),
            font=ctk.CTkFont(size=12, family="Courier")
        )
        self.empty_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Used locations tab
        self.used_text = ctk.CTkTextbox(
            self.results_tabview.tab("Used Locations"),
            font=ctk.CTkFont(size=12, family="Courier")
        )
        self.used_text.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Unknown locations tab
        self.unknown_text = ctk.CTkTextbox(
            self.results_tabview.tab("Unknown Locations"),
            font=ctk.CTkFont(size=12, family="Courier")
        )
        self.unknown_text.pack(fill="both", expand=True, padx=10, pady=10)
        
    def set_api(self, api):
        """Update API connection"""
        self.api = api
        self.analyzer.api = api
        
    def start_analysis_threaded(self):
        """Start analysis in a separate thread"""
        if not self.api:
            messagebox.showerror("Error", "API connection not available. Please connect to BrickLink first.")
            return
            
        # Disable button and show progress
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.progress_bar.set(0)
        self.progress_status.configure(text="Starting analysis...")
        
        def analysis_thread():
            try:
                # Step 1: Load warehouse locations
                self.progress_bar.set(0.2)
                self.progress_status.configure(text="Loading warehouse locations from config...")
                
                success, message = self.analyzer.load_warehouse_locations()
                if not success:
                    self.show_error(f"Failed to load warehouse locations: {message}")
                    return
                
                # Step 2: Get used locations from inventory
                self.progress_bar.set(0.5)
                self.progress_status.configure(text="Analyzing inventory locations...")
                
                success, message = self.analyzer.get_used_locations_from_inventory()
                if not success:
                    self.show_error(f"Failed to analyze inventory: {message}")
                    return
                
                # Step 3: Find empty locations
                self.progress_bar.set(0.8)
                self.progress_status.configure(text="Finding empty locations...")
                
                success, message = self.analyzer.find_empty_locations()
                if not success:
                    self.show_error(f"Failed to find empty locations: {message}")
                    return
                
                # Step 4: Display results
                self.progress_bar.set(1.0)
                self.progress_status.configure(text="Analysis complete!")
                
                # Update UI with results
                self.root.after(0, self.display_results)
                
            except Exception as e:
                self.show_error(f"Analysis error: {str(e)}")
            finally:
                self.root.after(0, self.reset_ui)
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def display_results(self):
        """Display analysis results in the UI"""
        try:
            stats = self.analyzer.get_location_statistics()
            
            # Summary tab
            summary = f"EMPTY LOCATION ANALYSIS RESULTS\n"
            summary += f"{'='*50}\n\n"
            summary += f"Total Warehouse Locations: {stats['total_warehouse_locations']}\n"
            summary += f"Currently Used Locations:  {stats['used_locations_count']}\n"
            summary += f"Empty Locations:          {stats['empty_locations_count']}\n"
            summary += f"Unknown Locations:        {len(stats['unknown_locations'])}\n\n"
            summary += f"Warehouse Utilization:    {stats['utilization_percentage']:.1f}%\n\n"
            
            if stats['empty_locations_count'] > 0:
                summary += f"Available for use: {stats['empty_locations_count']} locations\n"
            else:
                summary += "All warehouse locations are currently in use!\n"
            
            self.summary_text.delete("1.0", tk.END)
            self.summary_text.insert("1.0", summary)
            
            # Empty locations tab
            if stats['empty_locations']:
                empty_list = "EMPTY LOCATIONS (Available for Use)\n"
                empty_list += f"{'='*40}\n\n"
                
                # Group by first character (R, S, etc.)
                grouped = {}
                for location in stats['empty_locations']:
                    prefix = location[0] if location else 'Other'
                    if prefix not in grouped:
                        grouped[prefix] = []
                    grouped[prefix].append(location)
                
                for prefix in sorted(grouped.keys()):
                    empty_list += f"{prefix} Locations:\n"
                    for i, location in enumerate(grouped[prefix]):
                        if i % 5 == 0 and i > 0:
                            empty_list += "\n"
                        empty_list += f"{location:6} "
                    empty_list += "\n\n"
            else:
                empty_list = "No empty locations found.\nAll warehouse locations are currently in use."
            
            self.empty_text.delete("1.0", tk.END)
            self.empty_text.insert("1.0", empty_list)
            
            # Used locations tab
            used_list = f"CURRENTLY USED LOCATIONS ({len(stats['used_locations'])} total)\n"
            used_list += f"{'='*50}\n\n"
            
            if stats['used_locations']:
                # Group by first character
                grouped = {}
                for location in stats['used_locations']:
                    prefix = location[0] if location else 'Other'
                    if prefix not in grouped:
                        grouped[prefix] = []
                    grouped[prefix].append(location)
                
                for prefix in sorted(grouped.keys()):
                    used_list += f"{prefix} Locations ({len(grouped[prefix])}):\n"
                    for i, location in enumerate(grouped[prefix]):
                        if i % 5 == 0 and i > 0:
                            used_list += "\n"
                        used_list += f"{location:6} "
                    used_list += "\n\n"
            
            self.used_text.delete("1.0", tk.END)
            self.used_text.insert("1.0", used_list)
            
            # Unknown locations tab
            if stats['unknown_locations']:
                unknown_list = "UNKNOWN LOCATIONS (Not in warehouse config)\n"
                unknown_list += f"{'='*50}\n\n"
                unknown_list += "These locations are used in inventory but not defined\n"
                unknown_list += "in your warehouse configuration:\n\n"
                
                for i, location in enumerate(stats['unknown_locations']):
                    if i % 5 == 0 and i > 0:
                        unknown_list += "\n"
                    unknown_list += f"{location:6} "
                
                unknown_list += "\n\nConsider adding these to your warehouse config if they are valid."
            else:
                unknown_list = "No unknown locations found.\n\nAll inventory locations are defined in your warehouse configuration."
            
            self.unknown_text.delete("1.0", tk.END)
            self.unknown_text.insert("1.0", unknown_list)
            
            # Enable export button
            self.export_btn.configure(state="normal")
            
        except Exception as e:
            self.show_error(f"Error displaying results: {str(e)}")
    
    def export_results(self):
        """Export results to a text file"""
        try:
            from tkinter import filedialog
            
            stats = self.analyzer.get_location_statistics()
            
            # Create export content
            content = f"EMPTY LOCATION ANALYSIS RESULTS\n"
            content += f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
            content += f"{'='*60}\n\n"
            
            content += f"SUMMARY:\n"
            content += f"Total Warehouse Locations: {stats['total_warehouse_locations']}\n"
            content += f"Currently Used Locations:  {stats['used_locations_count']}\n"
            content += f"Empty Locations:          {stats['empty_locations_count']}\n"
            content += f"Unknown Locations:        {len(stats['unknown_locations'])}\n"
            content += f"Warehouse Utilization:    {stats['utilization_percentage']:.1f}%\n\n"
            
            content += f"EMPTY LOCATIONS ({len(stats['empty_locations'])}):\n"
            content += f"{'-'*30}\n"
            for location in stats['empty_locations']:
                content += f"{location}\n"
            
            content += f"\nUSED LOCATIONS ({len(stats['used_locations'])}):\n"
            content += f"{'-'*30}\n"
            for location in stats['used_locations']:
                content += f"{location}\n"
            
            if stats['unknown_locations']:
                content += f"\nUNKNOWN LOCATIONS ({len(stats['unknown_locations'])}):\n"
                content += f"{'-'*30}\n"
                for location in stats['unknown_locations']:
                    content += f"{location}\n"
            
            # Save file
            file_path = filedialog.asksaveasfilename(
                title="Export Empty Location Analysis",
                defaultextension=".txt",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
                initialname=f"empty_locations_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            )
            
            if file_path:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                messagebox.showinfo("Export Complete", f"Results exported to:\n{file_path}")
                
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export results: {str(e)}")
    
    def show_error(self, message: str):
        """Show error message and reset UI"""
        def show_error_ui():
            messagebox.showerror("Analysis Error", message)
            self.progress_status.configure(text="Analysis failed")
            self.reset_ui()
        
        self.root.after(0, show_error_ui)
    
    def reset_ui(self):
        """Reset UI elements after analysis"""
        self.analyze_btn.configure(state="normal", text="🔍 Analyze Empty Locations")
        self.progress_bar.set(0)
    
    def show(self):
        """Show the tool frame"""
        self.frame.pack(fill="both", expand=True)
        
    def hide(self):
        """Hide the tool frame"""
        self.frame.pack_forget()
    
    @property
    def root(self):
        """Get root window for after() calls"""
        widget = self.parent
        while widget.master:
            widget = widget.master
        return widget