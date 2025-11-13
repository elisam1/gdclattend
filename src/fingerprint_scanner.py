import serial
import serial.tools.list_ports
from pyfingerprint.pyfingerprint import PyFingerprint
import time

class FingerprintScanner:
    def __init__(self, port='/dev/ttyUSB0', baudrate=57600, address=0xFFFFFFFF, password=0x00000000):
        """
        Initialize the fingerprint scanner.

        Args:
            port: Serial port where the scanner is connected
            baudrate: Communication baudrate
            address: Device address
            password: Device password
        """
        self.port = port
        self.baudrate = baudrate
        self.address = address
        self.password = password
        self.fingerprint = None
        self.connected = False

    def connect(self):
        """Establish connection to the fingerprint scanner."""
        try:
            # Initialize serial connection
            serial_conn = serial.Serial(
                port=self.port,
                baudrate=self.baudrate,
                timeout=1
            )

            # Initialize fingerprint sensor
            self.fingerprint = PyFingerprint(
                serial_conn,
                self.address,
                self.password
            )

            if self.fingerprint.verifyPassword():
                self.connected = True
                return True
            else:
                print("Fingerprint sensor password verification failed")
                return False

        except Exception as e:
            print(f"Failed to connect to fingerprint scanner: {e}")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from the fingerprint scanner."""
        if self.fingerprint and hasattr(self.fingerprint, '_serial'):
            try:
                self.fingerprint._serial.close()
            except:
                pass
        self.connected = False

    def test_connection(self):
        """Attempt to connect and immediately disconnect to verify connectivity."""
        ok = self.connect()
        try:
            self.disconnect()
        except Exception:
            pass
        return ok

    def enroll_fingerprint(self):
        """
        Enroll a new fingerprint.

        Returns:
            tuple: (success, position_number, template_data) or (False, None, None)
        """
        if not self.connected:
            return False, None, None

        try:
            print("Place finger on scanner...")

            # Wait for finger
            while not self.fingerprint.readImage():
                time.sleep(0.1)

            # Convert image to characteristics
            self.fingerprint.convertImage(0x01)

            # Check if finger is already enrolled
            result = self.fingerprint.searchTemplate()
            position_number = result[0]

            if position_number >= 0:
                print(f"Fingerprint already exists at position #{position_number}")
                return False, position_number, None

            print("Remove finger...")
            time.sleep(2)

            print("Place same finger again...")

            # Wait for same finger again
            while not self.fingerprint.readImage():
                time.sleep(0.1)

            # Convert image to characteristics
            self.fingerprint.convertImage(0x02)

            # Create template
            self.fingerprint.createTemplate()

            # Get position number
            position_number = self.fingerprint.storeTemplate()

            # Get template data
            template_data = self.fingerprint.downloadCharacteristics(0x01)

            print(f"Fingerprint enrolled successfully at position #{position_number}")
            return True, position_number, template_data

        except Exception as e:
            print(f"Error during fingerprint enrollment: {e}")
            return False, None, None

    def verify_fingerprint(self):
        """
        Verify a fingerprint against stored templates.

        Returns:
            tuple: (success, position_number) or (False, None)
        """
        if not self.connected:
            return False, None

        try:
            print("Place finger on scanner...")

            # Wait for finger
            while not self.fingerprint.readImage():
                time.sleep(0.1)

            # Convert image to characteristics
            self.fingerprint.convertImage(0x01)

            # Search for template
            result = self.fingerprint.searchTemplate()
            position_number = result[0]
            accuracy_score = result[1]

            if position_number >= 0:
                print(f"Fingerprint found at position #{position_number} with accuracy {accuracy_score}")
                return True, position_number
            else:
                print("Fingerprint not found")
                return False, None

        except Exception as e:
            print(f"Error during fingerprint verification: {e}")
            return False, None

    def delete_fingerprint(self, position_number):
        """
        Delete a fingerprint template at the specified position.

        Args:
            position_number: Position of the template to delete

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            if self.fingerprint.deleteTemplate(position_number):
                print(f"Fingerprint at position #{position_number} deleted successfully")
                return True
            else:
                print(f"Failed to delete fingerprint at position #{position_number}")
                return False
        except Exception as e:
            print(f"Error deleting fingerprint: {e}")
            return False

    def get_template_count(self):
        """
        Get the number of stored templates.

        Returns:
            int: Number of stored templates, or -1 if error
        """
        if not self.connected:
            return -1

        try:
            return self.fingerprint.getTemplateCount()
        except Exception as e:
            print(f"Error getting template count: {e}")
            return -1

    def clear_database(self):
        """
        Clear all fingerprint templates from the sensor.

        Returns:
            bool: True if successful, False otherwise
        """
        if not self.connected:
            return False

        try:
            if self.fingerprint.clearDatabase():
                print("Fingerprint database cleared successfully")
                return True
            else:
                print("Failed to clear fingerprint database")
                return False
        except Exception as e:
            print(f"Error clearing database: {e}")
            return False

    @staticmethod
    def get_available_devices():
        """
        Get a list of available serial ports that might be fingerprint scanners.

        Returns:
            list: List of dictionaries with port info {'port': str, 'description': str}
        """
        ports = serial.tools.list_ports.comports()
        devices = []

        for port in ports:
            # Filter for common USB serial devices that might be fingerprint scanners
            description = str(getattr(port, 'description', '') or '').lower()
            if any(keyword in description for keyword in ['usb', 'serial', 'tty', 'com']):
                devices.append({
                    'port': port.device,
                    'description': port.description or f"Serial Port {port.device}",
                    'manufacturer': port.manufacturer or "Unknown",
                    'product': port.product or "Unknown"
                })

        return devices
