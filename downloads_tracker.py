"""
Downloads Watcher Agent
========================
This background script watches your local computer's Downloads directory
and sends real-time file download events to the User Behavior Analytics platform.

Requires:
  - Python 3.x
  - requests library (pip install requests)

To Run:
  python downloads_tracker.py
"""

import os
import sys
import time
import requests
import getpass
from datetime import datetime

# Default configuration
DEFAULT_URL = "http://localhost:5000"
POLL_INTERVAL = 1.0  # seconds

# Temporary/browser file extensions to ignore
TEMP_EXTENSIONS = (
    ".crdownload",  # Chrome
    ".tmp",          # General Windows / browsers
    ".download",     # Safari
    ".part",         # Firefox
    "~$",            # Office temp files
)


def get_downloads_dir():
    """Return the platform-specific default Downloads directory."""
    home = os.path.expanduser("~")
    # Common default paths
    downloads_path = os.path.join(home, "Downloads")
    if os.path.exists(downloads_path):
        return downloads_path
    return home


class DownloadsWatcher:
    def __init__(self, api_url, username, password):
        self.api_url = api_url.rstrip("/")
        self.username = username
        self.password = password
        self.token = None
        self.downloads_dir = get_downloads_dir()
        self.known_files = set()

    def login(self):
        """Authenticate against the Flask backend to obtain a JWT token."""
        print(f"\n🔐 Authenticating as '{self.username}' at {self.api_url}...")
        try:
            resp = requests.post(
                f"{self.api_url}/auth/login",
                json={"username": self.username, "password": self.password},
                timeout=5.0
            )
            if resp.status_code == 200:
                data = resp.json()
                self.token = data.get("token")
                print("✅ Authentication successful!")
                return True
            else:
                error = resp.json().get("error", "Unknown error")
                print(f"❌ Authentication failed: {error} (Status: {resp.status_code})")
        except Exception as e:
            print(f"❌ Connection error during login: {e}")
        return False

    def test_geolocation(self):
        """Check geolocation resolved by the backend to verify IP lookup is working."""
        print("\n📍 Querying local IP address and geolocation...")
        # We simulate a test event with "location": "detect" to see what city is resolved
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "user_id": self.username,
            "location": "detect",
            "downloads": 0,
            "failed_attempts": 0,
            "device_fingerprint": "Agent-Test-Script"
        }
        try:
            resp = requests.post(f"{self.api_url}/log-activity", json=payload, headers=headers, timeout=5.0)
            if resp.status_code == 200:
                # Get the latest logs to see resolved location
                logs_resp = requests.get(f"{self.api_url}/get-logs?page=1&per_page=1", headers=headers, timeout=5.0)
                if logs_resp.status_code == 200:
                    logs_data = logs_resp.json()
                    logs_list = logs_data.get("data", []) if isinstance(logs_data, dict) else logs_data
                    if logs_list:
                        latest = logs_list[0]
                        print(f"🌍 Detected Real Geolocation: {latest.get('location')} (IP: {latest.get('ip_address')})")
                        return
            print("⚠️ Could not geolocate IP address.")
        except Exception as e:
            print(f"⚠️ Geolocation test failed: {e}")

    def send_download_event(self, filename):
        """Send a real-time event log to the backend."""
        headers = {"Authorization": f"Bearer {self.token}"}
        payload = {
            "user_id": self.username,
            "location": "detect",  # Tells backend to geolocate automatically
            "downloads": 1,
            "failed_attempts": 0,
            "device_fingerprint": f"Agent-FileWatcher-Watcher"
        }
        print(f"📁 New file detected: {filename}")
        print("⚡ Sending log event to server...")
        try:
            resp = requests.post(f"{self.api_url}/log-activity", json=payload, headers=headers, timeout=5.0)
            if resp.status_code == 200:
                data = resp.json()
                print(f"✅ Success! Risk Score: {data.get('risk_score')} | Status: {data.get('status')}")
            elif resp.status_code == 401:
                print("🔑 Session expired. Re-authenticating...")
                if self.login():
                    # Retry
                    self.send_download_event(filename)
            else:
                print(f"❌ Failed to log event: {resp.text} (Status: {resp.status_code})")
        except Exception as e:
            print(f"❌ Error sending event: {e}")

    def get_current_files(self):
        """Scan the Downloads directory and return a dictionary of files with their sizes."""
        files = {}
        try:
            for item in os.listdir(self.downloads_dir):
                path = os.path.join(self.downloads_dir, item)
                if os.path.isfile(path):
                    # Ignore temporary browser download extensions
                    if not item.endswith(TEMP_EXTENSIONS):
                        try:
                            files[item] = os.path.getsize(path)
                        except OSError:
                            pass
        except Exception as e:
            print(f"⚠️ Error scanning Downloads folder: {e}")
        return files

    def run(self):
        """Initialize watcher and start polling for changes."""
        if not self.login():
            return

        self.test_geolocation()

        print(f"\n📂 Watching Downloads Directory: {self.downloads_dir}")
        print("👀 Monitoring started. Download any file on your computer to test!")
        print("Ctrl+C to stop.")

        # Establish baseline
        initial_files = self.get_current_files()
        self.known_files = set(initial_files.keys())

        # Keep track of file sizes to wait for download completion
        size_check = {}

        try:
            while True:
                time.sleep(POLL_INTERVAL)
                current_files = self.get_current_files()

                # Find newly added files
                new_files = set(current_files.keys()) - self.known_files

                for filename in new_files:
                    path = os.path.join(self.downloads_dir, filename)
                    if not os.path.exists(path):
                        continue

                    # Poll file size to make sure the download has finished
                    current_size = current_files[filename]
                    prev_size = size_check.get(filename, -1)

                    if current_size == prev_size and current_size > 0:
                        # Size is stable, download complete!
                        self.send_download_event(filename)
                        self.known_files.add(filename)
                        if filename in size_check:
                            del size_check[filename]
                    else:
                        # Size is still growing or not checked yet, monitor it in next tick
                        size_check[filename] = current_size

                # Remove deleted files from our known tracking list
                removed_files = self.known_files - set(current_files.keys())
                for filename in removed_files:
                    self.known_files.remove(filename)
                    if filename in size_check:
                        del size_check[filename]

        except KeyboardInterrupt:
            print("\n👋 Monitoring stopped. Exiting.")


if __name__ == "__main__":
    print("=" * 60)
    print("        User Behavior Analytics - Downloads Tracker Agent        ")
    print("=" * 60)

    url = input(f"Enter backend server URL [{DEFAULT_URL}]: ").strip()
    if not url:
        url = DEFAULT_URL

    username = input("Enter backend username [admin]: ").strip()
    if not username:
        username = "admin"

    password = getpass.getpass("Enter backend password: ").strip()
    if not password:
        password = "admin123"

    watcher = DownloadsWatcher(url, username, password)
    watcher.run()
