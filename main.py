#!/usr/bin/env python3
"""Bonkasse - Sports Club Cash Register System"""

import uvicorn
import webbrowser
import threading
import time
import shutil
import subprocess
import sys
import os
import urllib.request

from app.config import HOST, PORT


def _find_chrome():
    candidates = [
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
    ]
    if sys.platform == "win32":
        candidates.extend([
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ])
    for path in candidates:
        if path and os.path.exists(path):
            return path
    return None


def _launch_chrome(url):
    """Launch Chrome in kiosk mode as its own process. Returns the Popen or None."""
    path = _find_chrome()
    if not path:
        webbrowser.open(url)  # Fallback: can't track when this closes.
        return None

    # Dedicated user-data-dir so Chrome runs as its own process (otherwise it
    # delegates to an existing Chrome and exits immediately).
    import tempfile
    user_data_dir = os.path.join(tempfile.gettempdir(), "bonkasse-chrome")
    try:
        return subprocess.Popen([
            path,
            "--kiosk",
            f"--app={url}",
            f"--user-data-dir={user_data_dir}",
        ])
    except OSError:
        webbrowser.open(url)
        return None


def _wait_for_server(url, server_thread, timeout=20.0):
    """Block until the server answers or the server thread dies."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        if not server_thread.is_alive():
            return False
        try:
            urllib.request.urlopen(url, timeout=0.5)
            return True
        except Exception:
            time.sleep(0.25)
    return False


def main():
    url = f"http://{HOST}:{PORT}"

    config = uvicorn.Config(
        "app:create_app",
        factory=True,
        host=HOST,
        port=PORT,
        log_level="warning",
    )
    server = uvicorn.Server(config)
    server_thread = threading.Thread(target=server.run, daemon=True)
    server_thread.start()

    if not _wait_for_server(url, server_thread):
        print("Server failed to start.")
        sys.exit(1)  # non-zero -> the run.bat loop will restart us

    proc = _launch_chrome(url)

    # Exit when EITHER the browser window closes (intentional) OR the server
    # dies (crash). In both cases we tear down the other side so a restart
    # starts from a clean slate and Chrome is never left orphaned holding its
    # profile lock.
    crashed = False
    try:
        if proc is not None:
            while True:
                if not server_thread.is_alive():
                    crashed = True
                    print("Server stopped unexpectedly, closing browser...")
                    break
                if proc.poll() is not None:
                    print("Browser closed, shutting down server...")
                    break
                time.sleep(0.5)
        else:
            # No tracked browser process; just run until the server stops.
            server_thread.join()
            crashed = True
    finally:
        if proc is not None and proc.poll() is None:
            try:
                proc.terminate()
            except Exception:
                pass
        server.should_exit = True
        time.sleep(0.3)

    # Crash -> non-zero so the restart loop relaunches. Clean kiosk close -> 0.
    sys.exit(1 if crashed else 0)


if __name__ == "__main__":
    main()
