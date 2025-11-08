#!/usr/bin/env python3
"""Simple FileShare Client
Usage:
    python3 client.py --host 127.0.0.1 --port 9000
Interactive commands after connection:
    AUTH <password>
    LIST
    DOWNLOAD <filename>
    UPLOAD <local_filepath>
    QUIT
"""

import socket, argparse, os, sys
from pathlib import Path

ENC = 'utf-8'
BUFFER = 4096

def recv_line(sock):
    buf = bytearray()
    while True:
        ch = sock.recv(1)
        if not ch:
            return None
        if ch == b'\n':
            break
        buf.extend(ch)
    return buf.decode(ENC)

def send_line(sock, text):
    if not text.endswith('\n'):
        text = text + '\n'
    sock.sendall(text.encode(ENC))

def download_file(sock, filename):
    send_line(sock, f"DOWNLOAD {filename}")
    header = recv_line(sock)
    if header is None:
        print("Connection closed by server.")
        return
    if header.startswith("ERR"):
        print(header)
        return
    if not header.startswith("FILESIZE"):
        print("Unexpected response:", header)
        return
    _, size_str = header.split(maxsplit=1)
    total = int(size_str)
    print(f"Downloading {filename} ({total} bytes)...")
    outpath = Path(filename).name
    received = 0
    with open(outpath, 'wb') as fh:
        while received < total:
            chunk = sock.recv(min(BUFFER, total - received))
            if not chunk:
                break
            fh.write(chunk)
            received += len(chunk)
            # simple progress
            perc = (received/total)*100 if total>0 else 100
            print(f"\r{received}/{total} bytes ({perc:.1f}%)", end='', flush=True)
    print("\nDownload finished.")
    # read remaining EOF line
    _ = recv_line(sock)

def upload_file(sock, local_path):
    p = Path(local_path)
    if not p.exists() or not p.is_file():
        print("Local file not found:", local_path)
        return
    size = p.stat().st_size
    filename = p.name
    send_line(sock, f"UPLOAD {filename} {size}")
    resp = recv_line(sock)
    if resp is None:
        print("Disconnected")
        return
    if not resp.startswith("READY"):
        print("Server refused upload:", resp)
        return
    print(f"Uploading {filename} ({size} bytes)...")
    sent = 0
    with p.open('rb') as fh:
        while True:
            chunk = fh.read(BUFFER)
            if not chunk:
                break
            sock.sendall(chunk)
            sent += len(chunk)
            perc = (sent/size)*100 if size>0 else 100
            print(f"\r{sent}/{size} bytes ({perc:.1f}%)", end='', flush=True)
    # read OK
    print()
    ok = recv_line(sock)
    print(ok)

def interactive(host, port):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((host, port))
    print(f"Connected to {host}:{port}")
    greeting = recv_line(sock)
    if greeting:
        print("Server:", greeting)
    try:
        while True:
            cmd = input(">> ").strip()
            if not cmd:
                continue
            parts = cmd.split()
            verb = parts[0].upper()
            if verb == 'AUTH':
                send_line(sock, cmd)
                print(recv_line(sock))
            elif verb == 'LIST':
                send_line(sock, "LIST")
                header = recv_line(sock)
                print(header)
                if header and header.startswith("OK"):
                    while True:
                        line = recv_line(sock)
                        if not line or line.strip() == 'END':
                            break
                        print(line)
            elif verb == 'DOWNLOAD':
                if len(parts) < 2:
                    print("Usage: DOWNLOAD <filename>")
                    continue
                download_file(sock, parts[1])
            elif verb == 'UPLOAD':
                if len(parts) < 2:
                    print("Usage: UPLOAD <local_filepath>")
                    continue
                upload_file(sock, parts[1])
            elif verb == 'QUIT':
                send_line(sock, "QUIT")
                print(recv_line(sock))
                break
            else:
                print("Unknown. Use AUTH/LIST/DOWNLOAD/UPLOAD/QUIT")
    finally:
        sock.close()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--host', default='127.0.0.1')
    parser.add_argument('--port', default=9000, type=int)
    args = parser.parse_args()
    interactive(args.host, args.port)
