import requests
from datetime import datetime
from models.product import Product

class MainController:
    def __init__(self, db_manager):
        """אתחול הבקר - הפרדת רשויות SoC"""
        self.db = db_manager

    def add_product_gui(self, name, category, weight, date):
        try:
            weight_val = float(weight) if weight else 0.0
            new_prod = Product(name, category, weight_val, date)
            self.db.add_product(new_prod)
            return True
        except Exception as e:
            print(f"Error: {e}")
            return False

    def delete_product_gui(self, product_id):
        try:
            self.db.delete_product(product_id)
            return True
        except:
            return False

    def update_product_weight(self, product_id, new_weight):
        try:
            self.db.update_weight(product_id, float(new_weight))
            return True
        except:
            return False

    def get_expiry_data(self):
        """שליפת כל המלאי ממוין לפי תוקף (רמזור)"""
        all_products = self.db.get_all_products()
        product_data = [(p, p.days_to_expiry()) for p in all_products]
        product_data.sort(key=lambda x: x[1])
        return product_data

    def get_ai_recipe_flow(self, user_request=""):
        """
        הפקת מתכון באנגלית עם לוגיקה נוקשה למניעת מתכונים הזויים
        """
        products = self.db.get_all_products()
        if not products:
            return "Inventory empty. Please add items."

        ingredients_list = [p.name for p in products]
        all_ingredients = ", ".join(ingredients_list)
        
        url = "http://127.0.0.1:11434/api/generate"
        
        
       
    
        full_prompt = (
f"SYSTEM: You are a professional Kitchen Assistant. Your task is to suggest a recipe based on the user's request and the available inventory.\n"
f"AVAILABLE INVENTORY (from SQLite): {all_ingredients}\n"
f"USER REQUEST: \"{user_request}\"\n\n"

f"STRICT OPERATIONAL RULES:\n"
f"1. INVENTORY MAPPING: For every ingredient used, write it exactly as: English Name (Hebrew Name from inventory). Example: Spinach (תרד).\n"
f"2. NO HALLUCINATIONS: Do not list ingredients in the 'Ingredients Used' section that are not in the provided inventory list.\n"
f"3. CONSISTENCY: Every item listed in the 'Ingredients Used' section MUST appear in the 'Cooking Instructions' and vice versa.\n"
f"4. LANGUAGE: The recipe and instructions must be in English, but the Hebrew names from the inventory must be preserved in parentheses.\n"
f"5. SIMPLICITY: Keep instructions concise and easy to follow.\n\n"

f"FORMAT YOUR RESPONSE LIKE THIS:\n"
f"Dish Name: [Name]\n"
f"Ingredients Used from Inventory:\n"
f"* English Name (Hebrew Name)\n\n"
f"Cooking Instructions:\n"
f"1. [Step 1]..."
)    
        
        payload = {
            "model": "llama3:latest", 
            "prompt": full_prompt,
            "stream": False
        }
        
        try:
            response = requests.post(url, json=payload, timeout=35)
            if response.status_code == 200:
                recipe = response.json().get('response', "").strip()
                return recipe.split("</thought>")[-1].strip()
            return "AI Server Error."
        except:
            return "Ollama not running. Check terminal (ollama serve)."