from server import start_server
from client import start_client
import textwrap
import os

TERMS = """
Sentinel Link — Terms of Service
--------------------------------
1. You will NOT use Sentinel Link illegally.
2. You must have permission before connecting any device.
3. Misuse may violate laws. You are responsible for your actions.
"""

def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")

def show_terms():
    clear_screen()
    print("\n" + textwrap.dedent(TERMS).strip() + "\n")

def accept_terms():
    show_terms()
    while True:
        c = input("Accept terms? (y/n): ").strip().lower()
        if c in ("y", "yes"):
            return True
        if c in ("n", "no"):
            return False
        print("Enter y or n.")

def main_menu():
    print("Select mode:")
    print("1) Server")
    print("2) Client")
    while True:
        c = input("Choice: ").strip()
        if c in ("1", "2"):
            return int(c)
        print("Enter 1 or 2.")

def main():
    if not accept_terms():
        print("Terms not accepted. Exiting.")
        return

    choice = main_menu()

    if choice == 1:
        start_server()
    else:
        ip = input("Server IP: ").strip()
        port = int(input("Server Port: ").strip())
        start_client(ip, port)

if __name__ == "__main__":
    main()
