import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="attendance.db"):
        self.conn = sqlite3.connect(db_name)
        self.create_tables()

    def create_tables(self):
        query_employee = """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            fingerprint_id TEXT
        );
        """

        query_attendance = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            timestamp TEXT,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
        """
        
        query_users = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            employee_id INTEGER,
            FOREIGN KEY (employee_id) REFERENCES employees (id)
        );
        """

        cursor = self.conn.cursor()
        cursor.execute(query_employee)
        cursor.execute(query_attendance)
        cursor.execute(query_users)
        
        # Create default admin user if not exists
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if not cursor.fetchone():
            cursor.execute("INSERT INTO users (username, password, role) VALUES (?, ?, ?)", 
                          ('admin', 'admin123', 'admin'))
        
        self.conn.commit()

    def add_employee(self, name, email, fingerprint_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO employees (name, email, fingerprint_id) VALUES (?, ?, ?)",
                       (name, email, fingerprint_id))
        self.conn.commit()

    def mark_attendance(self, employee_id):
        cursor = self.conn.cursor()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("INSERT INTO attendance (employee_id, timestamp) VALUES (?, ?)",
                       (employee_id, timestamp))
        self.conn.commit()

    def get_all_employees(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM employees")
        return cursor.fetchall()

    def get_attendance_records(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT employees.name, attendance.timestamp
            FROM attendance
            JOIN employees ON attendance.employee_id = employees.id
            ORDER BY attendance.timestamp DESC
        """)
        return cursor.fetchall()
