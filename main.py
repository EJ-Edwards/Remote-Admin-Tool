from server import start_server
from client import start_client
import os, textwrap, random, string

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
        if c in ("y", "yes"): return True
        if c in ("n", "no"): return False
        print("Enter y or n.")

def generate_pin(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def main_menu():
    print("\nSelect mode:")
    print("1) Server")
    print("2) Client")
    while True:
        choice = input("Choice: ").strip()
        if choice in ("1","2"): return int(choice)
        print("Enter 1 or 2.")

def main():
    if not accept_terms():
        print("Terms not accepted. Exiting."); return

    mode = main_menu()

    if mode == 1:
        custom_pin = input("Custom PIN (leave blank to auto-generate): ").strip() or generate_pin()
        custom_port = input("Server port (default 8888): ").strip()
        custom_port = int(custom_port) if custom_port else 8888
        start_server(custom_pin, custom_port)
    else:
        ip = input("Server IP: ").strip()
        port = int(input("Server Port: ").strip())
        start_client(ip, port)

if __name__ == "__main__":
    main()
