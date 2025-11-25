from server import start_server
from client import start_client
import textwrap
import os


TERMS = """
Sentinel Link — Terms of Service
--------------------------------

1. You will NOT use Sentinel Link for illegal or unauthorized access.
2. You must have explicit permission before connecting any client.
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
        choice = input("Accept terms? (y/n): ").strip().lower()
        if choice in ("y", "yes"):
            return True
        if choice in ("n", "no"):
            return False
        print("Enter y or n.")


def main_menu():
    print("Select mode:")
    print("1) Server")
    print("2) Client")
    while True:
        choice = input("Choice: ").strip()
        if choice in ("1", "2"):
            return int(choice)
        print("Enter 1 or 2.")


def main():
    if not accept_terms():
        print("You must accept terms to continue.")
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
