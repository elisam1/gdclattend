import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import csv

class AttendanceRecordsPage:
    def __init__(self, parent, db, colors, fonts):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts

    def show(self):
        self.clear_parent()
        self.current_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
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
            font=self.fonts['text'],
            text_color=self.colors['text']
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
            font=self.fonts['text'],
            text_color=self.colors['text']
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
            try:
                import tkcalendar
                top = ctk.CTkToplevel(self.parent)
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
            except ImportError:
                # Fallback: simple date entry with validation
                from tkinter.simpledialog import askstring
                date = askstring("Enter Date", "Enter date in YYYY-MM-DD format:")
                if date:
                    try:
                        datetime.strptime(date, "%Y-%m-%d")
                        entry_widget.delete(0, 'end')
                        entry_widget.insert(0, date)
                    except ValueError:
                        messagebox.showerror("Invalid Date", "Please enter date in YYYY-MM-DD format")

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
            font=self.fonts['text'],
            text_color=self.colors['text']
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
            font=self.fonts['text'],
            text_color=self.colors['text']
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
            fg_color=self.colors['primary'],
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
            text_color=self.colors['text'],
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
                file_path = filedialog.asksaveasfilename(
                    defaultextension=".csv",
                    initialfile=filename,
                    filetypes=[("CSV files", "*.csv"), ("All files", "*.*")]
                )

                if not file_path:  # User cancelled
                    return

                # Write CSV file
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
            text_color=self.colors['primary'],
            border_width=1,
            border_color=self.colors['primary'],
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
                font=self.fonts['subheader'],
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

    def create_page_header(self, title, subtitle=None):
        """Create a consistent page header with title and optional subtitle"""
        header_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, 20))

        title_label = ctk.CTkLabel(
            header_frame,
            text=title,
            font=self.fonts['header'],
            text_color=self.colors['primary']
        )
        title_label.pack(anchor="w", pady=(0, 5))

        if subtitle:
            subtitle_label = ctk.CTkLabel(
                header_frame,
                text=subtitle,
                font=self.fonts['text'],
                text_color=self.colors['text']
            )
            subtitle_label.pack(anchor="w")

        # Separator
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.pack(fill="x", pady=(10, 0))

        return header_frame

    def clear_parent(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
