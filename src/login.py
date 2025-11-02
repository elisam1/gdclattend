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
        self.note_label.pack(pady=(20, 0))
        
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Login Error", "Please enter both username and password")
            return
            
        user = self.db.authenticate_user(username, password)
        
        if user:
            user_id, role = user
            self.on_login_success(user_id, role)
        else:
            messagebox.showerror("Login Error", "Invalid username or password")