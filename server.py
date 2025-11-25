import socket
import threading
import ctypes
import sys
import time

from flask import Flask, request, jsonify, render_template_string


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
        textarea { width:100%; height:150px; background:#000; color:#0f0; padding:10px; border-radius:5px; }
        input { width:80%; padding:8px; }
        button { padding:8px; cursor:pointer; }
    </style>
</head>
<body>

<h1>Sentinel Link Dashboard</h1>

<div id="client-list"></div>

<script>
async function load() {
    let res = await fetch("/api/clients");
    let data = await res.json();

    let container = document.getElementById("client-list");
    container.innerHTML = "";

    for (let c of data.clients) {
        container.innerHTML += `
            <div class="client-box">
                <strong>${c}</strong><br><br>

                <textarea id="out-${c.replaceAll(':','-')}" readonly></textarea><br>

                <input id="cmd-${c.replaceAll(':','-')}" placeholder="Enter command">
                <button onclick="sendCmd('${c}')">Send</button>
            </div>
        `;
    }

    loadOutputs();
}

async function loadOutputs() {
    let res = await fetch("/api/output");
    let data = await res.json();

    for (let addr in data) {
        const id = "out-" + addr.replaceAll(":","-");
        const box = document.getElementById(id);
        if (box) {
            box.value = data[addr].join("\\n");
            box.scrollTop = box.scrollHeight;
        }
    }
}

async function sendCmd(addr) {
    let id = "cmd-" + addr.replaceAll(":","-");
    let val = document.getElementById(id).value;

    await fetch("/api/send", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({addr, command: val})
    });
}

setInterval(loadOutputs, 1000);
load(); // run once on page load

</script>

</body>
</html>
"""

app = Flask(__name__)

# ---------------------------
# Web Routes
# ---------------------------

@app.route("/")
def home():
    return dashboard_html

@app.route("/api/clients")
def api_clients():
    with lock:
        return jsonify({"clients": [f"{ip}:{port}" for (ip, port) in clients.keys()]})

@app.route("/api/output")
def api_output():
    with lock:
        serializable = {
            f"{ip}:{port}": lines
            for (ip, port), lines in client_output.items()
        }
    return jsonify(serializable)

@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.json
    addr = data["addr"]
    command = data["command"]

    with lock:
        for (ip, port), sock in clients.items():
            if f"{ip}:{port}" == addr:
                try:
                    sock.send((command + "\n").encode())
                    return jsonify({"status": "sent"})
                except:
                    return jsonify({"status": "error"})

    return jsonify({"status": "not_found"})


# ---------------------------
# Console Title
# ---------------------------

def set_console_title(title):
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except:
        sys.stdout.write(f"\x1b]0;{title}\x07")

# ---------------------------
# Authentication
# ---------------------------

def authenticate_client(sock):
    sock.send(b"AUTH_REQ")
    recv_pin = sock.recv(1024).decode().strip()

    if recv_pin != PIN:
        sock.send(b"AUTH_FAIL")
        return False

    sock.send(b"AUTH_OK")
    return True

# ---------------------------
# Client Handler
# ---------------------------

def handle_client(sock, addr):
    if not authenticate_client(sock):
        print(f"[!] Auth failed: {addr}")
        sock.close()
        return

    print(f"[+] Authenticated client: {addr}")

    with lock:
        clients[addr] = sock
        client_output[addr] = []
        set_console_title(f"Clients: {len(clients)}")

    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break

            text = data.decode(errors="ignore")

            with lock:
                client_output[addr].append(text)
                if len(client_output[addr]) > 200:
                    client_output[addr] = client_output[addr][-200:]

            print(f"[{addr}] {text}")

        except:
            break

    print(f"[-] Client disconnected: {addr}")

    with lock:
        clients.pop(addr, None)
        client_output.pop(addr, None)
        set_console_title(f"Clients: {len(clients)}")

    sock.close()


def run_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)


def start_server(custom_pin, custom_port):
    global PIN
    PIN = custom_pin

    threading.Thread(target=run_dashboard, daemon=True).start()

    print(f"[+] Sentinel Link Server Running")
    print(f"[+] PIN: {PIN}")
    print(f"[+] Dashboard: http://localhost:5000")
    print(f"[+] Listening on 0.0.0.0:{custom_port}\n")

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", custom_port))
    server.listen(5)

    while True:
        sock, addr = server.accept()
        print(f"[+] New client: {addr}")

        threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()


if __name__ == "__main__":
    start_server("1234", 9000)
