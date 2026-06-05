import hashlib
import hmac
import logging
import os
import secrets
import socket
import threading
from functools import wraps

from flask import Flask, jsonify, request, send_file, session

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

clients = {}
client_output = {}
PIN = None
lock = threading.Lock()
shutdown_event = threading.Event()
server_socket = None

EXPORT_DIR = "exports"
MAX_OUTPUT_LINES = 200
MAX_FILE_RECEIVE_BYTES = 100 * 1024 * 1024  # 100 MB server-side cap

os.makedirs(EXPORT_DIR, exist_ok=True)
EXPORT_DIR_REAL = os.path.realpath(EXPORT_DIR)

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY") or secrets.token_hex(32)
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

# -------------------------
#  DASHBOARD HTML (no inline user data — DOM built in JS via textContent)
# -------------------------
dashboard_html = """
<!DOCTYPE html>
<html>
<head>
<title>Sentinel Link Dashboard</title>
<style>
body { background:#111; color:#fff; font-family:Arial; padding:20px; }
.client-box { background:#222; padding:15px; border-radius:5px; margin-bottom:20px; }
textarea { width:100%; height:200px; background:#000; color:#0f0; padding:10px; border-radius:5px; }
input { width:75%; padding:8px; }
button { padding:8px; cursor:pointer; margin-right:6px; }
a { color:#4af; }
#login-panel { max-width:360px; margin:40px auto; padding:20px; background:#222; border-radius:8px; }
#app-panel { display:none; }
.error { color:#f66; font-size:14px; margin-top:8px; }
</style>
</head>
<body>
<div id="login-panel">
  <h1>Sentinel Link</h1>
  <p>Enter dashboard PIN to continue.</p>
  <input id="login-pin" type="password" placeholder="PIN" autocomplete="current-password">
  <button id="login-btn" type="button">Sign in</button>
  <p id="login-error" class="error"></p>
</div>
<div id="app-panel">
  <h1>Sentinel Link Dashboard</h1>
  <div id="client-list"></div>
</div>
<script>
function escId(addr) {
  return addr.replace(/[^a-zA-Z0-9._-]/g, "_");
}

async function apiFetch(path, options) {
  const res = await fetch(path, {
    credentials: "same-origin",
    headers: { "Content-Type": "application/json", ...(options && options.headers) },
    ...options,
  });
  if (res.status === 401) {
    document.getElementById("login-panel").style.display = "block";
    document.getElementById("app-panel").style.display = "none";
    throw new Error("Unauthorized");
  }
  return res;
}

async function login() {
  const pin = document.getElementById("login-pin").value;
  const err = document.getElementById("login-error");
  err.textContent = "";
  const res = await fetch("/api/login", {
    method: "POST",
    credentials: "same-origin",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ pin }),
  });
  if (!res.ok) {
    err.textContent = "Invalid PIN";
    return;
  }
  document.getElementById("login-panel").style.display = "none";
  document.getElementById("app-panel").style.display = "block";
  loadClients();
  setInterval(loadOutputs, 800);
}

document.getElementById("login-btn").addEventListener("click", login);

function buildClientBox(addr) {
  const box = document.createElement("div");
  box.className = "client-box";
  box.dataset.addr = addr;

  const title = document.createElement("strong");
  title.textContent = addr;
  box.appendChild(title);
  box.appendChild(document.createElement("br"));
  box.appendChild(document.createElement("br"));

  const out = document.createElement("textarea");
  out.id = "out-" + escId(addr);
  out.readOnly = true;
  box.appendChild(out);
  box.appendChild(document.createElement("br"));

  const cmd = document.createElement("input");
  cmd.id = "cmd-" + escId(addr);
  cmd.placeholder = "Enter command";
  box.appendChild(cmd);

  const sendBtn = document.createElement("button");
  sendBtn.type = "button";
  sendBtn.textContent = "Send";
  sendBtn.addEventListener("click", () => sendCmd(addr));
  box.appendChild(sendBtn);

  const exportBtn = document.createElement("button");
  exportBtn.type = "button";
  exportBtn.textContent = "Export File";
  exportBtn.addEventListener("click", () => exportFile(addr));
  box.appendChild(exportBtn);

  const dl = document.createElement("div");
  dl.id = "download-" + escId(addr);
  box.appendChild(dl);

  return box;
}

async function loadClients() {
  const res = await apiFetch("/api/clients");
  const data = await res.json();
  const container = document.getElementById("client-list");
  container.replaceChildren();
  for (const c of data.clients) {
    container.appendChild(buildClientBox(c));
  }
}

async function loadOutputs() {
  const res = await apiFetch("/api/output");
  const data = await res.json();
  for (const addr in data) {
    const id = "out-" + escId(addr);
    const box = document.getElementById(id);
    if (!box) continue;
    const shouldStick = box.scrollTop + box.clientHeight >= box.scrollHeight - 10;
    box.value = data[addr].join("\\n");
    if (shouldStick) box.scrollTop = box.scrollHeight;
  }
}

async function sendCmd(addr) {
  const id = "cmd-" + escId(addr);
  const cmd = document.getElementById(id).value;
  await apiFetch("/api/send", {
    method: "POST",
    body: JSON.stringify({ addr, command: cmd }),
  });
}

function exportFile(addr) {
  const path = prompt("Enter file or folder path to export:");
  if (!path) return;
  apiFetch("/api/send", {
    method: "POST",
    body: JSON.stringify({ addr, command: "FILE_REQ " + path }),
  });
  alert("File request sent. When the client sends it, a download link will appear.");
}
</script>
</body>
</html>
"""


