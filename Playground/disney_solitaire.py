# -*- coding: utf-8 -*-
"""
Automatisierung über ADB + UI-Prüfung (Windows freundlich)

Voraussetzungen:
- ADB im PATH (adb --version funktioniert)
- USB-Debugging + ADB (WLAN oder USB)
- Koordinaten unten angepasst
"""

import subprocess as sp
import time
import shutil
from pathlib import Path
import re

# ==================== KONFIG ====================
OUTDIR = Path(r"C:\Users\Viet-Desktop\Downloads\Disney_Solitaire_Automation")
OUTDIR.mkdir(parents=True, exist_ok=True)

# Loops & Pausen
LOOPS = 50
PAUSE_AFTER_COLLECT_S = 1

# Koordinaten
TOGGLE_AUTO = (947, 317)     # Auto-Zeit Toggle
OPEN_TIME   = (520, 670)     # "Uhrzeit einstellen"
HOUR_UP     = (314, 868)     # +1h
MIN_UP      = (785, 868)     # +1min
TIME_OK     = (791, 1033)    # OK im Time Picker
COLLECT     = (540, 2150)    # "EINSAMMELN"

# Prüfen auf diese Strings (case-insensitive, Teilstrings ok)
NEEDLE_AFTER_TOGGLE_OFF = "Uhrzeit einstellen"
NEEDLE_TIMEPICKER_OPEN  = "OK"
NEEDLE_BACK_TO_SETTINGS = "Datum"
NEEDLE_AUTOMATIC_TEXT   = "Automatisch"
NEEDLE_COLLECT_VISIBLE  = "einsammeln"   # optional: Spiele-UI liefert oft keinen Dump
# =================================================


def run(cmd, check=False, capture=True):
    """Run command and return (returncode, stdout, stderr)."""
    if capture:
        proc = sp.run(cmd, stdout=sp.PIPE, stderr=sp.PIPE, text=True, shell=False)
    else:
        proc = sp.run(cmd, shell=False)
    if check and proc.returncode != 0:
        raise RuntimeError(f"Command failed: {' '.join(cmd)}\nSTDOUT:\n{proc.stdout}\nSTDERR:\n{proc.stderr}")
    return proc.returncode, (proc.stdout if capture else ""), (proc.stderr if capture else "")


def adb(*args, check=False):
    return run(["adb", *args], check=check)


def swipe(x, y, duration_ms=200):
    rc, out, err = adb("shell", "input", "swipe", str(x), str(y), str(x), str(y), str(duration_ms))
    if rc != 0:
        print(f"[E] swipe({x},{y}) failed: {err.strip()}")


def wait_for_device():
    rc, out, err = adb("wait-for-device")
    if rc != 0:
        print("[E] adb wait-for-device failed.")
    else:
        print("[i] Gerät verbunden.")


def dump_ui(dest: Path) -> bool:
    """
    Erstellt einen UI-Dump auf dem Gerät und zieht ihn lokal nach 'dest'.
    Gibt True zurück, wenn die Datei existiert und >0 Bytes hat.
    """
    # Dump auf Gerät
    rc, out, err = adb("shell", "uiautomator", "dump", "/sdcard/uidump.xml")
    # adb meldet Erfolg über stdout
    if rc != 0:
        print("[E] uiautomator dump RC != 0")
        print("    STDOUT:", out.strip())
        print("    STDERR:", err.strip())
        return False
    if "dumped to" not in out.lower():
        print("[W] Unerwartete Dump-Antwort:", out.strip())
    # Pull auf PC
    rc, out2, err2 = adb("pull", "/sdcard/uidump.xml", str(dest))
    if rc != 0:
        print("[E] adb pull fehlgeschlagen")
        print("    STDOUT:", out2.strip())
        print("    STDERR:", err2.strip())
        return False
    if not dest.exists() or dest.stat().st_size < 10:
        print("[E] Dump-Datei fehlt oder ist zu klein:", dest)
        return False
    return True


