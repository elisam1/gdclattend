class Permissions:
    """
    Handles role-based permissions for the GDC Attendance System
    """
    
    # Define role-based permissions
    ROLE_PERMISSIONS = {
        'admin': {
            'view_dashboard': True,
            'add_employee': True,
            'view_employees': True,
            'edit_employees': True,
            'delete_employees': True,
            'mark_attendance': True,
            'view_attendance': True,
            'manage_users': True,
            'export_data': True
        },
        'manager': {
            'view_dashboard': True,
            'add_employee': True,
            'view_employees': True,
            'edit_employees': True,
            'delete_employees': False,
            'mark_attendance': True,
            'view_attendance': True,
            'manage_users': False,
            'export_data': True
        },
        'staff': {
            'view_dashboard': True,
            'add_employee': False,
            'view_employees': True,
            'edit_employees': False,
            'delete_employees': False,
            'mark_attendance': True,
            'view_attendance': True,
            'manage_users': False,
            'export_data': False
        }
    }
    
    @staticmethod
    def check_permission(role, permission):
        """
        Check if a role has a specific permission
        
        Args:
            role (str): User role (admin, manager, staff)
            permission (str): Permission to check
            
        Returns:
            bool: True if the role has the permission, False otherwise
        """
        if role not in Permissions.ROLE_PERMISSIONS:
            return False
            
        return Permissions.ROLE_PERMISSIONS.get(role, {}).get(permission, False)
    
    @staticmethod
    def get_visible_sidebar_items(role):
        """
        Get the sidebar items that should be visible for a specific role
        
        Args:
            role (str): User role (admin, manager, staff)
            
        Returns:
            list: List of visible sidebar items
        """
        all_items = ['Dashboard', 'Add Employee', 'View Employees', 'Mark Attendance', 'Attendance Records', 'User Management', 'Fingerprint Management']
        
        if role == 'admin':
            return all_items
        elif role == 'manager':
            return ['Dashboard', 'Add Employee', 'View Employees', 'Mark Attendance', 'Attendance Records', 'Fingerprint Management']
        elif role == 'staff':
            return ['Dashboard', 'Mark Attendance', 'Attendance Records']
        else:
            return ['Dashboard']


def has_permission(role, permission):
    """Compatibility wrapper for older callers that import has_permission.

    Delegates to Permissions.check_permission.
    """
    return Permissions.check_permission(role, permission)