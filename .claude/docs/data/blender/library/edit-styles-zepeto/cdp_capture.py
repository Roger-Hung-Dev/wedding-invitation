# 用本機 Chrome（無頭模式）＋ DevTools 協定逐格截圖。不用另外安裝東西：只用 Python 內建的 asyncio、urllib 和已裝的 websockets。
# 給 render_edit.py（正式剪接）和 build_showcase.py（樣式縮圖）共用。
import asyncio, base64, json, os, subprocess, tempfile, time, urllib.request
import websockets

CHROME = r"C:/Program Files/Google/Chrome/Application/chrome.exe"


class Chrome:
    def __init__(self, width, height, port=9333):
        self.w, self.h, self.port = width, height, port
        self.tmp = tempfile.mkdtemp(prefix="cdp_")
        self.proc = subprocess.Popen([CHROME, "--headless=new", f"--remote-debugging-port={port}", f"--user-data-dir={self.tmp}",
                                      "--autoplay-policy=no-user-gesture-required", "--allow-file-access-from-files",
                                      "--hide-scrollbars", "--force-device-scale-factor=1", f"--window-size={width},{height}", "about:blank"],
                                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        self.ws = None; self.n = 0

    async def __aenter__(self):
        for _ in range(100):
            try:
                tabs = json.load(urllib.request.urlopen(f"http://127.0.0.1:{self.port}/json/list", timeout=1))
                page = next(t for t in tabs if t["type"] == "page")
                break
            except Exception:
                time.sleep(0.1)
        else:
            raise RuntimeError("Chrome 沒有開起來")
        self.ws = await websockets.connect(page["webSocketDebuggerUrl"], max_size=None)
        await self.call("Page.enable")
        await self.call("Emulation.setDeviceMetricsOverride", width=self.w, height=self.h, deviceScaleFactor=1, mobile=False)
        return self

    async def __aexit__(self, *a):
        try:
            await self.ws.close()
        finally:
            self.proc.terminate()

    async def call(self, method, **params):
        self.n += 1; mid = self.n
        await self.ws.send(json.dumps({"id": mid, "method": method, "params": params}))
        while True:
            m = json.loads(await self.ws.recv())
            if m.get("id") == mid:
                if "error" in m:
                    raise RuntimeError(f"{method}: {m['error']}")
                return m.get("result", {})

    async def goto(self, path):
        await self.call("Page.navigate", url="file:///" + os.path.abspath(path).replace("\\", "/"))
        for _ in range(200):                                   # 等 __player 準備好、字型載完
            r = await self.eval("window.__player && document.fonts.status === 'loaded' ? 1 : 0")
            if r == 1:
                return
            await asyncio.sleep(0.05)
        raise RuntimeError("頁面沒有準備好：" + path)

    async def eval(self, expr, await_promise=False):
        r = await self.call("Runtime.evaluate", expression=expr, awaitPromise=await_promise, returnByValue=True)
        if "exceptionDetails" in r:
            raise RuntimeError(str(r["exceptionDetails"])[:300])
        return r.get("result", {}).get("value")

    async def shot(self, out):
        r = await self.call("Page.captureScreenshot", format="png", fromSurface=True)
        open(out, "wb").write(base64.b64decode(r["data"]))
