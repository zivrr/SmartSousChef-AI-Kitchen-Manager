import customtkinter as ctk
from datetime import datetime
from tkinter import messagebox

class KitchenGUI(ctk.CTk):
    def __init__(self, controller):
        super().__init__()
        
        self.controller = controller
        self.title("Smart Sous Chef - ניהול מלאי חכם")
        self.geometry("1150x850") # הגדלנו מעט לנוחות
        
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")

        # יצירת הלשוניות (מודולציה של התצוגה)
        self.tabview = ctk.CTkTabview(self, width=1100, height=780)
        self.tabview.pack(padx=20, pady=20, fill="both", expand=True)
        
        self.tab_ai = self.tabview.add("הצעת מתכון AI")
        self.tab_inventory = self.tabview.add("ניהול מלאי")
        self.tab_expiry = self.tabview.add("תוקף מוצרים")

        # אתחול המסכים
        self.setup_ai_tab()
        self.setup_inventory_tab()
        self.setup_expiry_tab()

    # --- מסך 1: ממשק AI עם פרומפט אישי ---
    def setup_ai_tab(self):
        ctk.CTkLabel(self.tab_ai, text="השף האישי (Ollama)", font=("Arial", 22, "bold")).pack(pady=10)
        
        # שדה קלט לבקשת המשתמש
        self.user_prompt_entry = ctk.CTkEntry(self.tab_ai, 
                                              placeholder_text="מה בא לך לבשל? (למשל: אוכל איטלקי, או רק דברים שפגים בקרוב)", 
                                              width=650, height=45)
        self.user_prompt_entry.pack(pady=15)

        self.ai_btn = ctk.CTkButton(self.tab_ai, text="צור מתכון מותאם אישית", 
                                    command=self.generate_recipe, height=40, font=("Arial", 14, "bold"))
        self.ai_btn.pack(pady=5)

        self.ai_result = ctk.CTkTextbox(self.tab_ai, width=850, height=450, font=("Arial", 16))
        self.ai_result.pack(pady=20, padx=20)

    def generate_recipe(self):
        user_req = self.user_prompt_entry.get()
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", "השף חושב על מתכון... אנא המתן...")
        self.update_idletasks()
        
        # שליחת הבקשה לבקר
        res = self.controller.get_ai_recipe_flow(user_req)
        self.ai_result.delete("1.0", "end")
        self.ai_result.insert("1.0", res)

    # --- מסך 2: ניהול מלאי (CRUD) ---
    def setup_inventory_tab(self):
        # הגדרת הגריד למניעת מסך ריק
        self.tab_inventory.grid_columnconfigure(0, weight=1) 
        self.tab_inventory.grid_columnconfigure(1, weight=0) 
        self.tab_inventory.grid_rowconfigure(0, weight=1)

        # צד ימין: טופס
        add_frame = ctk.CTkFrame(self.tab_inventory, width=320)
        add_frame.grid(row=0, column=1, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(add_frame, text="הוספת מוצר חדש", font=("Arial", 18, "bold")).pack(pady=15)
        
        self.name_entry = ctk.CTkEntry(add_frame, placeholder_text="שם המוצר", width=240)
        self.name_entry.pack(pady=10)

        self.weight_entry = ctk.CTkEntry(add_frame, placeholder_text="משקל בגרמים", width=240)
        self.weight_entry.pack(pady=10)

        self.date_entry = ctk.CTkEntry(add_frame, placeholder_text="תאריך (DD/MM/YYYY)", width=240)
        self.date_entry.pack(pady=10)

        ctk.CTkButton(add_frame, text="שמור במלאי", command=self.save_product, 
                      fg_color="green", width=160, font=("Arial", 13, "bold")).pack(pady=25)

        # צד שמאל: רשימה
        list_frame = ctk.CTkFrame(self.tab_inventory)
        list_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        ctk.CTkLabel(list_frame, text="המלאי הקיים שלך", font=("Arial", 18, "bold")).pack(pady=15)
        
        self.inventory_scroll = ctk.CTkScrollableFrame(list_frame, width=650, height=580)
        self.inventory_scroll.pack(pady=5, padx=10, fill="both", expand=True)
        
        self.refresh_inventory_list()

    def refresh_inventory_list(self):
        for widget in self.inventory_scroll.winfo_children():
            widget.destroy()

        products = self.controller.db.get_all_products()
        for p in products:
            item_row = ctk.CTkFrame(self.inventory_scroll)
            item_row.pack(fill="x", pady=5, padx=5)

            info_text = f"מוצר: {p.name} | משקל: {p.weight}g | תוקף: {p.expiry_date}"
            ctk.CTkLabel(item_row, text=info_text, width=420, anchor="e", font=("Arial", 13)).pack(side="right", padx=15)

            ctk.CTkButton(item_row, text="מחק", width=65, fg_color="#C62828", 
                          command=lambda pid=p.id: self.delete_item(pid)).pack(side="left", padx=5)
            
            ctk.CTkButton(item_row, text="עדכן", width=65, 
                          command=lambda prod=p: self.update_item_weight(prod)).pack(side="left", padx=5)

    def delete_item(self, pid):
        self.controller.delete_product_gui(pid)
        self.refresh_inventory_list()
        self.refresh_expiry()

    def update_item_weight(self, prod):
        dialog = ctk.CTkInputDialog(text=f"הכנס משקל חדש עבור {prod.name}:", title="עדכון משקל")
        new_w = dialog.get_input()
        if new_w:
            self.controller.update_product_weight(prod.id, new_w)
            self.refresh_inventory_list()
            self.refresh_expiry()

    def save_product(self):
        # 1. שליפת הנתונים וניקוי רווחים
        name = self.name_entry.get().strip()
        weight = self.weight_entry.get().strip()
        date_str = self.date_entry.get().strip()

        # 2. בדיקה שכל השדות מלאים
        if not name or not weight or not date_str:
            messagebox.showwarning("שדה חסר", "נא למלא את כל השדות: שם, משקל ותאריך.")
            return

        # 3. אימות משקל (מספר חיובי)
        try:
            w_val = float(weight)
            if w_val <= 0:
                messagebox.showerror("שגיאה במשקל", "המשקל חייב להיות מספר גדול מאפס.")
                return
        except ValueError:
            messagebox.showerror("שגיאה במשקל", "נא להזין מספר בלבד בשדה המשקל.")
            return

        # 4. אימות פורמט ותקינות תאריך (DD/MM/YYYY)
        try:
            datetime.strptime(date_str, "%d/%m/%Y")
        except ValueError:
            messagebox.showerror("פורמט תאריך שגוי", 
                                 f"התאריך '{date_str}' אינו תקין.\nנא להזין בפורמט: DD/MM/YYYY\n(לדוגמה: 01/05/2026)")
            return

        # 5. ניסיון שמירה
        success = self.controller.add_product_gui(name, "כללי", weight, date_str)
        
        if success:
            self.refresh_inventory_list()
            self.refresh_expiry()
            
            # ניקוי שדות
            self.name_entry.delete(0, 'end')
            self.weight_entry.delete(0, 'end')
            self.date_entry.delete(0, 'end')
            
            # הודעת הצלחה
            messagebox.showinfo("הצלחה", f"המוצר '{name}' נוסף למלאי!")
        else:
            messagebox.showerror("שגיאת מערכת", "אירעה שגיאה בשמירת המוצר במסד הנתונים.")
    # --- מסך 3: תוקף מוצרים ---
    def setup_expiry_tab(self):
        # כותרת ראשית מעודכנת
        ctk.CTkLabel(self.tab_expiry, text="סטטוס תוקף מוצרים", font=("Arial", 22, "bold")).pack(pady=10)

        # --- הוספת מקרא צבעים (Legend) ---
        legend_frame = ctk.CTkFrame(self.tab_expiry, fg_color="transparent")
        legend_frame.pack(pady=5, padx=20, fill="x")
        
        # פונקציית עזר ליצירת פריט במקרא
        def add_legend_item(text, color, side):
            item = ctk.CTkFrame(legend_frame, fg_color="transparent")
            item.pack(side=side, padx=15)
            ctk.CTkLabel(item, text="", fg_color=color, width=20, height=20, corner_radius=5).pack(side="right", padx=5)
            ctk.CTkLabel(item, text=text, font=("Arial", 12)).pack(side="right")

        # הוספת הפריטים למקרא (מימין לשמאל)
        add_legend_item("פג תוקף בקרוב (72 שע')", "#D32F2F", "right")
        add_legend_item("תוקף בינוני (עד שבוע)", "#FBC02D", "right")
        add_legend_item("תוקף ארוך", "#388E3C", "right")

        # --- רשימת המוצרים הממוינת ---
        self.expiry_scroll = ctk.CTkScrollableFrame(self.tab_expiry, width=950, height=500)
        self.expiry_scroll.pack(pady=10, padx=20, fill="both", expand=True)
        
        self.refresh_expiry()

   
    def refresh_expiry(self):
        for widget in self.expiry_scroll.winfo_children():
            widget.destroy()
            
        data = self.controller.get_expiry_data()
        
        for p, hours in data:
            # לוגיקת צבעים לפי בקשתך:
            if hours <= 72:
                color = "#D32F2F"  # אדום (דחוף)
            elif hours <= 240: # 72 שעות + 168 שעות (שבוע) = 240 שעות סה"כ מהיום
                color = "#FBC02D"  # צהוב (שבוע אחרי ה-72 שעות)
            else:
                color = "#388E3C"  # ירוק (רחוק)

            f = ctk.CTkFrame(self.expiry_scroll, fg_color=color)
            f.pack(fill="x", pady=5, padx=15)
            
            # חישוב ימים ושעות לתצוגה יפה
            days_left = int(hours // 24)
            remaining_hours = int(hours % 24)
            
            txt = f"מוצר: {p.name} | תוקף בעוד: {days_left} ימים ו-{remaining_hours} שעות"
            ctk.CTkLabel(f, text=txt, text_color="black" if color == "#FBC02D" else "white", 
                          font=("Arial", 15, "bold"), anchor="e").pack(side="right", padx=25, pady=12)