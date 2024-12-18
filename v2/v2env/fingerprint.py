import serial
import adafruit_fingerprint


class FingerprintManager:
    def __init__(self, port="/dev/ttyS1", baudrate=57600):
        self.uart = serial.Serial(port, baudrate=baudrate, timeout=1)
        self.finger = adafruit_fingerprint.Adafruit_Fingerprint(self.uart)

    def find_empty_slot(self):
        """Find the next available fingerprint slot."""
        for slot in range(1, 128):  # 128 is the max capacity for most fingerprint modules
            if self.finger.read_templates() == adafruit_fingerprint.OK:
                if slot not in self.finger.templates:
                    return slot
        return None

    def enroll_fingerprint(self):
        """Enroll a new fingerprint."""
        print("Place your finger on the sensor...")
        if self.finger.get_image() != adafruit_fingerprint.OK:
            print("Fingerprint not detected. Please try again.")
            return False
        
        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("Error processing fingerprint. Please try again.")
            return False
        
        if self.finger.get_image() != adafruit_fingerprint.OK:
            return False
        if self.finger.image_2_tz(2) != adafruit_fingerprint.OK:
            return False
        
        if self.finger.finger_fast_search() == adafruit_fingerprint.OK:
            print("Already enrolled!")
            return False

        if self.finger.create_model() != adafruit_fingerprint.OK:
            print("Failed to create a fingerprint model.")
            return False

        position = self.find_empty_slot()
        if position is None:
            print("No available slots for new fingerprints.")
            return False

        if self.finger.store_model(position) == adafruit_fingerprint.OK:
            print(f"Fingerprint successfully enrolled at position {position}.")
            return True
        else:
            print("Failed to store fingerprint.")
            return False

    def search_fingerprint(self):
        """Search for a fingerprint."""
        print("Place your finger on the sensor...")
        if self.finger.get_image() != adafruit_fingerprint.OK:
            print("Fingerprint not detected.")
            return None
        if self.finger.image_2_tz(1) != adafruit_fingerprint.OK:
            print("Error processing fingerprint.")
            return None

        if self.finger.finger_fast_search() == adafruit_fingerprint.OK:
            print(f"Fingerprint found! ID: {self.finger.finger_id}, Confidence: {self.finger.confidence}")
            return self.finger.finger_id
        else:
            print("No match found.")
            return None

    def delete_fingerprint(self, position):
        """Delete a fingerprint by its ID."""
        if self.finger.delete_model(position) == adafruit_fingerprint.OK:
            print(f"Fingerprint at position {position} successfully deleted.")
            return True
        else:
            print(f"Failed to delete fingerprint at position {position}.")
            return False

    def list_fingerprints(self):
        """List all stored fingerprints."""
        if self.finger.read_templates() == adafruit_fingerprint.OK:
            print("Stored Fingerprints:", self.finger.templates)
        else:
            print("Failed to read templates.")

    def clear_all_fingerprints(self):
        """Clear all fingerprints from the library."""
        print("Clearing all fingerprints from the library...")
        if self.empty_library() == adafruit_fingerprint.OK:
            print("All fingerprints have been successfully deleted.")
            return True
        else:
            print("Failed to clear fingerprints. Please try again.")
            return False
