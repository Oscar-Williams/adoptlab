"""Exercise the HTTP workbench and three offline protocol cases in CI."""
import os
import subprocess
import sys
import time
import httpx

def main():
    server=subprocess.Popen([sys.executable,'-m','uvicorn','adoptlab.web:app','--host','127.0.0.1','--port','8780'],env=os.environ.copy())
    try:
        with httpx.Client(trust_env=False) as client:
            for attempt in range(50):
                if server.poll() is not None:raise RuntimeError('SERVER_EXITED')
                try:
                    if client.get('http://127.0.0.1:8780/api/workbench/summary').is_success:break
                except httpx.HTTPError:pass
                time.sleep(.2)
            else:raise RuntimeError('SERVER_START_TIMEOUT')
        subprocess.run([sys.executable,'scripts/validate_workbench.py'],check=True)
    finally:
        server.terminate()
        try:server.wait(timeout=10)
        except subprocess.TimeoutExpired:server.kill();server.wait()

if __name__=='__main__':main()
