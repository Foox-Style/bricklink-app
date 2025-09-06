import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime
from shared.base_tool import BaseTool
from minifigure_analyzer import MinifigureAnalyzer

class Feature3Tool(BaseTool):
    """Feature 3 - Buildable Minifigures Analysis"""
    
    def __init__(self, parent_frame: ctk.CTkFrame, api=None):
        self.minifigure_analyzer = None
        self.analysis_results = None
        super().__init__(parent_frame, api)
    
    def get_tool_name(self) -> str:
        return "Buildable Minifigures"
    
    def get_tool_icon(self) -> str:
        return "🧱"
    
    def setup_ui(self):
        """Setup the Buildable Minifigures Analysis interface"""
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"{self.get_tool_icon()} {self.get_tool_name()} Analysis",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 10))
        
        # Description
        desc_label = ctk.CTkLabel(
            self.main_frame,
            text="Identify complete minifigures that can be built from your current inventory parts.\nAnalyzes torsos to find buildable minifigures with exact part matching.",
            font=ctk.CTkFont(size=14),
            justify="center",
            text_color=("gray60", "gray40")
        )
        desc_label.pack(pady=(0, 20))
        
        # Card-style layout
        cards_frame = ctk.CTkFrame(self.main_frame)
        cards_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Status card
        status_card = ctk.CTkFrame(cards_frame)
        status_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(status_card, text="📊 Analysis Status", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.status_label = ctk.CTkLabel(status_card, text="Ready - Connect API to begin analysis", text_color="orange")
        self.status_label.pack(pady=5)
        
        # Actions card
        actions_card = ctk.CTkFrame(cards_frame)
        actions_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(actions_card, text="🔧 Analysis Actions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        actions_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_row.pack(pady=10)
        
        self.analyze_btn = ctk.CTkButton(
            actions_row, 
            text="🔍 Analyze Buildables", 
            command=self.start_analysis, 
            width=150,
            state="disabled"
        )
        self.analyze_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            actions_row, 
            text="📄 Export BSX", 
            command=self.export_minifigures, 
            width=120,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)
        
        self.clear_btn = ctk.CTkButton(
            actions_row, 
            text="🗑️ Clear Results", 
            command=self.clear_results, 
            width=120
        )
        self.clear_btn.pack(side="left", padx=5)
        
        # Progress card
        progress_card = ctk.CTkFrame(cards_frame)
        progress_card.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(progress_card, text="📋 Analysis Progress & Results", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_card, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.results_text = ctk.CTkTextbox(progress_card, height=300)
        self.results_text.pack(fill="both", expand=True, padx=20, pady=20)
        self.results_text.insert("1.0", "Welcome to Buildable Minifigures Analysis!\n\n")
        self.results_text.insert(tk.END, "This tool will:\n")
        self.results_text.insert(tk.END, "1. Scan your inventory for torso parts\n")
        self.results_text.insert(tk.END, "2. Find minifigures that use those torsos\n")
        self.results_text.insert(tk.END, "3. Check if all required parts are available\n")
        self.results_text.insert(tk.END, "4. Calculate maximum buildable quantities\n")
        self.results_text.insert(tk.END, "5. Export results to BSX file\n\n")
        self.results_text.insert(tk.END, "Connect to BrickLink API to get started.\n")
    
    def start_analysis(self):
        """Start minifigure buildability analysis"""
        if not self.api:
            messagebox.showerror("Error", "API connection required for analysis")
            return
        
        if not self.minifigure_analyzer:
            self.minifigure_analyzer = MinifigureAnalyzer(self.api)
        
        # Update UI
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.status_label.configure(text="Running Analysis...", text_color="orange")
        self.progress_bar.set(0)
        self.results_text.delete("1.0", tk.END)
        self.results_text.insert("1.0", "Starting buildable minifigures analysis...\n\n")
        
        def progress_callback(status):
            """Callback for progress updates"""
            def update_ui():
                self.results_text.insert(tk.END, f"{status}\n")
                self.results_text.see(tk.END)
            
            # Use after to update UI from thread
            self.main_frame.after(0, update_ui)
        
        def analysis_thread():
            """Run analysis in separate thread"""
            try:
                success, results = self.minifigure_analyzer.analyze_buildable_minifigures(progress_callback)
                
                # Update UI from main thread
                self.main_frame.after(0, lambda: self.analysis_complete(success, results))
                
            except Exception as e:
                self.main_frame.after(0, lambda: self.analysis_complete(False, {"error": str(e)}))
        
        # Start analysis in background thread
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def analysis_complete(self, success: bool, results):
        """Handle analysis completion"""
        self.analyze_btn.configure(state="normal", text="🔍 Analyze Buildables")
        
        if success:
            self.analysis_results = results
            self.status_label.configure(text="Analysis Complete!", text_color="green")
            self.progress_bar.set(1.0)
            
            # Display results
            self.results_text.insert(tk.END, "\n" + "="*50 + "\n")
            self.results_text.insert(tk.END, "BUILDABLE MINIFIGURES ANALYSIS COMPLETE\n")
            self.results_text.insert(tk.END, "="*50 + "\n\n")
            
            self.results_text.insert(tk.END, f"📊 Analysis Summary:\n")
            self.results_text.insert(tk.END, f"• Torsos processed: {results.get('total_torsos_processed', 0)}\n")
            self.results_text.insert(tk.END, f"• Minifigures checked: {results.get('total_minifigures_checked', 0)}\n")
            self.results_text.insert(tk.END, f"• Buildable minifigures: {results.get('buildable_count', 0)}\n")
            self.results_text.insert(tk.END, f"• {results.get('summary', '')}\n\n")
            
            buildable_minifigures = results.get('buildable_minifigures', [])
            if buildable_minifigures:
                self.results_text.insert(tk.END, "🧱 Buildable Minifigures Found:\n")
                self.results_text.insert(tk.END, "-" * 40 + "\n")
                
                for i, minifig in enumerate(buildable_minifigures, 1):
                    limiting_part = minifig.limiting_part
                    self.results_text.insert(tk.END, f"\n{i}. {minifig.minifig_name}\n")
                    self.results_text.insert(tk.END, f"   -> Can build: {minifig.max_buildable_quantity} complete minifigures\n")
                    self.results_text.insert(tk.END, f"   -> Limited by: {limiting_part.get('item_name', 'Unknown')}\n")
                    self.results_text.insert(tk.END, f"   -> Part ID: {limiting_part.get('item_id', 'N/A')}\n")
                    self.results_text.insert(tk.END, f"   -> Required parts: {len(minifig.required_parts)} different parts\n")
                
                # Enable export button
                self.export_btn.configure(state="normal")
                
                self.results_text.insert(tk.END, f"\n\nReady to export {len(buildable_minifigures)} buildable minifigures to BSX file!\n")
            else:
                self.results_text.insert(tk.END, "❌ No buildable minifigures found with current inventory.\n")
                self.results_text.insert(tk.END, "\nThis could mean:\n")
                self.results_text.insert(tk.END, "• No torso parts in inventory\n")
                self.results_text.insert(tk.END, "• Missing required parts for complete minifigures\n")
                self.results_text.insert(tk.END, "• Inventory doesn't contain complete sets\n")
        else:
            self.status_label.configure(text="Analysis Failed", text_color="red")
            self.progress_bar.set(0)
            error_msg = results.get('error', 'Unknown error') if isinstance(results, dict) else str(results)
            self.results_text.insert(tk.END, f"\n❌ ERROR: {error_msg}\n")
            messagebox.showerror("Analysis Error", f"Analysis failed: {error_msg}")
    
    def export_minifigures(self):
        """Export buildable minifigures to BSX file"""
        if not self.analysis_results or not self.analysis_results.get('buildable_minifigures'):
            messagebox.showerror("Error", "No buildable minifigures to export")
            return
        
        try:
            # Generate default filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            default_filename = f"buildable_minifigures_{timestamp}.bsx"
            
            # Ask user for save location
            file_path = filedialog.asksaveasfilename(
                title="Save Buildable Minifigures BSX",
                defaultextension=".bsx",
                initialfile=default_filename,
                filetypes=[
                    ("BSX files", "*.bsx"),
                    ("XML files", "*.xml"),
                    ("All files", "*.*")
                ]
            )
            
            if file_path:
                buildable_minifigures = self.analysis_results['buildable_minifigures']
                success, result = self.minifigure_analyzer.create_minifigures_bsx(buildable_minifigures, file_path)
                
                if success:
                    self.results_text.insert(tk.END, f"\n✅ SUCCESS: Exported {len(buildable_minifigures)} buildable minifigures\n")
                    self.results_text.insert(tk.END, f"📁 File saved: {result}\n")
                    
                    messagebox.showinfo(
                        "Export Success", 
                        f"Buildable minifigures exported successfully!\n\n"
                        f"File: {result}\n"
                        f"Minifigures: {len(buildable_minifigures)}"
                    )
                else:
                    self.results_text.insert(tk.END, f"\n❌ Export failed: {result}\n")
                    messagebox.showerror("Export Error", f"Failed to export minifigures: {result}")
                    
        except Exception as e:
            error_msg = f"Unexpected error during export: {str(e)}"
            self.results_text.insert(tk.END, f"\n❌ {error_msg}\n")
            messagebox.showerror("Export Error", error_msg)
    
    def clear_results(self):
        """Clear analysis results and reset UI"""
        self.analysis_results = None
        self.export_btn.configure(state="disabled")
        self.progress_bar.set(0)
        self.results_text.delete("1.0", tk.END)
        
        if self.api:
            self.status_label.configure(text="Ready for Analysis", text_color="green")
            self.results_text.insert("1.0", "Results cleared. Ready for new analysis.\n\n")
        else:
            self.status_label.configure(text="Ready - Connect API to begin analysis", text_color="orange")
            self.results_text.insert("1.0", "Results cleared. Connect API to begin analysis.\n\n")
    
    def on_api_connected(self):
        """Called when API connection is established"""
        if self.api:
            self.minifigure_analyzer = MinifigureAnalyzer(self.api)
            self.analyze_btn.configure(state="normal")
            self.status_label.configure(text="Ready for Analysis", text_color="green")
            self.results_text.insert(tk.END, "✅ API connected! Minifigure analyzer ready.\n")
            self.results_text.insert(tk.END, "Click 'Analyze Buildables' to start scanning your inventory.\n\n")
        else:
            self.analyze_btn.configure(state="disabled")
            self.export_btn.configure(state="disabled")
            self.status_label.configure(text="Ready - Connect API to begin analysis", text_color="orange")