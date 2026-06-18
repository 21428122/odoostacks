"""Capture Odoo screenshots via headless Chrome + CDP, authenticated by session cookie.

Run with the bundled Odoo Python so websocket-client is available:
  & "C:\\Program Files\\Odoo 18.0.20260509\\python\\python.exe" `
      scripts\\capture_eu_screenshots.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.request

import websocket

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
CDP_PORT = 9333
ODOO_BASE = "http://localhost:8069"
OUT_DIR = r"c:\Users\InBody\Projects\odoostacks\eu_einvoicing_tracker\static\description"
SESSION_FILE = os.path.join(os.environ["TEMP"], "odoo_session.txt")
VIEWPORT = (1280, 720)


SHOTS = [
    # (filename, path, wait_seconds, label, post_load_js)
    ("screenshot_01_dashboard.png",
     "/odoo/action-eu_einvoicing_tracker.action_eu_dashboard",
     4.0, "Dashboard kanban - all 33 countries",
     # Remove the My country filter chip by clicking its X
     "(() => { const x = document.querySelector('.o_searchview_facet .o_facet_remove, .o_searchview .o_facet_remove'); if (x) { x.click(); return 'removed'; } return 'not-found'; })()"),
    ("screenshot_02_my_country.png",
     "/odoo/action-eu_einvoicing_tracker.action_eu_dashboard",
     4.0, "My country filtered (FR)",
     None),
    ("screenshot_03_mandates_list.png",
     "/odoo/action-eu_einvoicing_tracker.action_eu_mandates",
     4.0, "Mandates list view",
     None),
    ("screenshot_04_mandate_form.png",
     "/odoo/action-eu_einvoicing_tracker.action_eu_dashboard/9",
     4.0, "France mandate form view",
     None),
]


def cdp_id_counter():
    n = 0
    while True:
        n += 1
        yield n


def cdp_send(ws, msg_id, method, params=None):
    payload = {"id": msg_id, "method": method}
    if params is not None:
        payload["params"] = params
    ws.send(json.dumps(payload))
    while True:
        raw = ws.recv()
        msg = json.loads(raw)
        if msg.get("id") == msg_id:
            return msg.get("result", {})


def wait_for_load(ws, msg_id_gen, timeout=10.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        try:
            ws.settimeout(0.5)
            raw = ws.recv()
        except Exception:
            continue
        try:
            msg = json.loads(raw)
        except Exception:
            continue
        if msg.get("method") == "Page.loadEventFired":
            return
    return


def main():
    if not os.path.isfile(CHROME):
        print(f"FATAL: Chrome not found at {CHROME}")
        sys.exit(1)
    if not os.path.isfile(SESSION_FILE):
        print(f"FATAL: session file missing: {SESSION_FILE}")
        sys.exit(1)
    os.makedirs(OUT_DIR, exist_ok=True)

    with open(SESSION_FILE, "r", encoding="utf-8") as fh:
        session_id = fh.read().strip()
    print(f"session_id length: {len(session_id)}")

    profile_dir = tempfile.mkdtemp(prefix="chrome-screenshot-")
    print(f"Chrome profile dir: {profile_dir}")

    chrome_args = [
        CHROME,
        "--headless=new",
        "--disable-gpu",
        "--hide-scrollbars",
        "--no-sandbox",
        f"--remote-debugging-port={CDP_PORT}",
        "--remote-allow-origins=*",
        f"--user-data-dir={profile_dir}",
        f"--window-size={VIEWPORT[0]},{VIEWPORT[1]}",
        "about:blank",
    ]

    print("Launching Chrome ...")
    proc = subprocess.Popen(chrome_args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Wait for CDP HTTP endpoint to come up
    cdp_ws_url = None
    for _ in range(40):
        try:
            with urllib.request.urlopen(f"http://localhost:{CDP_PORT}/json", timeout=1) as resp:
                tabs = json.loads(resp.read().decode("utf-8"))
                for tab in tabs:
                    if tab.get("type") == "page":
                        cdp_ws_url = tab["webSocketDebuggerUrl"]
                        break
                if cdp_ws_url:
                    break
        except Exception:
            time.sleep(0.5)

    if not cdp_ws_url:
        print("FATAL: could not connect to CDP")
        proc.terminate()
        sys.exit(1)
    print(f"CDP target: {cdp_ws_url}")

    ws = websocket.create_connection(cdp_ws_url)
    msg_ids = cdp_id_counter()

    try:
        cdp_send(ws, next(msg_ids), "Page.enable")
        cdp_send(ws, next(msg_ids), "Network.enable")

        # Set session cookie
        cdp_send(ws, next(msg_ids), "Network.setCookie", {
            "domain": "localhost",
            "name": "session_id",
            "value": session_id,
            "path": "/",
            "httpOnly": True,
            "secure": False,
            "sameSite": "Lax",
        })
        print("session_id cookie set")

        # Force viewport
        cdp_send(ws, next(msg_ids), "Emulation.setDeviceMetricsOverride", {
            "width": VIEWPORT[0],
            "height": VIEWPORT[1],
            "deviceScaleFactor": 1,
            "mobile": False,
        })

        for filename, path, wait_s, label, post_js in SHOTS:
            url = ODOO_BASE + path
            print(f"--> {label}: {url}")
            cdp_send(ws, next(msg_ids), "Page.navigate", {"url": url})
            time.sleep(wait_s)
            if post_js:
                result = cdp_send(ws, next(msg_ids), "Runtime.evaluate",
                                  {"expression": post_js, "returnByValue": True})
                print(f"   post-js: {result.get('result', {}).get('value')}")
                time.sleep(1.5)
            shot = cdp_send(ws, next(msg_ids), "Page.captureScreenshot", {"format": "png"})
            data = shot.get("data")
            if not data:
                print(f"   FAIL no data")
                continue
            import base64
            png_bytes = base64.b64decode(data)
            dst = os.path.join(OUT_DIR, filename)
            with open(dst, "wb") as fh:
                fh.write(png_bytes)
            print(f"   OK {filename} ({len(png_bytes)} bytes)")

    finally:
        try:
            ws.close()
        except Exception:
            pass
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except Exception:
            proc.kill()
        try:
            shutil.rmtree(profile_dir, ignore_errors=True)
        except Exception:
            pass

    print("DONE")


if __name__ == "__main__":
    main()
