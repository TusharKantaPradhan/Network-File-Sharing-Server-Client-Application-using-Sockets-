#!/usr/bin/env python3
"""Simple Multi-Client Network File Sharing Server (Python)
Usage:
    python3 server.py --host 0.0.0.0 --port 9000 --password secret123
"""
import socket, threading, argparse, os
from pathlib import Path

BUFFER = 4096
ENC = 'utf-8'

def recv_line(conn):
    buf = bytearray()
    while True:
        ch = conn.recv(1)
        if not ch:
            return None
        if ch == b'\n':
            break
        buf.extend(ch)
    return buf.decode(ENC)

def send_line(conn, text):
    if not text.endswith('\n'):
        text = text + '\n'
    conn.sendall(text.encode(ENC))

def handle_client(conn, addr, shared_dir, password):
    print(f"[+] Connection from {addr}")
    authed = False
    try:
        send_line(conn, "WELCOME Simple FileShare Server")
        while True:
            line = recv_line(conn)
            if line is None:
                print(f"[-] {addr} disconnected")
                break
            parts = line.strip().split()
            if len(parts) == 0:
                continue
            cmd = parts[0].upper()

            if cmd == 'AUTH':
                if len(parts) < 2:
                    send_line(conn, "ERR Missing password")
                    continue
                if parts[1] == password:
                    authed = True
                    send_line(conn, "OK Authenticated")
                else:
                    send_line(conn, "ERR Authentication failed")

            elif cmd == 'QUIT':
                send_line(conn, "BYE")
                break

            else:
                if not authed:
                    send_line(conn, "ERR Not authenticated. Use: AUTH <password>")
                    continue

                if cmd == 'LIST':
                    files = os.listdir(shared_dir)
                    send_line(conn, f"OK {len(files)}")
                    for f in files:
                        fpath = Path(shared_dir) / f
                        size = fpath.stat().st_size if fpath.exists() else 0
                        send_line(conn, f"{f}\t{size}")
                    send_line(conn, "END")

                elif cmd == 'DOWNLOAD':
                    if len(parts) < 2:
                        send_line(conn, "ERR Missing filename")
                        continue
                    filename = parts[1]
                    fpath = Path(shared_dir) / filename
                    if not fpath.exists():
                        send_line(conn, "ERR File not found")
                        continue
                    size = fpath.stat().st_size
                    send_line(conn, f"FILESIZE {size}")
                    # send raw bytes
                    with fpath.open('rb') as fh:
                        while True:
                            chunk = fh.read(BUFFER)
                            if not chunk:
                                break
                            conn.sendall(chunk)
                    # after sending bytes, one final newline so client recv_line remains synced
                    send_line(conn, "EOF")
                    print(f"[>] Sent file {filename} to {addr}")

                elif cmd == 'UPLOAD':
                    if len(parts) < 3:
                        send_line(conn, "ERR Usage: UPLOAD <filename> <filesize>")
                        continue
                    filename = parts[1]
                    try:
                        filesize = int(parts[2])
                    except:
                        send_line(conn, "ERR Invalid filesize")
                        continue
                    target = Path(shared_dir) / filename
                    send_line(conn, "READY")
                    received = 0
                    with target.open('wb') as fh:
                        while received < filesize:
                            to_read = min(BUFFER, filesize - received)
                            chunk = conn.recv(to_read)
                            if not chunk:
                                break
                            fh.write(chunk)
                            received += len(chunk)
                    send_line(conn, "OK Upload complete")
                    print(f"[<] Received file {filename} ({filesize} bytes) from {addr}")

                else:
                    send_line(conn, f"ERR Unknown command: {cmd}")

    except Exception as ex:
        print(f"[!] Exception with {addr}: {ex}")
    finally:
        conn.close()
        print(f"[#] Connection closed {addr}")

def start_server(host, port, shared_dir, password):
    Path(shared_dir).mkdir(parents=True, exist_ok=True)
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind((host, port))
    sock.listen(5)
    print(f"[+] Server listening on {host}:{port}, shared_dir={shared_dir}")
    try:
        while True:
            conn, addr = sock.accept()
            t = threading.Thread(target=handle_client, args=(conn, addr, shared_dir, password), daemon=True)
            t.start()
    except KeyboardInterrupt:
        print("\n[!] Shutting down server")
    finally:
        sock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=9000, type=int)
    parser.add_argument('--shared', default='shared')
    parser.add_argument('--password', default='secret123')
    args = parser.parse_args()
    start_server(args.host, args.port, args.shared, args.password)
