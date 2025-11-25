import socket
import os
import platform
import getpass
import subprocess
import time

def handle_command(command):
    command = command.strip()
    
    if command == "whoami":
        return getpass.getuser()
    elif command == "hostname":
        return platform.node()
    elif command == "sysinfo":
        return f"OS: {platform.system()} {platform.release()}\nProcessor: {platform.processor()}"
    elif command == "list_processes":
        # Fallback: use 'tasklist' on Windows or 'ps -e' on Unix
        try:
            if os.name == "nt":
                return subprocess.getoutput("tasklist")
            else:
                return subprocess.getoutput("ps -e")
        except Exception as e:
            return f"Error: {e}"
    elif command in ["ls", "dir"]:
        try:
            return "\n".join(os.listdir(os.getcwd()))
        except Exception as e:
            return f"Error: {e}"
    elif command == "pwd":
        return os.getcwd()
    elif command.startswith("cd "):
        path = command[3:].strip()
        try:
            os.chdir(path)
            return f"Changed directory to {os.getcwd()}"
        except Exception as e:
            return f"Error: {e}"
    elif command.startswith("read_file "):
        path = command[10:].strip()
        try:
            with open(path, "r") as f:
                return f.read()
        except Exception as e:
            return f"Error: {e}"
    elif command.startswith("write_file "):
        try:
            _, path, content = command.split(" ", 2)
            with open(path, "w") as f:
                f.write(content)
            return f"File {path} written successfully."
        except Exception as e:
            return f"Error: {e}"
    elif command.startswith("delete_file "):
        path = command[12:].strip()
        try:
            os.remove(path)
            return f"Deleted {path}"
        except Exception as e:
            return f"Error: {e}"
    elif command.startswith("mkdir "):
        path = command[6:].strip()
        try:
            os.mkdir(path)
            return f"Directory {path} created."
        except Exception as e:
            return f"Error: {e}"
    elif command == "disk_usage":
        try:
            usage = os.statvfs(os.getcwd())
            total = usage.f_blocks * usage.f_frsize
            free = usage.f_bfree * usage.f_frsize
            used = total - free
            return f"Total: {total // (1024**3)} GB\nUsed: {used // (1024**3)} GB\nFree: {free // (1024**3)} GB"
        except Exception as e:
            return f"Error: {e}"
    elif command == "uptime":
        try:
            if os.name == "nt":
                # Windows uptime (using systeminfo)
                output = subprocess.getoutput("systeminfo | find \"System Boot Time\"")
                return output if output else "[!] Could not determine uptime"
            else:
                # Unix uptime
                return subprocess.getoutput("uptime -p")
        except Exception as e:
            return f"Error: {e}"
    elif command == "shutdown":
        return "[!] Shutdown disabled for portfolio demo"
    else:
        try:
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
        print("[!] Unexpected server response.")
        client.close()
        return

    pin = input("Enter support PIN: ").strip()
    client.send(pin.encode())

    auth_response = client.recv(1024).decode()
    if auth_response != "AUTH_OK":
        print("[!] Authentication failed.")
        client.close()
        return

    print("[+] Authenticated. Waiting for commands...\n")

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

    print("[-] Disconnected from server.")
    client.close()

if __name__ == "__main__":
    server_ip = input("Server IP: ").strip()
    server_port = int(input("Server Port: ").strip())
    start_client(server_ip, server_port)
