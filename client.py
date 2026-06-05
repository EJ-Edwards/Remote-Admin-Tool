import hashlib
import hmac
import logging
import os
import platform
import getpass
import socket
import ssl
import subprocess
import tempfile
import threading
import time
import zipfile
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

MAX_TRANSFER_SIZE = 100 * 1024 * 1024
CHUNK_SIZE = 64 * 1024

ALLOWED_COMMANDS = frozenset({
    "whoami",
    "hostname",
    "sysinfo",
    "list_processes",
    "ls",
    "dir",
    "pwd",
    "uptime",
})


def _safe_path(path: str) -> Optional[str]:
    """Restrict file ops to the current working directory tree."""
    if not path or not path.strip():
        return None
    try:
        base = os.path.realpath(os.getcwd())
        resolved = os.path.realpath(os.path.abspath(path.strip()))
        if resolved == base or resolved.startswith(base + os.sep):
            return resolved
    except OSError as e:
        logger.warning("Path resolution failed: %s", e)
    return None


def handle_command(command: str) -> str:
    command = command.strip()
    if not command:
        return "Error: empty command"

    try:
        if command == "whoami":
            return getpass.getuser()
        if command == "hostname":
            return platform.node()
        if command == "sysinfo":
            return f"OS: {platform.system()} {platform.release()}\nProcessor: {platform.processor()}"
        if command == "list_processes":
            return subprocess.getoutput("tasklist" if os.name == "nt" else "ps -e")
        if command in ("ls", "dir"):
            return "\n".join(os.listdir(os.getcwd()))
        if command == "pwd":
            return os.getcwd()
        if command.startswith("cd "):
            path = command[3:].strip()
            safe = _safe_path(path)
            if not safe or not os.path.isdir(safe):
                return "Error: invalid or inaccessible directory"
            os.chdir(safe)
            return f"Changed directory to {os.getcwd()}"
        if command.startswith("read_file "):
            path = command[10:].strip()
            safe = _safe_path(path)
            if not safe or not os.path.isfile(safe):
                return "Error: invalid or inaccessible file"
            with open(safe, "r", errors="ignore") as f:
                return f.read()
        if command.startswith("write_file "):
            try:
                _, path, content = command.split(" ", 2)
            except ValueError:
                return "Error: usage write_file <path> <content>"
            safe = _safe_path(path)
            if not safe:
                return "Error: write denied — path must stay under working directory"
            with open(safe, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Wrote to {safe}"
        if command.startswith("delete_file "):
            path = command[12:].strip()
            safe = _safe_path(path)
            if not safe or not os.path.isfile(safe):
                return "Error: delete denied — invalid path"
            os.remove(safe)
            return f"Deleted {safe}"
        if command.startswith("mkdir "):
            path = command[6:].strip()
            safe = _safe_path(path)
            if not safe:
                return "Error: mkdir denied — path must stay under working directory"
            os.mkdir(safe)
            return f"Created folder: {safe}"
        if command == "uptime":
            return subprocess.getoutput("net stats workstation" if os.name == "nt" else "uptime -p")
        return f"Error: unknown command '{command.split()[0]}'. Allowed: {', '.join(sorted(ALLOWED_COMMANDS))}"
    except Exception as e:
        logger.exception("Command failed: %s", command)
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
    except OSError as e:
        logger.warning("Could not stat file %s: %s", path, e)
        return (False, 0)


def send_file_bytes(sock: socket.socket, original_path: str, file_path_on_disk: str) -> bool:
    is_ok, size = _file_size_ok(file_path_on_disk)
    if not is_ok:
        try:
            sock.sendall(f"FILE_ERROR:size_exceeded:{original_path}\n".encode())
        except OSError as e:
            logger.warning("Failed to send size error: %s", e)
        return False
    header = f"FILE_BEGIN:{original_path}:{size}\n"
    try:
        sock.sendall(header.encode())
        with open(file_path_on_disk, "rb") as f:
            while True:
                chunk = f.read(CHUNK_SIZE)
                if not chunk:
                    break
                sock.sendall(chunk)
        return True
    except OSError as e:
        logger.warning("File send failed: %s", e)
        try:
            sock.sendall(f"FILE_ERROR:send_failed:{original_path}:{e}\n".encode())
        except OSError:
            pass
        return False


def handle_file_request(sock: socket.socket, path: str):
    path = path.strip()
    if not path:
        sock.sendall(b"FILE_ERROR:empty_path\n")
        return
    safe = _safe_path(path)
    if not safe:
        sock.sendall(f"FILE_ERROR:access_denied:{path}\n".encode())
        return
    if os.path.isfile(safe):
        if send_file_bytes(sock, safe, safe):
            sock.sendall(f"FILE_STATUS:sent:{safe}\n".encode())
    elif os.path.isdir(safe):
        zip_path = None
        try:
            zip_path = _zip_folder_to_temp(safe)
            if send_file_bytes(sock, safe, zip_path):
                sock.sendall(f"FILE_STATUS:sent_zip:{safe}\n".encode())
        except OSError as e:
            sock.sendall(f"FILE_ERROR:zip_failed:{safe}:{e}\n".encode())
        finally:
            if zip_path and os.path.exists(zip_path):
                os.remove(zip_path)
    else:
        sock.sendall(f"FILE_ERROR:not_found:{path}\n".encode())


def _authenticate(client: socket.socket, auth_pin: str, msg: str) -> bool:
    if not msg.startswith("AUTH_REQ:"):
        logger.warning("Unexpected auth message: %s", msg[:32])
        return False
    nonce_hex = msg.split(":", 1)[1].strip()
    nonce = bytes.fromhex(nonce_hex)
    digest = hmac.new(auth_pin.encode(), nonce, hashlib.sha256).hexdigest()
    client.send(digest.encode())
    auth_reply = client.recv(1024).decode(errors="ignore").strip()
    return auth_reply == "AUTH_OK"


def start_client(
    server_ip: str,
    server_port: int,
    auth_pin: str,
    use_tls: bool = False,
):
    while True:
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.settimeout(7)
        try:
            client.connect((server_ip, server_port))
            if use_tls:
                ctx = ssl.create_default_context()
                client = ctx.wrap_socket(client, server_hostname=server_ip)
            client.settimeout(None)
            logger.info("Connected to %s", server_ip)
            msg = client.recv(1024).decode(errors="ignore").strip()
            if not _authenticate(client, auth_pin, msg):
                logger.warning("Auth failed on %s", server_ip)
                return
            logger.info("Authenticated on %s", server_ip)
            while True:
                data = client.recv(4096)
                if not data:
                    break
                text = data.decode(errors="ignore")
                for line in text.splitlines():
                    cmd = line.strip()
                    if not cmd:
                        continue
                    if cmd.startswith("FILE_REQ "):
                        handle_file_request(client, cmd[9:])
                    else:
                        output = handle_command(cmd)
                        client.sendall((output + "\n").encode(errors="ignore"))
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            logger.warning("Unconnectable to %s: %s", server_ip, e)
            time.sleep(20)
        except Exception as e:
            logger.exception("%s error: %s", server_ip, e)
            break
        finally:
            try:
                client.close()
            except OSError as e:
                logger.debug("Error closing client socket: %s", e)


if __name__ == "__main__":
    SERVERS = ["SERVER1", "SERVER2"]
    PORT = 9000
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
