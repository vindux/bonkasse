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
import signal

from app.config import HOST, PORT


def open_browser_and_wait():
    """Wait for server to start, open browser in kiosk mode, then shutdown when it closes."""
    time.sleep(1.5)
    url = f"http://{HOST}:{PORT}"

    chrome_paths = [
        shutil.which("chrome"),
        shutil.which("chromium"),
        shutil.which("google-chrome"),
    ]

    if sys.platform == "win32":
        chrome_paths.extend([
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        ])

    # Use a dedicated user-data-dir so Chrome runs as its own process
    # (otherwise it delegates to an existing Chrome and exits immediately)
    import tempfile
    user_data_dir = os.path.join(tempfile.gettempdir(), "bonkasse-chrome")

    for path in chrome_paths:
        if path:
            try:
                proc = subprocess.Popen([
                    path,
                    "--kiosk",
                    f"--app={url}",
                    f"--user-data-dir={user_data_dir}",
                ])
                proc.wait()  # Block until browser window is closed
                print("Browser closed, shutting down server...")
                os._exit(0)
                return
            except OSError:
                continue

    # Fallback: can't track when default browser closes
    webbrowser.open(url)


def main():
    threading.Thread(target=open_browser_and_wait, daemon=True).start()
    uvicorn.run(
        "app:create_app",
        factory=True,
        host=HOST,
        port=PORT,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
