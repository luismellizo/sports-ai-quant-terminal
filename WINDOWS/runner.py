import os
import sys
import subprocess
import time
import webbrowser
import socket
from pathlib import Path

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('localhost', port)) == 0

def start_backend():
    # Detect if we are running in a PyInstaller bundle
    if getattr(sys, 'frozen', False):
        base_dir = Path(sys._MEIPASS)
    else:
        base_dir = Path(__file__).parent.parent

    backend_dir = base_dir / "backend"
    
    # Run uvicorn server
    # Note: We use sys.executable if we want to run the bundled python, 
    # but in a frozen app, we usually call the server directly or via a subprocess.
    # For a bundled FastAPI, we can import and run it, or spawn.
    
    print(f"Starting Backend from {backend_dir}...")
    
    # Set environment variables if needed
    os.environ["PYTHONPATH"] = str(base_dir)
    
    # Start the backend process
    # Command: uvicorn backend.main:app --host 127.0.0.1 --port 8000
    cmd = [
        sys.executable, "-m", "uvicorn", 
        "backend.main:app", 
        "--host", "127.0.0.1", 
        "--port", "8000"
    ]
    
    return subprocess.Popen(cmd, cwd=base_dir)

def main():
    print("Iniciando Sports AI - Pacheco Ruaa Edition...")
    
    # 1. Start backend
    backend_proc = start_backend()
    
    # 2. Wait for backend to be ready
    retries = 10
    while retries > 0 and not is_port_in_use(8000):
        print("Sincronizando con el satélite...")
        time.sleep(1)
        retries -= 1
        
    # 3. Open Frontend
    # If we have a standalone frontend server, start it too.
    # Otherwise, if it's static, serve it via the backend or a local server.
    # For now, let's assume it's running on port 3000 (standard dev)
    # In a real production build, we might serve it from the backend.
    
    print("Abriendo terminal de trading...")
    webbrowser.open("http://localhost:3000")
    
    try:
        backend_proc.wait()
    except KeyboardInterrupt:
        backend_proc.terminate()

if __name__ == "__main__":
    main()
