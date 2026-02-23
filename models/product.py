from datetime import datetime

class Product:
    def __init__(self, name, category, weight, expiry_date, id=None):
        self.id = id # ה-ID יגיע מהמסד נתונים אוטומטית
        self.name = name
        self.category = category
        self.weight = weight # בגרמים
        self.expiry_date = expiry_date # פורמט DD/MM/YYYY

    def days_to_expiry(self):
        try:
            # ניסיון להמיר את המחרוזת לאובייקט תאריך
            expiry = datetime.strptime(self.expiry_date, "%d/%m/%Y")
            now = datetime.now()
            diff = expiry - now
            # החזרת שעות (למניעת שגיאות חישוב)
            return max(0, diff.total_seconds() / 3600)
        except ValueError:
            # אם התאריך לא תקין (למשל 31/02), נחזיר 0 כדי שהתוכנית לא תקרוס
            print(f"שגיאה בתאריך של המוצר {self.name}: פורמט לא תקין")
            return 0
        except Exception:
            return 0
        
    def __str__(self):
        """פונקציה זו מחזירה ייצוג קריא של האובייקט עבור המשתמש הסופי"""
        return f"{self.name} ({self.weight}g) - Exp: {self.expiry_date}"

    def __repr__(self):
        """פונקציה זו מחזירה ייצוג טכני של האובייקט עבור המפתח (Debug)"""
        return f"Product(id={self.id}, name='{self.name}', weight={self.weight})"