import customtkinter as ctk
from src.database import Database
from src.firebase_manager import FirebaseManager
from src.admin_dashboard import AdminDashboard
from src.login import LoginScreen
from src.pages.company_select_page import CompanySelectPage
from src.api import start_api_server
from src.company_manager import CompanyManager

print("🚀 Starting GDC Attendance App...")
# Start the Flask API server in the background
start_api_server()

import os
firebase = FirebaseManager()   # make sure this connects to real Firebase

# Company-aware startup: load active company and use its DB file
cm = CompanyManager()
company_name, company_dir, faces_dir = cm.get_active()
db_path = cm.ensure_db_path(company_dir)
db = Database(db_name=db_path)

root = ctk.CTk()

def show_company_select():
    # Clear any existing widgets and show the company select page
    for w in root.winfo_children():
        try:
            w.destroy()
        except Exception:
            pass

    def on_company_continue(selected_name):
        # After selecting a company, initialize DB and show login
        try:
            cm.set_active(selected_name)
        except Exception:
            pass
        # Resolve active company context
        cname, cdir, fdir = cm.get_active()
        path = cm.ensure_db_path(cdir)
        # Create company-scoped database
        global db, faces_dir
        faces_dir = fdir
        db = Database(db_name=path)

        # Show login screen for the selected company
        for w in root.winfo_children():
            try:
                w.destroy()
            except Exception:
                pass

        def on_login_success(user_id, role):
            # Clear the root window and open the dashboard for the logged-in user
            for w in root.winfo_children():
                try:
                    w.destroy()
                except Exception:
                    pass

            def do_logout():
                # On logout, return to company selection to allow switching
                show_company_select()

            # Pass company-specific faces_dir and name into the dashboard
            AdminDashboard(
                root, db, firebase,
                user_id=user_id, role=role,
                on_logout=do_logout,
                faces_dir=faces_dir,
                company_name=cname
            )

        LoginScreen(root, db, on_login_success, company_name=cname)

    CompanySelectPage(root, cm, on_company_continue)

# Always show company select first
show_company_select()
root.mainloop()
