import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
import threading

class KitchenGUI(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        self.after(1000, self.show_startup_alerts) # מחכה שנייה אחת אחרי העלייה
        
        # הגדרות בסיסיות של חלון האפליקציה
        self.controller = controller
        self.title("Smart Sous Chef - Intelligent Inventory Management")
        self.geometry("1150x850")
        
        # הגדרת ערכת נושא
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        # משתנה לניהול השהיית החיפוש (Debounce)
        self._search_job = None

        # יצירת מערכת הלשוניות (Tabs)
        self.tabview = ctk.CTkTabview(self, width=1100, height=780)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_ai = self.tabview.add("AI Recipe Suggestion")
        self.tab_inventory = self.tabview.add("Inventory Management")
        self.tab_expiry = self.tabview.add("Product Expiry")

        # אתחול המסכים
        self.setup_ai_tab()
        self.setup_inventory_tab()
        self.setup_expiry_tab()

    # --- לשונית 1: ממשק ה-AI ---
    def setup_ai_tab(self):
        ctk.CTkLabel(self.tab_ai, text="Personal Chef (Ollama)", font=("Arial", 22, "bold")).pack(pady=10)
        
        self.user_prompt_entry = ctk.CTkEntry(self.tab_ai, 
                                              placeholder_text="What do you want to cook?", 
                                              width=650, height=45)
        self.user_prompt_entry.pack(pady=15)

        ai_button_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        ai_button_frame.pack(pady=5)

        self.ai_btn = ctk.CTkButton(ai_button_frame, text="Generate Custom Recipe", 
                                    command=self.generate_recipe_thread, height=40, font=("Arial", 14, "bold"))
        self.ai_btn.pack(side="left", padx=10)

        self.clear_ai_btn = ctk.CTkButton(ai_button_frame, text="Clear Screen", 
                                          command=self.clear_ai_screen, height=40, 
                                          fg_color="#454545", hover_color="#333333", font=("Arial", 14, "bold"))
        self.clear_ai_btn.pack(side="left", padx=10)

        self.ai_result = ctk.CTkTextbox(self.tab_ai, width=850, height=450, font=("Arial", 16))
        self.ai_result.pack(pady=20, padx=20)

    def clear_ai_screen(self):
        self.user_prompt_entry.delete(0, 'end')
        self.ai_result.delete("1.0", "end")
        self.user_prompt_entry.focus()

    def generate_recipe_thread(self):
        user_req = self.user_prompt_entry.get()
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", "The chef is thinking of a recipe... You can continue using the app.")
        self.ai_btn.configure(state="disabled")
        
        def run():
            try:
                res = self.controller.get_ai_recipe_flow(user_req)
                self.after(0, lambda: self.display_ai_result(res))
            except Exception as e:
                self.after(0, lambda: self.display_ai_result(f"AI Error: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def display_ai_result(self, result):
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", result)
        self.ai_btn.configure(state="normal")
        self.update_idletasks()

    def show_startup_alerts(self):
        # שליפת נתונים מהבקר לגבי מוצרים שסוננו
        all_prods = self.controller.db.get_all_products()
        # אם יש מוצרים ב-DB שלא נכנסו לרשימה (כי ה-DatabaseManager סינן אותם)
        total_in_db = self.controller.db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        
        skipped = total_in_db - len(all_prods)
        
        if skipped > 0:
            messagebox.showwarning("Inventory Update", 
                f"Notice: {skipped} expired products were hidden from your inventory list to ensure food safety.")

    # --- לשונית 2: ניהול מלאי ---
    def setup_inventory_tab(self):
        self.tab_inventory.grid_columnconfigure(0, weight=1) 
        self.tab_inventory.grid_columnconfigure(1, weight=0) 
        self.tab_inventory.grid_rowconfigure(0, weight=1)

        add_frame = ctk.CTkFrame(self.tab_inventory, width=320)
        add_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(add_frame, text="Add New Product", font=("Arial", 18, "bold")).pack(pady=15)
        self.name_entry = ctk.CTkEntry(add_frame, placeholder_text="Product Name", width=240)
        self.name_entry.pack(pady=10)
        self.weight_entry = ctk.CTkEntry(add_frame, placeholder_text="Weight (grams)", width=240)
        self.weight_entry.pack(pady=10)
        self.date_entry = ctk.CTkEntry(add_frame, placeholder_text="Expiry (DD/MM/YYYY)", width=240)
        self.date_entry.pack(pady=10)

        ctk.CTkButton(add_frame, text="Save to Inventory", command=self.save_product, 
                      fg_color="green", width=160, font=("Arial", 13, "bold")).pack(pady=25)

        list_frame = ctk.CTkFrame(self.tab_inventory)
        list_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(list_frame, text="Current Inventory", font=("Arial", 18, "bold")).pack(pady=15)
        
        search_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search product...", width=400)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search_keypress)
        
        ctk.CTkButton(search_frame, text="Clear", width=60, command=self.clear_search).pack(side="left")

        self.inventory_scroll = ctk.CTkScrollableFrame(list_frame, width=650, height=580)
        self.inventory_scroll.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.refresh_inventory_list()

    def on_search_keypress(self, event):
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, self.refresh_inventory_list)

    def clear_search(self):
        self.search_entry.delete(0, 'end')
        self.refresh_inventory_list()

    def refresh_inventory_list(self):
        for widget in self.inventory_scroll.winfo_children():
            widget.destroy()

        search_term = self.search_entry.get().strip()
        products = self.controller.search_products(search_term)
        
        if not products:
            ctk.CTkLabel(self.inventory_scroll, text="No products found").pack(pady=20)
        else:
            for p in products:
                item_row = ctk.CTkFrame(self.inventory_scroll)
                item_row.pack(fill="x", pady=5, padx=5)

                info_text = f"Product: {p.name} | Weight: {p.weight}g | Expiry: {p.expiry_date}"
                ctk.CTkLabel(item_row, text=info_text, width=420, anchor="w").pack(side="left", padx=15)

                ctk.CTkButton(item_row, text="Delete", width=65, fg_color="#C62828", 
                              command=lambda pid=p.id: self.delete_item(pid)).pack(side="right", padx=5)
                
                ctk.CTkButton(item_row, text="Update", width=65, 
                              command=lambda prod=p: self.update_item_weight(prod)).pack(side="right", padx=5)
        
        self.update_idletasks()

    def delete_item(self, pid):
        self.controller.delete_product_gui(pid)
        self.refresh_inventory_list()
        self.refresh_expiry()
        self.update_idletasks()

    def update_item_weight(self, prod):
        dialog = ctk.CTkInputDialog(text=f"Enter new weight for {prod.name}:", title="Update Weight")
        new_w = dialog.get_input()
        if new_w:
            self.controller.update_product_weight(prod.id, new_w)
            self.refresh_inventory_list()
            self.refresh_expiry()
            self.update_idletasks()

    def save_product(self):
        """מעבירה את הנתונים לבקר ומציגה הודעת שגיאה מפורטת במידת הצורך"""
        name = self.name_entry.get().strip()
        weight = self.weight_entry.get().strip()
        date_str = self.date_entry.get().strip()

        def run_save():
            # קבלת סטטוס והודעה מהבקר (שקיבל אותם מה-Model)
            success, message = self.controller.add_product_gui(name, "General", weight, date_str)
            if success:
                self.after(0, lambda: self.on_save_success(name))
            else:
                # הצגת סיבת השגיאה המדויקת (למשל: "Product name cannot be empty")
                self.after(0, lambda: messagebox.showerror("Validation Error", message))

        threading.Thread(target=run_save, daemon=True).start()

    def on_save_success(self, name):
        self.refresh_inventory_list()
        self.refresh_expiry()
        self.name_entry.delete(0, 'end')
        self.weight_entry.delete(0, 'end')
        self.date_entry.delete(0, 'end')
        self.update_idletasks()
        messagebox.showinfo("Success", f"Product '{name}' added successfully!")

    # --- לשונית 3: מעקב תוקף ---
    def setup_expiry_tab(self):
        ctk.CTkLabel(self.tab_expiry, text="Expiry Status", font=("Arial", 22, "bold")).pack(pady=10)
        
        legend_frame = ctk.CTkFrame(self.tab_expiry, fg_color="transparent")
        legend_frame.pack(pady=5, padx=20, fill="x")
        
        def add_legend_item(text, color, side):
            item = ctk.CTkFrame(legend_frame, fg_color="transparent")
            item.pack(side=side, padx=15)
            ctk.CTkLabel(item, text="", fg_color=color, width=20, height=20, corner_radius=5).pack(side="left", padx=5)
            ctk.CTkLabel(item, text=text, font=("Arial", 12)).pack(side="left")

        add_legend_item("Expiring Soon (72h)", "#D32F2F", "left")
        add_legend_item("Expiring Mid-term (1 Week)", "#FBC02D", "left")
        add_legend_item("Long-term Shelf Life", "#388E3C", "left")

        self.expiry_scroll = ctk.CTkScrollableFrame(self.tab_expiry, width=950, height=500)
        self.expiry_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        self.refresh_expiry()

    def refresh_expiry(self):
        for widget in self.expiry_scroll.winfo_children():
            widget.destroy()
            
        data = self.controller.get_expiry_data()
        for p, hours in data:
            if hours <= 72: color = "#D32F2F"
            elif hours <= 168: color = "#FBC02D"
            else: color = "#388E3C"

            f = ctk.CTkFrame(self.expiry_scroll, fg_color=color)
            f.pack(fill="x", pady=5, padx=15)
            
            days = int(hours // 24)
            h_rem = int(hours % 24)
            
            txt = f"Product: {p.name} | Expires in: {days} days and {h_rem} hours"
            ctk.CTkLabel(f, text=txt, text_color="black" if color == "#FBC02D" else "white", 
                          font=("Arial", 15, "bold"), anchor="w").pack(side="left", padx=25, pady=12)
        
        self.update_idletasks()