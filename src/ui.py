import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import os
from PIL import Image, ImageTk
from .permissions import Permissions

# Placeholder for real fingerprint SDK
# from fingerprint_sdk import FingerprintScanner

class AdminDashboard:
    def show_loading(self, message="Loading..."):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            return  # Already showing
        self._loading_overlay = ctk.CTkFrame(self.root, fg_color="#00000080")
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
        ctk.set_appearance_mode("system")  # Options: "system" (default), "light", "dark"
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

        def save_settings():
            try:
                ai = int(self.interval_var.get())
                if ai <= 0:
                    raise ValueError
            except Exception:
                messagebox.showerror("Error", "Interval must be a positive integer")
                return

            self.db.set_setting('auto_save_on_logout', str(self.auto_var.get()))
            self.db.set_setting('auto_save_interval', str(ai))
            self.db.set_setting('confirm_logout', str(self.confirm_var.get()))
            messagebox.showinfo("Saved", "Settings saved successfully")

            # restart autosave timer according to new settings
            if int(self.auto_var.get()):
                self.start_autosave_timer(ai)
            else:
                self.stop_autosave_timer()

        save_btn = ctk.CTkButton(controls, text="Save Settings", command=save_settings, fg_color=self.primary_color)
        save_btn.grid(row=4, column=0, pady=(20, 0))

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
        
        # Today's attendance card
        # This is a placeholder - you would need to implement the actual count
        today_count = len(self.db.get_attendance_records()) # This should be filtered for today
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
        records = self.db.get_attendance_records()
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
                    text=record[0], 
                    font=("Segoe UI", 14, "bold"),
                    text_color=self.text_color
                )
                name_label.pack(side="left", padx=15, pady=10)
                
                time_label = ctk.CTkLabel(
                    record_frame, 
                    text=record[1], 
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
            self.db.add_employee(name, email, fingerprint_id)
            self.hide_loading()
            messagebox.showinfo("Success", f"Employee {name} added successfully!")
            self.show_dashboard()
        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Failed to save employee: {e}")

    # ----------------- View Employees -----------------
    def show_view_employees(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Registered Employees", "View and manage all employees")
        
        # Search and filter bar
        filter_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10, height=60)
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
        
        search_btn = ctk.CTkButton(
            filter_frame, 
            text="Search", 
            command=lambda: None,  # Placeholder for search functionality
            fg_color=self.primary_color,
            text_color="white",
            width=100,
            height=36,
            corner_radius=5
        )
        search_btn.pack(side="left", padx=10)
        
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
        
        for i, emp in enumerate(employees):
            row_frame = ctk.CTkFrame(
                employees_list_frame, 
                fg_color="white" if i % 2 == 0 else "#f8f9fa", 
                height=50, 
                corner_radius=0
            )
            row_frame.pack(fill="x", pady=1)
            row_frame.pack_propagate(False)
            
            # Name
            name_label = ctk.CTkLabel(
                row_frame, 
                text=emp[1], 
                font=("Segoe UI", 14),
                text_color=self.text_color
            )
            name_label.place(relx=widths[0]/2, rely=0.5, anchor="center")
            
            # Email
            email_label = ctk.CTkLabel(
                row_frame, 
                text=emp[2], 
                font=("Segoe UI", 14),
                text_color=self.text_color
            )
            email_label.place(relx=widths[0] + widths[1]/2, rely=0.5, anchor="center")
            
            # Fingerprint ID
            fp_label = ctk.CTkLabel(
                row_frame, 
                text=emp[3], 
                font=("Segoe UI", 14),
                text_color=self.text_color
            )
            fp_label.place(relx=widths[0] + widths[1] + widths[2]/2, rely=0.5, anchor="center")
            
            # Actions
            actions_frame = ctk.CTkFrame(row_frame, fg_color="transparent")
            actions_frame.place(relx=widths[0] + widths[1] + widths[2] + widths[3]/2, rely=0.5, anchor="center")
            
            edit_btn = ctk.CTkButton(
                actions_frame, 
                text="Edit", 
                command=lambda: None,  # Placeholder for edit functionality
                fg_color="transparent",
                text_color=self.primary_color,
                hover_color="#e8eaed",
                width=60,
                height=30,
                corner_radius=5
            )
            edit_btn.pack(side="left", padx=5)

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
        fingerprint_id = self.entry_fingerprint_scan.get().strip()
        self.show_loading("Marking attendance...")
        self.root.after(100, lambda: self._real_scan_action(fingerprint_id))

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

    # ----------------- Attendance Records -----------------
    def show_attendance_records(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)
        
        self.create_page_header("Attendance Records", "View and export attendance data")
        
        # Filter bar
        filter_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10, height=60)
        filter_frame.pack(fill="x", pady=(0, 20))
        filter_frame.pack_propagate(False)
        
        date_label = ctk.CTkLabel(
            filter_frame, 
            text="Date:", 
            font=("Segoe UI", 14),
            text_color=self.text_color
        )
        date_label.pack(side="left", padx=(20, 5), pady=12)
        
        date_entry = ctk.CTkEntry(
            filter_frame, 
            placeholder_text="YYYY-MM-DD",
            width=150,
            height=36,
            corner_radius=5
        )
        date_entry.pack(side="left", padx=5, pady=12)
        
        filter_btn = ctk.CTkButton(
            filter_frame, 
            text="Filter", 
            command=lambda: None,  # Placeholder for filter functionality
            fg_color=self.primary_color,
            text_color="white",
            width=100,
            height=36,
            corner_radius=5
        )
        filter_btn.pack(side="left", padx=10)
        
        export_btn = ctk.CTkButton(
            filter_frame, 
            text="Export CSV", 
            command=lambda: None,  # Placeholder for export functionality
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
        tree.heading("date", text="Date")
        tree.heading("name", text="Employee Name")
        tree.heading("arrival", text="Arrival")
        tree.heading("departure", text="Departure")
        tree.column("date", width=120)
        tree.column("name", width=220)
        tree.column("arrival", width=120)
        tree.column("departure", width=120)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(records_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Insert records
        for record in records:
            # record is (date, name, arrival_time, departure_time)
            tree.insert("", "end", values=(record[0], record[1], record[2] or "", record[3] or ""))
