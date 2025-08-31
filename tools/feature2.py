import customtkinter as ctk
import tkinter as tk
from shared.base_tool import BaseTool

class Feature2Tool(BaseTool):
    """Feature 2 - Placeholder tool"""
    
    def get_tool_name(self) -> str:
        return "Feature 2"
    
    def get_tool_icon(self) -> str:
        return "📊"
    
    def setup_ui(self):
        """Setup the Feature 2 interface"""
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"{self.get_tool_icon()} {self.get_tool_name()}",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(20, 30))
        
        # Description
        desc_label = ctk.CTkLabel(
            self.main_frame,
            text="This is a placeholder for Feature 2.\nAnother BrickLink tool will be implemented here.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        desc_label.pack(pady=20)
        
        # Different layout for variety
        main_content = ctk.CTkFrame(self.main_frame)
        main_content.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Two column layout
        left_frame = ctk.CTkFrame(main_content)
        left_frame.pack(side="left", fill="both", expand=True, padx=(20, 10), pady=20)
        
        right_frame = ctk.CTkFrame(main_content)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 20), pady=20)
        
        # Left side
        ctk.CTkLabel(left_frame, text="Controls", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        ctk.CTkButton(left_frame, text="Option A", command=self.option_a).pack(pady=5)
        ctk.CTkButton(left_frame, text="Option B", command=self.option_b).pack(pady=5)
        ctk.CTkButton(left_frame, text="Clear Log", command=self.clear_log).pack(pady=5)
        
        # Right side
        ctk.CTkLabel(right_frame, text="Activity Log", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.log_text = ctk.CTkTextbox(right_frame, height=300)
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)
        self.log_text.insert("1.0", "Feature 2 initialized.\nReady for your implementation...\n")
    
    def option_a(self):
        """Sample option A"""
        self.log_text.insert(tk.END, "Option A selected in Feature 2\n")
    
    def option_b(self):
        """Sample option B"""
        self.log_text.insert(tk.END, "Option B selected in Feature 2\n")
    
    def clear_log(self):
        """Clear the log"""
        self.log_text.delete("1.0", tk.END)
        self.log_text.insert("1.0", "Log cleared.\n")
    
    def on_api_connected(self):
        """Called when API connection is established"""
        self.log_text.insert(tk.END, "API ready for Feature 2!\n")