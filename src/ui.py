import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import os
import importlib.util
from PIL import Image, ImageTk
from .permissions import Permissions

from .fingerprint_scanner import FingerprintScanner
from .face_recognition_manager import FaceRecognitionManager
from .email_manager import EmailManager

class AdminDashboard:
    def show_loading(self, message="Loading..."):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            return  # Already showing
        self._loading_overlay = ctk.CTkFrame(self.root, fg_color="#000000")
        self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        spinner = ctk.CTkLabel(self._loading_overlay, text="⏳", font=("Segoe UI", 48), text_color="white")
        spinner.pack(expand=True, pady=(100, 10))
        msg = ctk.CTkLabel(self._loading_overlay, text=message, font=("Segoe UI", 18), text_color="white")
        msg.pack()

    def hide_loading(self):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            self._loading_overlay.destroy()
            self._loading_overlay = None
    def __init__(self, root, db, firebase=None, user_id=None, role=None, on_logout=None):
        self.root = root
        self.db = db
        self.firebase = firebase
        self.user_id = user_id
        self.role = role
        self.on_logout = on_logout
        
        # Set the appearance mode and default color theme
        saved_theme = db.get_setting('theme_mode', 'System')
        ctk.set_appearance_mode(str(saved_theme).lower())  # Options: "system" (default), "light", "dark"
        ctk.set_default_color_theme("blue")  # Options: "blue" (default), "green", "dark-blue"
        
        self.root.title("GDC Attendance System")
        self.root.geometry("1200x750")
        
        # Define colors
        self.primary_color = "#1a73e8"  # Google blue
        self.secondary_color = "#f8f9fa"  # Light gray
        self.accent_color = "#4285f4"  # Lighter blue
        self.text_color = "#202124"  # Dark gray for text
        self.success_color = "#0f9d58"  # Green
        self.warning_color = "#f4b400"  # Yellow
        self.error_color = "#db4437"  # Red

        # Define font styles for consistency
        self.fonts = {
            'header': ("Segoe UI", 24, "bold"),     # Page headers
            'subheader': ("Segoe UI", 18, "bold"),  # Section headers
            'title': ("Segoe UI", 22, "bold"),      # App title
            'nav': ("Segoe UI", 14, "normal"),      # Navigation buttons
            'button': ("Segoe UI", 13, "normal"),   # Regular buttons
            'input': ("Segoe UI", 13, "normal"),    # Input fields
            'text': ("Segoe UI", 13, "normal"),     # Regular text
            'small': ("Segoe UI", 11, "normal"),    # Small text
            'footer': ("Segoe UI", 10, "normal")    # Footer text
        }
        
        # Configure style for ttk widgets
        self.style = ttk.Style()
        self.style.configure("Treeview", 
                            background=self.secondary_color,
                            foreground=self.text_color,
                            rowheight=25,
                            fieldbackground=self.secondary_color)
        self.style.map('Treeview', background=[('selected', self.primary_color)])
        
        # Create main container
        self.container = ctk.CTkFrame(root, fg_color=self.secondary_color)
        self.container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Header frame
        self.header = ctk.CTkFrame(self.container, height=60, corner_radius=0, fg_color=self.primary_color)
        self.header.pack(fill="x", padx=5, pady=(0, 5))
        
        # App title in header
        self.title_label = ctk.CTkLabel(
            self.header, 
            text="GDC ATTENDANCE SYSTEM", 
            font=self.fonts['title'],
            text_color="white"
        )
        self.title_label.pack(side="left", padx=20, pady=10)

        # User avatar in header
        self.avatar_frame = ctk.CTkFrame(
            self.header,
            width=40,
            height=40,
            corner_radius=20,
            fg_color=self.accent_color
        )
        self.avatar_frame.pack(side="right", padx=(0, 20), pady=10)
        self.avatar_frame.pack_propagate(False)

        # Default avatar icon
        self.avatar_label = ctk.CTkLabel(
            self.avatar_frame,
            text="👤",
            font=("Segoe UI", 20),
            text_color="white"
        )
        self.avatar_label.pack(expand=True)

        # User role label
        role_text = role.title() if role else "User"
        self.role_label = ctk.CTkLabel(
            self.header,
            text=role_text,
            font=("Segoe UI", 12),
            text_color="white"
        )
        self.role_label.pack(side="right", padx=(0, 10), pady=10)
        
        # Content area (sidebar + main content)
        self.content = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        
        # Sidebar with gradient effect
        self.sidebar = ctk.CTkFrame(self.content, width=250, corner_radius=0, fg_color="#f1f3f4")
        self.sidebar.pack(side="left", fill="y", padx=(0, 10), pady=5)
        self.sidebar.pack_propagate(False)  # Prevent sidebar from shrinking
        
        # Logo or branding area
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        self.logo_frame.pack(fill="x", pady=(20, 10))
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="Admin Dashboard", 
            font=self.fonts['subheader'],
            text_color=self.primary_color
        )
        self.logo_label.pack(pady=10)
        
        # Navigation menu
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=10)
        
        # Active button indicator
        self.active_btn = None
        
        # Sidebar buttons with hover effect
        self.btn_dashboard = self.create_nav_button("🏠  Dashboard", self.show_dashboard)
        self.btn_add_employee = self.create_nav_button("➕  Add Employee", self.show_add_employee)
        self.btn_view_employee = self.create_nav_button("👥  View Employees", self.show_view_employees)
        self.btn_mark_attendance = self.create_nav_button("🖐️  Mark Attendance", self.show_mark_attendance)
        self.btn_view_attendance = self.create_nav_button("📋  Attendance Records", self.show_attendance_records)
        self.btn_user_management = self.create_nav_button("👤  User Management", self.show_user_management)
        self.btn_settings = self.create_nav_button("⚙️  Settings", self.show_settings)
        # change password button in header
        self.change_pw_btn = ctk.CTkButton(
            self.header,
            text="Change Password",
            command=lambda: self.show_change_password_dialog(),
            fg_color="transparent",
            text_color="white",
            hover_color="#1967d2",
            width=140,
            height=32,
            corner_radius=6
        )
        self.change_pw_btn.pack(side="right", padx=10, pady=10)
        # Logout button (right of header)
        self.logout_btn = ctk.CTkButton(
            self.header,
            text="Logout",
            command=self.logout,
            fg_color="transparent",
            text_color="white",
            hover_color="#c62828",
            width=100,
            height=32,
            corner_radius=6
        )
        self.logout_btn.pack(side="right", padx=(0, 10), pady=10)
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self.content, corner_radius=15, fg_color="white")
        self.main_frame.pack(side="right", expand=True, fill="both", padx=20, pady=10)
        
        # Footer
        self.footer = ctk.CTkFrame(self.container, height=30, corner_radius=0, fg_color=self.primary_color)
        self.footer.pack(fill="x", padx=5, pady=(5, 0))
        
        self.footer_label = ctk.CTkLabel(
            self.footer, 
            text="© 2023 GDC Attendance System", 
            font=self.fonts['footer'],
            text_color="white"
        )
        self.footer_label.pack(side="right", padx=20)
        
        self.current_frame = None

        # Make UI responsive to window resizing
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.container.rowconfigure(1, weight=1)
        self.container.columnconfigure(0, weight=1)
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(1, weight=1)
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Configure UI based on permissions if role provided
        if self.role:
            self.configure_permissions()
        self.show_dashboard()

        # Start autosave timer based on settings (if enabled)
        try:
            auto_on_logout = int(self.db.get_setting('auto_save_on_logout', '1'))
            interval = int(self.db.get_setting('auto_save_interval', '60'))
            if auto_on_logout and interval > 0:
                self.start_autosave_timer(interval)
        except Exception:
            pass
        # Initialize face and email managers
        self.face_mgr = FaceRecognitionManager()
        self.email_mgr = EmailManager(self.db)
        
    def create_nav_button(self, text, command):
        """Create a styled navigation button with hover effect"""
        btn = ctk.CTkButton(
            self.nav_frame,
            text=text,
            command=lambda t=text, c=command: self.nav_button_click(t, c),
            fg_color="transparent",
            text_color=self.text_color,
            hover_color=self.accent_color,
            anchor="w",
            height=40,
            corner_radius=8,
            font=self.fonts['nav']
        )
        
        def on_enter(e):
            if not btn.cget("state") == "disabled":
                btn.configure(text_color=self.accent_color)
                
        def on_leave(e):
            if not btn.cget("state") == "disabled":
                btn.configure(text_color=self.text_color)
        
        btn.bind("<Enter>", on_enter)
        btn.bind("<Leave>", on_leave)
        btn.pack(fill="x", padx=10, pady=5)
        
        return btn
        
    def nav_button_click(self, text, command):
        """Handle navigation button click and highlight active button"""
        # Reset all buttons (include user management)
        for btn in [self.btn_dashboard, self.btn_add_employee, self.btn_view_employee,
                   self.btn_mark_attendance, self.btn_view_attendance, self.btn_user_management, self.btn_settings]:
            btn.configure(fg_color="transparent", text_color=self.text_color)

        # Highlight active button
        if text == "🏠 Dashboard":
            self.btn_dashboard.configure(fg_color=self.primary_color, text_color="white")
        elif text == "➕ Add Employee":
            self.btn_add_employee.configure(fg_color=self.primary_color, text_color="white")
        elif text == "👥 View Employees":
            self.btn_view_employee.configure(fg_color=self.primary_color, text_color="white")
        elif text == "🖐️ Mark Attendance":
            self.btn_mark_attendance.configure(fg_color=self.primary_color, text_color="white")
        elif text == "📋 Attendance Records":
            self.btn_view_attendance.configure(fg_color=self.primary_color, text_color="white")
        elif text == "👤 User Management":
            self.btn_user_management.configure(fg_color=self.primary_color, text_color="white")
        elif text == "⚙️ Settings":
            self.btn_settings.configure(fg_color=self.primary_color, text_color="white")

        # Execute the command
        command()

    def configure_permissions(self):
        """Hide or show sidebar buttons depending on the logged-in user's role."""
        role = self.role or 'staff'
        # add_employee
        if not Permissions.check_permission(role, 'add_employee'):
            self.btn_add_employee.pack_forget()
        else:
            if not self.btn_add_employee.winfo_ismapped():
                self.btn_add_employee.pack(fill="x", padx=10, pady=5)

        # view_employees
        if not Permissions.check_permission(role, 'view_employees'):
            self.btn_view_employee.pack_forget()
        else:
            if not self.btn_view_employee.winfo_ismapped():
                self.btn_view_employee.pack(fill="x", padx=10, pady=5)

        # mark_attendance
        if not Permissions.check_permission(role, 'mark_attendance'):
            self.btn_mark_attendance.pack_forget()
        else:
            if not self.btn_mark_attendance.winfo_ismapped():
                self.btn_mark_attendance.pack(fill="x", padx=10, pady=5)

        # view_attendance
        if not Permissions.check_permission(role, 'view_attendance'):
            self.btn_view_attendance.pack_forget()
        else:
            if not self.btn_view_attendance.winfo_ismapped():
                self.btn_view_attendance.pack(fill="x", padx=10, pady=5)

        # manage_users
        if not Permissions.check_permission(role, 'manage_users'):
            self.btn_user_management.pack_forget()
        else:
            if not self.btn_user_management.winfo_ismapped():
                self.btn_user_management.pack(fill="x", padx=10, pady=5)

    def show_change_password_dialog(self):
        """Show change password dialog for current user."""
        dialog = ctk.CTkToplevel(self.root)
        dialog.title("Change Password")
        dialog.geometry("400x400")  # Increased height
        
        # Make dialog modal and place it in center
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Center the dialog relative to main window
        x = self.root.winfo_x() + (self.root.winfo_width() - 400) // 2
        y = self.root.winfo_y() + (self.root.winfo_height() - 400) // 2
        dialog.geometry(f"+{x}+{y}")

        # Main container with padding
        container = ctk.CTkFrame(dialog, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        # Header
        header = ctk.CTkLabel(
            container,
            text="Change Your Password",
            font=self.fonts['subheader'],
            text_color=self.primary_color
        )
        header.pack(pady=(0, 20))

        # Password fields
        fields_frame = ctk.CTkFrame(container, fg_color="transparent")
        fields_frame.pack(fill="x")

        old_pass = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Current password",
            show="•",
            width=360,
            height=40
        )
        old_pass.pack(pady=(0, 10))

        new_pass = ctk.CTkEntry(
            fields_frame,
            placeholder_text="New password",
            show="•",
            width=360,
            height=40
        )
        new_pass.pack(pady=(0, 10))

        confirm_pass = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Confirm new password",
            show="•",
            width=360,
            height=40
        )
        confirm_pass.pack(pady=(0, 20))

        def do_change():
            old = old_pass.get()
            new = new_pass.get()
            confirm = confirm_pass.get()

            if not old or not new or not confirm:
                messagebox.showerror("Error", "Please fill in all fields")
                return

            if new != confirm:
                messagebox.showerror("Error", "New passwords do not match")
                return
            
            if len(new) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return

            # Attempt to change password via DB which validates the old password
            if self.db.change_password(self.user_id, old, new):
                messagebox.showinfo("Success", "Password changed successfully")
                dialog.destroy()
            else:
                messagebox.showerror("Error", "Failed to change password")

        # Buttons frame
        buttons_frame = ctk.CTkFrame(container, fg_color="transparent")
        buttons_frame.pack(fill="x", pady=(0, 10))

        # Cancel button
        cancel_btn = ctk.CTkButton(
            buttons_frame,
            text="Cancel",
            command=dialog.destroy,
            fg_color="transparent",
            border_width=1,
            border_color=self.primary_color,
            text_color=self.primary_color,
            hover_color="#f0f0f0",
            width=160,
            height=40
        )
        cancel_btn.pack(side="left", padx=10)

        # Change button
        change_btn = ctk.CTkButton(
            buttons_frame,
            text="Change Password",
            command=do_change,
            fg_color=self.primary_color,
            width=160,
            height=40
        )
        change_btn.pack(side="right", padx=10)

    def show_user_management(self):
        """Show user management screen."""
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.create_page_header("User Management", "Manage system users and roles")

        # Add user section
        add_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        add_frame.pack(fill="x", pady=(0, 20))

        add_header = ctk.CTkLabel(
            add_frame,
            text="Add New User",
            font=("Segoe UI", 16, "bold"),
            text_color=self.text_color
        )
        add_header.pack(anchor="w", padx=20, pady=15)

        fields_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        fields_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Username field
        username_label = ctk.CTkLabel(fields_frame, text="Username:", anchor="w")
        username_label.grid(row=0, column=0, padx=5, pady=5)
        username_entry = ctk.CTkEntry(fields_frame, width=200)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        # Password field
        password_label = ctk.CTkLabel(fields_frame, text="Initial Password:", anchor="w")
        password_label.grid(row=0, column=2, padx=5, pady=5)
        password_entry = ctk.CTkEntry(fields_frame, width=200, show="•")
        password_entry.grid(row=0, column=3, padx=5, pady=5)

        # Role selection
        role_label = ctk.CTkLabel(fields_frame, text="Role:", anchor="w")
        role_label.grid(row=1, column=0, padx=5, pady=5)
        role_var = ctk.StringVar(value="staff")
        role_menu = ctk.CTkOptionMenu(
            fields_frame,
            values=["staff", "manager"],
            variable=role_var,
            width=200
        )
        role_menu.grid(row=1, column=1, padx=5, pady=5)

        def add_user():
            username = username_entry.get()
            password = password_entry.get()
            role = role_var.get()

            if not username or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return
            
            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return

            try:
                self.db.add_user(username, password, role)
                messagebox.showinfo("Success", f"User {username} created successfully")
                username_entry.delete(0, 'end')
                password_entry.delete(0, 'end')
                self.refresh_user_list()
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    messagebox.showerror("Error", "Username already exists")
                else:
                    messagebox.showerror("Error", f"Failed to create user: {e}")

        add_btn = ctk.CTkButton(
            fields_frame,
            text="Add User",
            command=add_user,
            fg_color=self.primary_color
        )
        add_btn.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

        # Users list
        list_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        list_frame.pack(fill="both", expand=True)

        list_header = ctk.CTkLabel(
            list_frame,
            text="Existing Users",
            font=("Segoe UI", 16, "bold"),
            text_color=self.text_color
        )
        list_header.pack(anchor="w", padx=20, pady=15)

        # Treeview for users
        columns = ("username", "role", "employee", "status", "actions")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Treeview")

        tree.heading("username", text="Username")
        tree.heading("role", text="Role")
        tree.heading("employee", text="Linked Employee")
        tree.heading("status", text="Status")
        tree.heading("actions", text="Actions")

        tree.column("username", width=150)
        tree.column("role", width=100)
        tree.column("employee", width=200)
        tree.column("status", width=100)
        tree.column("actions", width=100)

        def refresh_user_list():
            for item in tree.get_children():
                tree.delete(item)
                
            users = self.db.get_all_users()
            for user in users:
                status = "First Login" if user['first_login'] else "Active"
                # Use the database user id as the tree item id (iid) so actions can reference it
                tree.insert("", "end", iid=str(user['id']), values=(
                    user['username'],
                    user['role'],
                    user['employee_name'] or "-",
                    status,
                    "Delete"
                ))

        def on_tree_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                column = tree.identify_column(event.x)
                item = tree.identify_row(event.y)
                if column == "#5":  # Actions column
                    if not item:
                        return
                    username = tree.item(item)['values'][0]
                    if messagebox.askyesno("Confirm Delete", f"Delete user {username}?"):
                        row_id = int(item)
                        if self.db.delete_user(row_id):
                            refresh_user_list()
                            messagebox.showinfo("Success", "User deleted")
                        else:
                            messagebox.showerror("Error", "Failed to delete user")

        tree.bind('<Button-1>', on_tree_click)
        tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Store refresh function
        self.refresh_user_list = refresh_user_list

        # Initial load
        refresh_user_list()

    def show_settings(self):
        """Show settings page where admin can configure autosave and logout confirmation."""
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.create_page_header("Settings", "Application settings and preferences")

        content = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Read current settings from DB
        auto_on_logout = int(self.db.get_setting('auto_save_on_logout', '1'))
        auto_interval = int(self.db.get_setting('auto_save_interval', '60'))
        confirm_logout = int(self.db.get_setting('confirm_logout', '1'))

        # Controls
        controls = ctk.CTkFrame(content, fg_color="transparent")
        controls.pack(padx=20, pady=10, anchor="nw")

        self.auto_var = ctk.IntVar(value=auto_on_logout)
        auto_cb = ctk.CTkCheckBox(controls, text="Auto-save on logout", variable=self.auto_var)
        auto_cb.grid(row=0, column=0, sticky="w", pady=8)

        self.confirm_var = ctk.IntVar(value=confirm_logout)
        confirm_cb = ctk.CTkCheckBox(controls, text="Confirm on logout", variable=self.confirm_var)
        confirm_cb.grid(row=1, column=0, sticky="w", pady=8)

        interval_label = ctk.CTkLabel(controls, text="Auto-save interval (seconds):")
        interval_label.grid(row=2, column=0, sticky="w", pady=(12, 2))
        self.interval_var = ctk.StringVar(value=str(auto_interval))
        interval_entry = ctk.CTkEntry(controls, textvariable=self.interval_var, width=120)
        interval_entry.grid(row=3, column=0, sticky="w", pady=4)

        # Theme selection
        theme_frame = ctk.CTkFrame(controls, fg_color="transparent")
        theme_frame.grid(row=4, column=0, sticky="w", pady=(20, 0))

        theme_label = ctk.CTkLabel(theme_frame, text="Theme Mode:", anchor="w")
        theme_label.pack(side="left", padx=(0, 10))

        self.theme_var = ctk.StringVar(value=ctk.get_appearance_mode())
        theme_menu = ctk.CTkOptionMenu(
            theme_frame,
            values=["Light", "Dark", "System"],
            variable=self.theme_var,
            width=120,
            command=self.change_theme_mode
        )
        theme_menu.pack(side="left")

        # Fingerprint Scanner Settings
        scanner_frame = ctk.CTkFrame(controls, fg_color="transparent")
        scanner_frame.grid(row=6, column=0, sticky="w", pady=(20, 0))

        scanner_label = ctk.CTkLabel(scanner_frame, text="Fingerprint Scanner:", anchor="w")
        scanner_label.pack(side="left", padx=(0, 10))

        # Get available devices
        from .fingerprint_scanner import FingerprintScanner
        available_devices = FingerprintScanner.get_available_devices()
        saved_port = self.db.get_setting('fingerprint_port', '')
        ports = [d['port'] for d in available_devices] or []
        if saved_port and saved_port not in ports:
            ports.insert(0, saved_port)
        if not ports:
            ports = ["None"]

        self.scanner_var = ctk.StringVar(value=saved_port if saved_port else ports[0])
        scanner_menu = ctk.CTkOptionMenu(
            scanner_frame,
            values=ports,
            variable=self.scanner_var,
            width=180
        )
        scanner_menu.pack(side="left")

        test_btn = ctk.CTkButton(
            scanner_frame,
            text="Test Connection",
            command=lambda: self.test_scanner_connection(self.scanner_var.get()),
            width=150
        )
        test_btn.pack(side="left", padx=10)

        # Printer selection (Windows)
        printer_frame = ctk.CTkFrame(controls, fg_color="transparent")
        printer_frame.grid(row=7, column=0, sticky="w", pady=(20, 0))

        printer_label = ctk.CTkLabel(printer_frame, text="Preferred Printer:", anchor="w")
        printer_label.pack(side="left", padx=(0, 10))

        printers = self._get_installed_printers()
        saved_printer = self.db.get_setting('preferred_printer', '')
        if saved_printer and saved_printer not in printers and saved_printer:
            printers = [saved_printer] + printers
        if not printers:
            printers = ["None"]

        self.printer_var = ctk.StringVar(value=saved_printer if saved_printer else printers[0])
        printer_menu = ctk.CTkOptionMenu(
            printer_frame,
            values=printers,
            variable=self.printer_var,
            width=240
        )
        printer_menu.pack(side="left")

        # Facial recognition settings
        face_frame = ctk.CTkFrame(controls, fg_color="transparent")
        face_frame.grid(row=8, column=0, sticky="w", pady=(20, 0))

        face_label = ctk.CTkLabel(face_frame, text="Facial Recognition:", anchor="w")
        face_label.pack(side="left", padx=(0, 10))

        face_enabled = self.db.get_setting('face_enabled', 'false')
        self.face_var = ctk.StringVar(value=face_enabled)
        face_switch = ctk.CTkSwitch(face_frame, text="Enable", variable=self.face_var, onvalue='true', offvalue='false')
        face_switch.pack(side="left")

        cams = self.face_mgr.enumerate_cameras()
        if not cams:
            cams = ['0']
        saved_cam = self.db.get_setting('camera_index', '0')
        if saved_cam and saved_cam not in cams:
            cams.insert(0, saved_cam)
        self.cam_var = ctk.StringVar(value=saved_cam if saved_cam else cams[0])
        cam_menu = ctk.CTkOptionMenu(face_frame, values=cams, variable=self.cam_var, width=100)
        cam_menu.pack(side="left", padx=(10, 0))

        # Save settings button
        save_btn = ctk.CTkButton(
            controls,
            text="Save Settings",
            command=self._save_settings,
            width=160
        )
        save_btn.grid(row=9, column=0, sticky="w", pady=(20, 0))

    def _get_installed_printers(self):
        """Enumerate installed printers on Windows. Fallback to empty list if unavailable."""
        printers = []
        try:
            if os.name == 'nt' and importlib.util.find_spec('win32print') is not None:
                win32print = importlib.import_module('win32print')
                flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                for p in win32print.EnumPrinters(flags):
                    # Entries are tuples; name commonly at index 2
                    name = p[2] if len(p) > 2 else None
                    if name:
                        printers.append(name)
        except Exception:
            pass
        # Fallback: try environment default
        default_printer = os.environ.get('PRINTER')
        if default_printer:
            printers.append(default_printer)
        # Deduplicate while preserving order
        seen = set()
        uniq = []
        for n in printers:
            if n not in seen:
                seen.add(n)
                uniq.append(n)
        return uniq

    def _save_settings(self):
        """Persist settings values to the database and apply changes."""
        try:
            # Core toggles
            self.db.set_setting('auto_save_on_logout', int(self.auto_var.get()))
            self.db.set_setting('confirm_logout', int(self.confirm_var.get()))
            self.db.set_setting('auto_save_interval', int(self.interval_var.get()))

            # Scanner and printer
            self.db.set_setting('fingerprint_port', self.scanner_var.get())
            self.db.set_setting('preferred_printer', self.printer_var.get())

            # Face settings
            self.db.set_setting('face_enabled', self.face_var.get())
            self.db.set_setting('camera_index', self.cam_var.get())

            # Apply autosave interval immediately
            try:
                self.stop_autosave_timer()
            except Exception:
                pass
            self.start_autosave_timer(int(self.interval_var.get()))

            messagebox.showinfo("Settings", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    # --- Auto-save and state management ---
    def collect_state(self):
        """Collect a lightweight snapshot of current UI state (forms) to persist."""
        state = {
            'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'last_page': getattr(self, 'last_page', '')
        }
        # Known form fields
        try:
            if hasattr(self, 'entry_name'):
                state['add_employee'] = {
                    'name': self.entry_name.get(),
                    'email': self.entry_email.get() if hasattr(self, 'entry_email') else '',
                    'fingerprint_id': self.entry_fingerprint.get() if hasattr(self, 'entry_fingerprint') else ''
                }
        except Exception:
            pass

        try:
            if hasattr(self, 'entry_fingerprint_scan'):
                state['mark_attendance'] = {'fingerprint_id': self.entry_fingerprint_scan.get()}
        except Exception:
            pass

        return state

    def save_state(self):
        """Persist the collected state to a local backup JSON file."""
        try:
            state = self.collect_state()
            backups_dir = os.path.join(os.getcwd(), 'backups')
            os.makedirs(backups_dir, exist_ok=True)
            fname = f"state_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
            path = os.path.join(backups_dir, fname)
            import json
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2)
            print(f"📦 Auto-saved state to {path}")
            return True
        except Exception as e:
            print("⚠️ Failed to auto-save state:", e)
            return False

    def start_autosave_timer(self, interval_seconds=60):
        """Start a periodic autosave timer. Stops previous if running."""
        try:
            self.stop_autosave_timer()
        except Exception:
            pass
        self._autosave_interval = max(1, int(interval_seconds))

        def tick():
            self.save_state()
            # schedule again
            self._autosave_id = self.root.after(self._autosave_interval * 1000, tick)

        self._autosave_id = self.root.after(self._autosave_interval * 1000, tick)

    def stop_autosave_timer(self):
        try:
            if hasattr(self, '_autosave_id') and self._autosave_id:
                self.root.after_cancel(self._autosave_id)
                self._autosave_id = None
        except Exception:
            pass

    def change_theme_mode(self, mode):
        """Change the application theme mode."""
        ctk.set_appearance_mode(str(mode).lower())
        self.db.set_setting('theme_mode', str(mode))

    def test_scanner_connection(self, port=None):
        """Test the fingerprint scanner connection."""
        if port is None:
            port = self.scanner_var.get() if hasattr(self, 'scanner_var') else None

        if not port or port == "None":
            messagebox.showerror("Error", "Please select a scanner port first")
            return

        try:
            # Try to initialize scanner with selected port
            scanner = FingerprintScanner(port=port)
            if scanner.test_connection():
                messagebox.showinfo("Success", f"Scanner connected successfully on {port}")
            else:
                messagebox.showerror("Connection Failed", f"Could not connect to scanner on {port}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test scanner: {str(e)}")

    def logout(self):
        """Logout the current user. If an on_logout callback was provided, call it.

        Otherwise, clear the root window and show the login screen.
        """
        # Confirmation dialog
        if not messagebox.askyesno("Confirm Logout", "Are you sure you want to logout?"):
            return
        if callable(self.on_logout):
            try:
                self.on_logout()
                return
            except Exception as e:
                print("⚠️ on_logout callback failed:", e)

        # Fallback: clear root children and show login screen
        try:
            from .login import LoginScreen
            for w in self.root.winfo_children():
                w.destroy()
            LoginScreen(self.root, self.db, lambda uid, role: None)
        except Exception as e:
            print("⚠️ Failed to logout cleanly:", e)
    # ----------------- Utility -----------------
    def clear_main_frame(self):
        if self.current_frame:
            self.current_frame.destroy()
            
    def create_page_header(self, title, subtitle=None):
        """Create a consistent page header with title and optional subtitle"""
        header_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))
        
        title_label = ctk.CTkLabel(
            header_frame, 
            text=title, 
            font=("Segoe UI", 24, "bold"),
            text_color=self.primary_color
        )
        title_label.pack(anchor="w", pady=(0, 5))
        
        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header_frame, 
                text=subtitle, 
                font=("Segoe UI", 14),
                text_color=self.text_color
            )
            subtitle_label.pack(anchor="w")
            
        # Separator
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.pack(fill="x", pady=(10, 0))
        
        return header_frame

    # ----------------- Dashboard -----------------
    def show_dashboard(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Dashboard", "Welcome to GDC Attendance System")
        
        # Stats cards row
        stats_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=20)
        
        # Employee count card
        count = len(self.db.get_all_employees())
        self.create_stat_card(stats_frame, "Total Employees", count, "👥", self.primary_color, 0)
        
        # Today's attendance card (filtered for today)
        try:
            today_count = int(self.db.get_today_attendance_count())
        except Exception:
            today_count = 0
        self.create_stat_card(stats_frame, "Today's Attendance", today_count, "📊", self.success_color, 1)
        
        # Absent employees card
        # This is a placeholder - you would need to implement the actual count
        absent_count = count - today_count if count > today_count else 0
        self.create_stat_card(stats_frame, "Absent Today", absent_count, "❗", self.error_color, 2)
        
        # Recent activity section
        activity_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        activity_frame.pack(fill="both", expand=True, pady=20)
        
        activity_header = ctk.CTkLabel(
            activity_frame, 
            text="Recent Activity", 
            font=("Segoe UI", 18, "bold"),
            text_color=self.text_color
        )
        activity_header.pack(anchor="w", padx=20, pady=15)
        
        # Recent attendance records
        try:
            records = self.db.get_today_attendance_records()
        except Exception:
            records = []
        if not records:
            empty_label = ctk.CTkLabel(
                activity_frame, 
                text="No recent activity to display", 
                font=("Segoe UI", 14),
                text_color="#757575"
            )
            empty_label.pack(pady=30)
        else:
            # Show only the 5 most recent records
            recent_records = records[-5:] if len(records) > 5 else records
            
            for record in recent_records:
                record_frame = ctk.CTkFrame(activity_frame, fg_color="#f8f9fa", corner_radius=5)
                record_frame.pack(fill="x", padx=20, pady=5)
                
                name_label = ctk.CTkLabel(
                    record_frame, 
                    text=f"{record['name']} — {record['date']}", 
                    font=("Segoe UI", 14, "bold"),
                    text_color=self.text_color
                )
                name_label.pack(side="left", padx=15, pady=10)

                times = []
                if record['arrival_time']:
                    times.append(f"Arrived {record['arrival_time']}")
                if record['departure_time']:
                    times.append(f"Left {record['departure_time']}")
                time_text = ",  ".join(times) if times else "No timestamps"
                time_label = ctk.CTkLabel(
                    record_frame, 
                    text=time_text, 
                    font=("Segoe UI", 12),
                    text_color="#757575"
                )
                time_label.pack(side="right", padx=15, pady=10)
    
    def create_stat_card(self, parent, title, value, icon, color, position):
        """Create a dashboard stat card"""
        # Calculate position (0=left, 1=middle, 2=right)
        relx = 0.16 + (position * 0.33)
        
        card = ctk.CTkFrame(parent, width=250, height=120, corner_radius=10, fg_color="white")
        card.place(relx=relx, rely=0.5, anchor="center")
        card.pack_propagate(False)
        
        # Icon with colored background
        icon_frame = ctk.CTkFrame(card, width=40, height=40, corner_radius=20, fg_color=color)
        icon_frame.place(x=20, y=20)
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(
            icon_frame, 
            text=icon, 
            font=("Segoe UI", 16),
            text_color="white"
        )
        icon_label.pack(expand=True)
        
        # Value (large number)
        value_label = ctk.CTkLabel(
            card, 
            text=str(value), 
            font=("Segoe UI", 28, "bold"),
            text_color=self.text_color
        )
        value_label.place(x=20, y=45)
        
        # Title
        title_label = ctk.CTkLabel(
            card, 
            text=title, 
            font=("Segoe UI", 14),
            text_color="#757575"
        )
        title_label.place(x=20, y=80)

    # ----------------- Add Employee -----------------
    def show_add_employee(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Register New Employee", "Add a new employee to the system")
        
        # Form container
        form_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        form_frame.pack(fill="both", expand=True, pady=20)
        
        # Form fields
        fields_frame = ctk.CTkFrame(form_frame, fg_color="transparent")
        fields_frame.pack(pady=30, padx=40)
        
        # Name field
        name_label = ctk.CTkLabel(
            fields_frame, 
            text="Full Name", 
            font=("Segoe UI", 14),
            text_color=self.text_color,
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        self.entry_name = ctk.CTkEntry(
            fields_frame, 
            placeholder_text="Enter employee's full name",
            width=400,
            height=40,
            corner_radius=5,
            border_color=self.primary_color
        )
        self.entry_name.grid(row=1, column=0, sticky="ew", pady=(0, 15))
        
        # Email field
        email_label = ctk.CTkLabel(
            fields_frame, 
            text="Email Address", 
            font=("Segoe UI", 14),
            text_color=self.text_color,
            anchor="w"
        )
        email_label.grid(row=2, column=0, sticky="w", pady=(0, 5))
        
        self.entry_email = ctk.CTkEntry(
            fields_frame, 
            placeholder_text="Enter employee's email address",
            width=400,
            height=40,
            corner_radius=5,
            border_color=self.primary_color
        )
        self.entry_email.grid(row=3, column=0, sticky="ew", pady=(0, 15))
        
        # Fingerprint field
        fingerprint_label = ctk.CTkLabel(
            fields_frame, 
            text="Fingerprint ID", 
            font=("Segoe UI", 14),
            text_color=self.text_color,
            anchor="w"
        )
        fingerprint_label.grid(row=4, column=0, sticky="w", pady=(0, 5))
        
        self.entry_fingerprint = ctk.CTkEntry(
            fields_frame, 
            placeholder_text="Enter fingerprint ID or use scanner",
            width=400,
            height=40,
            corner_radius=5,
            border_color=self.primary_color
        )
        self.entry_fingerprint.grid(row=5, column=0, sticky="ew", pady=(0, 25))
        
        # Buttons
        buttons_frame = ctk.CTkFrame(fields_frame, fg_color="transparent")
        buttons_frame.grid(row=6, column=0, sticky="ew")
        
        cancel_btn = ctk.CTkButton(
            buttons_frame, 
            text="Cancel", 
            command=self.show_dashboard,
            fg_color="transparent",
            text_color=self.text_color,
            border_width=1,
            border_color="#d1d1d1",
            hover_color="#e8eaed",
            width=120,
            height=40,
            corner_radius=5
        )
        cancel_btn.pack(side="left", padx=(0, 10))
        
        enroll_fp_btn = ctk.CTkButton(
            buttons_frame,
            text="Enroll Fingerprint",
            command=self.enroll_fingerprint_for_new_employee,
            fg_color=self.success_color,
            text_color="white",
            hover_color="#0b8043",
            width=160,
            height=40,
            corner_radius=5
        )
        enroll_fp_btn.pack(side="left")

        enroll_face_btn = ctk.CTkButton(
            buttons_frame,
            text="Enroll Face",
            command=self.enroll_face_for_new_employee,
            fg_color=self.primary_color,
            text_color="white",
            hover_color=self.accent_color,
            width=140,
            height=40,
            corner_radius=5
        )
        enroll_face_btn.pack(side="left", padx=(10, 10))

        save_btn = ctk.CTkButton(
            buttons_frame, 
            text="Save Employee", 
            command=self.save_employee,
            fg_color=self.primary_color,
            text_color="white",
            hover_color=self.accent_color,
            width=150,
            height=40,
            corner_radius=5
        )
        save_btn.pack(side="left")

    def save_employee(self):
        name = self.entry_name.get()
        email = self.entry_email.get()
        fingerprint_id = self.entry_fingerprint.get()

        if not name or not email or not fingerprint_id:
            messagebox.showwarning("Input Error", "Please fill all fields!")
            return

        self.show_loading("Saving employee...")
        self.root.after(100, lambda: self._save_employee_action(name, email, fingerprint_id))

    def _save_employee_action(self, name, email, fingerprint_id):
        try:
            tpl = getattr(self, 'enrolled_template', None)
            new_id = self.db.add_employee(name, email, fingerprint_id, fingerprint_template=tpl)
            # If face is enabled, try to capture and link immediately
            try:
                if self.db.get_setting('face_enabled', 'false') == 'true':
                    cam_idx = int(self.db.get_setting('camera_index', '0'))
                    self.face_mgr.enroll_face(employee_id=new_id, camera_index=cam_idx)
            except Exception:
                pass
            # Notify employee via email if enabled
            try:
                if email:
                    self.email_mgr.send_email(
                        to_address=email,
                        subject="Welcome to GDC Attendance",
                        body=f"Hello {name}, your details have been added. Your fingerprint ID is {fingerprint_id}."
                    )
            except Exception:
                pass
            # reset cached template after save
            try:
                self.enrolled_template = None
            except Exception:
                pass
            self.hide_loading()
            messagebox.showinfo("Success", f"Employee {name} added successfully!")
            self.show_dashboard()
        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Failed to save employee: {e}")

    def enroll_fingerprint_for_new_employee(self):
        """Connect to scanner, enroll fingerprint, fill ID and cache template for saving."""
        try:
            port = self.db.get_setting('fingerprint_port', '')
            if not port or port == 'None':
                messagebox.showerror("Scanner", "Please select scanner port in Settings first")
                return
            scanner = FingerprintScanner(port=port)
            if not scanner.connect():
                messagebox.showerror("Scanner", "Unable to connect to scanner on selected port")
                return
            ok, position, template = scanner.enroll_fingerprint()
            scanner.disconnect()
            if ok and position is not None:
                self.entry_fingerprint.delete(0, 'end')
                self.entry_fingerprint.insert(0, str(position))
                self.enrolled_template = template
                messagebox.showinfo("Enrollment", f"Fingerprint enrolled at position {position}")
            else:
                messagebox.showerror("Enrollment", "Fingerprint enrollment failed or already exists")
        except Exception as e:
            messagebox.showerror("Enrollment", f"Error during enrollment: {e}")

    def enroll_face_for_new_employee(self):
        """Capture and store a face image for the employee using the selected camera."""
        try:
            # Temporarily create a fake ID to preview; actual file is saved at employee_id after save.
            # For pre-save, we store image under a temp name and move on save if needed.
            cam_idx = int(self.db.get_setting('camera_index', '0'))
            # Use a temporary employee_id of 0 to capture; We'll re-capture after save if needed.
            # Instead, simply notify user to capture after saving with Edit Employee in future.
            # For now, capture into a temp file for verification preview.
            ok = self.face_mgr.enroll_face(employee_id=0, camera_index=cam_idx)
            if ok:
                messagebox.showinfo("Face Enrollment", "Face captured. It will be linked after saving employee.")
            else:
                messagebox.showerror("Face Enrollment", "Unable to capture a face. Ensure lighting and camera availability.")
        except Exception as e:
            messagebox.showerror("Face Enrollment", f"Error capturing face: {e}")

    # ----------------- View Employees -----------------
    def show_view_employees(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Registered Employees", "View and manage all employees")
        
        # Main container
        main_container = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        main_container.pack(fill="both", expand=True)
        
        # Search and filter bar
        filter_frame = ctk.CTkFrame(main_container, fg_color="white", corner_radius=10, height=60)
        filter_frame.pack(fill="x", pady=(0, 20))
        filter_frame.pack_propagate(False)
        
        search_entry = ctk.CTkEntry(
            filter_frame, 
            placeholder_text="Search employees...",
            width=300,
            height=36,
            corner_radius=5
        )
        search_entry.pack(side="left", padx=20, pady=12)
        
        def search_employees():
            query = search_entry.get().strip().lower()
            for item in employee_tree.get_children():
                employee_tree.delete(item)

            for emp in employees:
                name = str(emp[1] or '').lower()
                email = str(emp[2] or '').lower()
                fid = str(emp[3] or '').lower()
                if query in name or query in email or query in fid:
                    employee_tree.insert("", "end", values=(emp[1], emp[2], emp[3], "Edit"))

        search_btn = ctk.CTkButton(
            filter_frame, 
            text="Search", 
            command=search_employees,
            fg_color=self.primary_color,
            text_color="white",
            width=100,
            height=36,
            corner_radius=5
        )
        search_btn.pack(side="left", padx=10)

        # Clear search button
        clear_btn = ctk.CTkButton(
            filter_frame,
            text="Clear",
            command=lambda: [search_entry.delete(0, 'end'), refresh_employee_tree()],
            fg_color="transparent",
            text_color=self.text_color,
            border_width=1,
            border_color="#d1d1d1",
            hover_color="#e8eaed",
            width=80,
            height=36,
            corner_radius=5
        )
        clear_btn.pack(side="left", padx=5)

        def export_employees():
            try:
                import csv
                from tkinter import filedialog
                
                # Ask user where to save the file
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    filetypes=[
                        ("CSV files", "*.csv"),
                        ("Excel files", "*.xlsx"),
                        ("All files", "*.*")
                    ],
                    initialfile="employee_data.csv"
                )
                
                if not file_path:  # User cancelled
                    return

                if file_path.endswith('.xlsx'):
                    try:
                        import pandas as pd
                        # Convert to DataFrame and export
                        df = pd.DataFrame(employees, columns=['ID', 'Name', 'Email', 'Fingerprint ID'])
                        df.to_excel(file_path, index=False)
                    except ImportError:
                        messagebox.showerror("Error", "Excel export requires pandas. Please install it or use CSV format.")
                        return
                else:
                    # Export as CSV
                    with open(file_path, mode='w', newline='', encoding='utf-8') as file:
                        writer = csv.writer(file)
                        writer.writerow(['Name', 'Email', 'Fingerprint ID'])  # Header
                        for emp in employees:
                            writer.writerow(emp[1:])  # Skip ID column
                
                messagebox.showinfo("Success", f"Employee data exported successfully to {file_path}")
            
            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export data: {str(e)}")

        # Export button
        export_btn = ctk.CTkButton(
            filter_frame,
            text="Export Data",
            command=export_employees,
            fg_color="transparent",
            text_color=self.primary_color,
            border_width=1,
            border_color=self.primary_color,
            hover_color="#e8eaed",
            width=120,
            height=36,
            corner_radius=5
        )
        export_btn.pack(side="right", padx=5)

        def import_employees():
            try:
                from tkinter import filedialog
                import csv
                
                # Ask user to select the file
                file_path = filedialog.askopenfilename(
                    filetypes=[
                        ("CSV files", "*.csv"),
                        ("Excel files", "*.xlsx"),
                        ("All files", "*.*")
                    ]
                )
                
                if not file_path:  # User cancelled
                    return

                # Show preview dialog
                preview_dialog = ctk.CTkToplevel(self.root)
                preview_dialog.title("Import Preview")
                preview_dialog.geometry("800x600")
                preview_dialog.transient(self.root)
                preview_dialog.grab_set()

                # Center dialog
                x = self.root.winfo_x() + (self.root.winfo_width() - 800) // 2
                y = self.root.winfo_y() + (self.root.winfo_height() - 600) // 2
                preview_dialog.geometry(f"+{x}+{y}")

                # Create preview tree
                preview_frame = ctk.CTkFrame(preview_dialog)
                preview_frame.pack(fill="both", expand=True, padx=20, pady=20)

                info_label = ctk.CTkLabel(
                    preview_frame,
                    text="Review the data before importing. Existing fingerprint IDs will be skipped.",
                    font=("Segoe UI", 12)
                )
                info_label.pack(pady=(0, 10))

                columns = ("name", "email", "fingerprint")
                preview_tree = ttk.Treeview(preview_frame, columns=columns, show="headings")
                
                preview_tree.heading("name", text="Name")
                preview_tree.heading("email", text="Email")
                preview_tree.heading("fingerprint", text="Fingerprint ID")

                # Add scrollbar
                scrollbar = ttk.Scrollbar(preview_frame, orient="vertical", command=preview_tree.yview)
                preview_tree.configure(yscrollcommand=scrollbar.set)
                scrollbar.pack(side="right", fill="y")
                preview_tree.pack(fill="both", expand=True)

                # Load data
                data_to_import = []
                try:
                    if file_path.endswith('.xlsx'):
                        try:
                            import pandas as pd
                            df = pd.read_excel(file_path)
                            data_to_import = df.values.tolist()
                        except ImportError:
                            messagebox.showerror("Error", "Excel import requires pandas. Please use CSV format.")
                            preview_dialog.destroy()
                            return
                    else:
                        with open(file_path, mode='r', encoding='utf-8') as file:
                            reader = csv.reader(file)
                            next(reader)  # Skip header
                            data_to_import = list(reader)

                    # Show preview
                    for row in data_to_import:
                        preview_tree.insert("", "end", values=row)

                except Exception as e:
                    messagebox.showerror("Import Error", f"Failed to read file: {str(e)}")
                    preview_dialog.destroy()
                    return

                def do_import():
                    try:
                        imported = 0
                        skipped = 0
                        for row in data_to_import:
                            try:
                                if len(row) >= 3:  # Ensure we have all required fields
                                    name, email, fingerprint = row[0], row[1], row[2]
                                    try:
                                        self.db.add_employee(name, email, fingerprint)
                                        imported += 1
                                    except Exception:  # Assuming duplicate fingerprint ID
                                        skipped += 1
                            except Exception as e:
                                print(f"Error importing row {row}: {e}")
                                skipped += 1

                        messagebox.showinfo("Import Complete", 
                                          f"Successfully imported {imported} employees.\n"
                                          f"Skipped {skipped} duplicate/invalid records.")
                        preview_dialog.destroy()
                        refresh_employee_tree()  # Refresh the main tree view
                    except Exception as e:
                        messagebox.showerror("Import Error", f"Failed to import data: {str(e)}")

                # Buttons
                btn_frame = ctk.CTkFrame(preview_dialog, fg_color="transparent")
                btn_frame.pack(fill="x", padx=20, pady=10)

                cancel_btn = ctk.CTkButton(
                    btn_frame,
                    text="Cancel",
                    command=preview_dialog.destroy,
                    fg_color="transparent",
                    border_width=1,
                    border_color="#d1d1d1",
                    text_color=self.text_color,
                    hover_color="#e8eaed",
                    width=100
                )
                cancel_btn.pack(side="left", padx=5)

                import_btn = ctk.CTkButton(
                    btn_frame,
                    text="Import",
                    command=do_import,
                    fg_color=self.primary_color,
                    text_color="white",
                    width=100
                )
                import_btn.pack(side="right", padx=5)

            except Exception as e:
                messagebox.showerror("Error", f"Failed to start import: {str(e)}")

        # Import button
        import_btn = ctk.CTkButton(
            filter_frame,
            text="Import Data",
            command=import_employees,
            fg_color="transparent",
            text_color=self.primary_color,
            border_width=1,
            border_color=self.primary_color,
            hover_color="#e8eaed",
            width=120,
            height=36,
            corner_radius=5
        )
        import_btn.pack(side="right", padx=5)
        
        # Employees list
        employees_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        employees_frame.pack(fill="both", expand=True)
        
        employees = self.db.get_all_employees()
        if not employees:
            empty_label = ctk.CTkLabel(
                employees_frame, 
                text="No employees registered yet.", 
                font=("Segoe UI", 16),
                text_color="#757575"
            )
            empty_label.pack(pady=50)
            
            add_btn = ctk.CTkButton(
                employees_frame, 
                text="Add Employee", 
                command=self.show_add_employee,
                fg_color=self.primary_color,
                text_color="white",
                width=150,
                height=40,
                corner_radius=5
            )
            add_btn.pack(pady=10)
            return
        
        # Table headers
        headers_frame = ctk.CTkFrame(employees_frame, fg_color="#f1f3f4", height=40, corner_radius=0)
        headers_frame.pack(fill="x", padx=20, pady=(20, 0))
        headers_frame.pack_propagate(False)
        
        headers = ["Name", "Email", "Fingerprint ID", "Actions"]
        widths = [0.35, 0.35, 0.2, 0.1]  # Proportional widths
        
        for i, header in enumerate(headers):
            header_label = ctk.CTkLabel(
                headers_frame, 
                text=header, 
                font=("Segoe UI", 14, "bold"),
                text_color=self.text_color
            )
            header_label.place(relx=sum(widths[:i]) + widths[i]/2, rely=0.5, anchor="center")
        
        # Employee rows
        employees_list_frame = ctk.CTkFrame(employees_frame, fg_color="transparent")
        employees_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))
        
        # Use Treeview instead of custom frames for better performance and built-in features
        columns = ("name", "email", "fingerprint", "actions")
        employee_tree = ttk.Treeview(employees_list_frame, columns=columns, show="headings", style="Treeview")
        
        # Configure sorting
        self.emp_sort_states = {col: False for col in columns}  # False = ascending, True = descending
        
        def sort_employee_column(col):
            items = [(employee_tree.set(item, col), item) for item in employee_tree.get_children("")]
            
            # Regular string sort
            items.sort(key=lambda x: str(x[0] or '').lower(), reverse=self.emp_sort_states[col])
            
            # Rearrange items
            for idx, (_, item) in enumerate(items):
                employee_tree.move(item, "", idx)
            
            # Toggle sort state
            self.emp_sort_states[col] = not self.emp_sort_states[col]
            
            # Update column headers
            for c in columns:
                if c == col:
                    direction = "↓" if self.emp_sort_states[c] else "↑"
                    employee_tree.heading(c, text=f"{c.title()} {direction}", 
                                       command=lambda _c=c: sort_employee_column(_c))
                else:
                    employee_tree.heading(c, text=c.title(), 
                                       command=lambda _c=c: sort_employee_column(_c))
        
        # Set up columns
        employee_tree.heading("name", text="Name", command=lambda: sort_employee_column("name"))
        employee_tree.heading("email", text="Email", command=lambda: sort_employee_column("email"))
        employee_tree.heading("fingerprint", text="Fingerprint ID", command=lambda: sort_employee_column("fingerprint"))
        employee_tree.heading("actions", text="Actions")
        
        employee_tree.column("name", width=200, minwidth=150)
        employee_tree.column("email", width=250, minwidth=200)
        employee_tree.column("fingerprint", width=120, minwidth=100)
        employee_tree.column("actions", width=100, minwidth=80)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(employees_list_frame, orient="vertical", command=employee_tree.yview)
        employee_tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        employee_tree.pack(expand=True, fill="both", padx=20, pady=20)
        
        def refresh_employee_tree():
            for item in employee_tree.get_children():
                employee_tree.delete(item)
            for emp in employees:
                employee_tree.insert("", "end", values=(emp[1], emp[2], emp[3], "Edit"))
        
        # Initial load
        refresh_employee_tree()
        
        def on_tree_click(event):
            region = employee_tree.identify("region", event.x, event.y)
            if region == "cell":
                column = employee_tree.identify_column(event.x)
                if str(column) == "#4":  # Actions column
                    item = employee_tree.selection()[0]
                    emp_name = employee_tree.item(item)['values'][0]
                    messagebox.showinfo("Edit", f"Edit functionality for {emp_name} (to be implemented)")
        
        employee_tree.bind('<ButtonRelease-1>', on_tree_click)

    # ----------------- Mark Attendance -----------------
    def show_mark_attendance(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Mark Attendance", "Record employee attendance")
        
        # Main content
        content_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        content_frame.pack(fill="both", expand=True, pady=20)
        
        # Fingerprint scan section
        scan_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        scan_frame.pack(expand=True, fill="both", padx=40, pady=40)
        
        # Fingerprint icon/image
        icon_frame = ctk.CTkFrame(scan_frame, width=150, height=150, corner_radius=75, fg_color=self.primary_color)
        icon_frame.pack(pady=(0, 30))
        icon_frame.pack_propagate(False)
        
        icon_label = ctk.CTkLabel(
            icon_frame, 
            text="👆", 
            font=("Segoe UI", 60),
            text_color="white"
        )
        icon_label.pack(expand=True)
        
        # Instructions
        instructions = ctk.CTkLabel(
            scan_frame, 
            text="Place finger on scanner or enter ID below", 
            font=("Segoe UI", 16),
            text_color=self.text_color
        )
        instructions.pack(pady=(0, 20))
        
        # Fingerprint ID entry
        self.entry_fingerprint_scan = ctk.CTkEntry(
            scan_frame, 
            placeholder_text="Enter Fingerprint ID",
            width=300,
            height=40,
            corner_radius=5
        )
        self.entry_fingerprint_scan.pack(pady=(0, 20))
        
        # Scan button
        scan_button = ctk.CTkButton(
            scan_frame, 
            text="Mark Attendance", 
            command=self.real_scan,
            fg_color=self.success_color,
            text_color="white",
            hover_color="#0b8043",  # Darker green
            width=200,
            height=50,
            corner_radius=5,
            font=("Segoe UI", 16)
        )
        scan_button.pack()

    def real_scan(self):
        # Attempt hardware scan first if a scanner port is configured
        employee_id = None
        fingerprint_id = None
        scanner_error = None
        try:
            port = self.db.get_setting('fingerprint_port', '')
            if port and port != 'None':
                scanner = FingerprintScanner(port=port)
                if scanner.connect():
                    ok, position = scanner.verify_fingerprint()
                    scanner.disconnect()
                    if ok and position is not None:
                        fingerprint_id = str(position)
                        # Map fingerprint position to employee_id
                        employees = self.db.get_all_employees()
                        for emp in employees:
                            if emp[3] and str(emp[3]) == fingerprint_id:
                                employee_id = emp[0]
                                break
                else:
                    scanner_error = "Scanner not reachable on selected port"
        except Exception as e:
            scanner_error = str(e)

        # Facial recognition fallback if enabled and no employee match yet
        if employee_id is None and self.db.get_setting('face_enabled', 'false') == 'true':
            try:
                cam_idx = int(self.db.get_setting('camera_index', '0'))
                emp_id, score = self.face_mgr.verify_face(camera_index=cam_idx)
                if emp_id is not None:
                    employee_id = emp_id
            except Exception:
                pass

        # Manual fallback: map entered fingerprint ID to employee
        if employee_id is None:
            manual = self.entry_fingerprint_scan.get().strip()
            if manual:
                try:
                    employees = self.db.get_all_employees()
                    for emp in employees:
                        if emp[3] and str(emp[3]) == manual:
                            employee_id = emp[0]
                            break
                except Exception:
                    employee_id = None

        if employee_id is None:
            msg = scanner_error or "No match from scanner/face and manual input empty"
            messagebox.showerror("Scan Failed", msg)
            return

        # Clear manual input for next day's fresh entries
        try:
            self.entry_fingerprint_scan.delete(0, 'end')
        except Exception:
            pass

        self.show_loading("Marking attendance...")
        self.root.after(100, lambda: self._mark_by_employee_id(employee_id))

    def _real_scan_action(self, fingerprint_id):
        try:
            employees = self.db.get_all_employees()
            match = next((emp for emp in employees if emp[3] == fingerprint_id), None)

            if match:
                emp_id = match[0]
                name = match[1]
                # mark arrival or departure depending on today's record
                result = self.db.mark_arrival_or_departure(emp_id)

                date = result.get('date')
                time = result.get('time')
                action = result.get('action')

                if self.firebase:
                    try:
                        self.firebase.upload_attendance({"name": name, "status": action, "timestamp": f"{date} {time}"})
                    except Exception as e:
                        print("⚠️ Firebase upload failed:", e)

                self.hide_loading()
                messagebox.showinfo("Attendance Marked", f"{action.title()} recorded for {name} on {date} at {time}")
            else:
                self.hide_loading()
                messagebox.showerror("Scan Failed", "Fingerprint not recognized!")
        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Failed to mark attendance: {e}")

    def _mark_by_employee_id(self, employee_id: int):
        try:
            employees = self.db.get_all_employees()
            match = next((emp for emp in employees if int(emp[0]) == int(employee_id)), None)
            if match:
                emp_id = match[0]
                name = match[1]
                email = match[2] if len(match) > 2 else ''
                result = self.db.mark_arrival_or_departure(emp_id)
                date = result.get('date')
                time = result.get('time')
                action = result.get('action')
                if self.firebase:
                    try:
                        self.firebase.upload_attendance({"name": name, "status": action, "timestamp": f"{date} {time}"})
                    except Exception:
                        pass
                # Email notification
                try:
                    if email:
                        self.email_mgr.send_email(
                            to_address=email,
                            subject=f"Attendance {action.title()} Recorded",
                            body=f"Hello {name}, your {action} was recorded on {date} at {time}."
                        )
                except Exception:
                    pass
                self.hide_loading()
                messagebox.showinfo("Attendance Marked", f"{action.title()} recorded for {name} on {date} at {time}")
            else:
                self.hide_loading()
                messagebox.showerror("Scan Failed", "Employee not recognized!")
        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Failed to mark attendance: {e}")

    # ----------------- Attendance Records -----------------
    def show_attendance_records(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Attendance Records", "View and export attendance data")
        
        # Filter bar with advanced options
        filter_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        filter_frame.pack(fill="x", pady=(0, 20))

        # Top row - Date range and employee filter
        top_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        top_row.pack(fill="x", padx=20, pady=10)

        # Date range
        date_range_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        date_range_frame.pack(side="left")

        from_label = ctk.CTkLabel(
            date_range_frame, 
            text="From:", 
            font=("Segoe UI", 14),
            text_color=self.text_color
        )
        from_label.pack(side="left", padx=(0, 5))
        
        from_date = ctk.CTkEntry(
            date_range_frame, 
            placeholder_text="YYYY-MM-DD",
            width=120,
            height=36,
            corner_radius=5
        )
        from_date.pack(side="left", padx=5)

        to_label = ctk.CTkLabel(
            date_range_frame, 
            text="To:", 
            font=("Segoe UI", 14),
            text_color=self.text_color
        )
        to_label.pack(side="left", padx=(10, 5))
        
        to_date = ctk.CTkEntry(
            date_range_frame, 
            placeholder_text="YYYY-MM-DD",
            width=120,
            height=36,
            corner_radius=5
        )
        to_date.pack(side="left", padx=5)

        # Calendar picker buttons
        def show_calendar(entry_widget):
            import tkcalendar
            
            top = ctk.CTkToplevel(self.root)
            top.title("Select Date")
            
            def set_date():
                selected_date = cal.get_date()
                entry_widget.delete(0, 'end')
                entry_widget.insert(0, selected_date)
                top.destroy()
            
            cal = tkcalendar.Calendar(
                top,
                selectmode='day',
                date_pattern='yyyy-mm-dd'
            )
            cal.pack(padx=10, pady=10)
            
            ok_btn = ctk.CTkButton(
                top,
                text="OK",
                command=set_date,
                width=80
            )
            ok_btn.pack(pady=5)
            
            # Position calendar popup near the entry widget
            x = entry_widget.winfo_rootx()
            y = entry_widget.winfo_rooty() + entry_widget.winfo_height()
            top.geometry(f"+{x}+{y}")

        from_cal_btn = ctk.CTkButton(
            date_range_frame,
            text="📅",
            width=36,
            height=36,
            command=lambda: show_calendar(from_date)
        )
        from_cal_btn.pack(side="left", padx=(0, 10))

        to_cal_btn = ctk.CTkButton(
            date_range_frame,
            text="📅",
            width=36,
            height=36,
            command=lambda: show_calendar(to_date)
        )
        to_cal_btn.pack(side="left")

        # Employee filter
        employee_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        employee_frame.pack(side="left", padx=20)

        emp_label = ctk.CTkLabel(
            employee_frame,
            text="Employee:",
            font=("Segoe UI", 14),
            text_color=self.text_color
        )
        emp_label.pack(side="left", padx=(0, 5))

        # Get all employee names for the dropdown
        all_employees = self.db.get_all_employees()
        employee_names = ["All Employees"] + [emp[1] for emp in all_employees]
        employee_var = ctk.StringVar(value="All Employees")
        
        employee_dropdown = ctk.CTkOptionMenu(
            employee_frame,
            values=employee_names,
            variable=employee_var,
            width=200,
            height=36
        )
        employee_dropdown.pack(side="left")

        # Bottom row - Status filter and buttons
        bottom_row = ctk.CTkFrame(filter_frame, fg_color="transparent")
        bottom_row.pack(fill="x", padx=20, pady=(0, 10))

        # Status filter
        status_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        status_frame.pack(side="left")

        status_label = ctk.CTkLabel(
            status_frame,
            text="Status:",
            font=("Segoe UI", 14),
            text_color=self.text_color
        )
        status_label.pack(side="left", padx=(0, 5))

        status_var = ctk.StringVar(value="All")
        status_dropdown = ctk.CTkOptionMenu(
            status_frame,
            values=["All", "Present", "Absent", "Late"],
            variable=status_var,
            width=120,
            height=36
        )
        status_dropdown.pack(side="left", padx=5)

        def apply_filters():
            try:
                # Get filter values
                start_date = from_date.get().strip()
                end_date = to_date.get().strip()
                employee = employee_var.get()
                status = status_var.get()

                # Validate dates if provided
                if start_date:
                    try:
                        datetime.strptime(start_date, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format for start date")
                        return

                if end_date:
                    try:
                        datetime.strptime(end_date, "%Y-%m-%d")
                    except ValueError:
                        messagebox.showerror("Invalid Date", "Please use YYYY-MM-DD format for end date")
                        return

                # Clear current records
                for item in tree.get_children():
                    tree.delete(item)

                # Get all records
                records = self.db.get_attendance_records()

                # Apply filters
                filtered_records = []
                for record in records:
                    record_date = datetime.strptime(record[0], "%Y-%m-%d")
                    
                    # Date range filter
                    if start_date and record_date < datetime.strptime(start_date, "%Y-%m-%d"):
                        continue
                    if end_date and record_date > datetime.strptime(end_date, "%Y-%m-%d"):
                        continue

                    # Employee filter
                    if employee != "All Employees" and record[1] != employee:
                        continue

                    # Status filter
                    if status != "All":
                        arrival_time = record[2] if record[2] else ""
                        if status == "Present" and not arrival_time:
                            continue
                        elif status == "Absent" and arrival_time:
                            continue
                        elif status == "Late" and arrival_time:
                            # Consider "late" if arrival is after 9:00 AM
                            try:
                                arrival_dt = datetime.strptime(arrival_time, "%H:%M:%S")
                                if arrival_dt.time() <= datetime.strptime("09:00:00", "%H:%M:%S").time():
                                    continue
                            except:
                                continue

                    filtered_records.append(record)

                if not filtered_records:
                    messagebox.showinfo("No Records", "No attendance records found matching the filters")

                # Display filtered records
                for record in filtered_records:
                    tree.insert("", "end", values=(record[0], record[1], record[2] or "", record[3] or ""))

            except Exception as e:
                messagebox.showerror("Error", f"Failed to apply filters: {str(e)}")

        def clear_filters():
            from_date.delete(0, 'end')
            to_date.delete(0, 'end')
            employee_var.set("All Employees")
            status_var.set("All")
            refresh_attendance_records(tree)

        # Filter and Clear buttons
        buttons_frame = ctk.CTkFrame(bottom_row, fg_color="transparent")
        buttons_frame.pack(side="right")

        apply_btn = ctk.CTkButton(
            buttons_frame,
            text="Apply Filters",
            command=apply_filters,
            fg_color=self.primary_color,
            text_color="white",
            width=120,
            height=36,
            corner_radius=5
        )
        apply_btn.pack(side="left", padx=5)

        clear_btn = ctk.CTkButton(
            buttons_frame,
            text="Clear Filters",
            command=clear_filters,
            fg_color="transparent",
            text_color=self.text_color,
            border_width=1,
            border_color="#d1d1d1",
            hover_color="#e8eaed",
            width=120,
            height=36,
            corner_radius=5
        )
        clear_btn.pack(side="left", padx=5)
        
        def export_to_csv():
            try:
                # Get currently displayed records (filtered or all)
                records_to_export = []
                for item in tree.get_children():
                    values = tree.item(item)['values']
                    records_to_export.append(values)

                if not records_to_export:
                    messagebox.showinfo("No Data", "No records to export")
                    return

                # Ask user where to save the file
                current_date = datetime.now().strftime("%Y%m%d")
                filename = f"attendance_{current_date}.csv"
                import tkinter.filedialog as fd
                file_path = fd.asksaveasfilename(
                    defaultextension=".csv",
                    initialfile=filename,
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )

                if not file_path:  # User cancelled
                    return

                # Write CSV file
                import csv
                with open(file_path, 'w', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Date", "Employee Name", "Arrival Time", "Departure Time"])
                    writer.writerows(records_to_export)

                messagebox.showinfo("Success", f"Records exported to {file_path}")

            except Exception as e:
                messagebox.showerror("Export Error", f"Failed to export records: {e}")

        # Export button
        export_btn = ctk.CTkButton(
            filter_frame,
            text="Export Data",
            command=export_to_csv,
            fg_color="transparent",
            text_color=self.primary_color,
            border_width=1,
            border_color=self.primary_color,
            hover_color="#e8eaed",
            width=120,
            height=36,
            corner_radius=5
        )
        export_btn.pack(side="right", padx=20)
        
        # Records table
        records_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        records_frame.pack(fill="both", expand=True)
        
        records = self.db.get_attendance_records()
        if not records:
            empty_label = ctk.CTkLabel(
                records_frame, 
                text="No attendance records yet.", 
                font=("Segoe UI", 16),
                text_color="#757575"
            )
            empty_label.pack(pady=50)
            return
        
        # Use ttk.Treeview for the table
        columns = ("date", "name", "arrival", "departure")
        tree = ttk.Treeview(records_frame, columns=columns, show="headings", style="Treeview")
        
        # Configure sorting
        self.sort_states = {col: False for col in columns}  # False = ascending, True = descending
        
        def sort_column(col):
            # Get all items
            items = [(tree.set(item, col), item) for item in tree.get_children("")]
            
            # Determine sort method based on column
            if col == "date":
                # Sort dates
                items.sort(key=lambda x: (x[0] is None or x[0] == "", x[0]), reverse=self.sort_states[col])
            elif col in ["arrival", "departure"]:
                # Sort times, handling empty values
                items.sort(key=lambda x: (x[0] is None or x[0] == "", x[0]), reverse=self.sort_states[col])
            else:
                # Regular string sort
                items.sort(key=lambda x: str(x[0] or '').lower(), reverse=self.sort_states[col])
            
            # Rearrange items
            for idx, (_, item) in enumerate(items):
                tree.move(item, "", idx)
            
            # Toggle sort state
            self.sort_states[col] = not self.sort_states[col]
            
            # Update column headers to show sort direction
            for c in columns:
                if c == col:
                    direction = "↓" if self.sort_states[c] else "↑"
                    tree.heading(c, text=f"{c.title()} {direction}", command=lambda _c=c: sort_column(_c))
                else:
                    tree.heading(c, text=c.title(), command=lambda _c=c: sort_column(_c))
        
        # Set up column headings with sort functionality
        tree.heading("date", text="Date", command=lambda: sort_column("date"))
        tree.heading("name", text="Employee Name", command=lambda: sort_column("name"))
        tree.heading("arrival", text="Arrival", command=lambda: sort_column("arrival"))
        tree.heading("departure", text="Departure", command=lambda: sort_column("departure"))
        
        tree.column("date", width=120, minwidth=100)
        tree.column("name", width=220, minwidth=150)
        tree.column("arrival", width=120, minwidth=100)
        tree.column("departure", width=120, minwidth=100)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(records_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(expand=True, fill="both", padx=20, pady=20)
        
        def refresh_attendance_records(tree):
            for item in tree.get_children():
                tree.delete(item)
            records = self.db.get_attendance_records()
            for record in records:
                tree.insert("", "end", values=(record[0], record[1], record[2] or "", record[3] or ""))
        
        # Initial load
        refresh_attendance_records(tree)
