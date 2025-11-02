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
            fingerprint_id TEXT
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

    def add_employee(self, name, email, fingerprint_id):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO employees (name, email, fingerprint_id) VALUES (?, ?, ?)",
                       (name, email, fingerprint_id))
        self.conn.commit()

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
