#!/usr/bin/env python3
"""Android emulator end-to-end check for the CommuniAI APKs.

For each APK: install -> launch -> onboarding visible -> skip -> login screen -> log in with a user that
exists on the backend running on the CI host (reachable from the emulator as 10.0.2.2:8000) -> dashboard.
Evidence (screenshots, UI dumps, logcat, summary) goes to dist/diagnostics/.
"""
import re
import subprocess
import sys
import time
from pathlib import Path

OUT = Path("dist/diagnostics")
OUT.mkdir(parents=True, exist_ok=True)
PKG = "uz.communiai.app"
EMAIL, PASSWORD = "emulator@example.uz", "Kuchli-Parol-2026"


def adb(*args, check=False, capture=True):
    r = subprocess.run(["adb", *args], capture_output=capture, text=True)
    if check and r.returncode != 0:
        raise RuntimeError(f"adb {' '.join(args)} failed: {r.stderr or r.stdout}")
    return r.stdout if capture else ""


def dump() -> list[dict]:
    adb("shell", "uiautomator", "dump", "/sdcard/ui.xml")
    xml = adb("shell", "cat", "/sdcard/ui.xml")
    nodes = []
    for m in re.finditer(r"<node [^>]*>", xml):
        n = m.group(0)
        get = lambda k: (re.search(k + r'="([^"]*)"', n) or [None, ""])[1]
        b = re.findall(r"\d+", get("bounds"))
        if len(b) == 4:
            nodes.append({"cls": get("class"), "label": (get("content-desc") + " " + get("text")).strip(),
                          "x": (int(b[0]) + int(b[2])) // 2, "y": (int(b[1]) + int(b[3])) // 2})
    return nodes


def find(pattern: str, nodes=None):
    for n in nodes if nodes is not None else dump():
        if re.search(pattern, n["label"]):
            return n
    return None


def wait_for(pattern: str, timeout=45) -> dict | None:
    end = time.time() + timeout
    while time.time() < end:
        n = find(pattern)
        if n:
            return n
        time.sleep(2)
    return None


def tap(n):
    adb("shell", "input", "tap", str(n["x"]), str(n["y"]))


def shot(name):
    with open(OUT / f"{name}.png", "wb") as f:
        f.write(subprocess.run(["adb", "exec-out", "screencap", "-p"], capture_output=True).stdout)


def run_apk(apk: Path) -> list[str]:
    name = apk.stem
    steps, ok = [], True

    def step(desc, passed):
        nonlocal ok
        steps.append(f"{'OK  ' if passed else 'FAIL'} {desc}")
        print(f"[{name}] {steps[-1]}", flush=True)
        ok = ok and passed
        return passed

    adb("uninstall", PKG)
    r = subprocess.run(["adb", "install", "-r", str(apk)], capture_output=True, text=True)
    if not step("install", r.returncode == 0):
        steps.append(r.stdout + r.stderr)
        return steps
    adb("logcat", "-c")
    adb("shell", "monkey", "-p", PKG, "-c", "android.intent.category.LAUNCHER", "1")
    time.sleep(1.5)
    shot(f"{name}-1-splash")
    n = wait_for(r"tkazib yuborish", 60)
    shot(f"{name}-2-onboarding")
    if step("app started, onboarding visible", n is not None):
        tap(n)
        login = wait_for(r"Tizimga kirish", 20)
        shot(f"{name}-3-login")
        if step("login screen", login is not None):
            fields = [x for x in dump() if x["cls"].endswith("EditText")]
            if step("email/password fields found", len(fields) >= 2):
                tap(fields[0]); time.sleep(0.8); adb("shell", "input", "text", EMAIL)
                tap(fields[1]); time.sleep(0.8); adb("shell", "input", "text", PASSWORD)
                time.sleep(0.5)
                adb("shell", "input", "keyevent", "66")  # Enter on the password field submits the form
                home = wait_for(r"Salom", 40)
                shot(f"{name}-4-after-login")
                step("logged in over the network, dashboard visible", home is not None)
    pid = adb("shell", "pidof", PKG).strip()
    step("process still running", bool(pid))
    log = adb("logcat", "-d")
    (OUT / f"{name}-logcat.txt").write_text(log)
    crashes = [l for l in log.splitlines() if re.search(r"FATAL EXCEPTION|E/flutter|Unhandled Exception", l)]
    (OUT / f"{name}-errors.txt").write_text("\n".join(crashes))
    step(f"no crash / Dart errors in logcat ({len(crashes)} lines)", not crashes)
    steps.insert(0, "RESULT: " + ("PASS" if ok else "FAIL"))
    return steps


def main():
    adb("wait-for-device")
    (OUT / "android_version.txt").write_text(adb("shell", "getprop", "ro.build.version.release"))
    overall = True
    report = []
    for apk in [Path("dist/CommuniAI-1.0.0-dev-http.apk"), Path("dist/CommuniAI-1.0.0-release.apk")]:
        steps = run_apk(apk)
        report.append(f"== {apk.name}\n" + "\n".join(steps))
        overall = overall and steps[0].endswith("PASS")
    (OUT / "summary.txt").write_text("\n\n".join(report) + "\n")
    (OUT / "RESULT.txt").write_text("PASS\n" if overall else "FAIL\n")
    print("\n\n".join(report))
    print("SMOKE RESULT:", "PASS" if overall else "FAIL")


if __name__ == "__main__":
    sys.exit(main())
