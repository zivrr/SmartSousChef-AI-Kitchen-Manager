from datetime import datetime

class Product:
    def __init__(self, name, category, weight, expiry_date, id=None):
        self.id = id
        self.name = name
        self.category = category
        self.weight = weight
        self.expiry_date = expiry_date

    @property
    def hours_to_expiry(self):
        """הופך את החישוב למאפיין (Property) במקום פונקציה רגילה"""
        try:
            expiry = datetime.strptime(self.expiry_date, "%d/%m/%Y")
            now = datetime.now()
            diff = expiry - now
            return max(0, diff.total_seconds() / 3600)
        except (ValueError, Exception):
            return 0

    def __str__(self):
        return f"{self.name} ({self.weight}g) - Exp: {self.expiry_date}"

    def __repr__(self):
        return f"Product(id={self.id}, name='{self.name}', weight={self.weight})"