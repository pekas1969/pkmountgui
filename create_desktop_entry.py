#!/usr/bin/env python3
import os

# Verzeichnis, von dem das Skript aufgerufen wird
base_dir = os.getcwd()
exec_path = os.path.join(base_dir, "pkmountgui.py")

# Optional: Ein Standard-Icon (kann angepasst oder leer gelassen werden)
icon_path = "/usr/share/icons/hicolor/48x48/apps/folder-harddisk.svg"

desktop_entry_content = f"""[Desktop Entry]
Type=Application
Name=PKMountGUI
Comment=Mount-Manager im Tray
Exec=python3 "{exec_path}"
Icon={icon_path}
Terminal=false
Categories=System;
"""

def write_desktop_file(path):
    with open(path, "w") as f:
        f.write(desktop_entry_content)
    os.chmod(path, 0o755)
    print(f"Desktop-Datei erstellt: {path}")

def main():
    system_path = "/usr/share/applications/pkmountgui.desktop"
    try:
        write_desktop_file(system_path)
        print("Systemweiter Menüeintrag erstellt.")
    except PermissionError:
        print(f"FEHLER: Keine Rechte für {system_path}. Bitte als root ausführen oder manuell anlegen.")

    desktop_dir = os.path.expanduser("~/Desktop")
    os.makedirs(desktop_dir, exist_ok=True)
    desktop_file_path = os.path.join(desktop_dir, "pkmountgui.desktop")
    write_desktop_file(desktop_file_path)
    print("Desktop-Verknüpfung erstellt.")

if __name__ == "__main__":
    main()
