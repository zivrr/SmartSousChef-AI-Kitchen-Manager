import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
import threading

class KitchenGUI(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        # הפונקציה מוגדרת כעת בתוך המחלקה, לכן self.show_startup_alerts יעבוד
        self.after(1000, self.show_startup_alerts)
        
        self.controller = controller
        self.title("Smart Sous Chef - Intelligent Inventory Management")
        self.geometry("1150x850")
        
        ctk.set_appearance_mode("light")
        ctk.set_default_color_theme("green")

        self._search_job = None

        self.tabview = ctk.CTkTabview(self, width=1100, height=780)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_ai = self.tabview.add("AI Recipe Suggestion")
        self.tab_inventory = self.tabview.add("Inventory Management")
        self.tab_expiry = self.tabview.add("Product Expiry")

        self.setup_ai_tab()
        self.setup_inventory_tab()
        self.setup_expiry_tab()

    # --- פונקציות עזר של המחלקה ---
    def show_startup_alerts(self):
        """בדיקת מוצרים פגי תוקף עם העלייה"""
        all_prods = self.controller.db.get_all_products()
        total_in_db = self.controller.db.conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        
        skipped = total_in_db - len(all_prods)
        if skipped > 0:
            messagebox.showwarning("Inventory Update", 
                f"Notice: {skipped} expired products were hidden from your inventory list.")

    # --- לשונית 1: AI ---
    def setup_ai_tab(self):
        ctk.CTkLabel(self.tab_ai, text="Personal Chef (Ollama)", font=("Arial", 22, "bold")).pack(pady=10)
        self.user_prompt_entry = ctk.CTkEntry(self.tab_ai, placeholder_text="What do you want to cook?", width=650, height=45)
        self.user_prompt_entry.pack(pady=15)
        
        ai_button_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        ai_button_frame.pack(pady=5)
        self.ai_btn = ctk.CTkButton(ai_button_frame, text="Generate Custom Recipe", command=self.generate_recipe_thread, height=40, font=("Arial", 14, "bold"))
        self.ai_btn.pack(side="left", padx=10)
        self.clear_ai_btn = ctk.CTkButton(ai_button_frame, text="Clear Screen", command=self.clear_ai_screen, height=40, fg_color="#454545")
        self.clear_ai_btn.pack(side="left", padx=10)
        
        self.ai_result = ctk.CTkTextbox(self.tab_ai, width=850, height=450, font=("Arial", 16))
        self.ai_result.pack(pady=20, padx=20)

    def clear_ai_screen(self):
        self.user_prompt_entry.delete(0, 'end')
        self.ai_result.delete("1.0", "end")

    def generate_recipe_thread(self):
        user_req = self.user_prompt_entry.get()
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", "Thinking...")
        self.ai_btn.configure(state="disabled")
        
        def run():
            res = self.controller.get_ai_recipe_flow(user_req)
            self.after(0, lambda: self.display_ai_result(res))

        threading.Thread(target=run, daemon=True).start()

    def display_ai_result(self, result):
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", result)
        self.ai_btn.configure(state="normal")

    # --- לשונית 2: ניהול מלאי ---
    def setup_inventory_tab(self):
        self.tab_inventory.grid_columnconfigure(0, weight=1)
        self.tab_inventory.grid_columnconfigure(1, weight=0)
        self.tab_inventory.grid_rowconfigure(0, weight=1)

        add_frame = ctk.CTkFrame(self.tab_inventory, width=320)
        add_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")
        
        ctk.CTkLabel(add_frame, text="Add New Product", font=("Arial", 18, "bold")).pack(pady=15)
        self.name_entry = ctk.CTkEntry(add_frame, placeholder_text="Name", width=240)
        self.name_entry.pack(pady=10)
        self.weight_entry = ctk.CTkEntry(add_frame, placeholder_text="Weight", width=240)
        self.weight_entry.pack(pady=10)
        self.date_entry = ctk.CTkEntry(add_frame, placeholder_text="Expiry (DD/MM/YYYY)", width=240)
        self.date_entry.pack(pady=10)
        ctk.CTkButton(add_frame, text="Save", fg_color="green", command=self.save_product).pack(pady=25)

        list_frame = ctk.CTkFrame(self.tab_inventory)
        list_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")
        
        search_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search...", width=200)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search_keypress)
        
        ctk.CTkButton(search_frame, text="Show Expired", fg_color="#D32F2F", width=100, command=self.display_expired_only).pack(side="left", padx=5)
        ctk.CTkButton(search_frame, text="All", width=60, command=self.refresh_inventory_list).pack(side="left", padx=5)

        self.inventory_scroll = ctk.CTkScrollableFrame(list_frame, width=650, height=580)
        self.inventory_scroll.pack(pady=5, padx=10, fill="both", expand=True)
        self.refresh_inventory_list()

    def display_expired_only(self):
        for widget in self.inventory_scroll.winfo_children():
            widget.destroy()
        
        invalid_prods = self.controller.get_only_invalid_products()
        for p in invalid_prods:
            item_row = ctk.CTkFrame(self.inventory_scroll, border_width=1, border_color="red")
            item_row.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(item_row, text=f"EXPIRED: {p['name']} | Date: {p['date']}", text_color="red").pack(side="left", padx=15)
            ctk.CTkButton(item_row, text="Delete", fg_color="#C62828", width=60, 
                          command=lambda pid=p['id']: self.delete_and_refresh(pid)).pack(side="right", padx=5)

    def delete_and_refresh(self, pid):
        self.controller.delete_product_gui(pid)
        self.display_expired_only()
        self.refresh_expiry()

    def refresh_inventory_list(self):
        for widget in self.inventory_scroll.winfo_children():
            widget.destroy()
        products = self.controller.search_products(self.search_entry.get().strip())
        for p in products:
            item_row = ctk.CTkFrame(self.inventory_scroll)
            item_row.pack(fill="x", pady=5, padx=5)
            ctk.CTkLabel(item_row, text=f"{p.name} | {p.weight}g | Exp: {p.expiry_date}", width=400, anchor="w").pack(side="left", padx=15)
            ctk.CTkButton(item_row, text="Delete", fg_color="#C62828", width=60, command=lambda pid=p.id: self.delete_item(pid)).pack(side="right", padx=5)

    def delete_item(self, pid):
        self.controller.delete_product_gui(pid)
        self.refresh_inventory_list()
        self.refresh_expiry()

    def save_product(self):
        success, msg = self.controller.add_product_gui(self.name_entry.get(), "General", self.weight_entry.get(), self.date_entry.get())
        if success:
            self.refresh_inventory_list()
            self.refresh_expiry()
            messagebox.showinfo("Success", "Added!")
        else:
            messagebox.showerror("Error", msg)

    # --- לשונית 3: תוקף ---
    def setup_expiry_tab(self):
        self.expiry_scroll = ctk.CTkScrollableFrame(self.tab_expiry, width=950, height=500)
        self.expiry_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        self.refresh_expiry()

    def refresh_expiry(self):
        for widget in self.expiry_scroll.winfo_children():
            widget.destroy()
        for p, hours in self.controller.get_expiry_data():
            color = "#D32F2F" if hours <= 72 else ("#FBC02D" if hours <= 168 else "#388E3C")
            f = ctk.CTkFrame(self.expiry_scroll, fg_color=color)
            f.pack(fill="x", pady=5, padx=15)
            ctk.CTkLabel(f, text=f"{p.name} | Expires in {int(hours//24)} days", text_color="white", font=("Arial", 15, "bold")).pack(side="left", padx=25)

    def on_search_keypress(self, event):
        if self._search_job: self.after_cancel(self._search_job)
        self._search_job = self.after(300, self.refresh_inventory_list)