import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox
import threading

class KitchenGUI(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        
        # הגדרות בסיסיות של חלון האפליקציה
        self.controller = controller
        self.title("Smart Sous Chef - Intelligent Inventory Management")
        self.geometry("1150x850")
        
        # הגדרת ערכת נושא כהה וצבע כחול כברירת מחדל
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # משתנה לניהול השהיית החיפוש (Debounce) למניעת עומס בזמן הקלדה מהירה
        self._search_job = None

        # יצירת מערכת הלשוניות (Tabs) במרכז המסך
        self.tabview = ctk.CTkTabview(self, width=1100, height=780)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        # הוספת שלוש לשוניות: הצעת מתכון, ניהול מלאי ומעקב תוקף
        self.tab_ai = self.tabview.add("AI Recipe Suggestion")
        self.tab_inventory = self.tabview.add("Inventory Management")
        self.tab_expiry = self.tabview.add("Product Expiry")

        # קריאה לפונקציות הבנייה של כל לשונית
        self.setup_ai_tab()
        self.setup_inventory_tab()
        self.setup_expiry_tab()

    # --- לשונית 1: ממשק ה-AI (השף האישי) ---
    def setup_ai_tab(self):
        # כותרת הלשונית
        ctk.CTkLabel(self.tab_ai, text="Personal Chef (Ollama)", font=("Arial", 22, "bold")).pack(pady=10)
        
        # שדה קלט לבקשת המתכון מהמשתמש
        self.user_prompt_entry = ctk.CTkEntry(self.tab_ai, 
                                              placeholder_text="What do you want to cook? (e.g., Italian food, or only expiring items)", 
                                              width=650, height=45)
        self.user_prompt_entry.pack(pady=15)

        # יצירת מסגרת לכפתורים כדי שיעמדו אחד ליד השני
        ai_button_frame = ctk.CTkFrame(self.tab_ai, fg_color="transparent")
        ai_button_frame.pack(pady=5)

        # כפתור ליצירת מתכון
        self.ai_btn = ctk.CTkButton(ai_button_frame, text="Generate Custom Recipe", 
                                    command=self.generate_recipe_thread, height=40, font=("Arial", 14, "bold"))
        self.ai_btn.pack(side="left", padx=10)

        # כפתור ניקוי (Clear) - צבע אפור/כהה יותר כדי להבדיל מהכפתור הראשי
        self.clear_ai_btn = ctk.CTkButton(ai_button_frame, text="Clear Screen", 
                                          command=self.clear_ai_screen, height=40, 
                                          fg_color="#454545", hover_color="#333333", font=("Arial", 14, "bold"))
        self.clear_ai_btn.pack(side="left", padx=10)

        # תיבת טקסט גדולה להצגת תוצאת המתכון
        self.ai_result = ctk.CTkTextbox(self.tab_ai, width=850, height=450, font=("Arial", 16))
        self.ai_result.pack(pady=20, padx=20)

    def clear_ai_screen(self):
        """פונקציה המנקה את שדה הקלט ואת תיבת הטקסט של המתכון"""
        # מחיקת הטקסט משדה הקלט
        self.user_prompt_entry.delete(0, 'end')
        # מחיקת כל הטקסט מתיבת התוצאה
        self.ai_result.delete("1.0", "end")
        # החזרת הפוקוס לשדה הקלט לנוחות המשתמש
        self.user_prompt_entry.focus()

    def generate_recipe_thread(self):
        """מפעילה את ה-AI ב-Thread נפרד כדי שהממשק לא יקפא בזמן שהמודל חושב"""
        user_req = self.user_prompt_entry.get()
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", "The chef is thinking of a recipe... You can continue using the app.")
        self.ai_btn.configure(state="disabled") # נטרול הכפתור בזמן העבודה
        
        def run():
            try:
                # שליחת הבקשה ללוגיקה של ה-Controller
                res = self.controller.get_ai_recipe_flow(user_req)
                # עדכון התוצאה ב-Main Thread של ה-UI
                self.after(0, lambda: self.display_ai_result(res))
            except Exception as e:
                self.after(0, lambda: self.display_ai_result(f"AI Error: {e}"))

        threading.Thread(target=run, daemon=True).start()

    def display_ai_result(self, result):
        """מציגה את תוצאת ה-AI ומחזירה את הכפתור למצב פעיל"""
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", result)
        self.ai_btn.configure(state="normal")
        self.update_idletasks()

    # --- לשונית 2: ניהול מלאי (הוספה, חיפוש ומחיקה) ---
    def setup_inventory_tab(self):
        # הגדרת גריד (Grid) לחלוקת המסך לטופס ורשימה
        self.tab_inventory.grid_columnconfigure(0, weight=1) 
        self.tab_inventory.grid_columnconfigure(1, weight=0) 
        self.tab_inventory.grid_rowconfigure(0, weight=1)

        # צד ימין: טופס הוספת מוצר חדש
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

        # צד שמאל: תצוגת הרשימה ושורת חיפוש
        list_frame = ctk.CTkFrame(self.tab_inventory)
        list_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(list_frame, text="Current Inventory", font=("Arial", 18, "bold")).pack(pady=15)
        
        # שורת חיפוש (מסודרת משמאל לימין)
        search_frame = ctk.CTkFrame(list_frame, fg_color="transparent")
        search_frame.pack(fill="x", padx=20, pady=5)
        
        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Search product...", width=400)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<KeyRelease>", self.on_search_keypress)
        
        ctk.CTkButton(search_frame, text="Clear", width=60, command=self.clear_search).pack(side="left")

        # מסגרת נגללת (Scrollable) לרשימת המוצרים
        self.inventory_scroll = ctk.CTkScrollableFrame(list_frame, width=650, height=580)
        self.inventory_scroll.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.refresh_inventory_list()

    def on_search_keypress(self, event):
        """מנגנון השהייה: מחכה 300 מילישניות מסוף ההקלדה לפני ביצוע החיפוש"""
        if self._search_job:
            self.after_cancel(self._search_job)
        self._search_job = self.after(300, self.refresh_inventory_list)

    def clear_search(self):
        """מנקה את שדה החיפוש ומרענן את הרשימה המלאה"""
        self.search_entry.delete(0, 'end')
        self.refresh_inventory_list()

    def refresh_inventory_list(self):
        """בונה מחדש את רשימת המוצרים לפי החיפוש הנוכחי"""
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

                # פרטי המוצר מיושרים לשמאל
                info_text = f"Product: {p.name} | Weight: {p.weight}g | Expiry: {p.expiry_date}"
                ctk.CTkLabel(item_row, text=info_text, width=420, anchor="w").pack(side="left", padx=15)

                # כפתורי פעולה מיושרים לימין השורה
                ctk.CTkButton(item_row, text="Delete", width=65, fg_color="#C62828", 
                              command=lambda pid=p.id: self.delete_item(pid)).pack(side="right", padx=5)
                
                ctk.CTkButton(item_row, text="Update", width=65, 
                              command=lambda prod=p: self.update_item_weight(prod)).pack(side="right", padx=5)
        
        self.update_idletasks()

    def delete_item(self, pid):
        """מחיקת פריט וריענון כל המסכים הרלוונטיים"""
        self.controller.delete_product_gui(pid)
        self.refresh_inventory_list()
        self.refresh_expiry()
        self.update_idletasks()

    def update_item_weight(self, prod):
        """פתיחת חלונית קלט לעדכון משקל המוצר"""
        dialog = ctk.CTkInputDialog(text=f"Enter new weight for {prod.name}:", title="Update Weight")
        new_w = dialog.get_input()
        if new_w:
            self.controller.update_product_weight(prod.id, new_w)
            self.refresh_inventory_list()
            self.refresh_expiry()
            self.update_idletasks()

    def save_product(self):
        """אימות נתונים ושמירת מוצר חדש למסד הנתונים"""
        name = self.name_entry.get().strip()
        weight = self.weight_entry.get().strip()
        date_str = self.date_entry.get().strip()

        # בדיקת שדות ריקים
        if not name or not weight or not date_str:
            messagebox.showwarning("Missing Data", "Please fill in all fields.")
            return

        # בדיקת תקינות מספר המשקל
        try:
            w_val = float(weight)
            if w_val <= 0:
                messagebox.showerror("Weight Error", "Weight must be a positive number.")
                return
        except ValueError:
            messagebox.showerror("Weight Error", "Please enter a valid number for weight.")
            return

        # בדיקת פורמט תאריך
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("Invalid Date", "Please enter a valid date (DD/MM/YYYY)")
            return

        # ביצוע השמירה ב-Thread נפרד כדי לא לתקוע את הממשק
        def run_save():
            try:
                success = self.controller.add_product_gui(name, "General", weight, date_str)
                if success:
                    self.after(0, lambda: self.on_save_success(name))
                else:
                    self.after(0, lambda: messagebox.showerror("Error", "Failed to save to database."))
            except Exception as e:
                print(f"Save Error: {e}")

        threading.Thread(target=run_save, daemon=True).start()

    def on_save_success(self, name):
        """פעולות לביצוע לאחר שמירה מוצלחת: ניקוי שדות וריענון רשימות"""
        self.refresh_inventory_list()
        self.refresh_expiry()
        self.name_entry.delete(0, 'end')
        self.weight_entry.delete(0, 'end')
        self.date_entry.delete(0, 'end')
        self.update_idletasks()
        messagebox.showinfo("Success", f"Product '{name}' added successfully!")

    # --- לשונית 3: מעקב תוקף מוצרים ---
    def setup_expiry_tab(self):
        # כותרת ראשית
        ctk.CTkLabel(self.tab_expiry, text="Expiry Status", font=("Arial", 22, "bold")).pack(pady=10)
        
        # בניית מקרא צבעים (Legend)
        legend_frame = ctk.CTkFrame(self.tab_expiry, fg_color="transparent")
        legend_frame.pack(pady=5, padx=20, fill="x")
        
        def add_legend_item(text, color, side):
            item = ctk.CTkFrame(legend_frame, fg_color="transparent")
            item.pack(side=side, padx=15)
            ctk.CTkLabel(item, text="", fg_color=color, width=20, height=20, corner_radius=5).pack(side="left", padx=5)
            ctk.CTkLabel(item, text=text, font=("Arial", 12)).pack(side="left")

        # הוספת פריטים למקרא (אדום, צהוב, ירוק)
        add_legend_item("Expiring Soon (72h)", "#D32F2F", "left")
        add_legend_item("Expiring Mid-term (1 Week)", "#FBC02D", "left")
        add_legend_item("Long-term Shelf Life", "#388E3C", "left")

        # רשימה נגללת של סטטוס התוקף של המוצרים
        self.expiry_scroll = ctk.CTkScrollableFrame(self.tab_expiry, width=950, height=500)
        self.expiry_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        self.refresh_expiry()

    def refresh_expiry(self):
        """חישוב מחדש של זמני התוקף והצגתם עם צבע מתאים"""
        for widget in self.expiry_scroll.winfo_children():
            widget.destroy()
            
        # קבלת נתונים מה-Controller (רשימת מוצרים ושעות שנותרו)
        data = self.controller.get_expiry_data()
        for p, hours in data:
            # קביעת צבע הרקע לפי דחיפות (72 שעות או שבוע)
            if hours <= 72: color = "#D32F2F" # אדום
            elif hours <= 168: color = "#FBC02D" # צהוב
            else: color = "#388E3C" # ירוק

            f = ctk.CTkFrame(self.expiry_scroll, fg_color=color)
            f.pack(fill="x", pady=5, padx=15)
            
            # חישוב ימים ושעות מתוך סך השעות
            days = int(hours // 24)
            h_rem = int(hours % 24)
            
            txt = f"Product: {p.name} | Expires in: {days} days and {h_rem} hours"
            # כיתוב שחור על רקע צהוב לשיפור הניגודיות, לבן על האחרים
            ctk.CTkLabel(f, text=txt, text_color="black" if color == "#FBC02D" else "white", 
                          font=("Arial", 15, "bold"), anchor="w").pack(side="left", padx=25, pady=12)
        
        self.update_idletasks()