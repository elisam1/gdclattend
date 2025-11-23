import os
import shutil
import cv2
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk
import pickle


class FaceEnrollmentWindow(ctk.CTkToplevel):
    """A Toplevel window that shows a live camera preview with capture/retake/save controls.

    Usage:
        win = FaceEnrollmentWindow(parent, face_mgr, camera_index)
        win.wait_window()  # blocks until window closed
        result = win.result  # dict with keys: saved (bool), image_path (str or None), encoding (object or None)
    """

    def __init__(self, parent, face_mgr, camera_index=0, temp_dir=None, db=None):
        super().__init__(parent)
        self.title("Face Enrollment")
        self.face_mgr = face_mgr
        self.camera_index = camera_index
        self.temp_dir = temp_dir or os.path.join(os.getcwd(), "faces")
        os.makedirs(self.temp_dir, exist_ok=True)
        self.db = db

        # result to be inspected by caller
        self.result = {"saved": False, "image_path": None, "encoding": None}

        # UI state
        self.cap = None
        self.preview_running = False
        self.captured_frame = None

        # Build UI
        self.preview_label = ctk.CTkLabel(self, text="", width=640, height=480)
        self.preview_label.grid(row=0, column=0, columnspan=4, padx=10, pady=10)

        # Live status label to show duplicate/quality info
        self.status_label = ctk.CTkLabel(self, text="", font=("Segoe UI", 12))
        self.status_label.grid(row=1, column=0, columnspan=4, padx=10, pady=(0, 6))

        self.capture_btn = ctk.CTkButton(self, text="CAPTURE", command=self.capture)
        self.capture_btn.grid(row=2, column=0, padx=6, pady=8)

        self.retake_btn = ctk.CTkButton(self, text="RETAKE", command=self.retake, state="disabled")
        self.retake_btn.grid(row=2, column=1, padx=6, pady=8)

        self.save_btn = ctk.CTkButton(self, text="SAVE", command=self.save, state="disabled")
        self.save_btn.grid(row=2, column=2, padx=6, pady=8)

        self.cancel_btn = ctk.CTkButton(self, text="CANCEL", command=self.on_cancel)
        self.cancel_btn.grid(row=2, column=3, padx=6, pady=8)

        # Start camera preview
        self.protocol("WM_DELETE_WINDOW", self.on_cancel)
        self.start_preview()

    def start_preview(self):
        # Try platform default, fallback backends if needed left to caller
        self.cap = cv2.VideoCapture(self.camera_index)
        if not self.cap.isOpened():
            # Try common alternative backends
            try:
                self.cap = cv2.VideoCapture(self.camera_index, cv2.CAP_DSHOW)
            except Exception:
                pass
        if not self.cap.isOpened():
            messagebox.showerror("Camera", "Unable to open camera. Check index and permissions.")
            self.destroy()
            return

        # warm up
        for _ in range(6):
            if self.cap and hasattr(self.cap, 'read'):
                self.cap.read()

        self.preview_running = True
        self._update_preview()

    def _update_preview(self):
        if not self.preview_running:
            return
        # Defensive guard for camera readiness
        if not self.cap or not hasattr(self.cap, 'read') or not self.cap.isOpened():
            self.after(50, self._update_preview)
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            # try again next tick
            self.after(50, self._update_preview)
            return

        # perform detection overlay (use face_mgr detector)
        faces = []
        display = frame.copy()
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            if getattr(self.face_mgr, 'use_dlib', False):
                # dlib faces are objects with left/top/width/height
                faces = self.face_mgr.face_detector(gray)
                for f in faces:
                    x, y, w, h = f.left(), f.top(), f.width(), f.height()
                    cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
            else:
                faces = self.face_mgr.face_cascade.detectMultiScale(gray, 1.3, 5)
                for (x, y, w, h) in faces:
                    cv2.rectangle(display, (x, y), (x+w, y+h), (0, 255, 0), 2)
        except Exception:
            pass

        # Live duplicate check when exactly one face is present
        try:
            dup = False
            if len(faces) == 1:
                if getattr(self.face_mgr, 'use_dlib', False):
                    f = faces[0]
                    x, y, w, h = f.left(), f.top(), f.width(), f.height()
                else:
                    x, y, w, h = faces[0]
                # clip and crop
                h_frame, w_frame = frame.shape[:2]
                x, y, w, h = max(0, x), max(0, y), max(1, w), max(1, h)
                x2 = min(x + w, w_frame)
                y2 = min(y + h, h_frame)
                face_img = frame[y:y2, x:x2]
                dup, matched = self.face_mgr.is_face_duplicate(face_img)
                if dup:
                    try:
                        cv2.putText(display, 'Duplicate face detected', (max(0, x), max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                    except Exception:
                        pass
                    self.status_label.configure(text=f"Duplicate face found ({matched}). Save disabled.", text_color="#b00020")
                    self.save_btn.configure(state="disabled")
                else:
                    self.status_label.configure(text="Face OK — ready to capture", text_color="#188038")
            else:
                # No or multiple faces: reset status
                if len(faces) > 1:
                    self.status_label.configure(text="Multiple faces detected — please isolate one face", text_color="#b00020")
                else:
                    self.status_label.configure(text="")
        except Exception:
            pass

        # convert to ImageTk
        cv2image = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image)
        img = img.resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        # keep reference
        self.preview_label.image = imgtk  # type: ignore
        self.preview_label.configure(image=imgtk)

        # schedule next frame
        self.after(30, self._update_preview)

    def capture(self):
        if not self.cap or not hasattr(self.cap, 'read') or not self.cap.isOpened():
            messagebox.showerror("Capture", "Camera not ready. Try restarting preview.")
            return
        ret, frame = self.cap.read()
        if not ret or frame is None:
            messagebox.showerror("Capture", "Failed to capture frame. Try again.")
            return
        # freeze preview
        self.captured_frame = frame.copy()
        self.preview_running = False
        self.retake_btn.configure(state="normal")
        self.save_btn.configure(state="normal")
        self.capture_btn.configure(state="disabled")
        # show captured frame
        cv2image = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(cv2image).resize((640, 480))
        imgtk = ImageTk.PhotoImage(image=img)
        self.preview_label.configure(image=imgtk)

        # Post-capture duplicate check
        faces = []
        try:
            gray = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2GRAY)
            if getattr(self.face_mgr, 'use_dlib', False):
                faces = self.face_mgr.face_detector(gray)
                if len(faces) > 0:
                    f = faces[0]
                    x, y, w, h = f.left(), f.top(), f.width(), f.height()
                else:
                    x, y, w, h = 0, 0, self.captured_frame.shape[1], self.captured_frame.shape[0]
            else:
                faces = self.face_mgr.face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    x, y, w, h = faces[0]
                else:
                    x, y, w, h = 0, 0, self.captured_frame.shape[1], self.captured_frame.shape[0]
            h_frame, w_frame = self.captured_frame.shape[:2]
            x, y, w, h = max(0, x), max(0, y), max(1, w), max(1, h)
            x2, y2 = min(x + w, w_frame), min(y + h, h_frame)
            face_img = self.captured_frame[y:y2, x:x2]
            dup, matched = self.face_mgr.is_face_duplicate(face_img)
            if dup:
                self.status_label.configure(text=f"Duplicate face found ({matched}). Please retake.", text_color="#b00020")
                self.save_btn.configure(state="disabled")
            else:
                self.status_label.configure(text="Captured face OK — you may save", text_color="#188038")
        except Exception:
            pass

    def retake(self):
        # resume preview
        if not self.cap:
            return
        self.captured_frame = None
        self.preview_running = True
        self.capture_btn.configure(state="normal")
        self.retake_btn.configure(state="disabled")
        self.save_btn.configure(state="disabled")
        self._update_preview()

    def save(self):
        # Save captured frame to a temp file and produce encoding (if dlib available)
        if self.captured_frame is None:
            messagebox.showwarning("Save", "No captured frame to save. Press Capture first.")
            return
        # Quality checks: single face, sharpness, brightness
        import cv2
        frame = self.captured_frame
        try:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        except Exception:
            gray = None
        # Default thresholds
        try:
            min_sharp = float(self.db.get_setting('enroll_min_sharpness', '100')) if self.db else 100.0
            bmin = float(self.db.get_setting('enroll_brightness_min', '40')) if self.db else 40.0
            bmax = float(self.db.get_setting('enroll_brightness_max', '220')) if self.db else 220.0
            require_single = (self.db.get_setting('enroll_require_single_face', 'true') == 'true') if self.db else True
        except Exception:
            min_sharp, bmin, bmax, require_single = 100.0, 40.0, 220.0, True

        # brightness
        if gray is not None:
            # OpenCV's mean returns a 4-tuple; first element is the channel mean
            brightness = float(cv2.mean(gray)[0])
            if brightness < bmin or brightness > bmax:
                messagebox.showwarning("Quality", f"Lighting unsuitable (brightness {brightness:.0f}). Please retake.")
                return

        # sharpness
        try:
            ddepth = getattr(cv2, 'CV_64F', -1)
            lap = cv2.Laplacian(gray if gray is not None else frame, ddepth).var()
            if float(lap) < min_sharp:
                messagebox.showwarning("Quality", f"Image is blurry (sharpness {lap:.0f}). Please retake.")
                return
        except Exception:
            pass

        # face count
        try:
            faces = []
            face_count = 0
            if getattr(self.face_mgr, 'use_dlib', False):
                faces = self.face_mgr.face_detector(gray)
                face_count = len(faces)
            else:
                faces = self.face_mgr.face_cascade.detectMultiScale(gray, 1.3, 5)
                face_count = len(faces)
            if require_single and face_count != 1:
                messagebox.showwarning("Quality", f"Detected {face_count} faces. Please ensure only one face is visible.")
                return
        except Exception:
            pass

        temp_path = os.path.join(self.temp_dir, "employee_temp.jpg")
        try:
            cv2.imwrite(temp_path, self.captured_frame)
            encoding = None
            if getattr(self.face_mgr, 'use_dlib', False):
                try:
                    gray = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2GRAY)
                    faces = self.face_mgr.face_detector(gray)
                    if len(faces) > 0:
                        # compute encoding using full-face crop to be safe
                        f = faces[0]
                        x, y, w, h = f.left(), f.top(), f.width(), f.height()
                        crop = self.captured_frame[max(0, y):y+h, max(0, x):x+w]
                        dlib_mod = getattr(self.face_mgr, 'dlib', None)
                        if dlib_mod is None:
                            raise RuntimeError("dlib not available")
                        rect = dlib_mod.rectangle(0, 0, crop.shape[1], crop.shape[0])  # type: ignore
                        shape = self.face_mgr.shape_predictor(cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY), rect)
                        encoding = self.face_mgr.face_recognizer.compute_face_descriptor(crop, shape)
                except Exception:
                    encoding = None

            # Duplicate prevention using face manager helper
            try:
                gray2 = cv2.cvtColor(self.captured_frame, cv2.COLOR_BGR2GRAY)
                if getattr(self.face_mgr, 'use_dlib', False):
                    faces2 = self.face_mgr.face_detector(gray2)
                    if len(faces2) > 0:
                        f = faces2[0]
                        x, y, w, h = f.left(), f.top(), f.width(), f.height()
                    else:
                        x, y, w, h = 0, 0, self.captured_frame.shape[1], self.captured_frame.shape[0]
                else:
                    faces2 = self.face_mgr.face_cascade.detectMultiScale(gray2, 1.3, 5)
                    if len(faces2) > 0:
                        x, y, w, h = faces2[0]
                    else:
                        x, y, w, h = 0, 0, self.captured_frame.shape[1], self.captured_frame.shape[0]
                h_frame, w_frame = self.captured_frame.shape[:2]
                x, y, w, h = max(0, x), max(0, y), max(1, w), max(1, h)
                x2, y2 = min(x + w, w_frame), min(y + h, h_frame)
                face_img = self.captured_frame[y:y2, x:x2]
                is_dup, matched = self.face_mgr.is_face_duplicate(face_img)
                if is_dup:
                    messagebox.showwarning("Duplicate", f"This face matches an already registered face ({matched}). Please retake or use a different person.")
                    return
            except Exception:
                pass

            self.result = {"saved": True, "image_path": temp_path, "encoding": encoding}
            messagebox.showinfo("Saved", "Face captured and saved temporarily. It will be linked when you save the employee.")
            self.destroy()
        except Exception as e:
            messagebox.showerror("Save Error", f"Failed to save captured face: {e}")

    def on_cancel(self):
        self.result = {"saved": False, "image_path": None, "encoding": None}
        self.destroy()

    def destroy(self):
        try:
            if self.cap and self.cap.isOpened():
                self.cap.release()
        except Exception:
            pass
        super().destroy()


