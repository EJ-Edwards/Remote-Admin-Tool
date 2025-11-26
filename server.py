import socket
import threading
import ctypes
import sys
from flask import Flask, request, jsonify


clients = {}            
client_output = {}      
PIN = None
lock = threading.Lock()


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
                <button onclick="exportCmd('${c}')">Export</button>
            </div>
        `;
    }
}

async function loadOutputs() {
    const res = await fetch("/api/output");
    const data = await res.json();

    for (let addr in data) {
        const id = "out-" + addr.replaceAll(":","-");
        const box = document.getElementById(id);
        if (!box) continue;

        const shouldStick = box.scrollTop + box.clientHeight >= box.scrollHeight - 10;
        box.value = data[addr].join("\\n");
        if (shouldStick) box.scrollTop = box.scrollHeight;
    }
}

async function sendCmd(addr) {
    const id = "cmd-" + addr.replaceAll(":","-");
    const cmd = document.getElementById(id).value;
    await fetch("/api/send", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({addr, command: cmd})
    });
}

setInterval(loadOutputs, 800);
loadClients();
</script>
</body>
</html>
"""

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


def authenticate(sock):
    sock.send(b"AUTH_REQ")
    recv_pin = sock.recv(128).decode().strip()
    if recv_pin != PIN:
        sock.send(b"AUTH_FAIL")
        return False
    sock.send(b"AUTH_OK")
    return True


def handle_client(sock, addr):
    if not authenticate(sock):
        print(f"[!] Auth failed: {addr}")
        sock.close()
        return

    print(f"[+] Authenticated: {addr}")

    with lock:
        clients[addr] = sock
        client_output[addr] = []

    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break
            text = data.decode(errors="ignore")

            with lock:
                client_output[addr].append(text.strip())
                client_output[addr] = client_output[addr][-200:]  

            print(f"[{addr}] {text.strip()}")
        except:
            break

    print(f"[-] Client disconnected: {addr}")
    with lock:
        clients.pop(addr, None)
        client_output.pop(addr, None)
    sock.close()


def run_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

def start_server(pin, port):
    global PIN
    PIN = pin

    threading.Thread(target=run_dashboard, daemon=True).start()

    print(f"\n[+] Sentinel Link Server Running")
    print(f"[+] Dashboard: http://localhost:5000")
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
