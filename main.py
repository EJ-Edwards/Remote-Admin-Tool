import os
import textwrap

from server import start_server
from client import start_client


TERMS = """
Sentinel Link — Terms of Service
--------------------------------
(terms unchanged)
"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def show_terms():
    clear_screen()
    print("\n" + textwrap.dedent(TERMS).strip() + "\n")

def accept_terms() -> bool:
    show_terms()

    while True:
        accept = input("Do you accept these Terms and Conditions? (y/n): ").strip().lower()

        if accept in ("y", "yes"):
            print("\nThank you. You may now use Sentinel Link.\n")
            return True
        elif accept in ("n", "no"):
            print("\nYou must accept the Terms and Conditions to use Sentinel Link.\n")
            return False
        else:
            print("Invalid input. Please type 'y' or 'n'.\n")

def mode_menu() -> int:
    print("Select mode:")
    print("1) Run as Server")
    print("2) Run as Client\n")

    while True:
        choice = input("Enter choice (1/2): ").strip()

        if choice == "1":
            return 1
        elif choice == "2":
            return 2
        else:
            print("Invalid choice. Enter 1 or 2.\n")

def main():
    if not accept_terms():
        return

    mode = mode_menu()

    if mode == 1:
        print("Starting server...")
        start_server()

    elif mode == 2:
        print("Starting client...")
        server_ip = input("Enter server IP: ").strip()
        server_port = int(input("Enter server port: ").strip())

        start_client(server_ip, server_port)


if __name__ == "__main__":
    main()
