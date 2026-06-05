import os
import secrets
import string
import textwrap

from client import start_client
from server import start_server

TERMS = """
Sentinel Link — Terms of Service
--------------------------------
1. You must have explicit permission to connect any device.
2. Unauthorized use is strictly prohibited.
3. Misuse may violate laws. You are responsible for your actions.
"""


def clear_screen():
    os.system("cls" if os.name == "nt" else "clear")


def accept_terms():
    clear_screen()
    print(textwrap.dedent(TERMS))
    while True:
        c = input("Accept terms? (y/n): ").strip().lower()
        if c in ("y", "yes"):
            return True
        if c in ("n", "no"):
            return False
        print("Enter y or n.")


def generate_pin(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(secrets.choice(chars) for _ in range(length))


def main_menu():
    print("\nSelect mode:")
    print("1) Server")
    print("2) Client")
    print("3) Dropper")
    while True:
        choice = input("Choice: ").strip()
        if choice in ("1", "2", "3"):
            return int(choice)
        print("Enter 1, 2, or 3.")


def main():
    if not accept_terms():
        print("Terms not accepted. Exiting.")
        return

    mode = main_menu()

    if mode == 1:
        custom_pin = input("Custom PIN (leave blank to auto-generate): ").strip() or generate_pin()
        custom_port = input("Server port (default 8888): ").strip()
        custom_port = int(custom_port) if custom_port else 8888
        tls = input("Enable TLS for agent listener? (y/n): ").strip().lower() in ("y", "yes")
        certfile = keyfile = None
        if tls:
            certfile = input("Certificate file path: ").strip()
            keyfile = input("Private key file path: ").strip()
        start_server(custom_pin, custom_port, use_tls=tls, certfile=certfile, keyfile=keyfile)
    elif mode == 2:
        ip = input("Server IP: ").strip()
        port = int(input("Server Port: ").strip())
        pin = input("Server PIN: ").strip()
        if not pin:
            print("PIN is required.")
            return
        tls = input("Use TLS? (y/n): ").strip().lower() in ("y", "yes")
        start_client(ip, port, pin, use_tls=tls)
    else:
        from dropper import run_dropper_menu

        run_dropper_menu()


if __name__ == "__main__":
    main()
