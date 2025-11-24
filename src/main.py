import os
import textwrap

TERMS = """
Sentinel Link — Terms of Service
--------------------------------
1. You agree to use this software responsibly and lawfully.
2. You understand that no guarantees of uptime or data retention are provided.
3. You accept that misuse or unauthorized access attempts may result in termination.
4. You acknowledge that logs may be stored for security and debugging purposes.
5. You accept all risks associated with the use of this software.

Please read carefully before continuing.
"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def show_terms():
    clear_screen()
    print("\n" + textwrap.dedent(TERMS).strip() + "\n")

def accept_terms() -> bool:
    """Ask user to accept ToS. Returns True/False."""
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
    """Show server/client selection. Returns 1 or 2."""

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
        # import server and run it
        # from server import start_server
        # start_server()

    elif mode == 2:
        print("Starting client...")
        # import client and run it
        # from client import start_client
        # start_client()

if __name__ == "__main__":
    main()
