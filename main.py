import customtkinter as ctk
from src.database import Database
from src.firebase_manager import FirebaseManager
from src.ui import AdminDashboard

print("🚀 Starting GDC Attendance App...")

firebase = FirebaseManager()   # make sure this connects to real Firebase
db = Database()

root = ctk.CTk()
app = AdminDashboard(root, db, firebase)
root.mainloop()
