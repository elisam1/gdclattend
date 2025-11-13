import customtkinter as ctk
from tkinter import messagebox

class LoginScreen:
    def __init__(self, root, db, on_login_success):
        self.root = root
        self.db = db
        self.on_login_success = on_login_success
        
        # Configure the window
        self.root.title("GDC Attendance System - Login")
        self.root.geometry("400x450")
        
        # Set color scheme
        self.primary_color = "#1E88E5"  # Blue
        self.secondary_color = "#FFC107"  # Amber
        self.bg_color = "#F5F5F5"  # Light gray
        self.text_color = "#212121"  # Dark gray
        
        # Create main frame
        self.main_frame = ctk.CTkFrame(self.root, fg_color=self.bg_color)
        self.main_frame.pack(fill="both", expand=True)
        
        # Create header
        self.header_frame = ctk.CTkFrame(self.main_frame, fg_color=self.primary_color, height=80)
        self.header_frame.pack(fill="x", padx=0, pady=0)
        
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="GDC ATTENDANCE SYSTEM", 
            font=("Roboto", 22, "bold"),
            text_color="white"
        )
        self.title_label.place(relx=0.5, rely=0.5, anchor="center")
        
        # Create login form
        self.form_frame = ctk.CTkFrame(self.main_frame, fg_color=self.bg_color)
        self.form_frame.pack(fill="both", expand=True, padx=40, pady=40)
        
        # Login title
        self.login_label = ctk.CTkLabel(
            self.form_frame,
            text="Login to your account",
            font=("Roboto", 18),
            text_color=self.text_color
        )
        self.login_label.pack(pady=(0, 20))
        
        # Username
        self.username_label = ctk.CTkLabel(
            self.form_frame,
            text="Username",
            font=("Roboto", 14),
            text_color=self.text_color
        )
        self.username_label.pack(anchor="w", pady=(10, 5))
        
        self.username_entry = ctk.CTkEntry(
            self.form_frame,
            width=320,
            height=40,
            placeholder_text="Enter your username"
        )
        self.username_entry.pack(pady=(0, 10))
        
        # Password
        self.password_label = ctk.CTkLabel(
            self.form_frame,
            text="Password",
            font=("Roboto", 14),
            text_color=self.text_color
        )
        self.password_label.pack(anchor="w", pady=(10, 5))
        
        self.password_entry = ctk.CTkEntry(
            self.form_frame,
            width=320,
            height=40,
            placeholder_text="Enter your password",
            show="•"
        )
        self.password_entry.pack(pady=(0, 20))
        
        # Login button
        self.login_button = ctk.CTkButton(
            self.form_frame,
            text="Login",
            font=("Roboto", 14, "bold"),
            fg_color=self.primary_color,
            hover_color="#1976D2",
            height=40,
            command=self.login
        )
        self.login_button.pack(pady=10)
        
        # Default credentials note
        self.note_label = ctk.CTkLabel(
            self.form_frame,
            text="Default admin: username 'admin', password 'admin123'",
            font=("Roboto", 12),
            text_color="#757575"
        )
        self.note_label.pack(pady=(20, 8))

        # Reset admin helper
        reset_btn = ctk.CTkButton(
            self.form_frame,
            text="Reset Admin",
            command=self.reset_admin_account,
            fg_color="#9E9E9E",
            hover_color="#757575",
            height=32,
            width=140
        )
        reset_btn.pack(pady=(0, 0))
        
    def show_password_change(self, user_id, current_password, first_login=False):
        """Show password change dialog."""
        change_window = ctk.CTkToplevel(self.root)
        change_window.title("Change Password")
        change_window.geometry("400x300")
        
        title = "Change Password" if not first_login else "First Login - Change Password"
        header = ctk.CTkLabel(
            change_window,
            text=title,
            font=("Roboto", 18, "bold"),
            text_color=self.text_color
        )
        header.pack(pady=(20, 30))
        
        if first_login:
            msg = ctk.CTkLabel(
                change_window,
                text="You must change your password before continuing.",
                font=("Roboto", 12),
                text_color="#757575"
            )
            msg.pack(pady=(0, 20))
        
        # New password entry
        new_pass = ctk.CTkEntry(
            change_window,
            width=280,
            placeholder_text="Enter new password",
            show="•"
        )
        new_pass.pack(pady=10)
        
        # Confirm password entry
        confirm_pass = ctk.CTkEntry(
            change_window,
            width=280,
            placeholder_text="Confirm new password",
            show="•"
        )
        confirm_pass.pack(pady=10)
        
        def do_change():
            new = new_pass.get()
            confirm = confirm_pass.get()
            
            if not new or not confirm:
                messagebox.showerror("Error", "Please fill in all fields")
                return
                
            if new != confirm:
                messagebox.showerror("Error", "Passwords do not match")
                return
                
            if len(new) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return
                
            if self.db.change_password(user_id, current_password, new):
                messagebox.showinfo("Success", "Password changed successfully")
                change_window.destroy()
                # If this was a first login, proceed with normal login flow
                if first_login:
                    self.on_login_success(user_id, self.pending_role)
            else:
                messagebox.showerror("Error", "Failed to change password")
        
        # Change button
        change_btn = ctk.CTkButton(
            change_window,
            text="Change Password",
            command=do_change,
            width=200
        )
        change_btn.pack(pady=20)
        
        # Don't allow closing window on first login
        if first_login:
            change_window.protocol("WM_DELETE_WINDOW", lambda: None)
            change_window.transient(self.root)
            change_window.grab_set()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Login Error", "Please enter both username and password")
            return
            
        result = self.db.authenticate_user(username, password)
        
        if result:
            user_id, role, first_login = result
            if first_login:
                # Store role for after password change
                self.pending_role = role
                # Show forced password change dialog
                self.show_password_change(user_id, password, first_login=True)
            else:
                self.on_login_success(user_id, role)
        else:
            messagebox.showerror("Login Error", "Invalid username or password")

    def reset_admin_account(self):
        ok = False
        try:
            ok = self.db.reset_admin()
        except Exception:
            ok = False
        if ok:
            messagebox.showinfo("Admin Reset", "Admin reset complete. Use username 'admin' and password 'admin123'.")
        else:
            messagebox.showerror("Admin Reset", "Failed to reset admin account.")