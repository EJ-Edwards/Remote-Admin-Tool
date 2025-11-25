import socket
import os
import platform
import getpass
import subprocess
import time

def handle_command(command):
    command = command.strip()

    try:
        if command == "whoami":
            return getpass.getuser()

        elif command == "hostname":
            return platform.node()

        elif command == "sysinfo":
            return f"OS: {platform.system()} {platform.release()}\nProcessor: {platform.processor()}"

        elif command == "list_processes":
            return subprocess.getoutput("tasklist" if os.name == "nt" else "ps -e")

        elif command in ["ls", "dir"]:
            return "\n".join(os.listdir(os.getcwd()))

        elif command == "pwd":
            return os.getcwd()

        elif command.startswith("cd "):
            path = command[3:].strip()
            os.chdir(path)
            return f"Changed directory to {os.getcwd()}"

        elif command.startswith("read_file "):
            path = command[10:].strip()
            with open(path, "r") as f:
                return f.read()

        elif command.startswith("write_file "):
            _, path, content = command.split(" ", 2)
            with open(path, "w") as f:
                f.write(content)
            return f"Wrote to {path}"

        elif command.startswith("delete_file "):
            path = command[12:].strip()
            os.remove(path)
            return f"Deleted {path}"

        elif command.startswith("mkdir "):
            path = command[6:].strip()
            os.mkdir(path)
            return f"Created {path}"

        elif command == "disk_usage":
            usage = os.statvfs(os.getcwd())
            total = usage.f_blocks * usage.f_frsize
            free = usage.f_bfree * usage.f_frsize
            used = total - free
            return f"Total: {total // (1024**3)} GB\nUsed: {used // (1024**3)} GB\nFree: {free // (1024**3)} GB"

        elif command == "uptime":
            return subprocess.getoutput("systeminfo | find \"System Boot Time\"" if os.name == "nt" else "uptime -p")

        elif command == "shutdown":
            return "[!] Shutdown disabled for demo"

        else:
            return subprocess.getoutput(command)

    except Exception as e:
        return f"Error: {e}"


def start_client(server_ip, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_ip, server_port))
    except:
        print("[!] Could not connect to server.")
        return

    auth_msg = client.recv(1024).decode()
    if auth_msg != "AUTH_REQ":
        print("[!] Invalid authentication handshake.")
        client.close()
        return

    pin = input("Enter PIN: ").strip()
    client.send(pin.encode())

    if client.recv(1024).decode() != "AUTH_OK":
        print("[!] Authentication failed.")
        client.close()
        return

    print("[+] Authenticated.\nListening for commands...\n")

    while True:
        try:
            data = client.recv(4096)
            if not data:
                break
            command = data.decode()
            output = handle_command(command)
            client.send(output.encode())
        except:
            break

    print("[-] Disconnected.")
    client.close()


if __name__ == "__main__":
    server_ip = input("Server IP: ").strip()
    server_port = int(input("Server Port: ").strip())
    start_client(server_ip, server_port)
