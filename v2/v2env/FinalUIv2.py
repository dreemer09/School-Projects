import customtkinter
from fingerprint import FingerprintManager
import os
import subprocess
from datetime import datetime
import sqlite3
import time

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.attributes('-fullscreen', True)
        self.title("Attendance System")
        self.geometry("800x480")

        # Initialize fingerprint manager
        self.fp_manager = FingerprintManager()

        # Create a container to hold frames
        self.container = customtkinter.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

        # Centering all frames within the container
        self.container.grid_rowconfigure(0, weight=1)  # Top empty space
        self.container.grid_rowconfigure(1, weight=0)  # Centered content
        self.container.grid_rowconfigure(2, weight=1)  # Bottom empty space
        self.container.grid_columnconfigure(0, weight=1)  # Left empty space
        self.container.grid_columnconfigure(1, weight=0)  # Centered content
        self.container.grid_columnconfigure(2, weight=1)  # Right empty space

        # Frames dictionary to manage views
        self.frames = {}

        # Initialize all frames
        for F in (MainFrame, AdminFrame):
            frame = F(parent=self.container, app=self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        # Show the main frame initially
        self.show_frame(MainFrame)

    def show_frame(self, frame_class):
        """Display the requested frame."""
        frame = self.frames[frame_class]
        frame.tkraise()  # Bring the frame to the front


class MainFrame(customtkinter.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Main interface
        self.label = customtkinter.CTkLabel(self, text="Place your finger on the sensor", font=("Arial", 18))
        self.label.pack(pady=20,)

        self.image_label = customtkinter.CTkLabel(self)
        self.image_label.pack(pady=20)

        self.result_label = customtkinter.CTkLabel(self, text="", font=("Arial", 16))
        self.result_label.pack(pady=10)

        # Start the continuous verification loop
        self.continuous_verification()

    def continuous_verification(self):
        """Continuously check for fingerprint scans."""
        if self.fp_manager.wait_for_fingerprint():
            finger_id = self.app.fp_manager.search_fingerprint()
            if finger_id is not None:

                if self.is_admin(finger_id):
                    # Display admin-specific message
                    self.result_label.configure(text=f"Admin detected: {name}", text_color="green")
                    self.app.show_frame(AdminFrame)  # Switch to AdminFrame
                else:
                    # Check the current time period
                    current_time = datetime.now().time()
                    if self.is_time_in_period(current_time):
                        attendance_type = "time-in"
                    elif self.is_time_out_period(current_time):
                        attendance_type = "time-out"
                    else:
                        self.result_label.configure(
                            text="Outside of attendance hours.", text_color="orange"
                        )
                        return  # Skip processing if outside valid attendance times

                    # Process fingerprint match
                    name = self.get_name_by_id(finger_id)
                    if not name:
                        self.result_label.configure(
                            text="Error: Fingerprint ID not associated with a name.",
                            text_color="red"
                        )
                        return
                    
                    # Record attendance for normal user
                    self.result_label.configure(
                        text=f"{attendance_type.capitalize()} recorded for {name}.",
                        text_color="blue"
                    )
                    self.record_attendance(name, attendance_type)

                # Reset label after processing
                self.label.configure(text="Place your finger on the sensor again.")
            else:
                self.result_label.configure(text="No match found. Try again.", text_color="red")

            # Schedule the next check
            self.after(1000, self.continuous_verification)  # Adjust delay as needed

    def record_attendance(self, name, attendance_type):
        """Record attendance for the given user."""
        current_time = datetime.now()
        start_time, end_time = self.get_current_interval()

        # Check if an entry exists for the current interval
        with sqlite3.connect("attendance.db") as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM attendance
                WHERE name = ? AND type = ? AND timestamp BETWEEN ? AND ?
            """, (name, attendance_type, start_time, end_time))
            
            result = cursor.fetchone()

            if result:
                # Notify user that attendance has already been recorded
                self.result_label.configure(
                    text=f"{attendance_type.capitalize()} already recorded for {name}.",
                    text_color="orange"
                )
            else:
                # Insert new attendance record
                cursor.execute("""
                    INSERT INTO attendance (name, timestamp, type)
                    VALUES (?, ?, ?)
                """, (name, current_time, attendance_type))
                conn.commit()

                # Notify user of successful attendance recording
                self.result_label.configure(
                    text=f"{attendance_type.capitalize()} recorded for {name}.",
                    text_color="blue"
                )

    def get_current_interval(self):
        """Get the current attendance interval."""
        now = datetime.now()
        time_intervals = {
            "morning_time_in": (time(8, 0), time(11, 59)),
            "midday_time_out": (time(12, 0), time(12, 59)),
            "afternoon_time_in": (time(13, 0), time(16, 59)),
            "evening_time_out": (time(17, 0), time(18, 0)),
        }

        for start, end in time_intervals.values():
            if start <= now.time() <= end:
                # Return start and end as datetime objects
                return datetime.combine(now.date(), start), datetime.combine(now.date(), end)

        return None, None  # Return None if outside defined intervals

    def is_time_in_period(self, current_time):
        """Check if current time falls in a time-in period."""
        return any(
            start <= current_time <= end
            for start, end in [(time(8, 0), time(11, 59)), (time(13, 0), time(16, 59))]
        )

    def is_time_out_period(self, current_time):
        """Check if current time falls in a time-out period."""
        return any(
            start <= current_time <= end
            for start, end in [(time(12, 0), time(12, 59)), (time(17, 0), time(18, 0))]
        )


    def is_admin(self, finger_id):
        """Determine if the fingerprint ID belongs to an admin."""
        admin_ids = [1, 2]  # Replace with actual admin IDs
        return finger_id in admin_ids

    def record_attendance(self, finger_id):
        """Record attendance for the given fingerprint ID."""
        # Example: Add logic to record attendance in the database
        print(f"Attendance recorded for ID: {finger_id}")



class AdminFrame(customtkinter.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Admin interface
        self.label = customtkinter.CTkLabel(self, text="Admin Panel", font=("Arial", 18))
        self.label.pack(pady=20)

        self.enroll_button = customtkinter.CTkButton(self, text="Enroll New Fingerprint", command=self.enroll_fingerprint)
        self.enroll_button.pack(pady=10)

        self.clear_button = customtkinter.CTkButton(self, text="Clear All Fingerprints", command=self.clear_fingerprints)
        self.clear_button.pack(pady=10)

        self.delete_button = customtkinter.CTkButton(self, text="Delete Fingerprint", command=self.delete_fingerprint)
        self.delete_button.pack(pady=10)

        self.export_button = customtkinter.CTkButton(self, text="Export Database", command=self.export_database)
        self.export_button.pack(pady=10)

        self.back_button = customtkinter.CTkButton(self, text="Back to Main", command=lambda: self.app.show_frame(MainFrame))
        self.back_button.pack(pady=20)

    def enroll_fingerprint(self):
        """Enroll a new fingerprint."""
        self.label.configure(text="Enrolling new fingerprint...")

        # Open on-screen keyboard for name entry
        user_name = self.open_keyboard("Enter Name:")
        if not user_name:
            self.label.configure(text="Enrollment cancelled.")
            return

        self.label.configure(text="Place your finger on the sensor.")
        success = self.app.fp_manager.enroll_fingerprint()
        if success:
            self.label.configure(text=f"Fingerprint enrolled successfully for {user_name}.")
        else:
            self.label.configure(text="Failed to enroll fingerprint. Try again.")

    def clear_fingerprints(self):
        """Clear all fingerprints."""
        if self.app.fp_manager.clear_all_fingerprints():
            self.label.configure(text="All fingerprints cleared.")
        else:
            self.label.configure(text="Failed to clear fingerprints.")

    def delete_fingerprint(self):
        """Delete a specific fingerprint."""
        finger_id = self.open_keyboard("Enter Fingerprint ID to delete:")
        if finger_id and self.app.fp_manager.delete_fingerprint(int(finger_id)):
            self.label.configure(text=f"Fingerprint ID {finger_id} deleted.")
        else:
            self.label.configure(text=f"Failed to delete Fingerprint ID {finger_id}.")

    def export_database(self):
        """Export the attendance database."""
        self.label.configure(text="Database exported!")
        # Example: Add logic to export the database

    def open_keyboard(self, prompt):
        """Open an on-screen keyboard for user input."""
        # Launch matchbox keyboard
        subprocess.call("matchbox-keyboard &", shell=True)
        return customtkinter.CTkInputDialog(text=prompt, title="Input").get_input()


if __name__ == "__main__":
    app = App()
    app.mainloop()
