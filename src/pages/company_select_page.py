import customtkinter as ctk
from tkinter import messagebox


class CompanySelectPage:
    def __init__(self, root, company_mgr, on_continue):
        self.root = root
        self.company_mgr = company_mgr
        self.on_continue = on_continue

        # Window setup
        self.root.title("Select Company - GDC Attendance System")
        self.root.geometry("500x420")

        self.primary_color = "#1a73e8"
        self.text_color = "#202124"

        self.frame = ctk.CTkFrame(self.root, fg_color="#ffffff")
        self.frame.pack(fill="both", expand=True, padx=20, pady=20)

        header = ctk.CTkLabel(
            self.frame,
            text="Select Company",
            font=("Segoe UI", 22, "bold"),
            text_color=self.text_color,
        )
        header.pack(pady=(8, 4))

        sub = ctk.CTkLabel(
            self.frame,
            text="Choose an existing company or create a new one",
            font=("Segoe UI", 12),
            text_color="#5f6368",
        )
        sub.pack(pady=(0, 16))

        # Existing companies dropdown
        self.dropdown_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.dropdown_frame.pack(fill="x", pady=(4, 12))

        ctk.CTkLabel(self.dropdown_frame, text="Companies:").pack(side="left", padx=(0, 10))

        try:
            active_name, _, _ = self.company_mgr.get_active()
            companies = self.company_mgr.list_companies() or []
            if active_name and active_name not in companies:
                companies.insert(0, active_name)
            if not companies:
                companies = ["default"]
        except Exception:
            active_name = "default"
            companies = ["default"]

        self.company_var = ctk.StringVar(value=active_name or companies[0])
        self.company_menu = ctk.CTkOptionMenu(self.dropdown_frame, values=companies, variable=self.company_var, width=240)
        self.company_menu.pack(side="left")

        # Create new company
        self.create_frame = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.create_frame.pack(fill="x", pady=(8, 4))

        ctk.CTkLabel(self.create_frame, text="New company name:").pack(side="left", padx=(0, 10))
        self.new_company_var = ctk.StringVar(value="")
        ctk.CTkEntry(self.create_frame, textvariable=self.new_company_var, width=240).pack(side="left")

        ctk.CTkButton(self.create_frame, text="Create", width=100, command=self._create_company).pack(side="left", padx=(10, 0))

        # Continue button
        self.actions = ctk.CTkFrame(self.frame, fg_color="transparent")
        self.actions.pack(fill="x", pady=(18, 0))

        ctk.CTkButton(
            self.actions,
            text="Continue",
            width=180,
            fg_color=self.primary_color,
            text_color="white",
            command=self._continue
        ).pack()

    def _refresh_companies(self):
        try:
            companies = self.company_mgr.list_companies() or []
            active_name, _, _ = self.company_mgr.get_active()
            if active_name and active_name not in companies:
                companies.insert(0, active_name)
            if not companies:
                companies = ["default"]
            self.company_menu.configure(values=companies)
            self.company_var.set(active_name or companies[0])
        except Exception:
            pass

    def _create_company(self):
        name = (self.new_company_var.get() or "").strip()
        if not name:
            messagebox.showerror("Company", "Please enter a company name.")
            return
        try:
            ok = self.company_mgr.create_company(name)
            if ok:
                messagebox.showinfo("Company", f"Company '{name}' created.")
                self.company_mgr.set_active(name)
                self._refresh_companies()
                self.company_var.set(name)
                self.new_company_var.set("")
            else:
                messagebox.showerror("Company", f"Could not create company '{name}'.")
        except Exception as e:
            messagebox.showerror("Company", f"Error creating company: {e}")

    def _continue(self):
        try:
            target = self.company_var.get()
            if not target:
                messagebox.showerror("Company", "Please select a company.")
                return
            # Set active and proceed
            self.company_mgr.set_active(target)
            if callable(self.on_continue):
                self.on_continue(target)
        except Exception as e:
            messagebox.showerror("Company", f"Failed to continue: {e}")