import os
import sys
import signal
import subprocess
import uvicorn
from uvicorn.config import LOGGING_CONFIG

PORT = 8000
LOG_FILE = "server.log"

def check_and_kill_port(port: int):
    try:
        # Find PIDs bound to the port
        result = subprocess.run(["lsof", "-t", f"-i:{port}"], capture_output=True, text=True)
        pids = [p.strip() for p in result.stdout.strip().split() if p.strip()]
        
        if pids:
            pid = pids[0]
            # Fetch process name
            proc_name_res = subprocess.run(["ps", "-p", pid, "-o", "comm="], capture_output=True, text=True)
            proc_name = proc_name_res.stdout.strip().split('/')[-1]
            
            print(f"\n\033[93m[WARNING] Port {port} is already in use by process '{proc_name}' (PID: {pid}).\033[0m")
            ans = input("Do you want to kill it? [Y/n]: ").strip().lower()
            if ans in ["", "y", "yes"]:
                os.kill(int(pid), signal.SIGKILL)
                print(f"Killed process {pid}. Port {port} is now free.\n")
            else:
                print("Exiting server startup.")
                sys.exit(0)
    except Exception:
        pass

if __name__ == "__main__":
    # 1. Manage Port
    check_and_kill_port(PORT)
    
    # 2. Redirect Uvicorn logging output programmatically to file
    custom_logging = LOGGING_CONFIG.copy()
    custom_logging["handlers"]["file"] = {
        "class": "logging.FileHandler",
        "filename": LOG_FILE,
        "mode": "a",
        "formatter": "default",
        "encoding": "utf-8"
    }
    custom_logging["loggers"]["uvicorn"]["handlers"] = ["file"]
    custom_logging["loggers"]["uvicorn.error"]["handlers"] = ["file"]
    custom_logging["loggers"]["uvicorn.access"]["handlers"] = ["file"]

    print("\033[94m[SYSTEM] Starting server programmatically...\033[0m")
    print(f"\033[94m[SYSTEM] All server outputs are being redirected to '{LOG_FILE}'\033[0m")
    print(f"\033[92m[SYSTEM] Web Chat Interface: http://127.0.0.1:{PORT}\033[0m")
    print("\033[94m--------------------------------------------------\033[0m")
    
    # 3. Launch Server
    uvicorn.run(
        "app.main:app", 
        host="127.0.0.1", 
        port=PORT, 
        log_config=custom_logging
    )