from models.database_manager import DatabaseManager
from controllers.main_controller import MainController
from views.gui_view import KitchenGUI

def main():
    try:
        # 1. אתחול מודל הנתונים (Model) - יצירת חיבור ל-SQLite
        db = DatabaseManager()
        
        # 2. אתחול הבקר (Controller) והזרקת המודל לתוכו
        # הבקר מנהל את הקשר בין הנתונים ל-AI
        controller = MainController(db)
        
        # 3. אתחול התצוגה (View) והזרקת הבקר לתוכה
        # ה-GUI משתמש בבקר כדי לבצע פעולות
        app = KitchenGUI(controller)
        
        # 4. הרצת הלולאה הראשית - פקודה קריטית כדי שהחלון לא ייסגר
        app.mainloop()
        
    except Exception as e:
        print(f"שגיאה בהפעלת האפליקציה: {e}")

if __name__ == "__main__":
    main()