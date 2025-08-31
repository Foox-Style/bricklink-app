import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from shared.base_tool import BaseTool
from bsx_handler import BSXHandler
import xml.etree.ElementTree as ET

class RestockAnalysisTool(BaseTool):
    """Sold Out Parts Restock Analysis Tool"""
    
    def __init__(self, parent_frame: ctk.CTkFrame, api=None):
        self.analysis_results: Optional[Dict] = None
        self.time_period = tk.StringVar(value="3")  # Default 3 months
        self.processing = False
        super().__init__(parent_frame, api)
    
    def get_tool_name(self) -> str:
        return "Restock Analysis"
    
    def get_tool_icon(self) -> str:
        return "📊"
    
    def setup_ui(self):
        """Setup the restock analysis interface"""
        self.main_frame = ctk.CTkFrame(self.parent_frame)
        
        # Title
        title_label = ctk.CTkLabel(
            self.main_frame,
            text=f"{self.get_tool_icon()} {self.get_tool_name()}",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title_label.pack(pady=(15, 20))
        
        # Configuration section
        config_frame = ctk.CTkFrame(self.main_frame)
        config_frame.pack(fill="x", padx=20, pady=10)
        
        ctk.CTkLabel(config_frame, text="Analysis Configuration", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        # Description
        desc_text = "Identify parts that sold in the past but are currently out of stock."
        desc_label = ctk.CTkLabel(
            config_frame,
            text=desc_text,
            font=ctk.CTkFont(size=12)
        )
        desc_label.pack(pady=(0, 10))
        
        # Time period selector
        time_config = ctk.CTkFrame(config_frame, fg_color="transparent")
        time_config.pack(pady=10)
        
        ctk.CTkLabel(time_config, text="Look back period:").pack(side="left", padx=(15, 5))
        
        period_menu = ctk.CTkOptionMenu(
            time_config,
            variable=self.time_period,
            values=["1", "2", "3", "4", "5", "6"],
            width=80
        )
        period_menu.pack(side="left", padx=5)
        
        ctk.CTkLabel(time_config, text="months").pack(side="left", padx=(5, 15))
        
        # Control buttons
        button_frame = ctk.CTkFrame(config_frame, fg_color="transparent")
        button_frame.pack(pady=15)
        
        self.analyze_btn = ctk.CTkButton(
            button_frame,
            text="Start Analysis",
            command=self.start_analysis,
            width=140,
            height=30,
            state="disabled"
        )
        self.analyze_btn.pack(side="left", padx=5)
        
        self.export_btn = ctk.CTkButton(
            button_frame,
            text="Export BSX",
            command=self.export_results,
            width=100,
            height=30,
            state="disabled"
        )
        self.export_btn.pack(side="left", padx=5)
        
        # Progress section
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.pack(fill="x", padx=20, pady=10)
        
        self.progress_bar = ctk.CTkProgressBar(progress_frame, width=400)
        self.progress_bar.pack(pady=10)
        self.progress_bar.set(0)
        
        self.progress_status = ctk.CTkLabel(progress_frame, text="Connect API to begin analysis")
        self.progress_status.pack(pady=5)
        
        # Log area (combined with results)
        log_frame = ctk.CTkFrame(self.main_frame)
        log_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(log_frame, text="Analysis Log", 
                    font=ctk.CTkFont(size=14, weight="bold")).pack(pady=(10, 5))
        
        self.log_text = ctk.CTkTextbox(log_frame, height=250)
        self.log_text.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.log_text.insert("1.0", "Ready for restock analysis...\n")
    
    def start_analysis(self):
        """Start the restock analysis process"""
        if not self.api or self.processing:
            return
        
        self.processing = True
        self.analyze_btn.configure(state="disabled", text="Analyzing...")
        self.progress_bar.set(0)
        self.progress_status.configure(text="Starting analysis...")
        
        # Clear previous results
        self.log_text.delete("1.0", tk.END)
        self.analysis_results = None
        
        def analysis_thread():
            try:
                months = int(self.time_period.get())
                self.log_text.insert(tk.END, f"Starting restock analysis for {months} months lookback...\n\n")
                
                # Step 1: Get current inventory
                self.progress_bar.set(0.1)
                self.progress_status.configure(text="Fetching current inventory...")
                self.log_text.insert(tk.END, "Step 1: Fetching current inventory...\n")
                self.log_text.see(tk.END)  # Scroll to bottom
                self.log_text.update()  # Force UI update
                
                success, inventory = self.get_current_inventory()
                if not success:
                    self.log_text.insert(tk.END, f"ERROR: Failed to get inventory: {inventory}\n")
                    self.log_text.see(tk.END)
                    self.reset_ui()
                    return
                
                self.log_text.insert(tk.END, f"-> Found {len(inventory)} inventory items\n\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                # Step 2: Get order history
                self.progress_bar.set(0.3)
                self.progress_status.configure(text="Fetching order history...")
                self.log_text.insert(tk.END, "Step 2: Fetching order history...\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                success, orders = self.get_order_history(months)
                if not success:
                    self.log_text.insert(tk.END, f"ERROR: Failed to get orders: {orders}\n")
                    self.log_text.see(tk.END)
                    self.reset_ui()
                    return
                
                self.log_text.insert(tk.END, f"-> Found {len(orders)} completed orders\n\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                # Step 3: Extract sold items from orders
                self.progress_bar.set(0.5)
                self.progress_status.configure(text="Processing sold items...")
                self.log_text.insert(tk.END, "Step 3: Extracting sold items from orders...\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                sold_items = self.extract_sold_items(orders)
                self.log_text.insert(tk.END, f"-> Found {len(sold_items)} unique item+color combinations sold\n\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                # Step 4: Cross-reference with inventory
                self.progress_bar.set(0.7)
                self.progress_status.configure(text="Identifying out-of-stock items...")
                self.log_text.insert(tk.END, "Step 4: Cross-referencing with current inventory...\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                out_of_stock = self.find_out_of_stock_items(sold_items, inventory)
                self.log_text.insert(tk.END, f"-> Identified {len(out_of_stock)} out-of-stock items with sales history\n\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                # Step 5: Generate results
                self.progress_bar.set(0.9)
                self.progress_status.configure(text="Generating analysis results...")
                self.log_text.insert(tk.END, "Step 5: Generating analysis results...\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                self.analysis_results = {
                    'out_of_stock_items': out_of_stock,
                    'total_sold_items': len(sold_items),
                    'total_inventory_items': len(inventory),
                    'lookback_months': months,
                    'analysis_date': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                # Display summary in log
                self.display_summary()
                
                self.progress_bar.set(1.0)
                self.progress_status.configure(text="Analysis complete!")
                self.log_text.insert(tk.END, "Analysis completed successfully!\n\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                self.export_btn.configure(state="normal")
                
            except Exception as e:
                self.log_text.insert(tk.END, f"ERROR: Analysis failed: {str(e)}\n")
            finally:
                self.reset_ui()
        
        threading.Thread(target=analysis_thread, daemon=True).start()
    
    def get_current_inventory(self) -> Tuple[bool, List[Dict]]:
        """Get current inventory from BrickLink API"""
        try:
            success, inventory_data = self.api.get_inventory()
            if success:
                return True, inventory_data
            else:
                return False, inventory_data
        except Exception as e:
            return False, str(e)
    
    def get_order_history(self, months: int) -> Tuple[bool, List[Dict]]:
        """Get order history from BrickLink API"""
        try:
            # Get all sales orders (direction="in" means orders where you are the seller)
            self.log_text.insert(tk.END, "   Fetching all sales orders...\n")
            self.log_text.see(tk.END)
            self.log_text.update()
            
            success, response_data = self.api._make_request("/orders", params={"direction": "in"})
            
            if success:
                all_orders = response_data.get('data', [])
                self.log_text.insert(tk.END, f"   Found {len(all_orders)} total orders\n")
                
                # Show status breakdown for debugging
                status_counts = {}
                for order in all_orders:
                    status = order.get('status', 'unknown')
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                if status_counts:
                    self.log_text.insert(tk.END, "   Status breakdown: ")
                    status_list = [f"{status}({count})" for status, count in sorted(status_counts.items())]
                    self.log_text.insert(tk.END, f"{', '.join(status_list)}\n")
                
                # Filter for fulfilled orders (orders that have been sold and shipped)
                fulfilled_statuses = {"COMPLETED", "SHIPPED", "RECEIVED", "OCR"}  # OCR = Order Complete & Rated
                fulfilled_orders = [order for order in all_orders if order.get('status') in fulfilled_statuses]
                
                self.log_text.insert(tk.END, f"   Fulfilled orders for analysis: {len(fulfilled_orders)}\n")
                self.log_text.see(tk.END)
                self.log_text.update()
                
                # TODO: Implement proper date filtering based on BrickLink API date format
                # For now, return all fulfilled orders
                return True, fulfilled_orders
            else:
                error_msg = response_data.get('error', 'Failed to fetch orders')
                return False, error_msg
                
        except Exception as e:
            return False, str(e)
    
    def extract_sold_items(self, orders: List[Dict]) -> Dict[str, Dict]:
        """Extract and aggregate sold items from order data"""
        sold_items = {}  # Key: "ItemID_ColorID", Value: {item_info, total_quantity}
        total_orders = len(orders)
        
        for i, order in enumerate(orders):
            order_id = order.get('order_id', 'unknown')
            
            # Update progress every 10 orders or for small order counts
            if i % max(1, total_orders // 10) == 0 or total_orders < 20:
                progress_text = f"Processing order {i+1}/{total_orders} ({order_id})"
                self.log_text.insert(tk.END, f"   {progress_text}...\n")
                self.log_text.see(tk.END)
                self.log_text.update()
            
            # Get order items from API
            success, items = self.api.get_order_items(order_id)
            if not success:
                self.log_text.insert(tk.END, f"   Warning: Could not get items for order {order_id}\n")
                continue
            
            # Handle nested list structure from BrickLink API
            # Sometimes the API returns items as [[ item1, item2... ]] instead of [ item1, item2... ]
            if items and isinstance(items[0], list):
                items = items[0]  # Flatten the nested list
            
            for item in items:
                try:
                    # BrickLink API structure: item has nested 'item' with details
                    if not isinstance(item, dict) or 'item' not in item:
                        continue
                    
                    item_info = item.get('item', {})
                    item_id = item_info.get('no', '')
                    color_id = item.get('color_id', 0)
                    quantity = item.get('quantity', 0)
                    item_name = item_info.get('name', '')
                    item_type = item_info.get('type', '')
                    category_id = item_info.get('category_id', 0)
                    
                    # Get price information (try different possible field names)
                    unit_price = float(item.get('unit_price_final', 0) or 
                                     item.get('unit_price', 0) or 
                                     item.get('disp_unit_price_final', 0) or 
                                     item.get('disp_unit_price', 0) or 0)
                    
                    if item_id:  # Valid item
                        # Normalize item ID (remove variant suffixes for matching)
                        normalized_item_id = self._normalize_item_id(item_id)
                        key = f"{normalized_item_id}_{color_id}"
                        
                        if key not in sold_items:
                            sold_items[key] = {
                                'item_id': item_id,
                                'color_id': color_id,
                                'item_name': item_name,
                                'item_type': item_type,
                                'category_id': category_id,
                                'total_quantity': 0,
                                'total_value': 0.0,
                                'price_count': 0
                            }
                        
                        sold_items[key]['total_quantity'] += quantity
                        
                        # Track pricing for average calculation
                        if unit_price > 0:
                            sold_items[key]['total_value'] += (unit_price * quantity)
                            sold_items[key]['price_count'] += quantity
                        
                except Exception as e:
                    self.log_text.insert(tk.END, f"   Warning: Error processing item in order {order_id}: {str(e)}\n")
                    continue
        
        
        return sold_items
    
    def find_out_of_stock_items(self, sold_items: Dict[str, Dict], inventory: List[Dict]) -> List[Dict]:
        """Find sold items that are currently out of stock"""
        # Create inventory lookup by ItemID_ColorID
        inventory_lookup = {}
        
        
        for inv_item in inventory:
            item_info = inv_item.get('item', {})
            item_id = item_info.get('no', '')
            color_id = inv_item.get('color_id', 0)
            quantity = inv_item.get('quantity', 0)
            
            if item_id:
                # Normalize item ID (remove variant suffixes for matching)
                normalized_item_id = self._normalize_item_id(item_id)
                key = f"{normalized_item_id}_{color_id}"
                if key not in inventory_lookup:
                    inventory_lookup[key] = 0
                inventory_lookup[key] += quantity
        
        
        # Find sold items with zero current stock
        out_of_stock = []
        items_with_stock = []
        
        
        for key, sold_item in sold_items.items():
            current_stock = inventory_lookup.get(key, 0)
            item_name = sold_item.get('item_name', 'Unknown')
            
            
            if current_stock == 0:  # Out of stock
                out_of_stock_item = sold_item.copy()
                out_of_stock_item['current_stock'] = current_stock
                out_of_stock.append(out_of_stock_item)
            else:
                # Track items that have stock for debugging
                items_with_stock.append({
                    'key': key,
                    'item_name': item_name,
                    'sold_qty': sold_item.get('total_quantity', 0),
                    'current_stock': current_stock
                })
        
        
        # Sort by sales volume (descending)
        out_of_stock.sort(key=lambda x: x['total_quantity'], reverse=True)
        
        return out_of_stock
    
    def display_summary(self):
        """Display the results summary in the log"""
        if not self.analysis_results:
            return
        
        results = self.analysis_results
        out_of_stock = results['out_of_stock_items']
        
        summary = f"\n=== ANALYSIS SUMMARY ({results['lookback_months']} months) ===\n"
        summary += f"• Out-of-stock items with sales history: {len(out_of_stock)}\n"
        summary += f"• Total unique items sold: {results['total_sold_items']}\n"
        summary += f"• Current inventory items: {results['total_inventory_items']}\n"
        
        if out_of_stock:
            top_item = out_of_stock[0]
            summary += f"• Highest volume item: {top_item['item_name']} ({top_item['total_quantity']} sold)\n"
            
            # Show top 5 items
            if len(out_of_stock) > 1:
                summary += f"\n=== TOP RESTOCK CANDIDATES ===\n"
                for i, item in enumerate(out_of_stock[:5]):
                    summary += f"{i+1}. {item['item_name']} - {item['total_quantity']} sold\n"
        else:
            summary += "• No out-of-stock items found with sales history\n"
        
        summary += "="*50 + "\n"
        self.log_text.insert(tk.END, summary)
    
    def export_results(self):
        """Export results to BSX file"""
        if not self.analysis_results:
            messagebox.showerror("Error", "No analysis results to export")
            return
        
        out_of_stock = self.analysis_results['out_of_stock_items']
        if not out_of_stock:
            messagebox.showinfo("No Results", "No out-of-stock items found to export")
            return
        
        # Ask for save location
        filename = filedialog.asksaveasfilename(
            title="Save Restock Analysis BSX",
            defaultextension=".bsx",
            filetypes=[("BSX files", "*.bsx"), ("All files", "*.*")],
            initialfile=f"restock_analysis_{self.analysis_results['lookback_months']}months_{datetime.now().strftime('%Y%m%d')}.bsx"
        )
        
        if filename:
            try:
                
                success = self.create_bsx_file(out_of_stock, filename)
                if success:
                    messagebox.showinfo("Export Complete", f"BSX file saved:\n{filename}\n\nContains {len(out_of_stock)} items for restocking consideration.")
                else:
                    messagebox.showerror("Export Failed", "Failed to create BSX file")
            except Exception as e:
                messagebox.showerror("Export Error", f"Error creating BSX file: {str(e)}")
    
    def create_bsx_file(self, out_of_stock_items: List[Dict], filename: str) -> bool:
        """Create BSX file with out-of-stock items and their sales volumes"""
        try:
            # Create BSX structure
            root = ET.Element("BrickStockXML")
            inventory = ET.SubElement(root, "Inventory")
            
            for item in out_of_stock_items:
                item_element = ET.SubElement(inventory, "Item")
                
                # Add item details - ensure ItemID is present and correct
                ET.SubElement(item_element, "ItemID").text = str(item['item_id'])
                
                # Convert item type to single character code
                item_type = item['item_type']
                type_code = "P"  # Default to Part
                if item_type == "PART":
                    type_code = "P"
                elif item_type == "SET":
                    type_code = "S"
                elif item_type == "MINIFIG":
                    type_code = "M"
                elif item_type == "BOOK":
                    type_code = "B"
                elif item_type == "GEAR":
                    type_code = "G"
                elif item_type == "CATALOG":
                    type_code = "C"
                elif item_type == "INSTRUCTION":
                    type_code = "I"
                
                ET.SubElement(item_element, "ItemTypeID").text = type_code
                ET.SubElement(item_element, "ColorID").text = str(item['color_id'])
                ET.SubElement(item_element, "ItemName").text = str(item['item_name'])
                ET.SubElement(item_element, "CategoryID").text = str(item['category_id'])
                
                # Use sales volume as quantity
                ET.SubElement(item_element, "Qty").text = str(item['total_quantity'])
                
                # Calculate average sale price
                if item.get('price_count', 0) > 0 and item.get('total_value', 0) > 0:
                    avg_price = item['total_value'] / item['price_count']
                    price_text = f"{avg_price:.4f}"
                else:
                    price_text = "0.0000"
                
                ET.SubElement(item_element, "Price").text = price_text
                
                # Add condition (default to New)
                ET.SubElement(item_element, "Condition").text = "N"
            
            # Format the XML nicely
            self._indent_xml(root)
            
            # Write to file
            tree = ET.ElementTree(root)
            tree.write(filename, encoding="utf-8", xml_declaration=True)
            
            return True
            
        except Exception as e:
            self.log_text.insert(tk.END, f"ERROR creating BSX file: {str(e)}\n")
            return False
    
    def _normalize_item_id(self, item_id: str) -> str:
        """Normalize BrickLink item IDs to handle variant suffixes
        
        Examples:
        - '58120c01' -> '58120'  (remove variant suffix)
        - '2335' -> '2335'       (no change)
        - '4265c' -> '4265'      (remove 'c' suffix)
        """
        if not item_id:
            return item_id
        
        # Remove common BrickLink variant suffixes
        # These patterns are used for different variants of the same base part
        normalized = item_id
        
        # Remove 'c' + digits (e.g., 'c01', 'c02')
        if 'c' in normalized:
            parts = normalized.split('c')
            if len(parts) == 2 and parts[1].isdigit():
                normalized = parts[0]
        
        # Remove standalone 'c' suffix (e.g., '4265c' -> '4265')
        if normalized.endswith('c') and len(normalized) > 1:
            normalized = normalized[:-1]
        
        return normalized
    
    def _indent_xml(self, elem, level=0):
        """Add indentation to XML elements for pretty printing"""
        indent = "  "  # 2 spaces per level
        if len(elem):  
            if not elem.text or not elem.text.strip():
                elem.text = f"\n{indent * (level + 1)}"
            if not elem.tail or not elem.tail.strip():
                elem.tail = f"\n{indent * level}"
            for child in elem:
                self._indent_xml(child, level + 1)
            if not child.tail or not child.tail.strip():
                child.tail = f"\n{indent * level}"
        else:
            if level and (not elem.tail or not elem.tail.strip()):
                elem.tail = f"\n{indent * level}"
    
    def reset_ui(self):
        """Reset UI to ready state"""
        self.processing = False
        self.analyze_btn.configure(state="normal", text="Start Analysis")
        self.progress_status.configure(text="Analysis ready")
    
    def on_api_connected(self):
        """Called when API connection is established"""
        self.log_text.insert(tk.END, "API connected! Ready to analyze restock opportunities.\n\n")
        self.analyze_btn.configure(state="normal")
        self.progress_status.configure(text="Ready to start analysis")