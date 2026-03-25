"""
Startet cloudflared, liest die URL automatisch aus
und aktualisiert sie direkt in der GitHub index.html.

Ausfuehren: python updater.py
"""
import subprocess
import re
import requests
import base64
import os
import time
from dotenv import load_dotenv

load_dotenv()

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_REPO  = "moritz-sketch/test"
GITHUB_FILE  = "index.html"
CLOUDFLARED  = r"C:\ai-agent\cloudflared.exe"

def get_current_file():
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    r = requests.get(url, headers=headers)
    data = r.json()
    content = base64.b64decode(data["content"]).decode("utf-8")
    sha = data["sha"]
    return content, sha

def update_file(content, sha, new_url):
    updated = re.sub(
        r'https://[a-z0-9-]+\.trycloudflare\.com',
        new_url,
        content
    )
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {"Authorization": f"token {GITHUB_TOKEN}"}
    payload = {
        "message": f"Auto-update: Cloudflare URL -> {new_url}",
        "content": base64.b64encode(updated.encode("utf-8")).decode("utf-8"),
        "sha": sha
    }
    r = requests.put(url, headers=headers, json=payload)
    return r.status_code == 200

def start_tunnel():
    print("Starte Cloudflare Tunnel...")
    proc = subprocess.Popen(
        [CLOUDFLARED, "tunnel", "--url", "http://localhost:8000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    tunnel_url = None
    for line in proc.stdout:
        print(line, end="")
        match = re.search(r'https://[a-z0-9-]+\.trycloudflare\.com', line)
        if match:
            tunnel_url = match.group(0)
            print(f"\n Tunnel URL gefunden: {tunnel_url}")
            break

    if not tunnel_url:
        print("Keine URL gefunden!")
        return proc, None

    print("Aktualisiere GitHub Pages...")
    content, sha = get_current_file()
    success = update_file(content, sha, tunnel_url)
    if success:
        print(f"GitHub aktualisiert! Website nutzt jetzt: {tunnel_url}")
    else:
        print("GitHub Update fehlgeschlagen.")

    print("\nTunnel laeuft! Druecke Strg+C zum Beenden.\n")
    return proc, tunnel_url

if __name__ == "__main__":
    if not GITHUB_TOKEN:
        print("GITHUB_TOKEN fehlt in .env!")
        print("Erstelle einen Token unter: https://github.com/settings/tokens")
        exit(1)

    proc, url = start_tunnel()
    if proc:
        try:
            proc.wait()
        except KeyboardInterrupt:
            proc.terminate()
            print("\nTunnel gestoppt.")