def require_dashboard_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("authenticated"):
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)

    return decorated


def safe_export_path(filename: str):
    """Resolve download path and ensure it stays inside EXPORT_DIR."""
    if not filename or filename != os.path.basename(filename):
        return None
    candidate = os.path.join(EXPORT_DIR, filename)
    resolved = os.path.realpath(candidate)
    if not resolved.startswith(EXPORT_DIR_REAL + os.sep) and resolved != EXPORT_DIR_REAL:
        return None
    if not os.path.isfile(resolved):
        return None
    return resolved


def append_output(addr, line: str) -> None:
    with lock:
        lines = client_output.setdefault(addr, [])
        lines.append(line)
        if len(lines) > MAX_OUTPUT_LINES:
            client_output[addr] = ["[... older output truncated ...]"] + lines[-(MAX_OUTPUT_LINES - 1) :]


@app.route("/")
def home():
    return dashboard_html


@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    pin = data.get("pin")
    if not isinstance(pin, str) or pin != PIN:
        return jsonify({"error": "Invalid PIN"}), 401
    session["authenticated"] = True
    return jsonify({"status": "ok"})


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.clear()
    return jsonify({"status": "ok"})


@app.route("/api/clients")
@require_dashboard_auth
def api_clients():
    with lock:
        return jsonify({"clients": [f"{ip}:{port}" for (ip, port) in clients]})


@app.route("/api/output")
@require_dashboard_auth
def api_output():
    with lock:
        return jsonify({f"{ip}:{port}": lines for (ip, port), lines in client_output.items()})


@app.route("/api/send", methods=["POST"])
@require_dashboard_auth
def api_send():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return jsonify({"status": "error", "message": "Invalid JSON body"}), 400
    addr = data.get("addr")
    cmd = data.get("command")
    if not isinstance(addr, str) or not addr.strip():
        return jsonify({"status": "error", "message": "addr must be a non-empty string"}), 400
    if not isinstance(cmd, str) or not cmd.strip():
        return jsonify({"status": "error", "message": "command must be a non-empty string"}), 400

    with lock:
        for (ip, port), sock in clients.items():
            if f"{ip}:{port}" == addr:
                try:
                    sock.send((cmd + "\n").encode())
                    return jsonify({"status": "sent"})
                except OSError as e:
                    logger.warning("Send failed to %s: %s", addr, e)
                    return jsonify({"status": "send_error"}), 500
    return jsonify({"status": "not_found"}), 404


@app.route("/download/<path:filename>")
@require_dashboard_auth
def download(filename):
    safe_path = safe_export_path(filename)
    if not safe_path:
        return "Forbidden", 403
    return send_file(safe_path, as_attachment=True)


def authenticate(sock) -> bool:
    """HMAC challenge — PIN is never sent over the wire."""
    nonce = secrets.token_bytes(32)
    sock.send(b"AUTH_REQ:" + nonce.hex().encode())
    recv = sock.recv(128).decode(errors="ignore").strip()
    expected = hmac.new(PIN.encode(), nonce, hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, recv):
        sock.send(b"AUTH_FAIL")
        return False
    sock.send(b"AUTH_OK")
    return True