class AddEmployeePage:
    def __init__(self, parent, db, colors, fonts, face_mgr, email_mgr):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts
        self.face_mgr = face_mgr
        self.email_mgr = email_mgr
        self.enrolled_template = None
        self.enrolled_face_temp_path = None

    def show(self):
        self.clear_parent()
        # Use a scrollable frame so long forms remain usable on small windows
        self.current_frame = ctk.CTkScrollableFrame(self.parent, fg_color="transparent")
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
            font=self.fonts['text'],
            text_color=self.colors['text'],
            anchor="w"
        )
        name_label.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.entry_name = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter employee's full name",
            width=400,
            height=40,
            corner_radius=5,
            border_color=self.colors['primary']
        )
        self.entry_name.grid(row=1, column=0, sticky="ew", pady=(0, 15))

        # Email field
        email_label = ctk.CTkLabel(
            fields_frame,
            text="Email Address",
            font=self.fonts['text'],
            text_color=self.colors['text'],
            anchor="w"
        )
        email_label.grid(row=2, column=0, sticky="w", pady=(0, 5))

        self.entry_email = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter employee's email address",
            width=400,
            height=40,
            corner_radius=5,
            border_color=self.colors['primary']
        )
        self.entry_email.grid(row=3, column=0, sticky="ew", pady=(0, 15))

        # Fingerprint field
        fingerprint_label = ctk.CTkLabel(
            fields_frame,
            text="Fingerprint ID",
            font=self.fonts['text'],
            text_color=self.colors['text'],
            anchor="w"
        )
        fingerprint_label.grid(row=4, column=0, sticky="w", pady=(0, 5))

        self.entry_fingerprint = ctk.CTkEntry(
            fields_frame,
            placeholder_text="Enter fingerprint ID or use scanner",
            width=400,
            height=40,
            corner_radius=5,
            border_color=self.colors['primary']
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
            text_color=self.colors['text'],
            border_width=1,
            border_color="#d1d1d1",
            hover_color="#e8eaed",
            width=120,
            height=40,
            corner_radius=5
        )
        cancel_btn.pack(side="left", padx=(0, 10))

        enroll_fp_btn = ctk.CTkButton(
            buttons_frame,
            text="Enroll Fingerprint",
            command=self.enroll_fingerprint_for_new_employee,
            fg_color=self.colors['success'],
            text_color="white",
            hover_color="#0b8043",
            width=160,
            height=40,
            corner_radius=5
        )
        enroll_fp_btn.pack(side="left")

        enroll_face_btn = ctk.CTkButton(
            buttons_frame,
            text="Enroll Face",
            command=self.enroll_face_for_new_employee,
            fg_color=self.colors['primary'],
            text_color="white",
            hover_color=self.colors['accent'],
            width=140,
            height=40,
            corner_radius=5
        )
        enroll_face_btn.pack(side="left", padx=(10, 10))

        save_btn = ctk.CTkButton(
            buttons_frame,
            text="Save Employee",
            command=self.save_employee,
            fg_color=self.colors['primary'],
            text_color="white",
            hover_color=self.colors['accent'],
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
        self.parent.after(100, lambda: self._save_employee_action(name, email, fingerprint_id))

    def _save_employee_action(self, name, email, fingerprint_id):
        try:
            tpl = getattr(self, 'enrolled_template', None)
            new_id = self.db.add_employee(name, email, fingerprint_id, fingerprint_template=tpl)

            # If a temp face image exists (from enrollment window), move it to the proper employee file
            try:
                if self.enrolled_face_temp_path and os.path.isfile(self.enrolled_face_temp_path):
                    dst_img = os.path.join(self.face_mgr.faces_dir, f"employee_{new_id}.jpg")
                    shutil.move(self.enrolled_face_temp_path, dst_img)
                    # If we have an encoding object in enrolled_template, save that as .dat
                    if getattr(self, 'enrolled_face_encoding', None) is not None:
                        enc_path = os.path.join(self.face_mgr.faces_dir, f"employee_{new_id}.dat")
                        try:
                            with open(enc_path, 'wb') as f:
                                pickle.dump(self.enrolled_face_encoding, f)
                        except Exception:
                            pass
                else:
                    # If no temp image, and face is enabled, capture immediately
                    if self.db.get_setting('face_enabled', 'false') == 'true':
                        cam_idx = int(self.db.get_setting('camera_index', '0'))
                        self.face_mgr.enroll_face(employee_id=new_id, camera_index=cam_idx)
            except Exception:
                pass

            # Notify employee via email if enabled
            try:
                if email:
                    self.email_mgr.send_email(
                        to_address=email,
                        subject="Welcome to GDC Attendance",
                        body=f"Hello {name}, your details have been added. Your fingerprint ID is {fingerprint_id}."
                    )
            except Exception:
                pass

            # reset cached template after save
            try:
                self.enrolled_template = None
                self.enrolled_face_temp_path = None
                self.enrolled_face_encoding = None
            except Exception:
                pass

            self.hide_loading()
            messagebox.showinfo("Success", f"Employee {name} added successfully!")
            self.show_dashboard()
        except Exception as e:
            self.hide_loading()
            messagebox.showerror("Error", f"Failed to save employee: {e}")

    def enroll_fingerprint_for_new_employee(self):
        """Connect to scanner, enroll fingerprint, fill ID and cache template for saving."""
        try:
            from ..fingerprint_scanner import FingerprintScanner
            port = self.db.get_setting('fingerprint_port', '')
            if not port or port == 'None':
                messagebox.showerror("Scanner", "Please select scanner port in Settings first")
                return
            scanner = FingerprintScanner(port=port)
            if not scanner.connect():
                messagebox.showerror("Scanner", "Unable to connect to scanner on selected port")
                return
            ok, position, template = scanner.enroll_fingerprint()
            scanner.disconnect()
            if ok and position is not None:
                self.entry_fingerprint.delete(0, 'end')
                self.entry_fingerprint.insert(0, str(position))
                self.enrolled_template = template
                messagebox.showinfo("Enrollment", f"Fingerprint enrolled at position {position}")
            else:
                messagebox.showerror("Enrollment", "Fingerprint enrollment failed or already exists")
        except Exception as e:
            messagebox.showerror("Enrollment", f"Error during enrollment: {e}")

    def enroll_face_for_new_employee(self):
        """Open the FaceEnrollmentWindow (Design 2) and cache the temp image + encoding for later save."""
        try:
            cam_idx = int(self.db.get_setting('camera_index', '0'))
            win = FaceEnrollmentWindow(self.parent, self.face_mgr, camera_index=cam_idx, temp_dir=self.face_mgr.faces_dir, db=self.db)
            self.parent.wait_window(win)
            result = win.result
            if result and result.get('saved'):
                # store temp path and any encoding for saving after DB insert
                self.enrolled_face_temp_path = result.get('image_path')
                self.enrolled_face_encoding = result.get('encoding')
                messagebox.showinfo("Face Enrollment", "Face captured and will be linked after you save the employee.")
            else:
                messagebox.showinfo("Face Enrollment", "Face enrollment cancelled or not saved.")
        except Exception as e:
            messagebox.showerror("Face Enrollment", f"Error capturing face: {e}")

    def show_loading(self, message="Loading..."):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            return  # Already showing
        self._loading_overlay = ctk.CTkFrame(self.parent, fg_color="#000000")
        self._loading_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        spinner = ctk.CTkLabel(self._loading_overlay, text="⏳", font=("Segoe UI", 48), text_color="white")
        spinner.pack(expand=True, pady=(100, 10))
        msg = ctk.CTkLabel(self._loading_overlay, text=message, font=("Segoe UI", 18), text_color="white")
        msg.pack()

    def hide_loading(self):
        if hasattr(self, '_loading_overlay') and self._loading_overlay:
            self._loading_overlay.destroy()
            self._loading_overlay = None

    def show_dashboard(self):
        # This will be overridden by the main UI class
        pass

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
        from tkinter import ttk
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.pack(fill="x", pady=(10, 0))

        return header_frame

    def clear_parent(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
