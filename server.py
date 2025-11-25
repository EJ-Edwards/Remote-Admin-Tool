import socket
import threading
import ctypes
import random 
import string

def generate_password(length = 20):
    chars = string.ascii_letters + string.digits + "!@#$%^&*()_+=-{}[];:<>,.?/"
    return "".join(random.sample(chars, length))

PIN = generate_password()
print(f"Generated PIN: {PIN}")


clients = {}  
clientscmds = {
    "sysinfo": "Get OS, username, uptime, CPU/RAM info",
    "list_processes": "List running processes",
    "hostname": "Get machine hostname",
    "ls": "List directory contents",
    "cd": "Change directory",
    "pwd": "Show current directory",
    "read_file": "Read file contents",
    "write_file": "Write to a file",
    "delete_file": "Delete a file",
    "mkdir": "Create a directory",
    "disk_usage": "Show disk usage",
    "whoami": "Return current username",
    "uptime": "Return system uptime",
    "shutdown": "Shut down the client program or perform a safe system shutdown (only on machines you own)"
}


def logo():
    print(r"""
  ____             _   _            _ _     _       _    
 / ___|  ___ _ __ | |_(_)_ __   ___| | |   (_)_ __ | | __
 \___ \ / _ \ '_ \| __| | '_ \ / _ \ | |   | | '_ \| |/ /
  ___) |  __/ | | | |_| | | | |  __/ | |___| | | | |   < 
 |____/ \___|_| |_|\__|_|_| |_|\___|_|_____|_|_| |_|_|\_\
    """)


def handle_client(client_socket, addr):
    clients[addr] = client_socket
    ctypes.windll.kernel32.SetConsoleTitleW(
        f"Connected Clients: {len(clients)}"
    )

    print(f"[+] New client connected: {addr}")

    while True:
        try:
            data = client_socket.recv(4096)
            if not data:
                break

            decoded = data.decode("utf-8", errors="ignore")
            print(f"[{addr}] {decoded}")

        except Exception as e:
            print(f"[!] Error from {addr}: {e}")
            break

    print(f"[-] Client disconnected: {addr}")
    del clients[addr]
    client_socket.close()

    ctypes.windll.kernel32.SetConsoleTitleW(
        f"Connected Clients: {len(clients)}"
    )


def send_commands():
    """Allows server operator to send commands to a selected client."""
    while True:
        if not clients:
            continue

        cmd = input("CMD> ")

        if cmd.strip() == "":
            continue

        # broadcast to all clients for now
        for addr, sock in clients.items():
            try:
                sock.send(cmd.encode())
            except:
                pass


def start_server():
    logo()

    host = "0.0.0.0"
    port = 8888

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((host, port))
    server.listen(5)

    print(f"[+] Server started on {host}:{port}")

    threading.Thread(target=send_commands, daemon=True).start()

    while True:
        client_socket, addr = server.accept()
        thread = threading.Thread(
            target=handle_client, args=(client_socket, addr)
        )
        thread.daemon = True
        thread.start()


if __name__ == "__main__":
    start_server()
