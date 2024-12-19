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