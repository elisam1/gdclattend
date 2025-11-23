import os
import json
import re
from typing import List, Optional, Tuple


class CompanyManager:
    """Manages multi-company data isolation via per-company directories.

    Each company lives under `./companies/<slug>/` with:
    - `attendance.db` (SQLite file for that company)
    - `faces/` (face images and optional dlib encodings)

    The active company is tracked in `./active_company.json` at project root.
    """

    def __init__(self, root_dir: Optional[str] = None):
        self.root_dir = root_dir or os.getcwd()
        self.companies_dir = os.path.join(self.root_dir, "companies")
        os.makedirs(self.companies_dir, exist_ok=True)
        self.active_file = os.path.join(self.root_dir, "active_company.json")

    def _slugify(self, name: str) -> str:
        slug = re.sub(r"[^a-zA-Z0-9_-]+", "-", name.strip())
        slug = re.sub(r"-+", "-", slug).strip("-").lower()
        return slug or "company"

    def list_companies(self) -> List[str]:
        try:
            names = []
            for entry in os.listdir(self.companies_dir):
                path = os.path.join(self.companies_dir, entry)
                if os.path.isdir(path):
                    names.append(entry)
            return sorted(names)
        except Exception:
            return []

    def get_active(self) -> Tuple[str, str, str]:
        """Return (name, company_dir, faces_dir) of active company.

        If no active company is set, initialize a default one.
        """
        if os.path.isfile(self.active_file):
            try:
                with open(self.active_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                name = data.get("name") or "default"
                dir_path = data.get("dir") or os.path.join(self.companies_dir, self._slugify(name))
                faces_dir = os.path.join(dir_path, "faces")
                os.makedirs(dir_path, exist_ok=True)
                os.makedirs(faces_dir, exist_ok=True)
                return name, dir_path, faces_dir
            except Exception:
                pass

        # Initialize default company
        return self.set_active("default")

    def set_active(self, name: str) -> Tuple[str, str, str]:
        slug = self._slugify(name)
        company_dir = os.path.join(self.companies_dir, slug)
        faces_dir = os.path.join(company_dir, "faces")
        os.makedirs(company_dir, exist_ok=True)
        os.makedirs(faces_dir, exist_ok=True)
        # Persist active selection
        try:
            with open(self.active_file, "w", encoding="utf-8") as f:
                json.dump({"name": name, "dir": company_dir}, f)
        except Exception:
            pass
        return name, company_dir, faces_dir

    def get_paths_for(self, name: str) -> Tuple[str, str, str]:
        slug = self._slugify(name)
        company_dir = os.path.join(self.companies_dir, slug)
        faces_dir = os.path.join(company_dir, "faces")
        return name, company_dir, faces_dir

    def ensure_db_path(self, company_dir: str) -> str:
        """Return the SQLite DB path for the given company dir and ensure parent exists."""
        os.makedirs(company_dir, exist_ok=True)
        return os.path.join(company_dir, "attendance.db")

    def create_company(self, name: str) -> bool:
        """Create a new company directory structure.

        Returns True if the company directory exists or was created successfully.
        Does not change the active company.
        """
        try:
            slug = self._slugify(name)
            company_dir = os.path.join(self.companies_dir, slug)
            faces_dir = os.path.join(company_dir, "faces")
            os.makedirs(company_dir, exist_ok=True)
            os.makedirs(faces_dir, exist_ok=True)
            # Consider success if directories exist
            return os.path.isdir(company_dir) and os.path.isdir(faces_dir)
        except Exception:
            return False