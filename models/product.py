from datetime import datetime

class Product:
    def __init__(self, name, category, weight, expiry_date, id=None):
        self._id = id
        # קריאה ל-setters כדי להפעיל את הוולידציה כבר בשלב האתחול
        self.name = name
        self.category = category
        self.weight = weight
        self.expiry_date = expiry_date

    # --- Name Property ---
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        if not value or not value.strip():
            raise ValueError("Product name cannot be empty")
        self._name = value

    # --- Category Property ---
    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, value):
        self._category = value

    # --- Weight Property ---
    @property
    def weight(self):
        return self._weight

    @weight.setter
    def weight(self, value):
        try:
            val = float(value)
            if val <= 0:
                raise ValueError("Weight must be a positive number")
            self._weight = val
        except (ValueError, TypeError):
            raise ValueError("Weight must be a valid number")

    # --- Expiry Date Property ---
    @property
    def expiry_date(self):
        return self._expiry_date

    @expiry_date.setter
    def expiry_date(self, value):
        try:
            # בדיקת פורמט התאריך
            datetime.strptime(value, "%d/%m/%Y")
            self._expiry_date = value
        except (ValueError, TypeError):
            raise ValueError("Invalid date format. Use DD/MM/YYYY")

    # --- Logic Properties ---
    @property
    def hours_to_expiry(self):
        """מחשב בזמן אמת כמה שעות נותרו עד לפקיעת התוקף"""
        try:
            expiry = datetime.strptime(self._expiry_date, "%d/%m/%Y")
            now = datetime.now()
            diff = expiry - now
            return max(0, diff.total_seconds() / 3600)
        except:
            return 0

    @property
    def id(self):
        return self._id

    # --- Magic Methods ---
    def __str__(self):
        return f"{self._name} ({self._weight}g) - Exp: {self._expiry_date}"

    def __repr__(self):
        return f"Product(id={self._id}, name='{self._name}', weight={self._weight})"