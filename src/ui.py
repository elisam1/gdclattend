import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime
import os
from PIL import Image, ImageTk

# Placeholder for real fingerprint SDK
# from fingerprint_sdk import FingerprintScanner

class AdminDashboard:
    def __init__(self, root, db, firebase=None):
        self.root = root
        self.db = db
        self.firebase = firebase
        
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
        self.container.pack(fill="both", expand=True)
        
        # Header frame
        self.header = ctk.CTkFrame(self.container, height=60, corner_radius=0, fg_color=self.primary_color)
        self.header.pack(fill="x")
        
        # App title in header
        self.title_label = ctk.CTkLabel(
            self.header, 
            text="GDC ATTENDANCE SYSTEM", 
            font=("Segoe UI", 22, "bold"),
            text_color="white"
        )
        self.title_label.pack(side="left", padx=20, pady=10)
        
        # Content area (sidebar + main content)
        self.content = ctk.CTkFrame(self.container, fg_color="transparent")
        self.content.pack(fill="both", expand=True)
        
        # Sidebar with gradient effect
        self.sidebar = ctk.CTkFrame(self.content, width=250, corner_radius=0, fg_color="#f1f3f4")
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)  # Prevent sidebar from shrinking
        
        # Logo or branding area
        self.logo_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=100)
        self.logo_frame.pack(fill="x", pady=(20, 10))
        
        self.logo_label = ctk.CTkLabel(
            self.logo_frame, 
            text="Admin Dashboard", 
            font=("Segoe UI", 18, "bold"),
            text_color=self.primary_color
        )
        self.logo_label.pack(pady=10)
        
        # Navigation menu
        self.nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        self.nav_frame.pack(fill="x", pady=10)
        
        # Active button indicator
        self.active_btn = None
        
        # Sidebar buttons with hover effect
        self.btn_dashboard = self.create_nav_button("🏠 Dashboard", self.show_dashboard)
        self.btn_add_employee = self.create_nav_button("➕ Add Employee", self.show_add_employee)
        self.btn_view_employee = self.create_nav_button("👥 View Employees", self.show_view_employees)
        self.btn_mark_attendance = self.create_nav_button("🖐️ Mark Attendance", self.show_mark_attendance)
        self.btn_view_attendance = self.create_nav_button("📋 Attendance Records", self.show_attendance_records)
        
        # Main content area
        self.main_frame = ctk.CTkFrame(self.content, corner_radius=15, fg_color="white")
        self.main_frame.pack(side="right", expand=True, fill="both", padx=20, pady=20)
        
        # Footer
        self.footer = ctk.CTkFrame(self.container, height=30, corner_radius=0, fg_color=self.primary_color)
        self.footer.pack(fill="x")
        
        self.footer_label = ctk.CTkLabel(
            self.footer, 
            text="© 2023 GDC Attendance System", 
            font=("Segoe UI", 10),
            text_color="white"
        )
        self.footer_label.pack(side="right", padx=20)
        
        self.current_frame = None
        self.show_dashboard()
        
    def create_nav_button(self, text, command):
        """Create a styled navigation button with hover effect"""
        btn = ctk.CTkButton(
            self.nav_frame,
            text=text,
            command=lambda t=text, c=command: self.nav_button_click(t, c),
            fg_color="transparent",
            text_color=self.text_color,
            hover_color="#e8eaed",
            anchor="w",
            height=40,
            corner_radius=8,
            font=("Segoe UI", 14)
        )
        btn.pack(fill="x", padx=10, pady=5)
        return btn
        
    def nav_button_click(self, text, command):
        """Handle navigation button click and highlight active button"""
        # Reset all buttons
        for btn in [self.btn_dashboard, self.btn_add_employee, self.btn_view_employee, 
                   self.btn_mark_attendance, self.btn_view_attendance]:
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
            
        # Execute the command
        command()

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

        self.db.add_employee(name, email, fingerprint_id)
        messagebox.showinfo("Success", f"Employee {name} added successfully!")
        self.show_dashboard()

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

        # TODO: Replace below with actual scanner SDK code
        # scanner = FingerprintScanner()
        # fingerprint_id = scanner.scan()

        employees = self.db.get_all_employees()
        match = next((emp for emp in employees if emp[3] == fingerprint_id), None)

        if match:
            emp_id = match[0]
            name = match[1]
            self.db.mark_attendance(emp_id)

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            if self.firebase:
                try:
                    self.firebase.upload_attendance({"employee": name, "timestamp": timestamp})
                except Exception as e:
                    print("⚠️ Firebase upload failed:", e)

            messagebox.showinfo("Attendance Marked", f"Attendance recorded for {name} at {timestamp}")
        else:
            messagebox.showerror("Scan Failed", "Fingerprint not recognized!")

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
        columns = ("name", "timestamp")
        tree = ttk.Treeview(records_frame, columns=columns, show="headings", style="Treeview")
        tree.heading("name", text="Employee Name")
        tree.heading("timestamp", text="Timestamp")
        tree.column("name", width=250)
        tree.column("timestamp", width=250)
        
        # Add a scrollbar
        scrollbar = ttk.Scrollbar(records_frame, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        tree.pack(expand=True, fill="both", padx=20, pady=20)
        
        # Insert records
        for record in records:
            tree.insert("", "end", values=record)
