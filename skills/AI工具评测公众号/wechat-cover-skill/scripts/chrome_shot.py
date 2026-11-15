#!/usr/bin/env python3
"""Headless-Chrome helpers: full-page screenshot at fixed width, and DOM measurement.
Usage: chrome_shot.py page.html out.png [--width 375]
Env CHROME_BIN overrides the browser path.
"""
from __future__ import annotations
import argparse, os, re, shutil, subprocess, tempfile
from pathlib import Path

def chrome_bin() -> str:
    pf = os.environ.get("ProgramFiles", r"C:\Program Files")
    pf86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    lad = os.environ.get("LOCALAPPDATA", "")
    cands = [
        os.environ.get("CHROME_BIN"),
        "google-chrome", "chrome", "chromium", "chromium-browser", "msedge",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        os.path.join(pf, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(pf86, "Google", "Chrome", "Application", "chrome.exe"),
        os.path.join(lad, "Google", "Chrome", "Application", "chrome.exe") if lad else "",
        os.path.join(pf, "Microsoft", "Edge", "Application", "msedge.exe"),
    ]
    for c in cands:
        if c and (shutil.which(c) or Path(c).exists()):
            return shutil.which(c) or c
    raise SystemExit("找不到 Chrome/Edge，请设置 CHROME_BIN")

def _find_playwright_mjs() -> str:
    for c in [
        os.environ.get("PLAYWRIGHT_MJS"),
        str(Path.home() / ".workbuddy/skills/聊天记录说唱视频/node_modules/playwright/index.mjs"),
        str(Path.cwd() / "node_modules/playwright/index.mjs"),
    ]:
        if c and Path(c).exists():
            return c
    return ""

BASE = ["--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=1"]

def dump_dom(html_path: Path, width: int, height: int = 1000, budget_ms: int = 3000) -> str:
    pw_mod = _find_playwright_mjs()
    if pw_mod and Path(pw_mod).exists():
        js = f"""
        import {{ chromium }} from {repr(Path(pw_mod).resolve().as_uri())};
        const b = await chromium.launch({{ channel: 'chrome' }});
        const pg = await b.newPage({{ viewport: {{ width: {width}, height: {height} }}, deviceScaleFactor: 1 }});
        await pg.goto({repr(html_path.resolve().as_uri())}, {{ waitUntil: 'load' }});
        await pg.waitForTimeout(800);
        console.log(await pg.content());
        await b.close();
        """
        r = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout
    r = subprocess.run([chrome_bin(), *BASE, f"--window-size={width},{height}", f"--virtual-time-budget={budget_ms}",
                        "--dump-dom", html_path.resolve().as_uri()], capture_output=True, text=True, timeout=120)
    return r.stdout

def measure_height(html_path: Path, width: int) -> int:
    probe = html_path.read_text(encoding="utf-8")
    js = ("<script>window.addEventListener('load',()=>{const d=document.createElement('pre');"
          "d.id='__h';d.textContent='H='+Math.ceil(document.documentElement.scrollHeight);document.body.appendChild(d);});</script>")
    probe = probe.replace("</body>", js + "</body>") if "</body>" in probe else probe + js
    with tempfile.NamedTemporaryFile("w", suffix=".html", dir=html_path.parent, delete=False, encoding="utf-8") as f:
        f.write(probe); tmp = Path(f.name)
    try:
        m = re.search(r"H=(\d+)", dump_dom(tmp, width))
    finally:
        tmp.unlink(missing_ok=True)
    return int(m.group(1)) if m else 2000

def screenshot(html_path: Path, out: Path, width: int, height: int | None = None) -> Path:
    h = height or measure_height(html_path, width)
    pw_mod = _find_playwright_mjs()
    if pw_mod and Path(pw_mod).exists():
        js = f"""
        import {{ chromium }} from {repr(Path(pw_mod).resolve().as_uri())};
        const b = await chromium.launch({{ channel: 'chrome' }});
        const pg = await b.newPage({{ viewport: {{ width: {width}, height: {h} }}, deviceScaleFactor: 1 }});
        await pg.goto({repr(html_path.resolve().as_uri())}, {{ waitUntil: 'load' }});
        await pg.waitForTimeout(800);
        await pg.screenshot({{ path: {repr(str(out.resolve()))}, clip: {{ x: 0, y: 0, width: {width}, height: {h} }} }});
        await b.close();
        """
        r = subprocess.run(["node", "--input-type=module", "-e", js], capture_output=True, text=True, timeout=120)
        if r.returncode == 0 and out.exists():
            return out
    subprocess.run([chrome_bin(), *BASE, f"--window-size={width},{h}", "--virtual-time-budget=3000",
                    f"--screenshot={out.resolve()}", html_path.resolve().as_uri()],
                   capture_output=True, timeout=120, check=True)
    return out

if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("html"); ap.add_argument("out"); ap.add_argument("--width", type=int, default=375)
    a = ap.parse_args()
    print(screenshot(Path(a.html), Path(a.out), a.width))
