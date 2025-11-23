# Patched MarkAttendancePage with Live Camera Preview (Design 2 UI)
# ---------------------------------------------------------------
# This version adds a real-time camera preview window for face
# verification and improves the scan workflow for Auto / Face modes.

import customtkinter as ctk
from tkinter import messagebox, Label
import threading
import cv2
from PIL import Image, ImageTk
from typing import Optional, Any

class MarkAttendancePage:
    def __init__(self, parent, db, colors, fonts, face_mgr, firebase=None):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts
        self.face_mgr = face_mgr
        self.firebase = firebase
        self.cam_thread = None
        self.stop_cam = False
        self.preview_window = None
        self._live_thread = None
        # Preview image reference to satisfy type checker and prevent GC
        self._preview_imgtk: Optional[Any] = None

    # ------------------------------------------------------------
    # PAGE UI
    # ------------------------------------------------------------
    def show(self):
        self.clear_parent()
        self.current_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        # Determine authentication mode from settings (with migration)
        self.auth_mode = self._get_auth_mode()

        subtitle = {
            'fingerprint': 'Scan fingerprint to mark attendance',
            'face': 'Face recognition with embedded live camera',
            'manual': 'Enter employee ID manually',
        }.get(self.auth_mode, 'Record employee attendance')

        self.create_page_header("Mark Attendance", subtitle)

        content_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        content_frame.pack(fill="both", expand=True, pady=20)

        body = ctk.CTkScrollableFrame(content_frame, fg_color="transparent")
        body.pack(expand=True, fill="both", padx=40, pady=40)

        # Render UI for selected authentication mode
        if self.auth_mode == 'face':
            self._render_face_mode(body)
        elif self.auth_mode == 'manual':
            self._render_manual_mode(body)
        else:
            self._render_fingerprint_mode(body)

    # ------------------------------------------------------------
    # LIVE FACE PREVIEW (embedded in UI)
    # ------------------------------------------------------------
    def _start_live_preview(self, cam_index: int):
        # Initialize camera
        try:
            self.cap = cv2.VideoCapture(cam_index)
            if not self.cap.isOpened():
                raise RuntimeError("Camera not available")
        except Exception as e:
            messagebox.showerror("Camera", f"Failed to open camera: {e}")
            return

        self.preview_running = True
        self._pending_mark = False
        self._last_verify_ts = 0.0
        # Performance config from settings
        try:
            fps = int(self.db.get_setting('face_preview_fps', '15'))
            rate_hz = int(self.db.get_setting('face_verify_rate_hz', '3'))
        except Exception:
            fps, rate_hz = 15, 3
        fps = max(5, min(60, fps))
        rate_hz = max(1, min(15, rate_hz))
        self._preview_interval_ms = int(1000 / fps)
        self._verify_min_interval_s = 1.0 / float(rate_hz)
        # Preview label is created in _render_face_mode; do not recreate here

        # Kick off update loop
        self._update_preview()

    def _stop_live_preview(self):
        try:
            self.preview_running = False
            self._pending_mark = False
            if hasattr(self, 'cap') and self.cap:
                self.cap.release()
            # Clear label image
            if hasattr(self, 'preview_label') and self.preview_label:
                self.preview_label.configure(image=None)
                self.preview_label.image = None  # type: ignore
            if hasattr(self, 'recog_info_label') and self.recog_info_label:
                self.recog_info_label.configure(text="")
        except Exception:
            pass

    def _update_preview(self):
        if not getattr(self, 'preview_running', False):
            return
        cap = getattr(self, 'cap', None)
        if not cap or not hasattr(cap, 'read') or not cap.isOpened():
            self.parent.after(50, self._update_preview)
            return
        ret, frame = cap.read()
        if not ret or frame is None:
            # try again shortly
            self.parent.after(50, self._update_preview)
            return

        # draw detection boxes
        display = frame.copy()
        face_count = 0
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if getattr(self.face_mgr, 'use_dlib', False):
                faces = self.face_mgr.face_detector(gray)
                face_count = len(faces)
                for f in faces:
                    x, y, w, h = f.left(), f.top(), f.width(), f.height()
                    cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
            else:
                faces = self.face_mgr.face_cascade.detectMultiScale(gray, 1.3, 5)
                face_count = len(faces)
                for (x, y, w, h) in faces:
                    cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
        except Exception:
            pass

        # Overlay face count
        try:
            cv2.putText(display, f"Faces: {face_count}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 215, 0), 2)
        except Exception:
            pass

        # Attempt recognition on the current frame (throttled)
        try:
            import time
            now = time.monotonic()
            # Throttle verify calls using configured rate
            do_verify = (now - getattr(self, '_last_verify_ts', 0.0)) >= getattr(self, '_verify_min_interval_s', 0.33)
            emp_id, score = (None, None)
            if do_verify:
                emp_id, score = self.face_mgr.verify_frame(frame)
                self._last_verify_ts = now
            if emp_id is not None:
                # Prepare overlay text
                emp_name = None
                try:
                    for emp in self.db.get_all_employees():
                        if int(emp[0]) == int(emp_id):
                            emp_name = emp[1]
                            break
                except Exception:
                    pass

                # Ensure 'score' is numeric for Pylance and runtime safety
                if getattr(self.face_mgr, 'use_dlib', False):
                    try:
                        s = float(score) if score is not None else 0.0
                    except Exception:
                        s = 0.0
                    conf_text = f"{int(max(0.0, min(1.0, s)) * 100)}%"
                else:
                    try:
                        s_int = int(score) if isinstance(score, (int, float)) else 0
                    except Exception:
                        s_int = 0
                    conf_text = f"matches: {s_int}"

                rec_text = f"Recognized: {emp_name or emp_id} (conf {conf_text})"
                try:
                    cv2.putText(display, rec_text, (10, 52), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (50, 205, 50), 2)
                except Exception:
                    pass

                # Update UI status label if present
                try:
                    if hasattr(self, 'recog_info_label') and self.recog_info_label:
                        self.recog_info_label.configure(text=rec_text)
                except Exception:
                    pass

                # Briefly show overlays, then mark once
                if not getattr(self, '_pending_mark', False):
                    self._pending_mark = True
                    self.parent.after(800, lambda eid=emp_id: self._on_recognition_confirm(eid))
        except Exception:
            pass

        # convert to ImageTk and display
        cv2image = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        # keep reasonable size
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        # Keep a reference on the page object to prevent GC without assigning unknown attributes
        self._preview_imgtk = imgtk
        self.preview_label.configure(image=imgtk)

        # schedule next frame using configured FPS
        self.parent.after(getattr(self, '_preview_interval_ms', 66), self._update_preview)

    def _on_recognition_confirm(self, employee_id: int):
        # Optionally confirm before marking
        confirm = self.db.get_setting('face_confirm_before_mark', 'false') == 'true'
        emp_name = None
        try:
            for emp in self.db.get_all_employees():
                if int(emp[0]) == int(employee_id):
                    emp_name = emp[1]
                    break
        except Exception:
            pass

        proceed = True
        if confirm:
            try:
                proceed = messagebox.askyesno("Confirm", f"Mark attendance for {emp_name or employee_id}?")
            except Exception:
                proceed = True
        try:
            self._stop_live_preview()
        except Exception:
            pass
        if proceed:
            self._mark_by_employee_id(employee_id)
        else:
            # Reset and resume preview
            self._pending_mark = False
            try:
                cam_idx = int(self.db.get_setting('camera_index', '0'))
            except Exception:
                cam_idx = 0
            self._start_live_preview(cam_idx)

    # ------------------------------------------------------------
    # SCAN HANDLER
    # ------------------------------------------------------------
    def real_scan(self, mode: str | None = None):
        if mode is None:
            mode = getattr(self, 'auth_mode', 'fingerprint')
        employee_id = None
        fingerprint_id = None
        scanner_error = None

        # ------------------ Fingerprint Mode ------------------
        attendance_mode = self._get_auth_mode(raw=True)
        allow_fingerprint = attendance_mode == 'fingerprint'
        try:
            if mode == "Fingerprint" or (mode == 'fingerprint' and allow_fingerprint):
                from ..fingerprint_scanner import FingerprintScanner
                port = self.db.get_setting('fingerprint_port', '')
                if port and port != 'None':
                    scanner = FingerprintScanner(port=port)
                    if scanner.connect():
                        ok, position = scanner.verify_fingerprint()
                        scanner.disconnect()
                        if ok and position is not None:
                            fingerprint_id = str(position)
                            for emp in self.db.get_all_employees():
                                if emp[3] and str(emp[3]) == fingerprint_id:
                                    employee_id = emp[0]
                                    break
                    else:
                        scanner_error = "Scanner not reachable on selected port"
        except Exception as e:
            scanner_error = str(e)

        # ------------------ Facial Recognition ------------------
        face_enabled = self.db.get_setting('face_enabled', 'false') == 'true'
        allow_face = (attendance_mode == 'face') and face_enabled

        if employee_id is None and (mode == "Face" or mode == 'face') and allow_face:
            cam_idx = int(self.db.get_setting('camera_index', '0'))
            # Start embedded live preview; attendance marks when a face recognizes
            self._start_live_preview(cam_idx)
            return

        # ------------------ Manual Mode ------------------
        if employee_id is None and (mode == "Manual" or mode == 'manual'):
            manual = self.entry_fingerprint_scan.get().strip()
            if manual:
                for emp in self.db.get_all_employees():
                    if emp[3] and str(emp[3]) == manual:
                        employee_id = emp[0]
                        break

        # ------------------ No Match ------------------
        if employee_id is None:
            msg = scanner_error or (
                "Face not recognized" if (mode == "Face" or mode == 'face')
                else ("Fingerprint not recognized" if (mode == "Fingerprint" or mode == 'fingerprint')
                      else "No matching employee for manual input")
            )
            messagebox.showerror("Scan Failed", msg)
            return

        self.entry_fingerprint_scan.delete(0, 'end')
        self.show_loading("Marking attendance…")

        self.parent.after(100, lambda: self._mark_by_employee_id(employee_id))

    # ------------------------------------------------------------
    # RENDERERS FOR AUTH MODES
    # ------------------------------------------------------------
    def _render_face_mode(self, container):
        icon_frame = ctk.CTkFrame(container, width=150, height=150, corner_radius=75, fg_color=self.colors['primary'])
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="📷", font=("Segoe UI", 56), text_color="white").pack(expand=True)

        ctk.CTkLabel(container, text="Stand in front of the camera for recognition", font=self.fonts['subheader']).pack(pady=(0, 10))

        # Create preview holder before starting camera
        try:
            self.preview_label = ctk.CTkLabel(container, text="", width=640, height=480)
            self.preview_label.pack(pady=(10, 10))
        except Exception:
            self.preview_label = ctk.CTkLabel(container, text="")
            self.preview_label.pack(pady=(10, 10))

        # Start camera automatically
        try:
            cam_idx = int(self.db.get_setting('camera_index', '0'))
        except Exception:
            cam_idx = 0
        self._start_live_preview(cam_idx)

        # Optional controls
        controls = ctk.CTkFrame(container, fg_color="transparent")
        controls.pack(pady=(10, 0))
        ctk.CTkButton(controls, text="Stop Camera", command=self._stop_live_preview, width=140).pack(side="left", padx=(0, 10))

        # Recognition status label
        self.recog_info_label = ctk.CTkLabel(container, text="", font=self.fonts['text'], text_color=self.colors['text'])
        self.recog_info_label.pack(pady=(10, 0))

    def _render_fingerprint_mode(self, container):
        icon_frame = ctk.CTkFrame(container, width=150, height=150, corner_radius=75, fg_color=self.colors['primary'])
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="🖐️", font=("Segoe UI", 56), text_color="white").pack(expand=True)

        ctk.CTkLabel(container, text="Place finger on scanner, then tap Scan", font=self.fonts['subheader']).pack(pady=(0, 10))
        ctk.CTkButton(container, text="Scan Fingerprint", command=lambda: self.real_scan('fingerprint'), fg_color=self.colors['success'], text_color="white", hover_color="#0b8043", width=200, height=50, corner_radius=5, font=self.fonts['subheader']).pack()

    def _render_manual_mode(self, container):
        icon_frame = ctk.CTkFrame(container, width=150, height=150, corner_radius=75, fg_color=self.colors['primary'])
        icon_frame.pack(pady=(0, 20))
        icon_frame.pack_propagate(False)
        ctk.CTkLabel(icon_frame, text="⌨️", font=("Segoe UI", 56), text_color="white").pack(expand=True)

        ctk.CTkLabel(container, text="Enter employee ID then tap Mark", font=self.fonts['subheader']).pack(pady=(0, 10))
        self.entry_fingerprint_scan = ctk.CTkEntry(container, width=300, height=40, corner_radius=5)
        self.entry_fingerprint_scan.pack(pady=(0, 20))
        ctk.CTkButton(container, text="Mark Attendance", command=lambda: self.real_scan('manual'), fg_color=self.colors['success'], text_color="white", hover_color="#0b8043", width=200, height=50, corner_radius=5, font=self.fonts['subheader']).pack()

    # ------------------------------------------------------------
    # MODE HELPERS
    # ------------------------------------------------------------
    def _get_auth_mode(self, raw: bool = False) -> str:
        """Return current auth mode, migrating legacy values if needed.
        If raw=True, return the normalized stored value without fallback controls.
        """
        val = self.db.get_setting('attendance_mode', 'fingerprint')
        if val in ("both", "fingerprint_only"):
            val = "fingerprint"
        elif val == "facial_only":
            val = "face"
        elif val not in ("fingerprint", "face", "manual"):
            val = "fingerprint"
        return val

    # ------------------------------------------------------------
    # SAVE ATTENDANCE
    # ------------------------------------------------------------
    def _mark_by_employee_id(self, employee_id: int):
        try:
            employees = self.db.get_all_employees()
            match = next((emp for emp in employees if int(emp[0]) == int(employee_id)), None)
            if not match:
                self.hide_loading()
                messagebox.showerror("Error", "Employee not found")
                return

            emp_id, name, email = match[0], match[1], match[2]
            result = self.db.mark_arrival_or_departure(emp_id)
            date = result.get('date')
            time = result.get('time')
            action = result.get('action')

            if self.firebase:
                try:
                    self.firebase.upload_attendance({"name": name, "status": action, "timestamp": f"{date} {time}"})
                except:
                    pass

            self.hide_loading()
            
            messagebox.showinfo("Attendance Marked", f"{action.title()} recorded for {name} on {date} at {time}")

        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Failed to mark attendance: {e}")

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
        import tkinter.ttk as ttk
        separator = ttk.Separator(header_frame, orient="horizontal")  # type: ignore
        separator.pack(fill="x", pady=(10, 0))

        return header_frame

    def clear_parent(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
        # ensure any running preview is stopped
        self._stop_live_preview()

    def hide_loading(self):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            self._loading_overlay.destroy()
            self._loading_overlay = None

    # ------------------------------------------------------------
    def show_loading(self, message="Loading..."):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            return
        self._loading_overlay = ctk.CTkFrame(self.parent, fg_color="#000000")
        self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        spinner = ctk.CTkLabel(self._loading_overlay, text="⏳", font=("Segoe UI", 48), text_color="white")
        spinner.pack(expand=True, pady=(100, 0))
