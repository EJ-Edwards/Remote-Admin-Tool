# Sentinel Link — Remote Device Management System

A secure, authenticated remote administration system built with **Python**, **Sockets**, and a **Flask-based web dashboard**.  
Designed for **educational, security research, and authorized device management**.

> ⚠️ **This project allows remote viewing of system information, file content, and command execution only. It does NOT include remote desktop or input control.**

---

## 🚀 Features

- **Secure PIN Authentication**  
  Custom PIN handshake between server ↔ client.

- **Web Dashboard (Flask UI)**  
  - List connected clients  
  - View live output/logs per client  
  - Send commands and receive output  

- **Cross-Platform Client**  
  Works on Windows, Linux, macOS  

- **System Management Commands**  
  - `sysinfo` — OS and processor info  
  - `hostname` — Computer name  
  - `whoami` — Current user  
  - `ls` / `dir` — List files and folders  
  - `pwd` — Current directory  
  - `read_file` — View file content  
  - `disk_usage` — Show storage usage  
  - `list_processes` — Running processes  
  - `uptime` — System uptime  

- **Customizable PIN & Port**  
  Easily secure your server on launch  

---

