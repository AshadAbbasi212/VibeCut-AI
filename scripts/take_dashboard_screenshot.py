import asyncio
import base64
import json
import shutil
import subprocess
import tempfile
import time
import urllib.request
from pathlib import Path
import websockets

async def capture():
    chrome_path = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
    user_data_dir = tempfile.mkdtemp(prefix="chrome_snap_")
    proc = subprocess.Popen([
        chrome_path,
        "--headless=new",
        "--remote-debugging-port=9225",
        f"--user-data-dir={user_data_dir}",
        "--window-size=1920,1080",
        "--disable-gpu",
        "--no-sandbox",
        "http://127.0.0.1:8000/"
    ])
    try:
        await asyncio.sleep(3)
        tabs = None
        for _ in range(10):
            try:
                with urllib.request.urlopen("http://127.0.0.1:9225/json", timeout=2) as resp:
                    tabs = json.loads(resp.read().decode())
                if tabs:
                    break
            except Exception:
                await asyncio.sleep(0.5)

        page_tabs = [t for t in tabs if t.get("type") == "page"]
        ws_url = page_tabs[0]["webSocketDebuggerUrl"]
        print("Connected to WS URL:", ws_url)
        
        async with websockets.connect(ws_url, max_size=30 * 1024 * 1024) as ws:
            await ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
            await asyncio.sleep(1)
            
            # Click load sample button
            await ws.send(json.dumps({
                "id": 2,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.getElementById('loadSampleBtn').click()"}
            }))
            await asyncio.sleep(3)
            
            # Capture Dashboard 1
            await ws.send(json.dumps({
                "id": 3,
                "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            }))
            
            start = time.time()
            data1 = None
            while time.time() - start < 10:
                raw = await ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == 3:
                    data1 = msg["result"]["data"]
                    break
                    
            if data1:
                docs_dir = Path("docs")
                docs_dir.mkdir(exist_ok=True)
                (docs_dir / "dashboard.png").write_bytes(base64.b64decode(data1))
                print("SUCCESS: Saved docs/dashboard.png")

            # Click AI Viral Reels Studio tab
            await ws.send(json.dumps({
                "id": 4,
                "method": "Runtime.evaluate",
                "params": {"expression": "document.getElementById('tabClipsStudio').click()"}
            }))
            await asyncio.sleep(2)

            # Capture Reels Studio 2
            await ws.send(json.dumps({
                "id": 5,
                "method": "Page.captureScreenshot",
                "params": {"format": "png"}
            }))

            start = time.time()
            data2 = None
            while time.time() - start < 10:
                raw = await ws.recv()
                msg = json.loads(raw)
                if msg.get("id") == 5:
                    data2 = msg["result"]["data"]
                    break

            if data2:
                (Path("docs") / "viral_reels_studio.png").write_bytes(base64.b64decode(data2))
                print("SUCCESS: Saved docs/viral_reels_studio.png")

    finally:
        proc.terminate()
        try:
            shutil.rmtree(user_data_dir, ignore_errors=True)
        except Exception:
            pass

if __name__ == "__main__":
    asyncio.run(capture())
