import customtkinter
from fingerprint import FingerprintManager
import os
import subprocess
from PIL import Image, ImageTk


class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        self.title("Attendance System")
        self.geometry("800x480")

        # Initialize fingerprint manager
        self.fp_manager = FingerprintManager()

        # Create a container to hold frames
        self.container = customtkinter.CTkFrame(self)
        self.container.pack(fill="both", expand=True)

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
        self.label.pack(pady=20)

        self.image_label = customtkinter.CTkLabel(self)
        self.image_label.pack(pady=20)

        self.result_label = customtkinter.CTkLabel(self, text="", font=("Arial", 16))
        self.result_label.pack(pady=10)

        self.start_button = customtkinter.CTkButton(self, text="Start Verification", command=self.start_verification)
        self.start_button.pack(pady=20)

        # Animation attributes
        self.gif_path = "Animation/fingerprint.gif"  # Path to your GIF file
        self.gif = None
        self.gif_index = 0
        self.animation_running = False

    def load_gif(self):
        """Load the GIF into a PIL object."""
        self.gif = Image.open(self.gif_path)

    def start_animation(self):
        """Start the fingerprint scanning animation."""
        if not self.gif:
            self.load_gif()

        self.animation_running = True
        self.update_animation_frame()

    def update_animation_frame(self):
        """Update the current frame of the GIF."""
        if self.animation_running and self.gif:
            try:
                # Select frame and update image
                self.gif.seek(self.gif_index)
                frame_image = ImageTk.PhotoImage(self.gif)
                self.image_label.configure(image=frame_image)
                self.image_label.image = frame_image

                # Move to the next frame
                self.gif_index += 1
                self.after(100, self.update_animation_frame)  # Adjust speed as needed
            except EOFError:
                # Restart GIF animation
                self.gif_index = 0
                if self.animation_running:
                    self.update_animation_frame()

    def stop_animation(self):
        """Stop the fingerprint scanning animation."""
        self.animation_running = False
        self.image_label.configure(image="")  # Clear the animation

    def start_verification(self):
        """Start fingerprint verification."""
        self.label.configure(text="Checking fingerprint...")
        self.start_animation()

        # Simulate fingerprint scanning process
        self.after(3000, self.verify_fingerprint)  # Simulate a delay for scanning (3 seconds)

    def verify_fingerprint(self):
        """Verify the fingerprint after scanning."""
        self.stop_animation()

        finger_id = self.app.fp_manager.search_fingerprint()
        if finger_id is None:
            self.result_label.configure(text="No match found. Try again.", text_color="red")
        else:
            # Check if the fingerprint ID corresponds to an admin
            if self.is_admin(finger_id):
                self.result_label.configure(text=f"Admin detected (ID: {finger_id}).", text_color="green")
                self.app.show_frame(AdminFrame)  # Switch to AdminFrame
            else:
                self.result_label.configure(text=f"Attendance recorded (ID: {finger_id}).", text_color="blue")
                self.record_attendance(finger_id)

        # Reset label for next scan
        self.label.configure(text="Place your finger on the sensor again.")

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
