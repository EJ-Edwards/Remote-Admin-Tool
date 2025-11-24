import os
import textwrap

from server import start_server
from client import start_client

TERMS = """
Sentinel Link — Terms of Service
--------------------------------

By using Sentinel Link, you agree to the following terms:

1. You will NOT use Sentinel Link for any illegal, harmful, or unethical activity.
2. You will NOT use Sentinel Link to spy on individuals, monitor anyone without their
   explicit consent, or engage in any type of unauthorized surveillance.
3. You will NOT modify, alter, fork, or repurpose this code for the purpose of spying,
   surveillance, stalking, harassment, or gaining unauthorized access to systems,
   devices, networks, or data.
4. You will NOT use this software to access or interact with any system or device that
   you do not own or have explicit authorization to use.
5. You understand that misuse of this software may violate local, state, federal, or
   international laws. You accept full legal responsibility for your actions.
6. You acknowledge that the developers of Sentinel Link are not liable for any damages,
   legal consequences, or losses resulting from improper or unlawful use.
7. You agree to use this software strictly for legitimate, authorized, and ethical
   purposes only.

Please read these terms carefully before continuing.
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
        start_client()   

if __name__ == "__main__":
    main()