def handle_client(sock, addr):
    if not authenticate(sock):
        logger.warning("Auth failed: %s", addr)
        sock.close()
        return

    logger.info("Authenticated: %s", addr)

    with lock:
        clients[addr] = sock
        client_output[addr] = []

    buffer = b""
    pending_file = None  # {"size": int, "save_path": str, "display_name": str}

    while not shutdown_event.is_set():
        try:
            if pending_file:
                need = pending_file["size"] - len(pending_file.get("buffer", b""))
                chunk = sock.recv(min(4096, need))
                if not chunk:
                    break
                pending_file.setdefault("buffer", b"")
                pending_file["buffer"] += chunk
                if len(pending_file["buffer"]) < pending_file["size"]:
                    continue
                file_bytes = pending_file["buffer"][: pending_file["size"]]
                with open(pending_file["save_path"], "wb") as f:
                    f.write(file_bytes)
                logger.info("File saved: %s", pending_file["save_path"])
                append_output(
                    addr,
                    f"[FILE SAVED] Download: /download/{pending_file['display_name']}",
                )
                buffer = pending_file["buffer"][pending_file["size"] :] + buffer
                pending_file = None
                continue

            data = sock.recv(4096)
            if not data:
                break

            buffer += data

            while b"FILE_BEGIN:" in buffer:
                header_end = buffer.find(b"\n")
                if header_end == -1:
                    break
                header = buffer[:header_end].decode(errors="ignore")
                parts = header.split(":", 2)
                if len(parts) != 3 or parts[0] != "FILE_BEGIN":
                    buffer = buffer[header_end + 1 :]
                    continue
                _, path, size_str = parts
                try:
                    size = int(size_str)
                except ValueError:
                    logger.warning("Invalid file size from %s", addr)
                    buffer = buffer[header_end + 1 :]
                    continue
                if size < 0 or size > MAX_FILE_RECEIVE_BYTES:
                    logger.warning("Rejected oversized file (%s bytes) from %s", size, addr)
                    buffer = buffer[header_end + 1 :]
                    continue

                remaining = buffer[header_end + 1 :]
                safe_name = os.path.basename(path.replace("\\", "_").replace("/", "_")) or "export.bin"
                filename = f"{addr[0]}_{addr[1]}_{safe_name}"
                save_path = os.path.join(EXPORT_DIR, filename)

                if len(remaining) < size:
                    pending_file = {
                        "size": size,
                        "save_path": save_path,
                        "display_name": filename,
                        "buffer": remaining,
                    }
                    buffer = b""
                    break

                file_bytes = remaining[:size]
                buffer = remaining[size:]
                with open(save_path, "wb") as f:
                    f.write(file_bytes)
                logger.info("File saved: %s", save_path)
                append_output(addr, f"[FILE SAVED] Download: /download/{filename}")

            if pending_file:
                continue

            if buffer:
                text = buffer.decode(errors="ignore")
                buffer = b""
                if text.strip():
                    append_output(addr, text.strip())
                    logger.info("[%s] %s", addr, text.strip())

        except OSError as e:
            logger.error("Socket error for %s: %s", addr, e)
            break
        except Exception as e:
            logger.exception("Error handling client %s: %s", addr, e)
            break

    logger.info("Client disconnected: %s", addr)
    with lock:
        clients.pop(addr, None)
        client_output.pop(addr, None)
    try:
        sock.close()
    except OSError as e:
        logger.debug("Error closing socket: %s", e)


def run_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False, threaded=True)


def start_server(pin, port, use_tls=False, certfile=None, keyfile=None):
    global PIN, server_socket
    PIN = pin

    threading.Thread(target=run_dashboard, daemon=True).start()

    print("\n[+] Sentinel Link Server Running")
    print("[+] Dashboard: http://localhost:5000")
    print(f"[+] Listening on port {port}")
    print("[+] Dashboard PIN configured (not logged)")
    if use_tls:
        print("[+] TLS enabled on agent listener")

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(("0.0.0.0", port))
    server_socket.listen(5)

    try:
        while not shutdown_event.is_set():
            server_socket.settimeout(1.0)
            try:
                sock, addr = server_socket.accept()
            except socket.timeout:
                continue
            if use_tls:
                import ssl

                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                ctx.load_cert_chain(certfile=certfile, keyfile=keyfile)
                sock = ctx.wrap_socket(sock, server_side=True)
            logger.info("Client connected: %s", addr)
            threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\n[-] Shutting down...")
    finally:
        shutdown_event.set()
        with lock:
            for sock in list(clients.values()):
                try:
                    sock.close()
                except OSError as e:
                    logger.debug("Error closing client socket: %s", e)
            clients.clear()
        if server_socket:
            try:
                server_socket.close()
            except OSError as e:
                logger.debug("Error closing server socket: %s", e)
        print("[-] Server stopped.")


if __name__ == "__main__":
    start_server("1234", 9000)
