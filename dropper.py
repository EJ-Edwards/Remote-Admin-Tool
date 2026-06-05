def create_dropper_menu():
    print("\n--- Dropper Menu ---")
    print("1) Create Dropper for Windows")
    print("2) Create Dropper for Linux")
    print("3) Create Dropper for macOS")
    print("4) Configure Dropper (Set Options)")
    print("5) Exit")

    option = input("Select an option: ")

    if option == "1":
        create_windows_dropper()
    elif option == "2":
        create_linux_dropper()
    elif option == "3":
        create_macos_dropper()
    elif option == "4":
        configure_dropper_options()
    elif option == "5":
        print("Exiting...")
        return False
    else:
        print("Invalid option. Please try again.")
    return True


def create_windows_dropper():
    print("\nCreating Windows Dropper...")
    print("Windows dropper creation process initiated (placeholder)")


def create_linux_dropper():
    print("\nCreating Linux Dropper...")
    print("Linux dropper creation process initiated (placeholder)")


def create_macos_dropper():
    print("\nCreating macOS Dropper...")
    print("macOS dropper creation process initiated (placeholder)")


def configure_dropper_options():
    print("\n--- Dropper Configuration ---")
    print("1) Set Listener Port")
    print("2) Set Command Timeout")
    print("3) Configure Persistence (Windows)")
    print("4) Back to Main Menu")

    config_option = input("Select an option: ")

    if config_option == "1":
        port = input("Enter listener port: ")
        print(f"Listener port set to: {port}")
    elif config_option == "2":
        timeout = input("Enter command timeout (seconds): ")
        print(f"Command timeout set to: {timeout}")
    elif config_option == "3":
        print("Persistence configuration (Windows only - be cautious)")
    elif config_option == "4":
        return
    else:
        print("Invalid option.")


def run_dropper_menu():
    while create_dropper_menu():
        pass


if __name__ == "__main__":
    run_dropper_menu()