def show_texts(xml_path: Path, limit=20):
    try:
        text = xml_path.read_text(encoding="utf-8", errors="ignore")
    except Exception as e:
        print(f"[E] Konnte XML nicht lesen: {e}")
        return "", []
    texts = re.findall(r'text="([^"]*)"', text)
    print("— Erste Texte —")
    for t in texts[:limit]:
        if t:
            print(f'  {t}')
    return text, texts[:limit]


def wait_for_text(needle: str, timeout_s: int = 10, tag: str = "") -> bool:
    """
    Wiederholt dump/pull, zeigt die ersten Texte, speichert Debug-Kopien
    und prüft case-insensitive, ob 'needle' irgendwo in der XML vorkommt.
    """
    start = time.time()
    attempt = 0
    dest = OUTDIR / "ui.xml"
    print(f"[i] Warte auf '{needle}' (Timeout {timeout_s}s){' — '+tag if tag else ''}")
    while time.time() - start < timeout_s:
        attempt += 1
        ok = dump_ui(dest)
        if not ok:
            print(f"[W] Dump fehlgeschlagen (Versuch {attempt})")
            time.sleep(1)
            continue
        print(f"[i] Dump gespeichert: {dest}")
        xml_text, _ = show_texts(dest, limit=99999)
        # Debug-Kopie
        safe = re.sub(r"[^A-Za-z0-9_.-]", "_", needle)
        shutil.copyfile(dest, OUTDIR / f"ui_debug_{safe}_{attempt}.xml")

        if re.search(re.escape(needle), xml_text, re.IGNORECASE):
            print(f"[✓] Gefunden: {needle}")
            return True
        time.sleep(1)

    print(f"[×] Timeout: '{needle}' nicht gefunden.")
    return False


def main():
    print("=== Starte Automatisierung (Python) ===")
    print(f"[i] Logs & XML unter: {OUTDIR}")
    print(f"Loops: {LOOPS}")
    wait_for_device()

    for i in range(1, LOOPS + 1):
        print(f"\n=== Durchlauf {i} ===")

        # 1) Auto-Zeit AUS
        swipe(*TOGGLE_AUTO)
        if not wait_for_text(NEEDLE_AFTER_TOGGLE_OFF, timeout_s=12, tag="nach Toggle OFF"):
            print("[!] Weiter trotzdem… (UI-Text nicht gefunden)")

        # 2) Uhrzeit +2h
        swipe(*OPEN_TIME)
        if not wait_for_text(NEEDLE_TIMEPICKER_OPEN, timeout_s=12, tag="TimePicker offen"):
            print("[!] 'OK' im TimePicker nicht gefunden – versuche dennoch +2h/OK")
        swipe(*HOUR_UP)
        time.sleep(0.4)
        swipe(*MIN_UP)
        time.sleep(0.4)
        swipe(*TIME_OK)
        if not wait_for_text(NEEDLE_BACK_TO_SETTINGS, timeout_s=12, tag="zurück zu Datum & Uhrzeit"):
            print("[!] 'Datum' nicht gefunden – fahre fort…")

        # 3) Auto-Zeit wieder AN
        swipe(*TOGGLE_AUTO)
        if not wait_for_text(NEEDLE_AUTOMATIC_TEXT, timeout_s=12, tag="Automatisch sichtbar"):
            print("[!] 'Automatisch' nicht gefunden – fahre fort…")

        # 4) Einsammeln im Spiel
        swipe(*COLLECT)
        # Spiele sind oft nicht dumpbar – optionaler Check:
        dump_ui(OUTDIR / "ui.xml")  # ignorieren, wenn’s fehlschlägt
        print(f"[i] Warte {PAUSE_AFTER_COLLECT_S}s…")
        time.sleep(PAUSE_AFTER_COLLECT_S)

    print("\n✓ Fertig.")
    try:
        # Fenster offen halten bei Doppelklick-Start
        input("Enter drücken zum Schließen…")
    except EOFError:
        pass


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print("\n[CRASH] Unerwarteter Fehler:\n", e)
        try:
            input("Enter drücken zum Schließen…")
        except EOFError:
            pass
