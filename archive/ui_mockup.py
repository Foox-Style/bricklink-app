import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import os

# Set appearance mode and color theme
ctk.set_appearance_mode("light")
ctk.set_default_color_theme("blue")

class BrickLinkApp:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("BrickLink Storage Location Auto-Populator")
        self.root.geometry("800x600")
        self.root.minsize(600, 500)
        
        # Variables
        self.selected_file = tk.StringVar()
        self.api_key = tk.StringVar()
        self.api_secret = tk.StringVar()
        self.progress_var = tk.DoubleVar()
        
        self.setup_ui()
        
    def setup_ui(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title
        title_label = ctk.CTkLabel(
            main_frame, 
            text="BrickLink Storage Location Auto-Populator",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Create tabview
        tabview = ctk.CTkTabview(main_frame, width=750, height=450)
        tabview.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Add tabs
        tab1 = tabview.add("File Processing")
        tab2 = tabview.add("API Settings")
        tab3 = tabview.add("Results")
        
        self.setup_file_tab(tab1)
        self.setup_api_tab(tab2)
        self.setup_results_tab(tab3)
        
    def setup_file_tab(self, parent):
        # File selection section
        file_frame = ctk.CTkFrame(parent)
        file_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(file_frame, text="Select BSX File", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # File drag-drop area (simulated)
        self.file_drop_frame = ctk.CTkFrame(file_frame, height=100, fg_color=("gray90", "gray20"))
        self.file_drop_frame.pack(fill="x", padx=20, pady=10)
        
        self.file_label = ctk.CTkLabel(
            self.file_drop_frame,
            text="Drag & drop BSX file here or click Browse",
            font=ctk.CTkFont(size=14)
        )
        self.file_label.pack(expand=True)
        
        # Browse button
        browse_btn = ctk.CTkButton(
            file_frame,
            text="Browse Files",
            command=self.browse_file,
            width=150,
            height=35
        )
        browse_btn.pack(pady=10)
        
        # Selected file display
        self.file_path_label = ctk.CTkLabel(file_frame, text="No file selected", 
                                           font=ctk.CTkFont(size=12))
        self.file_path_label.pack(pady=5)
        
        # Processing options
        options_frame = ctk.CTkFrame(parent)
        options_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(options_frame, text="Processing Options", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Output option
        self.output_var = tk.StringVar(value="overwrite")
        
        output_frame = ctk.CTkFrame(options_frame, fg_color="transparent")
        output_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkRadioButton(output_frame, text="Overwrite original file", 
                          variable=self.output_var, value="overwrite").pack(anchor="w", pady=5)
        ctk.CTkRadioButton(output_frame, text="Create new file", 
                          variable=self.output_var, value="new").pack(anchor="w", pady=5)
        
        # Preview option
        self.preview_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(options_frame, text="Preview changes before saving", 
                       variable=self.preview_var).pack(padx=20, pady=10, anchor="w")
        
    def setup_api_tab(self, parent):
        # API credentials section
        api_frame = ctk.CTkFrame(parent)
        api_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(api_frame, text="BrickLink API Credentials", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 20))
        
        # API Key
        ctk.CTkLabel(api_frame, text="API Key:", anchor="w").pack(fill="x", padx=20, pady=(5, 0))
        self.api_key_entry = ctk.CTkEntry(api_frame, textvariable=self.api_key, width=400)
        self.api_key_entry.pack(padx=20, pady=(0, 10))
        
        # API Secret
        ctk.CTkLabel(api_frame, text="API Secret:", anchor="w").pack(fill="x", padx=20, pady=(5, 0))
        self.api_secret_entry = ctk.CTkEntry(api_frame, textvariable=self.api_secret, 
                                           show="*", width=400)
        self.api_secret_entry.pack(padx=20, pady=(0, 15))
        
        # Test connection button
        test_btn = ctk.CTkButton(api_frame, text="Test Connection", 
                                command=self.test_connection, width=150)
        test_btn.pack(pady=10)
        
        # Connection status
        self.connection_status = ctk.CTkLabel(api_frame, text="")
        self.connection_status.pack(pady=5)
        
        # Settings section
        settings_frame = ctk.CTkFrame(parent)
        settings_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(settings_frame, text="Processing Settings", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Cache option
        self.cache_var = tk.BooleanVar(value=True)
        ctk.CTkCheckBox(settings_frame, text="Cache inventory data locally", 
                       variable=self.cache_var).pack(padx=20, pady=5, anchor="w")
        
        # Rate limiting
        rate_frame = ctk.CTkFrame(settings_frame, fg_color="transparent")
        rate_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(rate_frame, text="API Rate Limit (requests/minute):").pack(anchor="w")
        self.rate_slider = ctk.CTkSlider(rate_frame, from_=10, to=100, number_of_steps=18)
        self.rate_slider.pack(fill="x", pady=5)
        self.rate_slider.set(30)
        
    def setup_results_tab(self, parent):
        # Progress section
        progress_frame = ctk.CTkFrame(parent)
        progress_frame.pack(fill="x", padx=20, pady=20)
        
        ctk.CTkLabel(progress_frame, text="Processing Status", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=500)
        self.progress_bar.pack(padx=20, pady=10)
        self.progress_bar.set(0)
        
        # Status label
        self.status_label = ctk.CTkLabel(progress_frame, text="Ready to process")
        self.status_label.pack(pady=5)
        
        # Results section
        results_frame = ctk.CTkFrame(parent)
        results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(results_frame, text="Processing Results", 
                    font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))
        
        # Results text area
        self.results_text = ctk.CTkTextbox(results_frame, width=600, height=200)
        self.results_text.pack(padx=20, pady=10, fill="both", expand=True)
        
        # Action buttons at bottom
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.pack(fill="x", padx=20, pady=10)
        
        self.process_btn = ctk.CTkButton(
            button_frame,
            text="Start Processing",
            command=self.start_processing,
            width=150,
            height=40,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        self.process_btn.pack(side="left", padx=10)
        
        self.save_btn = ctk.CTkButton(
            button_frame,
            text="Save Results",
            command=self.save_results,
            width=150,
            height=40,
            state="disabled"
        )
        self.save_btn.pack(side="right", padx=10)
        
    def browse_file(self):
        filename = filedialog.askopenfilename(
            title="Select BSX File",
            filetypes=[("BSX files", "*.bsx"), ("XML files", "*.xml"), ("All files", "*.*")]
        )
        if filename:
            self.selected_file.set(filename)
            self.file_path_label.configure(text=f"Selected: {os.path.basename(filename)}")
            self.file_label.configure(text=f"✓ {os.path.basename(filename)}")
    
    def test_connection(self):
        # Simulate API connection test
        self.connection_status.configure(text="Testing connection...", text_color="orange")
        self.root.after(2000, lambda: self.connection_status.configure(
            text="✓ Connected successfully", text_color="green"))
    
    def start_processing(self):
        if not self.selected_file.get():
            messagebox.showerror("Error", "Please select a BSX file first")
            return
            
        # Simulate processing
        self.process_btn.configure(state="disabled")
        self.simulate_processing()
    
    def simulate_processing(self):
        # Simulate processing steps
        steps = [
            "Loading BSX file...",
            "Connecting to BrickLink API...",
            "Fetching inventory data...",
            "Processing items (1/150)...",
            "Processing items (50/150)...",
            "Processing items (100/150)...",
            "Processing items (150/150)...",
            "Matching storage locations...",
            "Generating results...",
            "Complete!"
        ]
        
        def update_progress(step_index):
            if step_index < len(steps):
                progress = step_index / (len(steps) - 1)
                self.progress_bar.set(progress)
                self.status_label.configure(text=steps[step_index])
                
                if step_index == len(steps) - 1:
                    # Final step - show results
                    self.results_text.delete("1.0", tk.END)
                    results_text = """Processing Complete!

Summary:
• Total items processed: 150
• Locations assigned: 142
• Items with no existing location: 8
• API calls made: 1
• Processing time: 45 seconds

Items with locations assigned:
✓ Brick 2x4 (Red) → Storage: A1-B2
✓ Plate 1x1 (Blue) → Storage: C3-D4
✓ Technic Beam 1x8 (Black) → Storage: E5-F6
... (139 more)

Items without existing locations:
• Minifigure Head (Tan)
• Window 1x2x3 (Trans-Clear)
... (6 more)
"""
                    self.results_text.insert("1.0", results_text)
                    self.save_btn.configure(state="normal")
                    self.process_btn.configure(state="normal", text="Process Again")
                else:
                    self.root.after(500, lambda: update_progress(step_index + 1))
        
        update_progress(0)
    
    def save_results(self):
        messagebox.showinfo("Success", "Results saved successfully!")
    
    def run(self):
        self.root.mainloop()

# Note: This is a mockup - requires 'pip install customtkinter' to run
if __name__ == "__main__":
    print("This is a UI mockup for the BrickLink Storage Location Auto-Populator")
    print("To run this mockup, install: pip install customtkinter")
    print("Then run: python ui_mockup.py")
    
    try:
        app = BrickLinkApp()
        app.run()
    except ImportError:
        print("\nCustomTkinter not installed. Install with: pip install customtkinter")