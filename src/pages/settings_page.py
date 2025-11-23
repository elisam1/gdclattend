import customtkinter as ctk
from tkinter import messagebox, ttk, filedialog
from typing import Optional, Any
from datetime import datetime
import os
import importlib.util
from ..company_manager import CompanyManager
from .dashboard_page import DashboardPage

class SettingsPage:
    def __init__(self, parent, db, colors, fonts, face_mgr):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts
        self.face_mgr = face_mgr
        # Preview image reference to satisfy type checker and prevent GC
        self._settings_preview_imgtk: Optional[Any] = None

    def show(self):
        self.clear_parent()
        # Use a scrollable frame so content remains accessible on smaller windows
        self.current_frame = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.create_page_header("Settings", "Application settings and preferences")

        content = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Read current settings from DB
        auto_on_logout = int(self.db.get_setting('auto_save_on_logout', '1'))
        # Use a more conservative default autosave interval to reduce churn
        auto_interval = int(self.db.get_setting('auto_save_interval', '300'))
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

        # Autosave retention (number of files to keep)
        retention = int(self.db.get_setting('autosave_retention', '50'))
        retention_label = ctk.CTkLabel(controls, text="Auto-save retention (files):")
        retention_label.grid(row=4, column=0, sticky="w", pady=(12, 2))
        self.retention_var = ctk.StringVar(value=str(retention))
        retention_entry = ctk.CTkEntry(controls, textvariable=self.retention_var, width=120)
        retention_entry.grid(row=5, column=0, sticky="w", pady=4)

        # Theme selection
        theme_frame = ctk.CTkFrame(controls, fg_color="transparent")
        theme_frame.grid(row=6, column=0, sticky="w", pady=(20, 0))

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
        scanner_frame.grid(row=8, column=0, sticky="w", pady=(20, 0))

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
        printer_frame.grid(row=9, column=0, sticky="w", pady=(20, 0))

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
        mode_frame.grid(row=10, column=0, sticky="w", pady=(20, 0))

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
        face_frame.grid(row=11, column=0, sticky="w", pady=(20, 0))

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

        # Show face backend status (dlib or OpenCV)
        try:
            backend = "dlib" if getattr(self.face_mgr, 'use_dlib', False) else "OpenCV"
            ctk.CTkLabel(face_frame, text=f"Backend: {backend}").pack(side="left", padx=(10, 0))
        except Exception:
            pass

        # Advanced face config
        adv_frame = ctk.CTkFrame(controls, fg_color="transparent")
        adv_frame.grid(row=11, column=1, sticky="w", pady=(20, 0), padx=(20, 0))

        # Dlib distance threshold (lower is stricter). Default 0.6
        dlib_thr = self.db.get_setting('face_dlib_distance_threshold', '0.6')
        ctk.CTkLabel(adv_frame, text="Dlib distance threshold:").grid(row=0, column=0, sticky="w")
        self.dlib_thr_var = ctk.StringVar(value=str(dlib_thr))
        ctk.CTkEntry(adv_frame, textvariable=self.dlib_thr_var, width=100).grid(row=1, column=0, sticky="w", pady=(2, 8))

        # ORB match count threshold (higher is stricter). Default 10
        orb_thr = self.db.get_setting('face_orb_match_threshold', '10')
        ctk.CTkLabel(adv_frame, text="ORB match threshold:").grid(row=0, column=1, sticky="w", padx=(12, 0))
        self.orb_thr_var = ctk.StringVar(value=str(orb_thr))
        ctk.CTkEntry(adv_frame, textvariable=self.orb_thr_var, width=100).grid(row=1, column=1, sticky="w", pady=(2, 8), padx=(12, 0))

        # Preview FPS (target) and verify rate (Hz)
        preview_fps = self.db.get_setting('face_preview_fps', '15')
        verify_hz = self.db.get_setting('face_verify_rate_hz', '3')
        ctk.CTkLabel(adv_frame, text="Preview FPS:").grid(row=2, column=0, sticky="w")
        self.preview_fps_var = ctk.StringVar(value=str(preview_fps))
        ctk.CTkEntry(adv_frame, textvariable=self.preview_fps_var, width=100).grid(row=3, column=0, sticky="w", pady=(2, 8))

        ctk.CTkLabel(adv_frame, text="Verify rate (Hz):").grid(row=2, column=1, sticky="w", padx=(12, 0))
        self.verify_rate_var = ctk.StringVar(value=str(verify_hz))
        ctk.CTkEntry(adv_frame, textvariable=self.verify_rate_var, width=100).grid(row=3, column=1, sticky="w", pady=(2, 8), padx=(12, 0))

        # Confirmation before marking
        confirm_mark = self.db.get_setting('face_confirm_before_mark', 'false')
        self.confirm_mark_var = ctk.StringVar(value=confirm_mark)
        ctk.CTkSwitch(adv_frame, text="Confirm before marking", variable=self.confirm_mark_var, onvalue='true', offvalue='false').grid(row=4, column=0, columnspan=2, sticky="w", pady=(6, 0))

        # Camera Test Tool button
        ctk.CTkButton(adv_frame, text="Open Camera Test", width=160, command=self._open_camera_test).grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))

        # Enrollment quality controls
        quality_frame = ctk.CTkFrame(controls, fg_color="transparent")
        quality_frame.grid(row=12, column=0, sticky="w", pady=(20, 0))
        ctk.CTkLabel(quality_frame, text="Enrollment Quality:").grid(row=0, column=0, sticky="w")
        # Sharpness threshold
        self.enroll_sharp_var = ctk.StringVar(value=self.db.get_setting('enroll_min_sharpness', '100'))
        ctk.CTkLabel(quality_frame, text="Min sharpness:").grid(row=1, column=0, sticky="w")
        ctk.CTkEntry(quality_frame, textvariable=self.enroll_sharp_var, width=100).grid(row=2, column=0, sticky="w", pady=(2, 8))
        # Brightness range
        self.enroll_bmin_var = ctk.StringVar(value=self.db.get_setting('enroll_brightness_min', '40'))
        self.enroll_bmax_var = ctk.StringVar(value=self.db.get_setting('enroll_brightness_max', '220'))
        ctk.CTkLabel(quality_frame, text="Brightness min/max:").grid(row=1, column=1, sticky="w", padx=(12, 0))
        ctk.CTkEntry(quality_frame, textvariable=self.enroll_bmin_var, width=80).grid(row=2, column=1, sticky="w", pady=(2, 8), padx=(12, 0))
        ctk.CTkEntry(quality_frame, textvariable=self.enroll_bmax_var, width=80).grid(row=2, column=2, sticky="w", pady=(2, 8), padx=(6, 0))
        # Single face requirement
        self.enroll_single_var = ctk.StringVar(value=self.db.get_setting('enroll_require_single_face', 'true'))
        ctk.CTkSwitch(quality_frame, text="Require single face", variable=self.enroll_single_var, onvalue='true', offvalue='false').grid(row=3, column=0, columnspan=3, sticky="w", pady=(6, 0))

        # Email notifications settings
        email_frame = ctk.CTkFrame(controls, fg_color="transparent")
        email_frame.grid(row=12, column=0, sticky="w", pady=(20, 0))

        email_label = ctk.CTkLabel(email_frame, text="Email Notifications:", anchor="w")
        email_label.pack(side="left", padx=(0, 10))

        email_enabled = self.db.get_setting('email_enabled', 'true')
        self.email_var = ctk.StringVar(value=email_enabled)
        email_switch = ctk.CTkSwitch(email_frame, text="Enable", variable=self.email_var, onvalue='true', offvalue='false')
        email_switch.pack(side="left")

        # Save controls (placed on their own row to avoid overlap)
        actions_frame = ctk.CTkFrame(controls, fg_color="transparent")
        actions_frame.grid(row=13, column=0, sticky="w", pady=(20, 0))

        save_btn = ctk.CTkButton(
            actions_frame,
            text="Save Settings",
            command=self._save_settings,
            width=160
        )
        save_btn.pack(side="left")

        save_back_btn = ctk.CTkButton(
            actions_frame,
            text="Save & Back",
            command=self._save_and_back,
            width=160,
            fg_color=self.colors['primary']
        )
        save_back_btn.pack(side="left", padx=(10, 0))

        # Backup & Restore section
        backup_frame = ctk.CTkFrame(controls, fg_color="transparent")
        backup_frame.grid(row=14, column=0, sticky="w", pady=(20, 0))

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

        # Company Management section
        company_frame = ctk.CTkFrame(controls, fg_color="transparent")
        company_frame.grid(row=15, column=0, sticky="w", pady=(20, 0))

        ctk.CTkLabel(company_frame, text="Company Management:").pack(side="left", padx=(0, 10))

        # Initialize company manager and load companies
        try:
            self.company_mgr = CompanyManager()
            active_name, _, _ = self.company_mgr.get_active()
            companies = self.company_mgr.list_companies() or []
            if active_name and active_name not in companies:
                companies.insert(0, active_name)
            if not companies:
                companies = ["default"]
        except Exception:
            active_name = "default"
            companies = ["default"]

        self.company_select_var = ctk.StringVar(value=active_name or companies[0])
        self.company_menu = ctk.CTkOptionMenu(company_frame, values=companies, variable=self.company_select_var, width=200)
        self.company_menu.pack(side="left")

        switch_btn = ctk.CTkButton(company_frame, text="Set Active", width=120, command=self._switch_company)
        switch_btn.pack(side="left", padx=(10, 0))

        # Create new company controls
        new_company_frame = ctk.CTkFrame(controls, fg_color="transparent")
        new_company_frame.grid(row=16, column=0, sticky="w", pady=(8, 0))
        ctk.CTkLabel(new_company_frame, text="New company name:").pack(side="left", padx=(0, 10))
        self.new_company_var = ctk.StringVar(value="")
        ctk.CTkEntry(new_company_frame, textvariable=self.new_company_var, width=220).pack(side="left")
        ctk.CTkButton(new_company_frame, text="Create Company", width=160, command=self._create_company).pack(side="left", padx=(10, 0))

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
            self.db.set_setting('autosave_retention', int(self.retention_var.get()))

            # Scanner and printer
            self.db.set_setting('fingerprint_port', self.scanner_var.get())
            self.db.set_setting('preferred_printer', self.printer_var.get())

            # Face settings
            self.db.set_setting('face_enabled', self.face_var.get())
            self.db.set_setting('camera_index', self.cam_var.get())
            # Advanced face config
            try:
                # Clamp and store numeric values safely
                dlib_thr = float(str(self.dlib_thr_var.get()))
                orb_thr = int(str(self.orb_thr_var.get()))
                fps = max(5, min(60, int(str(self.preview_fps_var.get()))))
                hz = max(1, min(15, int(str(self.verify_rate_var.get()))))
            except Exception:
                dlib_thr, orb_thr, fps, hz = 0.6, 10, 15, 3
            self.db.set_setting('face_dlib_distance_threshold', str(dlib_thr))
            self.db.set_setting('face_orb_match_threshold', str(orb_thr))
            self.db.set_setting('face_preview_fps', str(fps))
            self.db.set_setting('face_verify_rate_hz', str(hz))
            self.db.set_setting('face_confirm_before_mark', self.confirm_mark_var.get())

            # Enrollment quality config
            try:
                sharp = float(str(self.enroll_sharp_var.get()))
                bmin = float(str(self.enroll_bmin_var.get()))
                bmax = float(str(self.enroll_bmax_var.get()))
            except Exception:
                sharp, bmin, bmax = 100.0, 40.0, 220.0
            self.db.set_setting('enroll_min_sharpness', str(sharp))
            self.db.set_setting('enroll_brightness_min', str(bmin))
            self.db.set_setting('enroll_brightness_max', str(bmax))
            self.db.set_setting('enroll_require_single_face', self.enroll_single_var.get())

            # Apply to live manager immediately
            try:
                if hasattr(self.face_mgr, 'set_thresholds'):
                    self.face_mgr.set_thresholds(dlib_distance=dlib_thr, orb_match=orb_thr)
            except Exception:
                pass

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

    def _save_and_back(self):
        """Save settings and navigate back to the dashboard."""
        try:
            self._save_settings()
            # Navigate back to dashboard content
            try:
                # Clear current content and show dashboard
                for widget in self.parent.winfo_children():
                    widget.destroy()
            except Exception:
                pass
            DashboardPage(self.parent, self.db, self.colors, self.fonts).show()
        except Exception:
            # Message already shown by _save_settings on error
            pass

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

    def _open_camera_test(self):
        """Open a simple camera test window with live preview, FPS, and face count."""
        try:
            cam_idx = int(self.cam_var.get()) if hasattr(self, 'cam_var') else int(self.db.get_setting('camera_index', '0'))
        except Exception:
            cam_idx = 0

        win = ctk.CTkToplevel(self.parent)
        win.title("Camera Test")
        preview = ctk.CTkLabel(win, text="", width=640, height=480)
        preview.pack(padx=10, pady=10)
        stats = ctk.CTkLabel(win, text="", font=("Segoe UI", 12))
        stats.pack(pady=(0, 10))

        import time
        last_ts = [time.monotonic()]
        fps = [0.0]
        cap = None

        def open_cap():
            nonlocal cap
            try:
                cap = self.face_mgr._open_capture(cam_idx, None) if hasattr(self.face_mgr, '_open_capture') else None
                if cap is None:
                    import cv2
                    cap = cv2.VideoCapture(cam_idx)
            except Exception:
                cap = None

        def close_cap():
            try:
                if cap and hasattr(cap, 'release'):
                    cap.release()
            except Exception:
                pass

        def loop():
            try:
                import cv2
                from PIL import Image, ImageTk
                if cap is None:
                    open_cap()
                if not cap or not cap.isOpened():
                    stats.configure(text="Camera not available")
                    win.after(500, loop)
                    return
                ret, frame = cap.read()
                if not ret or frame is None:
                    win.after(50, loop)
                    return

                # Compute FPS
                now = time.monotonic()
                dt = now - last_ts[0]
                last_ts[0] = now
                if dt > 0:
                    fps[0] = 0.9 * fps[0] + 0.1 * (1.0 / dt)

                # Face count
                face_count = 0
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    if getattr(self.face_mgr, 'use_dlib', False):
                        faces = self.face_mgr.face_detector(gray)
                        face_count = len(faces)
                    else:
                        faces = self.face_mgr.face_cascade.detectMultiScale(gray, 1.3, 5)
                        face_count = len(faces)
                except Exception:
                    pass

                # Draw overlay
                disp = frame.copy()
                try:
                    cv2.putText(disp, f"Faces: {face_count}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,215,0), 2)
                except Exception:
                    pass
                cv2image = cv2.cvtColor(disp, cv2.COLOR_BGR2RGB)
                img = Image.fromarray(cv2image).resize((640, 480))
                imgtk = ImageTk.PhotoImage(image=img)
                # Keep a reference to prevent garbage collection without assigning unknown attribute on CTkLabel
                self._settings_preview_imgtk = imgtk
                preview.configure(image=imgtk)
                stats.configure(text=f"FPS ~ {fps[0]:.1f} | Res {frame.shape[1]}x{frame.shape[0]}")
            except Exception as e:
                stats.configure(text=f"Error: {e}")
            finally:
                try:
                    if win.winfo_exists():
                        win.after(66, loop)
                    else:
                        close_cap()
                except Exception:
                    close_cap()

        def on_close():
            close_cap()
            try:
                win.destroy()
            except Exception:
                pass

        win.protocol("WM_DELETE_WINDOW", on_close)
        loop()

    def _refresh_company_options(self):
        """Refresh the company dropdown with the latest list and active selection."""
        try:
            companies = self.company_mgr.list_companies() or []
            active_name, _, _ = self.company_mgr.get_active()
            if active_name and active_name not in companies:
                companies.insert(0, active_name)
            if not companies:
                companies = ["default"]
            self.company_menu.configure(values=companies)
            self.company_select_var.set(active_name or companies[0])
        except Exception:
            pass

    def _create_company(self):
        """Create a new company directory structure and set it active optionally."""
        name = (self.new_company_var.get() or "").strip()
        if not name:
            messagebox.showerror("Company", "Please enter a company name.")
            return
        try:
            ok = self.company_mgr.create_company(name)
            if ok:
                self._refresh_company_options()
                messagebox.showinfo("Company", f"Company '{name}' created successfully.")
            else:
                messagebox.showerror("Company", f"Could not create company '{name}'.")
        except Exception as e:
            messagebox.showerror("Company", f"Error creating company: {e}")

    def _switch_company(self):
        """Switch the active company and prompt for app restart to apply context."""
        try:
            target = self.company_select_var.get()
            if not target:
                messagebox.showerror("Company", "Please select a company to set active.")
                return
            self.company_mgr.set_active(target)
            self._refresh_company_options()
            messagebox.showinfo("Company", f"Active company set to '{target}'.\nPlease restart the app to load its database and face data.")
        except Exception as e:
            messagebox.showerror("Company", f"Failed to set active company: {e}")

    def start_autosave_timer(self, interval_seconds=60):
        """Start a periodic autosave timer. Stops previous if running."""
        try:
            self.stop_autosave_timer()
        except Exception:
            pass
        # Enforce a reasonable minimum to avoid overwhelming disk and UI
        self._autosave_interval = max(30, int(interval_seconds))

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

            # Retention: prune old autosave files beyond configured limit
            try:
                max_files = int(self.db.get_setting('autosave_retention', '50'))
                entries = [fn for fn in os.listdir(backups_dir) if fn.startswith('state_') and fn.endswith('.json')]
                entries.sort(reverse=True)  # newest first by name timestamp
                if len(entries) > max_files:
                    for old in entries[max_files:]:
                        try:
                            os.remove(os.path.join(backups_dir, old))
                        except Exception:
                            pass
            except Exception:
                pass
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
