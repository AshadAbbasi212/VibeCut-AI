#!/usr/bin/env python3
"""Check that required tools exist. Prints install hints. Exit code 1 if a required tool is missing."""
import platform
import re
import shutil
import subprocess
import sys

REQUIRED_OK = True


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=20)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr) else ""
    except Exception as exc:  # noqa: BLE001
        return f"error: {exc}"


def check(name, ok, detail, hint="", required=True):
    global REQUIRED_OK
    status = "OK     " if ok else ("MISSING" if required else "optional")
    print(f"[{status}] {name:<10} {detail}")
    if not ok and hint:
        print(f"           hint: {hint}")
    if not ok and required:
        REQUIRED_OK = False


def main():
    v = sys.version_info
    check("python", v >= (3, 10), f"{v.major}.{v.minor}.{v.micro}", "Install Python 3.10+")

    node = shutil.which("node")
    if node:
        ver = run(["node", "--version"])
        m = re.match(r"v(\d+)", ver)
        check("node", bool(m) and int(m.group(1)) >= 20, ver, "Install Node.js 20+ (LTS)")
    else:
        check("node", False, "not found", "Install Node.js 20+ (LTS)")

    npm_bin = shutil.which("npm") or shutil.which("npm.cmd")
    check("npm", bool(npm_bin), run([npm_bin, "--version"]) if npm_bin else "not found",
          "npm ships with Node.js")
    for tool in ("ffmpeg", "ffprobe"):
        p = shutil.which(tool)
        check(tool, bool(p), run([tool, "-version"]) if p else "not found",
              "macOS: brew install ffmpeg | Ubuntu: sudo apt install ffmpeg | Windows: winget install Gyan.FFmpeg")
    check("git", bool(shutil.which("git")), run(["git", "--version"]) if shutil.which("git") else "not found",
          "Install git")
    smi = shutil.which("nvidia-smi")
    check("nvidia-gpu", bool(smi), "CUDA GPU detected" if smi else "none (CPU mode: use WHISPER_MODEL=small, int8)",
          required=False)
    print(f"\nPlatform: {platform.platform()}")
    if not REQUIRED_OK:
        print("\nSome required tools are missing. Install them and re-run.")
        sys.exit(1)
    print("\nAll required tools present.")


if __name__ == "__main__":
    main()
