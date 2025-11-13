import customtkinter as ctk
from src.database import Database
from src.firebase_manager import FirebaseManager
from src.ui import AdminDashboard
from src.login import LoginScreen

print("🚀 Starting GDC Attendance App...")

import os
firebase = FirebaseManager()   # make sure this connects to real Firebase
# Prefer existing 'database.db' if present; otherwise use default 'attendance.db'
db_path = os.path.join(os.getcwd(), "database.db")
db = Database(db_name=db_path) if os.path.exists(db_path) else Database()

root = ctk.CTk()

def on_login_success(user_id, role):
	# Clear the root window and open the dashboard for the logged-in user
	for w in root.winfo_children():
		w.destroy()
	def do_logout():
		# when logout is requested, destroy current widgets and show login again
		for w in root.winfo_children():
			w.destroy()
		LoginScreen(root, db, on_login_success)

	AdminDashboard(root, db, firebase, user_id=user_id, role=role, on_logout=do_logout)

# Show login first
login = LoginScreen(root, db, on_login_success)
root.mainloop()
