# Network File Sharing — MVP

Simple multi-client network file sharing server and client (Python).

## Features
- Password-based authentication (AUTH <password>)
- LIST server files
- DOWNLOAD file from server
- UPLOAD file to server
- Multi-client support (threading)
- Easy to run and test locally

## Files
- `server.py` — server implementation
- `client.py` — interactive client
- `shared/` — server files directory (create and populate)
- `report/` — place your final PDF report here

## Quick start (locally)
1. Make sure Python 3 is installed.
2. Create and populate the shared folder:
   ```
   mkdir shared
   echo "hello" > shared/example.txt
   ```
3. Start server:
   ```
   python3 server.py --host 0.0.0.0 --port 9000 --shared shared --password secret123
   ```
4. Start client (in another terminal):
   ```
   python3 client.py --host 127.0.0.1 --port 9000
   ```
5. In client:
   ```
   AUTH secret123
   LIST
   DOWNLOAD example.txt
   UPLOAD /path/to/localfile.pdf
   QUIT
   ```

## How to push to GitHub (one-time setup)
1. Create a new repository on GitHub (name: `network-file-sharing`).
2. On your machine:
   ```
   git init
   git add .
   git commit -m "Initial commit - Network File Sharing MVP"
   git branch -M main
   git remote add origin https://github.com/<your-username>/network-file-sharing.git
   git push -u origin main
   ```

## GitHub Codespaces setup
1. On your repo page, click **Code → Codespaces → Create codespace on main**.
2. Wait for the Codespace to start, then open a new terminal.
3. Run the server in one terminal and client in another (see Quick start).

## Notes / Extensions
- Add TLS (ssl.wrap_socket) for encrypted transfer
- Add AES encryption for payloads
- Add user accounts, file permissions, hashing, resumable transfers
