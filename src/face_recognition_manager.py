import os
import importlib
import pickle
import time
from typing import Optional, Any, Tuple

# Dynamically import cv2 so static type checkers don't complain about optional backends
cv2: Any = importlib.import_module('cv2')

# Try to import dlib for advanced face recognition
try:
    import dlib  # type: ignore[import]
    DLIB_AVAILABLE = True
except Exception:
    dlib = None
    DLIB_AVAILABLE = False


class FaceRecognitionManager:
    """Advanced face enrollment and verification using OpenCV + dlib (optional).

    Behavior and guarantees:
    - If dlib is installed *and* required model files are present, the class will use dlib for
      detection and 128-D face descriptors.
    - If dlib is not available or model files are missing, the class falls back to OpenCV
      Haar cascade detection + ORB feature matching.
    - All files (images and encodings) are stored under `faces_dir` (default: ./faces).

    Notes on dlib models (optional):
    - If you want dlib mode, download these two files and place them in the project folder or
      change the predictor_path/recog_model_path variables:
        - shape_predictor_68_face_landmarks.dat
        - dlib_face_recognition_resnet_model_v1.dat
    """

    def __init__(self, faces_dir: Optional[str] = None, dlib_predictor_path: Optional[str] = None,
                 dlib_recog_model_path: Optional[str] = None):
        self.faces_dir = faces_dir or os.path.join(os.getcwd(), "faces")
        os.makedirs(self.faces_dir, exist_ok=True)

        # Prepare OpenCV fallback resources
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.orb = cv2.ORB_create()
        self.use_dlib = False

        # Attempt to initialize dlib (graceful fallback if anything fails)
        # Expose dlib reference for external checks (may be None)
        self.dlib = dlib if DLIB_AVAILABLE else None

        if DLIB_AVAILABLE:
            try:
                # Default to project directory if not explicitly provided
                predictor_path = dlib_predictor_path or os.path.join(os.getcwd(), 'shape_predictor_68_face_landmarks.dat')
                recog_model_path = dlib_recog_model_path or os.path.join(os.getcwd(), 'dlib_face_recognition_resnet_model_v1.dat')

                if not (os.path.isfile(predictor_path) and os.path.isfile(recog_model_path)):
                    raise FileNotFoundError('One or both dlib model files are missing')

                self.face_detector = dlib.get_frontal_face_detector()  # type: ignore
                self.shape_predictor = dlib.shape_predictor(predictor_path)  # type: ignore
                self.face_recognizer = dlib.face_recognition_model_v1(recog_model_path)  # type: ignore
                self.use_dlib = True
                print('FaceRecognitionManager: dlib available and models loaded — using dlib mode')
            except Exception as e:
                print('FaceRecognitionManager: dlib initialization failed, falling back to OpenCV. Error:', e)
                self.use_dlib = False
        else:
            print('FaceRecognitionManager: dlib not installed — using OpenCV fallback')

    # -------------------- Camera helpers --------------------
    def _open_capture(self, camera_index: int = 0, backend: Optional[int] = None):
        if backend is None:
            cap = cv2.VideoCapture(camera_index)
        else:
            cap = cv2.VideoCapture(camera_index, backend)
        return cap

    def enumerate_cameras(self, max_index: int = 5):
        cams = []
        for idx in range(0, max_index + 1):
            cap = self._open_capture(idx)
            if cap.isOpened():
                cams.append(str(idx))
                cap.release()
        return cams

    def is_camera_available(self, camera_index: int = 0):
        cap = self._open_capture(camera_index)
        available = cap.isOpened()
        if available:
            cap.release()
        return available

    def _capture_frame(self, camera_index: int = 0, warmup_frames: int = 5, backend: Optional[int] = None):
        """Open the camera, warm up for a few frames, return a single frame or None."""
        cap = self._open_capture(camera_index, backend)
        if not cap.isOpened():
            print(f"_capture_frame: camera {camera_index} not opened")
            return None

        # Warm up camera (some cameras need a few frames to auto-expose)
        for _ in range(warmup_frames):
            ret, _ = cap.read()
            if not ret:
                time.sleep(0.02)

        ret, frame = cap.read()
        cap.release()
        if not ret or frame is None:
            print("_capture_frame: final read failed")
            return None
        return frame

    # -------------------- Face detection helpers --------------------
    def _detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
        if len(faces) == 0:
            return None
        x, y, w, h = faces[0]
        # Clip coordinates
        h_frame, w_frame = frame.shape[:2]
        x, y = max(0, x), max(0, y)
        x2, y2 = min(x + w, w_frame), min(y + h, h_frame)
        return frame[y:y2, x:x2]

    def _capture_best_face(self, camera_index: int = 0, max_frames: int = 30, backend: Optional[int] = None):
        cap = self._open_capture(camera_index, backend)
        if not cap.isOpened():
            print("_capture_best_face: camera could not be opened")
            return None

        best_face = None
        best_area = 0
        frames = 0

        try:
            while frames < max_frames:
                ret, frame = cap.read()
                frames += 1
                if not ret or frame is None:
                    continue

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Skip very dark frames
                m = cv2.mean(gray)
                brightness = float(m[0]) if isinstance(m, (tuple, list)) else float(m)
                if brightness < 30:
                    continue

                faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
                for (x, y, w, h) in faces:
                    area = w * h
                    if area > best_area and w >= 80 and h >= 80:
                        best_area = area
                        h_frame, w_frame = frame.shape[:2]
                        x2 = min(x + w, w_frame)
                        y2 = min(y + h, h_frame)
                        best_face = frame[y:y2, x:x2]
        finally:
            cap.release()

        return best_face

    # -------------------- Enrollment --------------------
    def enroll_face(self, employee_id: int, camera_index: int = 0, backend: Optional[int] = None):
        """Capture multiple frames and save the best face image (and dlib encoding if available)."""
        face_img = self._capture_best_face(camera_index=camera_index, max_frames=60, backend=backend)
        if face_img is None:
            print('enroll_face: no face captured')
            return False

        path = os.path.join(self.faces_dir, f"employee_{employee_id}.jpg")
        cv2.imwrite(path, face_img)

        if self.use_dlib:
            try:
                gray = cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY)
                faces = self.face_detector(gray)
                if len(faces) > 0:
                    shape = self.shape_predictor(gray, faces[0])
                    encoding = self.face_recognizer.compute_face_descriptor(face_img, shape)
                    encoding_path = os.path.join(self.faces_dir, f"employee_{employee_id}.dat")
                    with open(encoding_path, 'wb') as f:
                        pickle.dump(encoding, f)
            except Exception as e:
                print('enroll_face: saving dlib encoding failed:', e)

        print(f'enroll_face: saved employee_{employee_id}')
        return True

    def enroll_face_live(self, employee_id: int, camera_index: int = 0, on_success=None, backend: Optional[int] = None):
        """Open a live camera window to enroll a face. Press 'C' to capture, 'Q' to quit."""
        cap = self._open_capture(camera_index, backend)
        if not cap.isOpened():
            print('enroll_face_live: Camera not available')
            return False

        # Warm up
        for _ in range(8):
            cap.read()

        captured = False

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print('enroll_face_live: frame read failed')
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                faces = []
                if self.use_dlib:
                    try:
                        faces = self.face_detector(gray)
                    except Exception as e:
                        print('dlib detection error:', e)
                        faces = []
                else:
                    faces = list(self.face_cascade.detectMultiScale(gray, 1.3, 5))

                # draw faces and instructions
                if self.use_dlib:
                    for face in faces:
                        x, y, w, h = face.left(), face.top(), face.width(), face.height()
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, 'Press C to capture', (max(0, x), max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                else:
                    for (x, y, w, h) in faces:
                        cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                        cv2.putText(frame, 'Press C to capture', (max(0, x), max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

                cv2.imshow('Face Enrollment - Press C to capture, Q to quit', frame)
                key = cv2.waitKey(1) & 0xFF
                if key in (ord('q'), ord('Q')):
                    break
                if key in (ord('c'), ord('C')) and len(faces) > 0:
                    if self.use_dlib:
                        face = faces[0]
                        x, y, w, h = face.left(), face.top(), face.width(), face.height()
                    else:
                        x, y, w, h = faces[0]

                    # sanitize and clip coordinates
                    x, y, w, h = max(0, x), max(0, y), max(1, w), max(1, h)
                    h_frame, w_frame = frame.shape[:2]
                    x2 = min(x + w, w_frame)
                    y2 = min(y + h, h_frame)
                    face_img = frame[y:y2, x:x2]

                    if face_img is None or face_img.size == 0:
                        print('Captured face image invalid')
                        continue

                    path = os.path.join(self.faces_dir, f"employee_{employee_id}.jpg")
                    cv2.imwrite(path, face_img)

                    if self.use_dlib:
                        try:
                            # create a rectangle in face_img coords and compute descriptor
                            rect = dlib.rectangle(0, 0, face_img.shape[1], face_img.shape[0])  # type: ignore
                            shape = self.shape_predictor(cv2.cvtColor(face_img, cv2.COLOR_BGR2GRAY), rect)
                            encoding = self.face_recognizer.compute_face_descriptor(face_img, shape)
                            encoding_path = os.path.join(self.faces_dir, f"employee_{employee_id}.dat")
                            with open(encoding_path, 'wb') as f:
                                pickle.dump(encoding, f)
                        except Exception as e:
                            print('enroll_face_live: error saving dlib encoding:', e)

                    captured = True
                    if on_success:
                        try:
                            on_success()
                        except Exception as e:
                            print('on_success callback error:', e)
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()

        return captured

    # -------------------- Verification --------------------
    def _euclidean_distance(self, a, b):
        import numpy as np
        return float(np.linalg.norm(np.array(a) - np.array(b)))

    def verify_face(self, camera_index: int = 0, backend: Optional[int] = None) -> Tuple[Optional[int], float]:
        """Capture a single frame and verify it against stored faces.

        Returns (employee_id, score) or (None, 0.0).
        """
        frame = self._capture_frame(camera_index, backend=backend)
        if frame is None:
            return None, 0.0
        return self.verify_frame(frame)

    def verify_frame(self, frame) -> Tuple[Optional[int], float]:
        """Verify a provided BGR frame against stored faces.
        Returns (employee_id, score) or (None, 0). In dlib mode, score is -distance.
        """
        try:
            if frame is None:
                return None, 0.0
            if self.use_dlib:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_detector(gray)
                if len(faces) == 0:
                    return None, 0.0
                # Use first face for matching
                face = faces[0]
                shape = self.shape_predictor(gray, face)
                encoding = self.face_recognizer.compute_face_descriptor(frame, shape)

                best_id = None
                best_distance = float('inf')
                for fname in os.listdir(self.faces_dir):
                    if not fname.startswith('employee_') or not fname.endswith('.dat'):
                        continue
                    encoding_path = os.path.join(self.faces_dir, fname)
                    try:
                        with open(encoding_path, 'rb') as f:
                            stored_encoding = pickle.load(f)
                        distance = self._euclidean_distance(encoding, stored_encoding)
                        if distance < best_distance:
                            best_distance = distance
                            try:
                                emp_id = int(fname.replace('employee_', '').replace('.dat', ''))
                            except Exception:
                                emp_id = None
                            best_id = emp_id
                    except Exception:
                        continue
                # Convert distance to a score (higher is better)
                score = float(max(0.0, 1.0 - (best_distance / 1.0))) if best_distance != float('inf') else 0.0
                if best_id is not None:
                    return best_id, score
                return None, 0.0
            else:
                # OpenCV fallback: ORB feature matching against stored face images
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                if len(faces) == 0:
                    return None, 0.0
                x, y, w, h = faces[0]
                face_img = frame[y:y + h, x:x + w]
                keypoints1, descriptors1 = self.orb.detectAndCompute(face_img, None)
                if descriptors1 is None:
                    return None, 0.0

                bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                best_id = None
                best_score = 0
                for fname in os.listdir(self.faces_dir):
                    if not fname.startswith('employee_') or not fname.endswith('.jpg'):
                        continue
                    path = os.path.join(self.faces_dir, fname)
                    img = cv2.imread(path)
                    if img is None:
                        continue
                    kp2, des2 = self.orb.detectAndCompute(img, None)
                    if des2 is None:
                        continue
                    matches = bf.match(descriptors1, des2)
                    score = len(matches)
                    if score > best_score:
                        best_score = score
                        try:
                            emp_id = int(fname.replace('employee_', '').replace('.jpg', ''))
                        except Exception:
                            emp_id = None
                        best_id = emp_id
                if best_id is not None:
                    return best_id, float(best_score)
                return None, 0.0
        except Exception:
            return None, 0.0

    def verify_faces_live(self, camera_index: int = 0, on_detection=None, backend: Optional[int] = None):
        """Open a live camera window to detect and verify multiple faces in real-time.
        Calls on_detection(employee_id, name) for each detected face. Press 'q' to quit the window.
        """
        cap = self._open_capture(camera_index, backend)
        if not cap.isOpened():
            print('verify_faces_live: Camera not available')
            return

        # Warm up
        for _ in range(8):
            cap.read()

        detected_today = set()

        try:
            while True:
                ret, frame = cap.read()
                if not ret or frame is None:
                    print('verify_faces_live: frame read failed')
                    break

                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

                if self.use_dlib:
                    try:
                        faces = self.face_detector(gray)
                    except Exception as e:
                        print('dlib detection error:', e)
                        faces = []

                    for face in faces:
                        x, y, w, h = face.left(), face.top(), face.width(), face.height()
                        shape = self.shape_predictor(gray, face)
                        encoding = self.face_recognizer.compute_face_descriptor(frame, shape)

                        best_id = None
                        best_distance = float('inf')

                        for fname in os.listdir(self.faces_dir):
                            if not fname.startswith('employee_') or not fname.endswith('.dat'):
                                continue
                            encoding_path = os.path.join(self.faces_dir, fname)
                            try:
                                with open(encoding_path, 'rb') as f:
                                    stored_encoding = pickle.load(f)
                                distance = self._euclidean_distance(encoding, stored_encoding)
                                if distance < best_distance:
                                    best_distance = distance
                                    try:
                                        emp_id = int(fname.replace('employee_', '').replace('.dat', ''))
                                    except Exception:
                                        emp_id = None
                                    best_id = emp_id
                            except Exception:
                                continue

                        if best_distance < 0.6 and best_id is not None and best_id not in detected_today:
                            detected_today.add(best_id)
                            if on_detection:
                                try:
                                    on_detection(best_id, f"Employee {best_id}")
                                except Exception as e:
                                    print('on_detection callback error:', e)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(frame, f"Employee {best_id}", (max(0, x), max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        else:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)
                else:
                    faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
                    for (x, y, w, h) in faces:
                        face_img = frame[y:y + h, x:x + w]
                        keypoints1, descriptors1 = self.orb.detectAndCompute(face_img, None)
                        if descriptors1 is None:
                            continue

                        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
                        best_id = None
                        best_score = 0

                        for fname in os.listdir(self.faces_dir):
                            if not fname.startswith('employee_') or not fname.endswith('.jpg'):
                                continue
                            path = os.path.join(self.faces_dir, fname)
                            img = cv2.imread(path)
                            if img is None:
                                continue
                            kp2, des2 = self.orb.detectAndCompute(img, None)
                            if des2 is None:
                                continue
                            matches = bf.match(descriptors1, des2)
                            matches = sorted(matches, key=lambda x: x.distance)
                            good = [m for m in matches if m.distance < 40]
                            score = len(good)
                            if score > best_score:
                                best_score = score
                                try:
                                    emp_id = int(fname.replace('employee_', '').replace('.jpg', ''))
                                except Exception:
                                    emp_id = None
                                best_id = emp_id

                        if best_score >= 10 and best_id is not None and best_id not in detected_today:
                            detected_today.add(best_id)
                            if on_detection:
                                try:
                                    on_detection(best_id, f"Employee {best_id}")
                                except Exception as e:
                                    print('on_detection callback error:', e)
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                            cv2.putText(frame, f"Employee {best_id}", (max(0, x), max(0, y - 10)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 255, 0), 2)
                        else:
                            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                cv2.imshow('Face Recognition - Press Q to quit', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        finally:
            cap.release()
            cv2.destroyAllWindows()


# End of file