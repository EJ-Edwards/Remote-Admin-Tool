import socket
import os
import platform
import getpass
import subprocess
import tempfile
import zipfile
import sys
from typing import Tuple

# Maximum allowed file transfer size in bytes (adjust as needed). 500MB default.
MAX_TRANSFER_SIZE = 500 * 1024 * 1024

CHUNK_SIZE = 64 * 1024  # 64 KiB


def handle_command(command: str) -> str:
    """Return textual output for normal commands."""
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
            # For arbitrary shell commands, return output
            return subprocess.getoutput(command)
    except Exception as e:
        return f"Error: {e}"


def _zip_folder_to_temp(folder_path: str) -> str:
    """Create a temporary zip archive of folder_path and return the zip file path."""
    temp_fd, temp_path = tempfile.mkstemp(suffix=".zip")
    os.close(temp_fd)
    with zipfile.ZipFile(temp_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(folder_path):
            for f in files:
                full = os.path.join(root, f)
                # store the file path relative to the folder root
                arcname = os.path.relpath(full, start=folder_path)
                zf.write(full, arcname)
    return temp_path


def _file_size_ok(path: str) -> Tuple[bool, int]:
    """Return (is_ok, size) and check against MAX_TRANSFER_SIZE."""
    try:
        size = os.path.getsize(path)
        return (size <= MAX_TRANSFER_SIZE, size)
    except Exception:
        return (False, 0)


def send_file_bytes(sock: socket.socket, original_path: str, file_path_on_disk: str) -> bool:
    """
    Send a file in the required protocol:
      1) send header "FILE_BEGIN:<original_path>:<size>\\n"
      2) send exactly <size> bytes (raw)
    Returns True on success, False on failure.
    """
    is_ok, size = _file_size_ok(file_path_on_disk)
    if not is_ok:
        # send an error message back to server so it can log/notify
        try:
            sock.sendall(f"FILE_ERROR:size_exceeded:{original_path}\n".encode())
        except Exception:
            pass
        return False

    header = f"FILE_BEGIN:{original_path}:{size}\n"
    try:
        sock.sendall(header.encode())
        # stream the file in chunks
        with open(file_path_on_disk, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)
        # Optionally send a short confirmation line after bytes (server does not require it)
        # but avoid adding extra bytes that server might parse as file data.
        # Instead we rely on server to determine size and stop reading after `size` bytes.
        return True
    except Exception as e:
        try:
            sock.sendall(f"FILE_ERROR:send_failed:{original_path}:{e}\n".encode())
        except Exception:
            pass
        return False


def handle_file_request(sock: socket.socket, path: str):
    """
    Process FILE_REQ <path> from the server.
    If path is a file -> send exact bytes.
    If path is a folder -> zip and send the zip (then remove temp zip).
    """
    path = path.strip()
    if not path:
        try:
            sock.sendall(b"FILE_ERROR:empty_path\n")
        except Exception:
            pass
        return

    if os.path.isfile(path):
        ok = send_file_bytes(sock, path, path)
        if ok:
            try:
                sock.sendall(f"FILE_STATUS:sent:{path}\n".encode())
            except Exception:
                pass
        else:
            try:
                sock.sendall(f"FILE_STATUS:failed:{path}\n".encode())
            except Exception:
                pass
    elif os.path.isdir(path):
        # zip it first
        try:
            zip_path = _zip_folder_to_temp(path)
            ok = send_file_bytes(sock, zip_path, zip_path)
            # report and cleanup
            if ok:
                sock.sendall(f"FILE_STATUS:sent_zip:{path}\n".encode())
            else:
                sock.sendall(f"FILE_STATUS:failed_zip:{path}\n".encode())
        except Exception as e:
            try:
                sock.sendall(f"FILE_ERROR:zip_failed:{path}:{e}\n".encode())
            except Exception:
                pass
        finally:
            # remove the temp zip if it exists
            try:
                if 'zip_path' in locals() and os.path.exists(zip_path):
                    os.remove(zip_path)
            except Exception:
                pass
    else:
        try:
            sock.sendall(f"FILE_ERROR:not_found:{path}\n".encode())
        except Exception:
            pass


def start_client(server_ip: str, server_port: int):
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client.connect((server_ip, server_port))
        print("[+] Connected to server.")
    except Exception as e:
        print(f"[!] Could not connect: {e}")
        return

    # AUTH HANDSHAKE
    try:
        msg = client.recv(1024).decode()
    except Exception as e:
        print("[!] Handshake failed:", e)
        client.close()
        return

    if msg != "AUTH_REQ":
        print("[!] Unexpected handshake.")
        client.close()
        return

    pin = input("Enter PIN: ").strip()
    client.send(pin.encode())

    try:
        auth_reply = client.recv(1024).decode()
    except Exception as e:
        print("[!] Auth reply failed:", e)
        client.close()
        return

    if auth_reply != "AUTH_OK":
        print("[!] Auth failed.")
        client.close()
        return

    print("[+] Authenticated. Waiting for commands...")

    try:
        while True:
            data = client.recv(4096)
            if not data:
                break

            # Server may send multiple lines or a single command; parse robustly
            # We'll split on newline in case multiple commands were queued.
            text = data.decode(errors="ignore")
            lines = text.splitlines()
            for line in lines:
                cmd = line.strip()
                if not cmd:
                    continue

                # FILE request from server:
                if cmd.startswith("FILE_REQ "):
                    path = cmd[len("FILE_REQ "):].strip()
                    print(f"[+] Server requested file/folder: {path}")
                    handle_file_request(client, path)
                    # after handling, continue to next command
                    continue

                # Otherwise treat as a normal shell/utility command
                output = handle_command(cmd)
                # Always send textual outputs with a trailing newline for server parsing
                try:
                    client.sendall((output + "\n").encode(errors="ignore"))
                except Exception as e:
                    print("[!] Failed to send output:", e)
                    raise

    except KeyboardInterrupt:
        print("[-] Keyboard interrupt, exiting.")
    except Exception as e:
        print("[!] Error in command loop:", e)
    finally:
        print("[-] Disconnected.")
        try:
            client.close()
        except Exception:
            pass


if __name__ == "__main__":
    if len(sys.argv) >= 3:
        server_ip = sys.argv[1]
        server_port = int(sys.argv[2])
    else:
        server_ip = input("Server IP: ").strip()
        server_port = int(input("Server Port: ").strip())
    start_client(server_ip, server_port)
