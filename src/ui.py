import customtkinter as ctk
from tkinter import messagebox, ttk
from datetime import datetime

# Placeholder for real fingerprint SDK
# from fingerprint_sdk import FingerprintScanner

class AdminDashboard:
    def __init__(self, root, db, firebase=None):
        self.root = root
        self.db = db
        self.firebase = firebase
        self.root.title("GDC Attendance Admin Dashboard")
        self.root.geometry("1000x650")

        # Sidebar
        self.sidebar = ctk.CTkFrame(root, width=220, corner_radius=0, fg_color="#90caf9")
        self.sidebar.pack(side="left", fill="y")

        # Main content
        self.main_frame = ctk.CTkFrame(root, corner_radius=0)
        self.main_frame.pack(side="right", expand=True, fill="both")

        # Sidebar buttons
        self.btn_dashboard = ctk.CTkButton(self.sidebar, text="🏠 Dashboard", command=self.show_dashboard, fg_color="white", text_color="black")
        self.btn_dashboard.pack(pady=15, fill="x")

        self.btn_add_employee = ctk.CTkButton(self.sidebar, text="➕ Add Employee", command=self.show_add_employee, fg_color="white", text_color="black")
        self.btn_add_employee.pack(pady=15, fill="x")

        self.btn_view_employee = ctk.CTkButton(self.sidebar, text="👥 View Employees", command=self.show_view_employees, fg_color="white", text_color="black")
        self.btn_view_employee.pack(pady=15, fill="x")

        self.btn_mark_attendance = ctk.CTkButton(self.sidebar, text="🖐️ Mark Attendance", command=self.show_mark_attendance, fg_color="white", text_color="black")
        self.btn_mark_attendance.pack(pady=15, fill="x")

        self.btn_view_attendance = ctk.CTkButton(self.sidebar, text="📋 Attendance Records", command=self.show_attendance_records, fg_color="white", text_color="black")
        self.btn_view_attendance.pack(pady=15, fill="x")

        self.current_frame = None
        self.show_dashboard()

    # ----------------- Utility -----------------
    def clear_main_frame(self):
        if self.current_frame:
            self.current_frame.destroy()

    # ----------------- Dashboard -----------------
    def show_dashboard(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.pack(expand=True, fill="both")

        label = ctk.CTkLabel(self.current_frame, text="Welcome to GDC Attendance System", font=("Helvetica", 24, "bold"))
        label.pack(pady=50)

        count = len(self.db.get_all_employees())
        count_label = ctk.CTkLabel(self.current_frame, text=f"Total Registered Employees: {count}", font=("Helvetica", 16))
        count_label.pack(pady=10)

    # ----------------- Add Employee -----------------
    def show_add_employee(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.pack(expand=True, fill="both")

        title = ctk.CTkLabel(self.current_frame, text="Register New Employee", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)

        self.entry_name = ctk.CTkEntry(self.current_frame, placeholder_text="Full Name")
        self.entry_name.pack(pady=10, ipady=5, ipadx=100)

        self.entry_email = ctk.CTkEntry(self.current_frame, placeholder_text="Email Address")
        self.entry_email.pack(pady=10, ipady=5, ipadx=100)

        self.entry_fingerprint = ctk.CTkEntry(self.current_frame, placeholder_text="Fingerprint ID (from scanner)")
        self.entry_fingerprint.pack(pady=10, ipady=5, ipadx=100)

        btn_submit = ctk.CTkButton(self.current_frame, text="Save Employee", command=self.save_employee, fg_color="#2196F3", text_color="white")
        btn_submit.pack(pady=20)

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
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.pack(expand=True, fill="both")

        title = ctk.CTkLabel(self.current_frame, text="Registered Employees", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)

        employees = self.db.get_all_employees()
        if not employees:
            empty_label = ctk.CTkLabel(self.current_frame, text="No employees registered yet.", font=("Helvetica", 14))
            empty_label.pack(pady=10)
            return

        for emp in employees:
            emp_label = ctk.CTkLabel(self.current_frame, text=f"{emp[1]} - {emp[2]} (Fingerprint: {emp[3]})", font=("Helvetica", 14))
            emp_label.pack(pady=5)

    # ----------------- Mark Attendance -----------------
    def show_mark_attendance(self):
        self.clear_main_frame()
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.pack(expand=True, fill="both")

        title = ctk.CTkLabel(self.current_frame, text="Mark Attendance", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)

        self.entry_fingerprint_scan = ctk.CTkEntry(self.current_frame, placeholder_text="Enter Fingerprint ID or use scanner")
        self.entry_fingerprint_scan.pack(pady=10, ipady=5, ipadx=100)

        scan_button = ctk.CTkButton(self.current_frame, text="Scan Finger", command=self.real_scan, fg_color="#4CAF50", text_color="white")
        scan_button.pack(pady=20)

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
        self.current_frame = ctk.CTkFrame(self.main_frame)
        self.current_frame.pack(expand=True, fill="both")

        title = ctk.CTkLabel(self.current_frame, text="Attendance Records", font=("Helvetica", 20, "bold"))
        title.pack(pady=20)

        records = self.db.get_attendance_records()
        if not records:
            empty_label = ctk.CTkLabel(self.current_frame, text="No attendance records yet.", font=("Helvetica", 14))
            empty_label.pack(pady=10)
            return

        columns = ("name", "timestamp")
        tree = ttk.Treeview(self.current_frame, columns=columns, show="headings")
        tree.heading("name", text="Employee Name")
        tree.heading("timestamp", text="Timestamp")
        tree.pack(expand=True, fill="both", padx=20, pady=10)

        for record in records:
            tree.insert("", "end", values=record)
