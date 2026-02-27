import sqlite3
from .product import Product

class DatabaseManager:
    def __init__(self):
        # יצירת חיבור למסד הנתונים 
        self.conn = sqlite3.connect('kitchen.db', check_same_thread=False)
        self.create_table()

    def create_table(self):
        query = '''CREATE TABLE IF NOT EXISTS products 
                   (id INTEGER PRIMARY KEY AUTOINCREMENT, 
                    name TEXT, category TEXT, weight REAL, expiry_date TEXT)'''
        self.conn.execute(query)
        self.conn.commit()

    def add_product(self, product):
        query = "INSERT INTO products (name, category, weight, expiry_date) VALUES (?, ?, ?, ?)"
        self.conn.execute(query, (product.name, product.category, product.weight, product.expiry_date))
        self.conn.commit()

    def get_all_products(self):
        # שליפת כל המוצרים לצורך הצגת הרשימה 
        cursor = self.conn.execute("SELECT * FROM products")
        products = []
        for row in cursor:
            try:
                # ניסיון ליצור אובייקט Product. אם התאריך ישן, ה-Model יזרוק ValueError
                products.append(Product(row[1], row[2], row[3], row[4], row[0]))
            except ValueError as e:
                # במקום לקרוס, נדפיס אזהרה ונדלג על המוצר הבעייתי
                print(f"Skipping invalid product ID {row[0]}: {e}")
                continue
        return products
    
    def get_expired_raw(self):
        """שליפת מוצרים שפג תוקפם ישירות מה-DB ללא ולידציה של המודל"""
        cursor = self.conn.execute("SELECT id, name, category, weight, expiry_date FROM products")
        expired_list = []
        for row in cursor:
            # כאן אנחנו לא יוצרים אובייקט Product, אלא פשוט שומרים את הנתונים
            expired_list.append({
                "id": row[0],
                "name": row[1],
                "weight": row[3],
                "date": row[4]
            })
        return expired_list
    
    def delete_product(self, product_id):
        # מחיקת מוצר מהמלאי
        self.conn.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()

    def update_weight(self, product_id, new_weight):
        # עדכון משקל למוצר קיים
        self.conn.execute("UPDATE products SET weight = ? WHERE id = ?", (new_weight, product_id))
        self.conn.commit()