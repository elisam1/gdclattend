import os
import datetime
from typing import Dict, Any, List

# try to import firebase admin SDK, but keep a simulation fallback
try:
    import firebase_admin
    from firebase_admin import credentials, firestore, storage
    FIREBASE_AVAILABLE = True
except Exception:
    firebase_admin = None
    credentials = None
    firestore = None
    storage = None
    FIREBASE_AVAILABLE = False


class FirebaseManager:
    """Manages Firebase interactions when a service account is present.

    If `serviceAccountKey.json` is not present or firebase-admin isn't installed,
    this will run in simulation/local-backups mode.
    """

    def __init__(self, service_account_path: str = "serviceAccountKey.json"):
        self.service_account_path = service_account_path
        self.simulated_data: Dict[str, Dict[str, Any]] = {}
        self.local_backups_dir = os.path.join(os.getcwd(), "backups")
        os.makedirs(self.local_backups_dir, exist_ok=True)

        self._use_firebase = False
        self._firestore_client = None
        self._storage_bucket = None

        if FIREBASE_AVAILABLE and os.path.exists(self.service_account_path):
            try:
                cred = credentials.Certificate(self.service_account_path)
                # Allow specifying a default storage bucket via env var FIREBASE_STORAGE_BUCKET
                bucket_name = os.environ.get("FIREBASE_STORAGE_BUCKET")

                if bucket_name:
                    firebase_admin.initialize_app(cred, {"storageBucket": bucket_name})
                else:
                    firebase_admin.initialize_app(cred)

                self._firestore_client = firestore.client()
                try:
                    self._storage_bucket = storage.bucket() if bucket_name else None
                except Exception:
                    self._storage_bucket = None

                self._use_firebase = True
                print("🔥 FirebaseManager initialized (firebase-admin)")
            except Exception as e:
                print(f"⚠️ Firebase initialization failed, falling back to simulation: {e}")
                self._use_firebase = False
        else:
            print("🔥 FirebaseManager initialized (simulation/local-backups mode)")

    # --- Attendance ---
    def upload_attendance(self, *args, **kwargs):
        """Upload attendance record.

        Supports two call styles:
        - upload_attendance(name, status)
        - upload_attendance({'name': name, 'status': status, ...})
        """
        now = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        # Normalize args into a dict
        if len(args) == 1 and isinstance(args[0], dict):
            record = dict(args[0])
        elif len(args) >= 2:
            record = {"name": args[0], "status": args[1]}
        else:
            record = kwargs or {}

        record.setdefault("timestamp", now)

        if self._use_firebase and self._firestore_client:
            try:
                col = self._firestore_client.collection("attendance")
                col.add(record)
                print(f"📤 [FIRESTORE] Uploaded attendance: {record}")
                return True
            except Exception as e:
                print(f"⚠️ Failed to upload attendance to Firestore: {e}")

        # simulation fallback
        self.simulated_data[record["timestamp"]] = record
        print(f"📤 [SIMULATED UPLOAD] {record}")
        return True

    def get_all_attendance(self) -> Dict[str, Dict[str, Any]]:
        """Return attendance records from Firestore if available, otherwise simulated data."""
        if self._use_firebase and self._firestore_client:
            try:
                docs = list(self._firestore_client.collection("attendance").stream())
                return {d.id: d.to_dict() for d in docs}
            except Exception as e:
                print(f"⚠️ Failed to read attendance from Firestore: {e}")

        return self.simulated_data

    # --- Backups (storage/local) ---
    def list_backups(self) -> List[Dict[str, Any]]:
        """List available backups. Returns list of dicts with filename, timestamp, size_bytes."""
        backups = []
        if self._use_firebase and self._storage_bucket:
            try:
                blobs = list(self._storage_bucket.list_blobs(prefix="backups/"))
                for b in blobs:
                    if b.name.endswith("/"):
                        continue
                    backups.append({
                        "filename": os.path.basename(b.name),
                        "timestamp": b.updated.strftime("%Y-%m-%d %H:%M:%S") if b.updated else "",
                        "size_bytes": b.size or 0,
                    })
                return backups
            except Exception as e:
                print(f"⚠️ Failed to list backups from storage: {e}")

        # local backups
        try:
            for fname in os.listdir(self.local_backups_dir):
                path = os.path.join(self.local_backups_dir, fname)
                if os.path.isfile(path):
                    stat = os.stat(path)
                    backups.append({
                        "filename": fname,
                        "timestamp": datetime.datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                        "size_bytes": stat.st_size,
                    })
        except Exception as e:
            print(f"⚠️ Failed to list local backups: {e}")

        return backups

    def backup_database(self, db_path: str) -> bool:
        """Upload or store a backup copy of the database file.

        Returns True on success.
        """
        if not os.path.exists(db_path):
            print(f"⚠️ Database path not found: {db_path}")
            return False

        timestamp = datetime.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_{timestamp}.db"

        if self._use_firebase and self._storage_bucket:
            try:
                blob = self._storage_bucket.blob(f"backups/{filename}")
                blob.upload_from_filename(db_path)
                print(f"📦 Uploaded backup to storage: backups/{filename}")
                return True
            except Exception as e:
                print(f"⚠️ Failed to upload backup to storage: {e}")

        # fallback: copy file locally
        try:
            dest = os.path.join(self.local_backups_dir, filename)
            with open(db_path, "rb") as srcf, open(dest, "wb") as dstf:
                dstf.write(srcf.read())
            print(f"📦 Created local backup: {dest}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to create local backup: {e}")
            return False

    def restore_database(self, backup_filename: str, local_temp_path: str) -> bool:
        """Restore a backup to a local temp path. Returns True on success."""
        if self._use_firebase and self._storage_bucket:
            try:
                blob = self._storage_bucket.blob(f"backups/{backup_filename}")
                blob.download_to_filename(local_temp_path)
                print(f"⬇️ Downloaded backup from storage to {local_temp_path}")
                return True
            except Exception as e:
                print(f"⚠️ Failed to download backup from storage: {e}")

        # fallback: copy from local backups dir
        try:
            src = os.path.join(self.local_backups_dir, backup_filename)
            if not os.path.exists(src):
                print(f"⚠️ Local backup not found: {src}")
                return False
            with open(src, "rb") as sf, open(local_temp_path, "wb") as df:
                df.write(sf.read())
            print(f"⬇️ Restored local backup to {local_temp_path}")
            return True
        except Exception as e:
            print(f"⚠️ Failed to restore local backup: {e}")
            return False

