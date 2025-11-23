import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from datetime import datetime
import os
import importlib.util

class SettingsPage:
    def __init__(self, parent, db, colors, fonts, face_mgr):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts
        self.face_mgr = face_mgr

    def show(self):
        self.clear_parent()
        self.current_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.create_page_header("Settings", "Application settings and preferences")

        content = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Read current settings from DB
        auto_on_logout = int(self.db.get_setting('auto_save_on_logout', '1'))
        auto_interval = int(self.db.get_setting('auto_save_interval', '60'))
        confirm_logout = int(self.db.get_setting('confirm_logout', '1'))
        logout_message = self.db.get_setting('logout_message', 'Are you sure you want to logout?')

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
        from ..fingerprint_scanner import FingerprintScanner
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

        # Authentication Mode Settings
        mode_frame = ctk.CTkFrame(controls, fg_color="transparent")
        mode_frame.grid(row=8, column=0, sticky="w", pady=(20, 0))

        mode_label = ctk.CTkLabel(mode_frame, text="Authentication Mode:", anchor="w")
        mode_label.pack(side="left", padx=(0, 10))

        # Migrate old values to new single-choice modes
        saved_mode = self.db.get_setting('attendance_mode', 'fingerprint')
        if saved_mode in ("both", "fingerprint_only"):
            saved_mode = "fingerprint"
        elif saved_mode == "facial_only":
            saved_mode = "face"
        elif saved_mode not in ("fingerprint", "face", "manual"):
            saved_mode = "fingerprint"

        auth_modes = ["fingerprint", "face", "manual"]
        self.attendance_mode_var = ctk.StringVar(value=saved_mode)
        mode_menu = ctk.CTkOptionMenu(
            mode_frame,
            values=auth_modes,
            variable=self.attendance_mode_var,
            width=150
        )
        mode_menu.pack(side="left")

        # Facial recognition settings
        face_frame = ctk.CTkFrame(controls, fg_color="transparent")
        face_frame.grid(row=9, column=0, sticky="w", pady=(20, 0))

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

        # Email notifications settings
        email_frame = ctk.CTkFrame(controls, fg_color="transparent")
        email_frame.grid(row=10, column=0, sticky="w", pady=(20, 0))

        email_label = ctk.CTkLabel(email_frame, text="Email Notifications:", anchor="w")
        email_label.pack(side="left", padx=(0, 10))

        email_enabled = self.db.get_setting('email_enabled', 'true')
        self.email_var = ctk.StringVar(value=email_enabled)
        email_switch = ctk.CTkSwitch(email_frame, text="Enable", variable=self.email_var, onvalue='true', offvalue='false')
        email_switch.pack(side="left")

        # Save settings button
        save_btn = ctk.CTkButton(
            controls,
            text="Save Settings",
            command=self._save_settings,
            width=160
        )
        save_btn.grid(row=10, column=0, sticky="w", pady=(20, 0))

        # Backup & Restore section
        backup_frame = ctk.CTkFrame(controls, fg_color="transparent")
        backup_frame.grid(row=10, column=0, sticky="w", pady=(20, 0))

        backup_label = ctk.CTkLabel(backup_frame, text="Backup & Restore:", anchor="w")
        backup_label.pack(side="left", padx=(0, 10))

        backup_btn = ctk.CTkButton(
            backup_frame,
            text="Backup Database",
            command=self._backup_database,
            width=160
        )
        backup_btn.pack(side="left", padx=(0, 10))

        restore_btn = ctk.CTkButton(
            backup_frame,
            text="Restore Database",
            command=self._restore_database,
            width=160,
            fg_color=self.colors['error'],
            hover_color="#b00020"
        )
        restore_btn.pack(side="left")

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

            # Authentication mode
            if hasattr(self, 'attendance_mode_var'):
                self.db.set_setting('attendance_mode', self.attendance_mode_var.get())

            # Email notifications
            if hasattr(self, 'email_var'):
                self.db.set_setting('email_enabled', self.email_var.get())

            # Apply autosave interval immediately
            try:
                self.stop_autosave_timer()
            except Exception:
                pass
            self.start_autosave_timer(int(self.interval_var.get()))

            messagebox.showinfo("Settings", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")

    def _backup_database(self):
        """Backup the current database to the backups folder or chosen file."""
        try:
            ts = datetime.now().strftime('%Y%m%d_%H%M%S')
            default_dir = os.path.join(os.getcwd(), 'backups')
            os.makedirs(default_dir, exist_ok=True)
            default_path = os.path.join(default_dir, f"database_backup_{ts}.db")
            target = filedialog.asksaveasfilename(
                title="Save Database Backup",
                initialdir=default_dir,
                initialfile=f"database_backup_{ts}.db",
                defaultextension=".db",
                filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")]
            )
            if not target:
                return
            ok = self.db.backup_to(target)
            if ok:
                messagebox.showinfo("Backup Complete", f"Database backed up to:\n{target}")
            else:
                messagebox.showerror("Backup Failed", "Could not create database backup.")
        except Exception as e:
            messagebox.showerror("Backup Failed", str(e))

    def _restore_database(self):
        """Restore database from a backup file selected by the user."""
        try:
            source = filedialog.askopenfilename(
                title="Select Database Backup",
                initialdir=os.path.join(os.getcwd(), 'backups'),
                filetypes=[("SQLite DB", "*.db"), ("All Files", "*.*")]
            )
            if not source:
                return
            ok = self.db.restore_from(source)
            if ok:
                messagebox.showinfo("Restore Complete", "Database restore finished. Please restart the app.")
            else:
                messagebox.showerror("Restore Failed", "Could not restore database.")
        except Exception as e:
            messagebox.showerror("Restore Failed", str(e))

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
            from ..fingerprint_scanner import FingerprintScanner
            scanner = FingerprintScanner(port=port)
            if scanner.test_connection():
                messagebox.showinfo("Success", f"Scanner connected successfully on {port}")
            else:
                messagebox.showerror("Connection Failed", f"Could not connect to scanner on {port}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to test scanner: {str(e)}")

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
            self._autosave_id = self.parent.after(self._autosave_interval * 1000, tick)

        self._autosave_id = self.parent.after(self._autosave_interval * 1000, tick)

    def stop_autosave_timer(self):
        try:
            if hasattr(self, '_autosave_id') and self._autosave_id:
                self.parent.after_cancel(self._autosave_id)
                self._autosave_id = None
        except Exception:
            pass

    def collect_state(self):
        """Collect a lightweight snapshot of current UI state (forms) to persist."""
        state = {
            'timestamp': datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            'last_page': 'settings'
        }
        # Settings page has no form fields to collect
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
