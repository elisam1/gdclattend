import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="attendance.db"):
        self.conn = sqlite3.connect(db_name)
        # enable row access by name
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):
        query_employee = """
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT,
            fingerprint_id TEXT,
            fingerprint_template BLOB
        );
        """

        # New attendance schema supports arrival and departure times per date
        query_attendance = """
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            employee_id INTEGER,
            date TEXT,
            arrival_time TEXT,
            departure_time TEXT,
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
            first_login INTEGER DEFAULT 1,
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

        # Ensure users table has 'first_login' column (migration for older DBs)
        try:
            cursor.execute("PRAGMA table_info(users)")
            user_cols = [r[1] for r in cursor.fetchall()]
            if 'first_login' not in user_cols:
                cursor.execute("ALTER TABLE users ADD COLUMN first_login INTEGER DEFAULT 1")
                self.conn.commit()
        except Exception:
            pass
        # Settings table for app-level configuration
        try:
            cursor.execute("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT
            );
            """)
            # insert default settings if missing
            cursor.execute("SELECT key FROM settings WHERE key = 'auto_save_on_logout'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('auto_save_on_logout', '1'))
            cursor.execute("SELECT key FROM settings WHERE key = 'auto_save_interval'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('auto_save_interval', '60'))
            cursor.execute("SELECT key FROM settings WHERE key = 'confirm_logout'")
            if not cursor.fetchone():
                cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", ('confirm_logout', '1'))
            self.conn.commit()
        except Exception:
            pass
        # Migration: if an old attendance table exists with a 'timestamp' column, migrate it
        try:
            cursor.execute("PRAGMA table_info(attendance)")
            cols = [r[1] for r in cursor.fetchall()]
            if 'timestamp' in cols and 'arrival_time' not in cols:
                # old schema detected; migrate to new schema
                cursor.execute("ALTER TABLE attendance RENAME TO attendance_old")
                cursor.execute(query_attendance)
                # migrate rows
                cursor.execute("SELECT employee_id, timestamp FROM attendance_old")
                rows = cursor.fetchall()
                for er in rows:
                    emp_id = er[0]
                    ts = er[1]
                    try:
                        dt = datetime.strptime(ts, "%Y-%m-%d %H:%M:%S")
                        date_str = dt.strftime("%Y-%m-%d")
                        time_str = dt.strftime("%H:%M:%S")
                    except Exception:
                        date_str = ts.split()[0] if ts else ''
                        time_str = ts
                    cursor.execute("INSERT INTO attendance (employee_id, date, arrival_time, departure_time) VALUES (?, ?, ?, ?)",
                                   (emp_id, date_str, time_str, None))
                cursor.execute("DROP TABLE IF EXISTS attendance_old")
                self.conn.commit()
        except Exception:
            # If migration fails, ignore and continue with new schema
            pass

    def add_employee(self, name, email, fingerprint_id, fingerprint_template=None):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO employees (name, email, fingerprint_id, fingerprint_template) VALUES (?, ?, ?, ?)",
                       (name, email, fingerprint_id, fingerprint_template))
        self.conn.commit()
        return cursor.lastrowid  # Return the employee ID for reference

    # --- Attendance helpers: arrival/departure per day ---
    def _today_date(self):
        return datetime.now().strftime("%Y-%m-%d")

    def _current_time(self):
        return datetime.now().strftime("%H:%M:%S")

    def get_today_record(self, employee_id):
        cursor = self.conn.cursor()
        date_str = self._today_date()
        cursor.execute("SELECT * FROM attendance WHERE employee_id = ? AND date = ?", (employee_id, date_str))
        row = cursor.fetchone()
        return dict(row) if row else None

    def mark_arrival(self, employee_id):
        cursor = self.conn.cursor()
        date_str = self._today_date()
        time_str = self._current_time()
        # check existing record for today
        cursor.execute("SELECT id, arrival_time, departure_time FROM attendance WHERE employee_id = ? AND date = ?",
                       (employee_id, date_str))
        row = cursor.fetchone()
        if row is None:
            cursor.execute("INSERT INTO attendance (employee_id, date, arrival_time, departure_time) VALUES (?, ?, ?, ?)",
                           (employee_id, date_str, time_str, None))
        else:
            # if arrival_time missing, set it; if both present, create new entry
            if row['arrival_time'] is None:
                cursor.execute("UPDATE attendance SET arrival_time = ? WHERE id = ?", (time_str, row['id']))
            elif row['arrival_time'] and row['departure_time'] is not None:
                cursor.execute("INSERT INTO attendance (employee_id, date, arrival_time, departure_time) VALUES (?, ?, ?, ?)",
                               (employee_id, date_str, time_str, None))
            else:
                # arrival already set and departure missing; treat as duplicate arrival, leave as-is
                pass
        self.conn.commit()
        return {"action": "arrival", "time": time_str, "date": date_str}

    def mark_departure(self, employee_id):
        cursor = self.conn.cursor()
        date_str = self._today_date()
        time_str = self._current_time()
        # find today's row with arrival but no departure
        cursor.execute("SELECT id, arrival_time, departure_time FROM attendance WHERE employee_id = ? AND date = ? ORDER BY id DESC", (employee_id, date_str))
        rows = cursor.fetchall()
        target = None
        for r in rows:
            if r['arrival_time'] is not None and r['departure_time'] is None:
                target = r
                break
        if target:
            cursor.execute("UPDATE attendance SET departure_time = ? WHERE id = ?", (time_str, target['id']))
        else:
            # no matching arrival; create a record with only departure_time
            cursor.execute("INSERT INTO attendance (employee_id, date, arrival_time, departure_time) VALUES (?, ?, ?, ?)",
                           (employee_id, date_str, None, time_str))
        self.conn.commit()
        return {"action": "departure", "time": time_str, "date": date_str}

    def mark_arrival_or_departure(self, employee_id):
        """Decide whether to mark arrival or departure for the given employee for today.

        Returns a dict with keys: action ('arrival'|'departure'), time, date
        """
        rec = self.get_today_record(employee_id)
        if rec is None:
            return self.mark_arrival(employee_id)
        # if arrival exists and departure missing -> mark departure
        if rec.get('arrival_time') and not rec.get('departure_time'):
            return self.mark_departure(employee_id)
        # otherwise, create new arrival
        return self.mark_arrival(employee_id)

    def mark_attendance(self, employee_id):
        # Backwards-compatible wrapper: mark an arrival timestamp
        return self.mark_arrival_or_departure(employee_id)

    def get_all_employees(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM employees")
        return cursor.fetchall()

    def get_attendance_records(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT attendance.date, employees.name, attendance.arrival_time, attendance.departure_time
            FROM attendance
            JOIN employees ON attendance.employee_id = employees.id
            ORDER BY attendance.date DESC, employees.name ASC
        """)
        return cursor.fetchall()
        
    # --- User Management ---
    def authenticate_user(self, username, password):
        """Authenticate a user and return tuple (user_id, role) or None if failed."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id, role, first_login FROM users WHERE username = ? AND password = ?", 
                      (username, password))
        row = cursor.fetchone()
        if not row:
            return None
        # sqlite3.Row may not support dict.get; handle missing column defensively
        first_login = row['first_login'] if 'first_login' in row.keys() else 1
        return (row['id'], row['role'], first_login)
        
    def add_user(self, username, password, role, employee_id=None):
        """Add a new user with specified role."""
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO users (username, password, role, employee_id, first_login) VALUES (?, ?, ?, ?, 1)",
                       (username, password, role, employee_id))
        self.conn.commit()
        
    def change_password(self, user_id, old_password, new_password):
        """Change a user's password, returns True if successful."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM users WHERE id = ? AND password = ?", (user_id, old_password))
        if cursor.fetchone():
            cursor.execute("UPDATE users SET password = ?, first_login = 0 WHERE id = ?", 
                         (new_password, user_id))
            self.conn.commit()
            return True
        return False
    
    def get_all_users(self):
        """Get all users except admin for user management."""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT users.id, users.username, users.role, users.first_login,
                   employees.name as employee_name
            FROM users 
            LEFT JOIN employees ON users.employee_id = employees.id
            WHERE users.username != 'admin'
            ORDER BY users.username
        """)
        return cursor.fetchall()
    
    def delete_user(self, user_id):
        """Delete a user account."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM users WHERE id = ? AND username != 'admin'", (user_id,))
        self.conn.commit()
        return cursor.rowcount > 0

    # --- Settings helpers ---
    def get_setting(self, key, default=None):
        cursor = self.conn.cursor()
        cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
        row = cursor.fetchone()
        return row[0] if row else default

    def set_setting(self, key, value):
        cursor = self.conn.cursor()
        cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
        self.conn.commit()

    def get_all_settings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {r[0]: r[1] for r in cursor.fetchall()}
