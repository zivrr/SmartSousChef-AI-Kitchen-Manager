import requests
from datetime import datetime
from models.product import Product

class MainController:
    def __init__(self, db_manager):
        """אתחול הבקר - הפרדת רשויות SoC (Separation of Concerns)"""
        self.db = db_manager

    def add_product_gui(self, name, category, weight, date):
        """
        ניסיון הוספת מוצר חדש. 
        הבדיקות (Validations) מבוצעות בתוך מחלקת Product דרך ה-Setters.
        """
        try:
            # יצירת האובייקט תפעיל את ה-Setters של Product.
            # אם נתון לא תקין (למשל משקל שלילי), תיזרק שגיאת ValueError.
            new_prod = Product(name, category, weight, date)
            self.db.add_product(new_prod)
            return True, "Product added successfully!"
        except ValueError as e:
            # תפיסת שגיאת הולידציה והחזרת ההודעה המדויקת ל-GUI
            return False, str(e)
        except Exception as e:
            # תפיסת שגיאות כלליות (כמו בעיות במסד הנתונים)
            return False, f"System Error: {e}"

    def delete_product_gui(self, product_id):
        """מחיקת מוצר לפי ה-ID הייחודי שלו"""
        try:
            self.db.delete_product(product_id)
            return True
        except:
            return False

    def update_product_weight(self, product_id, new_weight):
        """עדכון משקל למוצר קיים במערכת"""
        try:
            # המרת הקלט למספר לפני השליחה למסד הנתונים
            self.db.update_weight(product_id, float(new_weight))
            return True
        except:
            return False

    def get_expiry_data(self):
        """שליפת המלאי וחישוב זמני תוקף לצורך תצוגת הרמזור"""
        all_products = self.db.get_all_products()
        # שימוש ב-Property hours_to_expiry שקיים ב-Model
        product_data = [(p, p.hours_to_expiry) for p in all_products]
        # מיון המוצרים כך שהדחופים ביותר יופיעו ראשונים
        product_data.sort(key=lambda x: x[1])
        return product_data
    
    def check_invalid_products(self):
        """בודק כמה מוצרים פגי תוקף קיימים ב-DB שאינם עומדים בחוקי ה-Model"""
        cursor = self.db.conn.execute("SELECT name FROM products")
        invalid_count = 0
        for row in cursor:
            try:
                # ניסיון ליצור אובייקט זמני רק כדי לבדוק תקינות
                Product(row[0], "temp", "1", "01/01/1990") # תאריך ישן בכוונה
                # אם הקוד מגיע לכאן, סימן שהמוצר ב-DB תקין (לא יקרה במקרה שלנו)
            except ValueError:
                invalid_count += 1
        return invalid_count
    
    def search_products(self, search_term):
        """סינון מוצרים לפי שם (Case-insensitive) לצורך ה-Search ב-GUI"""
        all_products = self.db.get_all_products()
        if not search_term:
            return all_products
        
        return [p for p in all_products if search_term.lower() in p.name.lower()]

    def get_ai_recipe_flow(self, user_request=""):
        """
        ניהול זרימת המידע מול שרת ה-AI (Ollama)
        הזרקת המלאי הקיים לתוך ה-Prompt כדי לקבל מתכון מותאם אישית.
        """
        products = self.db.get_all_products()
        if not products:
            return "Inventory empty. Please add items."

        # הכנת רשימת המצרכים כהקשר (Context) עבור ה-AI
        ingredients_list = [p.name for p in products]
        all_ingredients = ", ".join(ingredients_list)
        
        
        url = "http://127.0.0.1:11434/api/generate"
        
        
       
    
        full_prompt = (
f"SYSTEM: You are a professional Kitchen Assistant. Your task is to suggest a recipe based on the user's request and the available inventory.\n"
f"AVAILABLE INVENTORY (from SQLite): {all_ingredients}\n"
f"USER REQUEST: \"{user_request}\"\n\n"

f"STRICT OPERATIONAL RULES:\n"
f"1. INVENTORY MAPPING: For every ingredient used, write it exactly as: Name from inventory. Example: Spinach.\n"
f"2. NO HALLUCINATIONS: Do not list ingredients in the 'Ingredients Used' section that are not in the provided inventory list.\n"
f"3. CONSISTENCY: Every item listed in the 'Ingredients Used' section MUST appear in the 'Cooking Instructions' and vice versa.\n"
f"4. LANGUAGE: The recipe and instructions must be in English, but the Hebrew names from the inventory must be preserved in parentheses.\n"
f"5. SIMPLICITY: Keep instructions concise and easy to follow.\n\n"

f"FORMAT YOUR RESPONSE LIKE THIS:\n"
f"Dish Name: [Name]\n"
f"Ingredients Used from Inventory:\n"
f"* English Name \n\n"
f"Cooking Instructions:\n"
f"1. [Step 1]..."
)    
        
        payload = {
            "model": "llama3:latest", 
            "prompt": full_prompt,
            "stream": False
            }
        
        try:
            # שליחת הבקשה לשרת המקומי (Ollama)
            response = requests.post(url, json=payload, timeout=120)
            if response.status_code == 200:
                return response.json().get('response', "").strip()
            return "AI Server Error."
        except:
            return "Ollama not running. Ensure Docker/Ollama is active."
     