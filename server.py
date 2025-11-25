import socket
import threading
import random
import string
import sys
import time

try:
    import ctypes
except ImportError:
    ctypes = None

# Allowed portfolio commands
clientscmds = {
    "sysinfo": "Get OS and processor info",
    "list_processes": "List running processes",
    "hostname": "Get machine hostname",
    "ls": "List directory contents",
    "cd": "Change directory",
    "pwd": "Show current directory",
    "disk_usage": "Show disk usage",
    "whoami": "Return current username",
    "uptime": "Show system uptime",
}

clients = {}
PIN = None

def logo():
    print(r"""
  ____             _   _            _ _     _       _    
 / ___|  ___ _ __ | |_(_)_ __   ___| | |   (_)_ __ | | __
 \___ \ / _ \ '_ \| __| | '_ \ / _ \ | |   | | '_ \| |/ / 
  ___) |  __/ | | | |_| | | | |  __/ | |___| | | | |   <  
 |____/ \___|_| |_|\__|_|_| |_|\___|_|_____|_|_| |_|_|\_\
    """)

def set_console_title(title: str):
    if ctypes:
        try:
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        except:
            pass
    else:
        sys.stdout.write(f"\x1b]0;{title}\x07")

def generate_pin(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))

def authenticate_client(sock):
    """Authenticate client using shared PIN."""
    sock.send(b"AUTH_REQ")
    received = sock.recv(1024).decode().strip()
    if received != PIN:
        sock.send(b"AUTH_FAIL")
        return False
    sock.send(b"AUTH_OK")
    return True

def handle_client(sock, addr):
    if not authenticate_client(sock):
        print(f"[!] Client {addr} failed authentication.")
        sock.close()
        return

    print(f"[+] Client authenticated: {addr}")
    clients[addr] = sock
    set_console_title(f"Clients Connected: {len(clients)}")

    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break
            output = data.decode(errors="ignore")
            print(f"[{addr}] Output:\n{output}\n")
        except:
            break

    print(f"[-] Client disconnected: {addr}")
    clients.pop(addr, None)
    sock.close()
    set_console_title(f"Clients Connected: {len(clients)}")

def command_sender():
    """Send commands to clients and handle input safely."""
    while True:
        if not clients:
            time.sleep(0.1)
            continue

        cmd = input("CMD> ").strip()
        if not cmd:
            continue

        if cmd not in clientscmds:
            print(f"[!] Invalid command. Available: {list(clientscmds.keys())}")
            continue

        for addr, sock in list(clients.items()):
            try:
                sock.send(cmd.encode())
            except:
                print(f"[!] Failed to send command to {addr}")

def start_server():
    global PIN
    PIN = generate_pin()
    print(f"[+] Your support PIN: {PIN}\nGive this PIN to the person you're helping.\n")
    
    logo()
    
    host = "0.0.0.0"
    port = 8888

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)
    print(f"[+] Server listening on {host}:{port}")

    threading.Thread(target=command_sender, daemon=True).start()

    while True:
        sock, addr = server.accept()
        print(f"[+] New connection from {addr}")
        threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()

if __name__ == "__main__":
    start_server()
