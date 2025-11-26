import socket
import threading
import sys
import io
import os
from flask import Flask, request, jsonify, send_file

clients = {}
client_output = {}
PIN = None
lock = threading.Lock()

# Where exported files will be saved
EXPORT_DIR = "exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

# -------------------------
#  DASHBOARD HTML
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
button { padding:8px; cursor:pointer; }
a { color:#4af; }
</style>
</head>
<body>
<h1>Sentinel Link Dashboard</h1>
<div id="client-list"></div>

<script>
async function loadClients() {
    const res = await fetch("/api/clients");
    const data = await res.json();

    const container = document.getElementById("client-list");
    container.innerHTML = "";

    for (let c of data.clients) {
        container.innerHTML += `
            <div class="client-box">
                <strong>${c}</strong><br><br>
                <textarea id="out-${c.replaceAll(':','-')}" readonly></textarea><br>
                <input id="cmd-${c.replaceAll(':','-')}" placeholder="Enter command">
                <button onclick="sendCmd('${c}')">Send</button>
                <button onclick="exportFile('${c}')">Export File</button>
                <div id="download-${c.replaceAll(':','-')}"></div>
            </div>
        `;
    }
}

async function loadOutputs() {
    const res = await fetch("/api/output");
    const data = await res.json();

    for (let addr in data) {
        const id = "out-" + addr.replaceAll(":", "-");
        const box = document.getElementById(id);
        if (!box) continue;

        const shouldStick = box.scrollTop + box.clientHeight >= box.scrollHeight - 10;
        box.value = data[addr].join("\\n");
        if (shouldStick) box.scrollTop = box.scrollHeight;
    }
}

async function sendCmd(addr) {
    const id = "cmd-" + addr.replaceAll(":", "-");
    const cmd = document.getElementById(id).value;

    await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({addr, command: cmd})
    });
}

function exportFile(addr) {
    const path = prompt("Enter file or folder path to export:");
    if (!path) return;

    fetch("/api/send", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({
            addr,
            command: "FILE_REQ " + path
        })
    });

    alert("File request sent. When the client sends it, a download link will appear.");
}

setInterval(loadOutputs, 800);
loadClients();
</script>

</body>
</html>
"""

# -------------------------
#  FLASK ROUTES
# -------------------------

app = Flask(__name__)

@app.route("/")
def home():
    return dashboard_html

@app.route("/api/clients")
def api_clients():
    with lock:
        return jsonify({"clients": [f"{ip}:{port}" for (ip, port) in clients]})

@app.route("/api/output")
def api_output():
    with lock:
        return jsonify({f"{ip}:{port}": lines for (ip, port), lines in client_output.items()})

@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.json
    addr = data["addr"]
    cmd = data["command"]

    with lock:
        for (ip, port), sock in clients.items():
            if f"{ip}:{port}" == addr:
                try:
                    sock.send((cmd + "\n").encode())
                    return jsonify({"status": "sent"})
                except:
                    return jsonify({"status": "send_error"})
    return jsonify({"status": "not_found"})


@app.route("/download/<filename>")
def download(filename):
    path = os.path.join(EXPORT_DIR, filename)
    if not os.path.exists(path):
        return "File not found", 404
    return send_file(path, as_attachment=True)


# -------------------------
#  AUTHENTICATION
# -------------------------

def authenticate(sock):
    sock.send(b"AUTH_REQ")
    recv_pin = sock.recv(128).decode().strip()
    if recv_pin != PIN:
        sock.send(b"AUTH_FAIL")
        return False
    sock.send(b"AUTH_OK")
    return True


# -------------------------
#  HANDLE CLIENT
# -------------------------

def handle_client(sock, addr):
    if not authenticate(sock):
        print(f"[!] Auth failed: {addr}")
        sock.close()
        return

    print(f"[+] Authenticated: {addr}")

    with lock:
        clients[addr] = sock
        client_output[addr] = []

    buffer = b""

    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break

            buffer += data

            # ----------- FILE TRANSFER BEGIN ----------
            if b"FILE_BEGIN:" in buffer:
                header_end = buffer.find(b"\n")
                header = buffer[:header_end].decode()

                _, path, size = header.split(":")
                size = int(size)

                remaining = buffer[header_end+1:]

                # not enough data yet
                if len(remaining) < size:
                    continue

                file_bytes = remaining[:size]
                buffer = remaining[size:]  # trim used data

                safe_name = path.replace("\\", "_").replace("/", "_")
                filename = f"{addr[0]}_{addr[1]}_{safe_name}"
                save_path = os.path.join(EXPORT_DIR, filename)

                with open(save_path, "wb") as f:
                    f.write(file_bytes)

                print(f"[+] File saved: {save_path}")

                # append download link to output
                with lock:
                    client_output[addr].append(f"[FILE SAVED] Download: /download/{filename}")

                continue
            # ----------- FILE TRANSFER END ----------

            # Normal text output
            text = buffer.decode(errors="ignore")
            buffer = b""

            with lock:
                client_output[addr].append(text.strip())
                client_output[addr] = client_output[addr][-200:]

            print(f"[{addr}] {text.strip()}")

        except Exception as e:
            print("Error:", e)
            break

    print(f"[-] Client disconnected: {addr}")
    with lock:
        clients.pop(addr, None)
        client_output.pop(addr, None)
    sock.close()


# -------------------------
#  SERVER START
# -------------------------

def run_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def start_server(pin, port):
    global PIN
    PIN = pin

    threading.Thread(target=run_dashboard, daemon=True).start()

    print("\n[+] Sentinel Link Server Running")
    print("[+] Dashboard: http://localhost:5000")
    print(f"[+] Listening on port {port}")
    print(f"[+] PIN = {PIN}\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", port))
    server.listen(5)

    while True:
        sock, addr = server.accept()
        print(f"[+] Client connected: {addr}")
        threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()

if __name__ == "__main__":
    start_server("1234", 9000)
