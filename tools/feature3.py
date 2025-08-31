import customtkinter as ctk
import tkinter as tk
from shared.base_tool import BaseTool

class Feature3Tool(BaseTool):
    """Feature 3 - Placeholder tool"""
    
    def get_tool_name(self) -> str:
        return "Feature 3"
    
    def get_tool_icon(self) -> str:
        return "⚡"
    
    def setup_ui(self):
        """Setup the Feature 3 interface"""
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
            text="This is a placeholder for Feature 3.\nYet another BrickLink tool placeholder.",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        desc_label.pack(pady=20)
        
        # Card-style layout
        cards_frame = ctk.CTkFrame(self.main_frame)
        cards_frame.pack(fill="both", expand=True, padx=40, pady=20)
        
        # Status card
        status_card = ctk.CTkFrame(cards_frame)
        status_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(status_card, text="Status", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        self.status_label = ctk.CTkLabel(status_card, text="Ready", text_color="green")
        self.status_label.pack(pady=5)
        
        # Actions card
        actions_card = ctk.CTkFrame(cards_frame)
        actions_card.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(actions_card, text="Quick Actions", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        actions_row = ctk.CTkFrame(actions_card, fg_color="transparent")
        actions_row.pack(pady=10)
        
        ctk.CTkButton(actions_row, text="Start", command=self.start_action, width=80).pack(side="left", padx=5)
        ctk.CTkButton(actions_row, text="Stop", command=self.stop_action, width=80).pack(side="left", padx=5)
        ctk.CTkButton(actions_row, text="Reset", command=self.reset_action, width=80).pack(side="left", padx=5)
        
        # Progress card
        progress_card = ctk.CTkFrame(cards_frame)
        progress_card.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(progress_card, text="Progress", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_card, width=300)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.details_text = ctk.CTkTextbox(progress_card, height=150)
        self.details_text.pack(fill="both", expand=True, padx=20, pady=20)
        self.details_text.insert("1.0", "Feature 3 ready for development.\nThis tool uses a card-based layout.\n")
    
    def start_action(self):
        """Start action"""
        self.status_label.configure(text="Running", text_color="orange")
        self.progress_bar.set(0.3)
        self.details_text.insert(tk.END, "Started Feature 3 process...\n")
    
    def stop_action(self):
        """Stop action"""
        self.status_label.configure(text="Stopped", text_color="red")
        self.progress_bar.set(0)
        self.details_text.insert(tk.END, "Stopped Feature 3 process.\n")
    
    def reset_action(self):
        """Reset action"""
        self.status_label.configure(text="Ready", text_color="green")
        self.progress_bar.set(0)
        self.details_text.delete("1.0", tk.END)
        self.details_text.insert("1.0", "Feature 3 reset.\n")
    
    def on_api_connected(self):
        """Called when API connection is established"""
        self.details_text.insert(tk.END, "API connection established for Feature 3!\n")