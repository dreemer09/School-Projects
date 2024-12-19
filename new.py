class MainFrame(customtkinter.CTkFrame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app

        # Main interface
        self.label = customtkinter.CTkLabel(self, text="Place your finger on the sensor", font=("Arial", 18))
        self.label.pack(pady=20)

        self.result_label = customtkinter.CTkLabel(self, text="", font=("Arial", 16))
        self.result_label.pack(pady=10)

        # Start the continuous verification loop
        self.continuous_verification()

    def continuous_verification(self):
        """Continuously check for fingerprint scans."""
        if self.app.fp_manager.wait_for_fingerprint():
            finger_id = self.app.fp_manager.search_fingerprint()

            if finger_id is not None:
                name = self.get_name_by_id(finger_id)
                if self.is_admin(finger_id):
                    # Display admin-specific message
                    self.result_label.configure(text=f"Admin detected: {name}", text_color="green")
                    self.app.show_frame(AdminFrame)  # Switch to AdminFrame
                else:
                    # Determine attendance type
                    current_time = datetime.now().time()
                    if self.is_time_in_period(current_time):
                        attendance_type = "time-in"
                    elif self.is_time_out_period(current_time):
                        attendance_type = "time-out"
                    else:
                        self.result_label.configure(text="Outside of attendance hours.", text_color="orange")
                        return  # Skip processing if outside valid attendance times
                    
                    # Record attendance
                    self.record_attendance(name, attendance_type)
            else:
                self.result_label.configure(text="No match found. Try again.", text_color="red")

        # Schedule the next check
        self.after(1000, self.continuous_verification)

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
            
            if cursor.fetchone():
                self.result_label.configure(
                    text=f"{attendance_type.capitalize()} already recorded for {name}.",
                    text_color="orange"
                )
            else:
                cursor.execute("""
                    INSERT INTO attendance (name, timestamp, type)
                    VALUES (?, ?, ?)
                """, (name, current_time, attendance_type))
                conn.commit()
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
                return datetime.combine(now.date(), start), datetime.combine(now.date(), end)
        return None, None  # Outside intervals

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

    def get_name_by_id(self, finger_id):
        """Get the name associated with a fingerprint ID."""
        # Example implementation. Replace with actual database lookup.
        return "John Doe" if finger_id == 1 else None

    def is_admin(self, finger_id):
        """Check if the fingerprint ID belongs to an admin."""
        admin_ids = [1, 2]  # Example admin IDs
        return finger_id in admin_ids
