import customtkinter as ctk
from tkinter import messagebox

# Page modules
from .pages.dashboard_page import DashboardPage
from .pages.add_employee_page import AddEmployeePage
from .pages.mark_attendance_page import MarkAttendancePage
from .pages.attendance_records_page import AttendanceRecordsPage
from .pages.user_management_page import UserManagementPage
from .pages.settings_page import SettingsPage

# Shared managers
from .face_recognition_manager import FaceRecognitionManager
from .email_manager import EmailManager


class AdminDashboard:
    def __init__(self, root, db, firebase=None, user_id=None, role=None, on_logout=None, faces_dir=None, company_name=None):
        # Core refs
        self.root = root
        self.db = db
        self.firebase = firebase
        self.user_id = user_id
        self.role = role
        self.on_logout = on_logout

        # Theme from settings
        saved_theme = db.get_setting('theme_mode', 'System')
        ctk.set_appearance_mode(str(saved_theme).lower())
        ctk.set_default_color_theme("blue")

        # Window metadata
        self.root.title("GDC Attendance System")
        self.root.geometry("1200x750")

        # Unified colors and fonts shared with pages
        self.primary_color = "#1a73e8"
        self.secondary_color = "#f8f9fa"
        self.accent_color = "#4285f4"
        self.text_color = "#202124"
        self.success_color = "#0f9d58"
        self.warning_color = "#f4b400"
        self.error_color = "#db4437"

        self.colors = {
            'primary': self.primary_color,
            'secondary': self.secondary_color,
            'accent': self.accent_color,
            'text': self.text_color,
            'success': self.success_color,
            'warning': self.warning_color,
            'error': self.error_color,
        }

        self.fonts = {
            'header': ("Segoe UI", 24, "bold"),
            'subheader': ("Segoe UI", 18, "bold"),
            'title': ("Segoe UI", 22, "bold"),
            'nav': ("Segoe UI", 14, "normal"),
            'button': ("Segoe UI", 13, "normal"),
            'input': ("Segoe UI", 13, "normal"),
            'text': ("Segoe UI", 13, "normal"),
            'small': ("Segoe UI", 11, "normal"),
            'footer': ("Segoe UI", 10, "normal"),
        }

        # Shared managers
        # Use company-specific faces directory if provided
        if faces_dir:
            self.face_mgr = FaceRecognitionManager(faces_dir=faces_dir)
        else:
            self.face_mgr = FaceRecognitionManager()
        self.email_mgr = EmailManager(self.db)

        # Root layout: header, nav, content
        self.container = ctk.CTkFrame(root, fg_color=self.secondary_color)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)

        self.header = ctk.CTkFrame(self.container, height=60, corner_radius=0, fg_color=self.primary_color)
        self.header.pack(fill="x", padx=5, pady=(0, 5))

        title = ctk.CTkLabel(self.header, text="GDC ATTENDANCE SYSTEM", font=self.fonts['title'], text_color="white")
        title.pack(side="left", padx=20, pady=10)

        # Active company banner on the right
        try:
            company_text = company_name or "default"
            self.company_label = ctk.CTkLabel(
                self.header,
                text=f"Company: {company_text}",
                font=self.fonts['small'],
                text_color="white"
            )
            self.company_label.pack(side="right", padx=20)
        except Exception:
            pass

        # Simple top navigation
        self.nav = ctk.CTkFrame(self.container, fg_color="transparent")
        self.nav.pack(fill="x", padx=5, pady=(0, 5))

        def add_nav(text, cmd):
            btn = ctk.CTkButton(
                self.nav,
                text=text,
                command=cmd,
                fg_color=self.primary_color,
                text_color="white",
                hover_color=self.accent_color,
                height=34,
            )
            btn.pack(side="left", padx=(0, 8))

        add_nav("Dashboard", self.show_dashboard)
        add_nav("Add Employee", self.show_add_employee)
        add_nav("Mark Attendance", self.show_mark_attendance)
        add_nav("Attendance Records", self.show_attendance_records)
        add_nav("Users", self.show_user_management)
        add_nav("Settings", self.show_settings)
        add_nav("Logout", self.logout)

        # Content area
        self.main_frame = ctk.CTkFrame(self.container, fg_color="transparent")
        self.main_frame.pack(fill="both", expand=True, padx=5, pady=5)

        # Default page
        try:
            self.show_dashboard()
        except Exception:
            pass

    # Page delegations
    def show_dashboard(self):
        page = DashboardPage(self.main_frame, self.db, self.colors, self.fonts)
        page.show()

    def show_add_employee(self):
        page = AddEmployeePage(self.main_frame, self.db, self.colors, self.fonts, self.face_mgr, self.email_mgr)
        page.show()

    def show_mark_attendance(self):
        page = MarkAttendancePage(self.main_frame, self.db, self.colors, self.fonts, self.face_mgr, firebase=self.firebase)
        page.show()

    def show_attendance_records(self):
        page = AttendanceRecordsPage(self.main_frame, self.db, self.colors, self.fonts)
        page.show()

    def show_user_management(self):
        page = UserManagementPage(self.main_frame, self.db, self.colors, self.fonts)
        page.show()

    def show_settings(self):
        page = SettingsPage(self.main_frame, self.db, self.colors, self.fonts, self.face_mgr)
        page.show()

    def logout(self):
        if callable(self.on_logout):
            try:
                self.on_logout()
            except Exception:
                pass
        else:
            messagebox.showinfo("Logout", "No logout handler bound.")