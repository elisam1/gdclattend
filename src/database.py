import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_name="attendance.db"):
        self.db_name = db_name
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
            # email settings defaults
            defaults = [
                ('email_notifications', 'false'),
                ('smtp_server', ''),
                ('smtp_port', '587'),
                ('smtp_user', ''),
                ('smtp_password', ''),
                ('smtp_use_tls', 'true'),
                ('smtp_use_ssl', 'false'),
                ('attendance_mode', 'both'),
            ]
            for k, v in defaults:
                cursor.execute("SELECT key FROM settings WHERE key = ?", (k,))
                if not cursor.fetchone():
                    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (k, v))
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

        # Migration: handle legacy 'employee' table and missing columns
        try:
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name IN ('employee','employees')")
            names = [r[0] for r in cursor.fetchall()]
            if 'employee' in names and 'employees' not in names:
                cursor.execute("ALTER TABLE employee RENAME TO employees")
                self.conn.commit()
            # Ensure 'email' and 'fingerprint_template' columns exist
            cursor.execute("PRAGMA table_info(employees)")
            ecols = [r[1] for r in cursor.fetchall()]
            if 'email' not in ecols:
                cursor.execute("ALTER TABLE employees ADD COLUMN email TEXT")
            if 'fingerprint_template' not in ecols:
                cursor.execute("ALTER TABLE employees ADD COLUMN fingerprint_template BLOB")
            self.conn.commit()
        except Exception:
            pass

    def reset_admin(self):
        """Ensure a default admin user exists with username 'admin' and password 'admin123'.

        If an admin user already exists, update its password to 'admin123' and set first_login=1.
        """
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = 'admin'")
            row = cursor.fetchone()
            if row:
                cursor.execute("UPDATE users SET password = ?, role = ?, first_login = 1 WHERE username = 'admin'",
                               ('admin123', 'admin'))
            else:
                cursor.execute("INSERT INTO users (username, password, role, first_login) VALUES (?, ?, ?, 1)",
                               ('admin', 'admin123', 'admin'))
            self.conn.commit()
            return True
        except Exception:
            return False

    # --- App Settings helpers ---
    def get_setting(self, key, default=None):
        """Get a setting value by key. Returns default if missing."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = cursor.fetchone()
            return row[0] if row and row[0] is not None else default
        except Exception:
            return default

    def set_setting(self, key, value):
        """Upsert a setting value."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value", (key, str(value)))
            self.conn.commit()
            return True
        except Exception:
            try:
                # Fallback for older SQLite without upsert syntax
                cursor = self.conn.cursor()
                cursor.execute("UPDATE settings SET value = ? WHERE key = ?", (str(value), key))
                if cursor.rowcount == 0:
                    cursor.execute("INSERT INTO settings (key, value) VALUES (?, ?)", (key, str(value)))
                self.conn.commit()
                return True
            except Exception:
                return False

    def add_employee(self, name, email, fingerprint_id, fingerprint_template=None):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO employees (name, email, fingerprint_id, fingerprint_template) VALUES (?, ?, ?, ?)",
                       (name, email, fingerprint_id, fingerprint_template))
        self.conn.commit()
        return cursor.lastrowid  # Return the employee ID for reference

    def update_employee(self, employee_id, name=None, email=None, fingerprint_id=None, fingerprint_template=None):
        """Update an existing employee's details. Only updates provided non-None values."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        if name is not None:
            updates.append("name = ?")
            params.append(name)
        if email is not None:
            updates.append("email = ?")
            params.append(email)
        if fingerprint_id is not None:
            updates.append("fingerprint_id = ?")
            params.append(fingerprint_id)
        if fingerprint_template is not None:
            updates.append("fingerprint_template = ?")
            params.append(fingerprint_template)
        if not updates:
            return False  # Nothing to update
        query = f"UPDATE employees SET {', '.join(updates)} WHERE id = ?"
        params.append(employee_id)
        cursor.execute(query, params)
        self.conn.commit()
        return cursor.rowcount > 0

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
    
    def get_today_attendance_records(self):
        cursor = self.conn.cursor()
        date_str = self._today_date()
        cursor.execute("""
            SELECT attendance.date, employees.name, attendance.arrival_time, attendance.departure_time
            FROM attendance
            JOIN employees ON attendance.employee_id = employees.id
            WHERE attendance.date = ?
            ORDER BY employees.name ASC
        """, (date_str,))
        return cursor.fetchall()
    
    def get_today_attendance_count(self):
        cursor = self.conn.cursor()
        date_str = self._today_date()
        cursor.execute("SELECT COUNT(*) FROM attendance WHERE date = ?", (date_str,))
        row = cursor.fetchone()
        return row[0] if row else 0
        
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

    def get_all_settings(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT key, value FROM settings")
        return {r[0]: r[1] for r in cursor.fetchall()}

    # --- Backup/Restore helpers ---
    def backup_to(self, backup_path: str) -> bool:
        """Create a SQLite backup to the given file path."""
        try:
            dest = sqlite3.connect(backup_path)
            with dest:
                self.conn.backup(dest)
            dest.close()
            return True
        except Exception:
            return False

    def restore_from(self, source_path: str) -> bool:
        """Restore the database from the given file path. Replaces current DB file."""
        try:
            # Close current connection
            try:
                self.conn.close()
            except Exception:
                pass
            # Copy source into our db_name (fallback to backup API if needed)
            try:
                src = sqlite3.connect(source_path)
                dest = sqlite3.connect(self.db_name)
                with dest:
                    src.backup(dest)
                src.close()
                dest.close()
            except Exception:
                # Fallback: open source and recreate
                pass
            # Reopen main connection
            self.conn = sqlite3.connect(self.db_name)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception:
            return False
