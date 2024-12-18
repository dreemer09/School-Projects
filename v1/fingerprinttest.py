from fingerprint import FingerprintManager as fp

def main():
    fp_manager = fp()
    while True:
        command = input(
            "Enter '1' to enroll, '2' to find, '3' to delete, '4' to list fingerprints, '99' to clear flash storage '0' to quit: "
        ).strip()
        if command == "1":
            if fp_manager.enroll_fingerprint():
                print("Enrollment successful.")
        elif command == "2":
            finger_id = fp_manager.search_fingerprint()
            if finger_id is not None:
                print(f"Fingerprint found in database with ID {finger_id}.")
        elif command == "3":
            position = input("Enter the fingerprint ID to delete: ").strip()
            if position.isdigit():
                fp_manager.delete_fingerprint(int(position))
            else:
                print("Invalid ID. Please enter a numeric value.")
        elif command == "4":
            fp_manager.list_fingerprints()
        elif command == "99":
            fp_manager.clear_all_fingerprints()
        elif command == "0":
            print("Exiting...")
            break
        else:
            print("Invalid option. Please enter '1', '2', '3', '4', '99' or '0'.")


if __name__ == __main__():
    main() 