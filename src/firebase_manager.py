import datetime

class FirebaseManager:
    def __init__(self):
        self.simulated_data = {}
        print("🔥 FirebaseManager initialized (simulation mode)")

    def upload_attendance(self, student_name, status):
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.simulated_data[timestamp] = {
            "name": student_name,
            "status": status
        }
        print(f"📤 [SIMULATED UPLOAD] {student_name} marked {status} at {timestamp}")

    def get_all_attendance(self):
        return self.simulated_data
