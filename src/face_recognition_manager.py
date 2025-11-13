import os
import importlib
from typing import Optional, Any

# Dynamically import cv2 to keep type checkers calm about attributes
cv2: Any = importlib.import_module('cv2')


class FaceRecognitionManager:
    """Simple face enrollment and verification using OpenCV.

    - Stores one face image per employee under `faces/employee_<id>.jpg`.
    - Verification compares ORB features between live capture and stored images
      and picks the best match above a threshold.
    """

    def __init__(self, faces_dir: Optional[str] = None):
        self.faces_dir = faces_dir or os.path.join(os.getcwd(), "faces")
        os.makedirs(self.faces_dir, exist_ok=True)
        cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        self.orb = cv2.ORB_create()

    def _detect_face(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)
        if len(faces) == 0:
            return None
        x, y, w, h = faces[0]
        return frame[y:y+h, x:x+w]

    def _capture_frame(self, camera_index: int = 0):
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return None
        ret, frame = cap.read()
        cap.release()
        if not ret:
            return None
        return frame

    def _capture_best_face(self, camera_index: int = 0, max_frames: int = 30):
        """Capture up to max_frames and return the best detected face crop."""
        cap = cv2.VideoCapture(camera_index)
        if not cap.isOpened():
            return None

        best_face = None
        best_area = 0
        frames = 0

        try:
            while frames < max_frames:
                ret, frame = cap.read()
                if not ret or frame is None:
                    frames += 1
                    continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                # Skip very dark frames
                m = cv2.mean(gray)
                brightness = float(m[0]) if isinstance(m, (tuple, list)) else float(m)
                if brightness < 30:
                    frames += 1
                    continue
                faces = self.face_cascade.detectMultiScale(gray, 1.2, 5)
                for (x, y, w, h) in faces:
                    area = w * h
                    # Require minimally sized face to avoid false positives
                    if area > best_area and w >= 80 and h >= 80:
                        best_area = area
                        best_face = frame[y:y + h, x:x + w]
                frames += 1
        finally:
            cap.release()

        return best_face

    def enumerate_cameras(self, max_index: int = 5):
        cams = []
        for idx in range(0, max_index + 1):
            cap = cv2.VideoCapture(idx)
            if cap.isOpened():
                cams.append(str(idx))
                cap.release()
        return cams

    def enroll_face(self, employee_id: int, camera_index: int = 0):
        """Capture multiple frames to enroll the best detected face image for an employee."""
        face_img = self._capture_best_face(camera_index=camera_index, max_frames=60)
        if face_img is None:
            return False
        path = os.path.join(self.faces_dir, f"employee_{employee_id}.jpg")
        cv2.imwrite(path, face_img)
        return True

    def verify_face(self, camera_index: int = 0):
        """Capture a face and match to stored faces. Returns (employee_id, score) or (None, 0)."""
        frame = self._capture_frame(camera_index)
        if frame is None:
            return None, 0
        face_img = self._detect_face(frame)
        if face_img is None:
            return None, 0

        keypoints1, descriptors1 = self.orb.detectAndCompute(face_img, None)
        if descriptors1 is None:
            return None, 0

        bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=True)
        best_id = None
        best_score = 0

        for fname in os.listdir(self.faces_dir):
            if not fname.startswith("employee_") or not fname.endswith(".jpg"):
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
            # Higher score for more good matches (lower distance)
            good = [m for m in matches if m.distance < 40]
            score = len(good)
            if score > best_score:
                best_score = score
                try:
                    emp_id = int(fname.replace("employee_", "").replace(".jpg", ""))
                except Exception:
                    emp_id = None
                best_id = emp_id

        # Require minimal score to accept
        if best_score >= 10 and best_id is not None:
            return best_id, best_score
        return None, best_score