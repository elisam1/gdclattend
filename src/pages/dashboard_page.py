import customtkinter as ctk
import tkinter.ttk as ttk
from datetime import datetime

class DashboardPage:
    def __init__(self, parent, db, colors, fonts):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts

    def show(self):
        self.clear_parent()
        # Make dashboard scrollable so sections remain reachable on small windows
        self.current_frame = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.create_page_header("Dashboard", "Welcome to GDC Attendance System")

        # Live date & time (top-right)
        clock_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        clock_frame.pack(fill="x")
        self.dashboard_clock_label = ctk.CTkLabel(
            clock_frame,
            text="",
            font=self.fonts['text'],
            text_color="#757575"
        )
        self.dashboard_clock_label.pack(anchor="e")
        try:
            self._update_dashboard_clock()
        except Exception:
            pass

        # Stats cards row
        stats_frame = ctk.CTkFrame(self.current_frame, fg_color="transparent")
        stats_frame.pack(fill="x", pady=20)

        # Employee count card
        count = len(self.db.get_all_employees())
        self.create_stat_card(stats_frame, "Total Employees", count, "👥", self.colors['primary'], 0)

        # Today's attendance card (filtered for today)
        try:
            today_count = int(self.db.get_today_attendance_count())
        except Exception:
            today_count = 0
        self.create_stat_card(stats_frame, "Today's Attendance", today_count, "📊", self.colors['success'], 1)

        # Absent employees card
        # This is a placeholder - you would need to implement the actual count
        absent_count = count - today_count if count > today_count else 0
        self.create_stat_card(stats_frame, "Absent Today", absent_count, "❗", self.colors['error'], 2)

        # Recent activity section
        activity_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        activity_frame.pack(fill="both", expand=True, pady=20)

        activity_header = ctk.CTkLabel(
            activity_frame,
            text="Recent Activity",
            font=self.fonts['subheader'],
            text_color=self.colors['text']
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
                font=self.fonts['text'],
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
                    text_color=self.colors['text']
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

    def _update_dashboard_clock(self):
        try:
            now = datetime.now().strftime('%Y-%m-%d  %H:%M:%S')
            if hasattr(self, 'dashboard_clock_label'):
                self.dashboard_clock_label.configure(text=now)
            # schedule next update
            if hasattr(self, 'parent'):
                self.parent.after(1000, self._update_dashboard_clock)
        except Exception:
            pass

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
            text_color=self.colors['text']
        )
        value_label.place(x=20, y=45)

        # Title
        title_label = ctk.CTkLabel(
            card,
            text=title,
            font=self.fonts['text'],
            text_color="#757575"
        )
        title_label.place(x=20, y=80)

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
        separator = ttk.Separator(header_frame, orient="horizontal")  # type: ignore
        separator.pack(fill="x", pady=(10, 0))

        return header_frame

    def clear_parent(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
