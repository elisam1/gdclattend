import customtkinter as ctk
from tkinter import messagebox, ttk

class UserManagementPage:
    def __init__(self, parent, db, colors, fonts):
        self.parent = parent
        self.db = db
        self.colors = colors
        self.fonts = fonts

    def show(self):
        self.clear_parent()
        self.current_frame = ctk.CTkFrame(self.parent, fg_color="transparent")
        self.current_frame.pack(expand=True, fill="both", padx=20, pady=20)

        self.create_page_header("User Management", "Manage system users and roles")

        # Add user section
        add_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        add_frame.pack(fill="x", pady=(0, 20))

        add_header = ctk.CTkLabel(
            add_frame,
            text="Add New User",
            font=self.fonts['subheader'],
            text_color=self.colors['text']
        )
        add_header.pack(anchor="w", padx=20, pady=15)

        fields_frame = ctk.CTkFrame(add_frame, fg_color="transparent")
        fields_frame.pack(fill="x", padx=20, pady=(0, 20))

        # Username field
        username_label = ctk.CTkLabel(fields_frame, text="Username:", anchor="w")
        username_label.grid(row=0, column=0, padx=5, pady=5)
        username_entry = ctk.CTkEntry(fields_frame, width=200)
        username_entry.grid(row=0, column=1, padx=5, pady=5)

        # Password field
        password_label = ctk.CTkLabel(fields_frame, text="Initial Password:", anchor="w")
        password_label.grid(row=0, column=2, padx=5, pady=5)
        password_entry = ctk.CTkEntry(fields_frame, width=200, show="•")
        password_entry.grid(row=0, column=3, padx=5, pady=5)

        # Role selection
        role_label = ctk.CTkLabel(fields_frame, text="Role:", anchor="w")
        role_label.grid(row=1, column=0, padx=5, pady=5)
        role_var = ctk.StringVar(value="staff")
        role_menu = ctk.CTkOptionMenu(
            fields_frame,
            values=["staff", "manager"],
            variable=role_var,
            width=200
        )
        role_menu.grid(row=1, column=1, padx=5, pady=5)

        def add_user():
            username = username_entry.get()
            password = password_entry.get()
            role = role_var.get()

            if not username or not password:
                messagebox.showerror("Error", "Please fill in all fields")
                return

            if len(password) < 6:
                messagebox.showerror("Error", "Password must be at least 6 characters")
                return

            try:
                self.db.add_user(username, password, role)
                messagebox.showinfo("Success", f"User {username} created successfully")
                username_entry.delete(0, 'end')
                password_entry.delete(0, 'end')
                self.refresh_user_list()
            except Exception as e:
                if "UNIQUE constraint" in str(e):
                    messagebox.showerror("Error", "Username already exists")
                else:
                    messagebox.showerror("Error", f"Failed to create user: {e}")

        add_btn = ctk.CTkButton(
            fields_frame,
            text="Add User",
            command=add_user,
            fg_color=self.colors['primary']
        )
        add_btn.grid(row=1, column=2, columnspan=2, padx=5, pady=5, sticky="ew")

        # Users list
        list_frame = ctk.CTkFrame(self.current_frame, fg_color="white", corner_radius=10)
        list_frame.pack(fill="both", expand=True)

        list_header = ctk.CTkLabel(
            list_frame,
            text="Existing Users",
            font=self.fonts['subheader'],
            text_color=self.colors['text']
        )
        list_header.pack(anchor="w", padx=20, pady=15)

        # Treeview for users
        columns = ("username", "role", "employee", "status", "actions")
        tree = ttk.Treeview(list_frame, columns=columns, show="headings", style="Treeview")

        tree.heading("username", text="Username")
        tree.heading("role", text="Role")
        tree.heading("employee", text="Linked Employee")
        tree.heading("status", text="Status")
        tree.heading("actions", text="Actions")

        tree.column("username", width=150)
        tree.column("role", width=100)
        tree.column("employee", width=200)
        tree.column("status", width=100)
        tree.column("actions", width=100)

        def refresh_user_list():
            for item in tree.get_children():
                tree.delete(item)

            users = self.db.get_all_users()
            for user in users:
                status = "First Login" if user['first_login'] else "Active"
                # Use the database user id as the tree item id (iid) so actions can reference it
                tree.insert("", "end", iid=str(user['id']), values=(
                    user['username'],
                    user['role'],
                    user['employee_name'] or "-",
                    status,
                    "Delete"
                ))

        def on_tree_click(event):
            region = tree.identify("region", event.x, event.y)
            if region == "cell":
                column = tree.identify_column(event.x)
                item = tree.identify_row(event.y)
                if column == "#5":  # Actions column
                    if not item:
                        return
                    username = tree.item(item)['values'][0]
                    if messagebox.askyesno("Confirm Delete", f"Delete user {username}?"):
                        row_id = int(item)
                        if self.db.delete_user(row_id):
                            refresh_user_list()
                            messagebox.showinfo("Success", "User deleted")
                        else:
                            messagebox.showerror("Error", "Failed to delete user")

        tree.bind('<Button-1>', on_tree_click)
        tree.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        # Store refresh function
        self.refresh_user_list = refresh_user_list

        # Initial load
        refresh_user_list()

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
        separator = ttk.Separator(header_frame, orient="horizontal")
        separator.pack(fill="x", pady=(10, 0))

        return header_frame

    def clear_parent(self):
        for widget in self.parent.winfo_children():
            widget.destroy()
