import socket
import threading
import random
import string
import sys
import time
import ctypes
from flask import Flask, request, jsonify, render_template_string


clients = {}
PIN = None

client_commands = {
    "sysinfo": "Get OS and processor info",
    "list_processes": "List running processes",
    "hostname": "Get machine hostname",
    "ls": "List directory contents",
    "cd": "Change directory",
    "pwd": "Show current directory",
    "disk_usage": "Show disk usage",
    "whoami": "Return current username",
    "uptime": "Show system uptime",
}


dashboard_html = """
<!DOCTYPE html>
<html>
<head>
    <title>Sentinel Link Dashboard</title>
    <style>
        body { background: #111; color: white; font-family: Arial; padding: 20px; }
        .client { margin: 10px 0; padding: 10px; background: #222; border-radius: 5px; }
        input, button { padding: 8px; margin-top: 5px; }
        button { cursor: pointer; }
    </style>
</head>
<body>
    <h1>Connected Clients</h1>
    <div id="clients"></div>

    <script>
        async function loadClients() {
            let res = await fetch("/api/clients");
            let data = await res.json();
            let div = document.getElementById("clients");

            div.innerHTML = "";
            for (let c of data.clients) {
                div.innerHTML += `
                    <div class="client">
                        <strong>${c}</strong><br>
                        <input id="cmd-${c}" placeholder="Enter command">
                        <button onclick="sendCmd('${c}')">Send</button>
                    </div>
                `;
            }
        }

        async function sendCmd(addr) {
            let val = document.getElementById("cmd-" + addr).value;
            await fetch("/api/send", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ addr, command: val })
            });
        }

        setInterval(loadClients, 1000);
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
    return jsonify({"clients": [f"{ip}:{port}" for (ip, port) in clients.keys()]})

@app.route("/api/send", methods=["POST"])
def api_send():
    data = request.json
    addr = data["addr"]
    command = data["command"]

    for (ip, port), sock in clients.items():
        if f"{ip}:{port}" == addr:
            try:
                sock.send(command.encode())
                return jsonify({"status": "sent"})
            except:
                return jsonify({"status": "error"})

    return jsonify({"status": "client_not_found"})

def set_console_title(title: str):
    try:
        ctypes.windll.kernel32.SetConsoleTitleW(title)
    except:
        sys.stdout.write(f"\x1b]0;{title}\x07")

def generate_pin(length=8):
    chars = string.ascii_letters + string.digits
    return "".join(random.choice(chars) for _ in range(length))


def authenticate_client(sock):
    sock.send(b"AUTH_REQ")
    received = sock.recv(1024).decode().strip()
    if received != PIN:
        sock.send(b"AUTH_FAIL")
        return False
    sock.send(b"AUTH_OK")
    return True

def handle_client(sock, addr):
    if not authenticate_client(sock):
        print(f"[!] Client {addr} failed authentication.")
        sock.close()
        return

    print(f"[+] Client authenticated: {addr}")
    clients[addr] = sock
    set_console_title(f"Clients Connected: {len(clients)}")

    while True:
        try:
            data = sock.recv(4096)
            if not data:
                break

            print(f"[{addr}] Output:\n{data.decode(errors='ignore')}\n")
        except:
            break

    print(f"[-] Client disconnected: {addr}")
    clients.pop(addr, None)
    sock.close()
    set_console_title(f"Clients Connected: {len(clients)}")



def start_web_dashboard():
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)



def start_server():
    global PIN
    PIN = generate_pin()

    print(f"[+] Support PIN: {PIN}")
    print("[+] Web Dashboard: http://localhost:5000\n")

    threading.Thread(target=start_web_dashboard, daemon=True).start()

    host = "0.0.0.0"
    port = 8888

    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((host, port))
    server.listen(5)

    print(f"[+] Server listening on {host}:{port}")

    while True:
        sock, addr = server.accept()
        print(f"[+] New client: {addr}")
        threading.Thread(target=handle_client, args=(sock, addr), daemon=True).start()

