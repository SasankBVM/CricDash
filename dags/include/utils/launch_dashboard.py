"""
Start the CricMetrics Pro dashboard server (if it isn't already running) and
open it in the default browser.

Called as the final task of the ETL DAG, once the base tables and
materialized views have been refreshed. Reused as a plain function rather
than a script so the Airflow task can import it directly.
"""

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

DASHBOARD_DIR = Path(__file__).resolve().parents[3] / "cricket-dashboard"
SERVER_SCRIPT = DASHBOARD_DIR / "server.py"


def _port_is_open(host, port, timeout=0.5):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(timeout)
        return sock.connect_ex((host, port)) == 0


def launch_dashboard(host="localhost", port=8000, startup_timeout=15):
    if not _port_is_open(host, port):
        log_path = DASHBOARD_DIR / "server.log"
        with open(log_path, "a") as log_file:
            subprocess.Popen(
                [sys.executable, str(SERVER_SCRIPT), str(port)],
                cwd=str(DASHBOARD_DIR),
                stdout=log_file,
                stderr=log_file,
                start_new_session=True,
            )

        deadline = time.monotonic() + startup_timeout
        while time.monotonic() < deadline:
            if _port_is_open(host, port):
                break
            time.sleep(0.5)
        else:
            raise RuntimeError(f"Dashboard server did not start within {startup_timeout}s")

    url = f"http://{host}:{port}"
    webbrowser.open(url)
    return url


if __name__ == "__main__":
    print(f"Dashboard available at {launch_dashboard()}")
