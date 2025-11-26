import socket
import os
import platform
import getpass
import subprocess

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
            try:
                os.chdir(path)
                return f"Changed directory to {os.getcwd()}"
            except Exception as e:
                return f"Error changing directory: {e}"
        elif command.startswith("read_file "):
            path = command[10:].strip()
            try:
                with open(path, "r", errors="ignore") as f:
                    return f.read()
            except Exception as e:
                return f"Error reading file: {e}"
        elif command.startswith("write_file "):
            try:
                _, path, content = command.split(" ", 2)
                with open(path, "w") as f:
                    f.write(content)
                return f"Wrote to {path}"
            except Exception as e:
                return f"Error writing file: {e}"
        elif command.startswith("delete_file "):
            path = command[12:].strip()
            try:
                os.remove(path)
                return f"Deleted {path}"
            except Exception as e:
                return f"Error deleting file: {e}"
        elif command.startswith("mkdir "):
            try:
                path = command[6:].strip()
                os.mkdir(path)
                return f"Created folder: {path}"
            except Exception as e:
                return f"Error creating folder: {e}"
        elif command == "disk_usage":
            try:
                usage = os.statvfs(os.getcwd())
                total = usage.f_blocks * usage.f_frsize
                free = usage.f_bfree * usage.f_frsize
                used = total - free
                return f"Total: {total // (1024**3)} GB\nUsed: {used // (1024**3)} GB\nFree: {free // (1024**3)} GB"
            except:
                return "Disk usage not supported on this OS."
        elif command == "uptime":
            if os.name == "nt":
                return subprocess.getoutput("net stats workstation")
            else:
                return subprocess.getoutput("uptime -p")
        else:
            return subprocess.getoutput(command)
    except Exception as e:
        return f"Error: {e}"

def start_client(server_ip, server_port):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_ip, server_port))
        print("[+] Connected to server.")
    except:
        print("[!] Could not connect.")
        return

    # AUTH HANDSHAKE
    msg = client.recv(1024).decode()
    if msg != "AUTH_REQ":
        print("[!] Unexpected handshake.")
        return

    pin = input("Enter PIN: ").strip()
    client.send(pin.encode())

    auth_reply = client.recv(1024).decode()
    if auth_reply != "AUTH_OK":
        print("[!] Auth failed.")
        client.close()
        return

    print("[+] Authenticated. Waiting for commands...")

    while True:
        try:
            data = client.recv(4096)
            if not data:
                break
            command = data.decode(errors="ignore").strip()
            output = handle_command(command)
            client.send((output + "\n").encode(errors="ignore"))
        except:
            break

    print("[-] Disconnected.")
    client.close()

if __name__ == "__main__":
    server_ip = input("Server IP: ").strip()
    server_port = int(input("Server Port: ").strip())
    start_client(server_ip, server_port)
