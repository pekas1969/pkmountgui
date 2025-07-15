import sys
import os
import subprocess
import shutil
from PyQt6 import QtWidgets, QtGui, QtCore

FSTAB_PATH = "/etc/fstab"
CHECK_INTERVAL = 5000  # Millisekunden


class MountEntry:
    def __init__(self, device, mount_point, fs_type, options):
        self.device = device
        self.mount_point = mount_point
        self.fs_type = fs_type
        self.options = options

    def is_mounted(self):
        with open("/proc/mounts") as f:
            return any(line.split()[1] == self.mount_point for line in f)

    def is_reachable(self):
        return os.path.exists(self.mount_point)

    def requires_root(self):
        return "user" not in self.options.split(",")


def read_custom_fstab_entries():
    entries = []
    with open(FSTAB_PATH, "r") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split()
            if len(parts) < 4:
                continue
            device, mount_point, fs_type, options = parts[:4]

            # Systemmounts ignorieren
            if mount_point in ["/", "/boot", "/boot/efi", "/proc", "/sys", "/dev", "/run"]:
                continue

            entries.append(MountEntry(device, mount_point, fs_type, options))
    return entries


def get_terminal_command():
    candidates = [
        ["gnome-terminal", "--working-directory"],
        ["konsole", "--workdir"],
        ["xfce4-terminal", "--working-directory"],
        ["x-terminal-emulator", "--working-directory"],
        ["lxterminal", "--working-directory"],
        ["mate-terminal", "--working-directory"],
        ["alacritty", "--directory"],
        ["kitty", "--directory"],
        ["terminator", "--working-directory"]
    ]
    for cmd in candidates:
        if shutil.which(cmd[0]):
            return cmd
    return None


class TrayApp(QtWidgets.QSystemTrayIcon):
    def __init__(self, entries, app):
        super().__init__()
        self.entries = entries
        self.app = app
        self.menu = QtWidgets.QMenu()
        self.setIcon(QtGui.QIcon.fromTheme("drive-harddisk"))
        self.setContextMenu(self.menu)

        self.mount_actions = {}
        self.unmount_actions = {}
        self.open_file_manager_actions = {}
        self.open_terminal_actions = {}
        self.status_icons = {}
        self.submenus = {}

        self.build_menu()

        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_status)
        self.timer.start(CHECK_INTERVAL)

        self.update_status()
        self.show()

    def build_menu(self):
        for entry in self.entries:
            submenu = QtWidgets.QMenu(entry.mount_point, self.menu)
            self.submenus[entry.mount_point] = submenu  # Referenz behalten

            mount_action = submenu.addAction("Mount")
            unmount_action = submenu.addAction("Unmount")
            open_file_manager_action = submenu.addAction("Im Dateimanager öffnen")
            open_terminal_action = submenu.addAction("Im Terminal öffnen")

            mount_action.triggered.connect(lambda checked, e=entry: self.mount(e))
            unmount_action.triggered.connect(lambda checked, e=entry: self.unmount(e))
            open_file_manager_action.triggered.connect(lambda checked, e=entry: self.open_file_manager(e))
            open_terminal_action.triggered.connect(lambda checked, e=entry: self.open_terminal(e))

            self.mount_actions[entry.mount_point] = mount_action
            self.unmount_actions[entry.mount_point] = unmount_action
            self.open_file_manager_actions[entry.mount_point] = open_file_manager_action
            self.open_terminal_actions[entry.mount_point] = open_terminal_action

            action_with_icon = QtGui.QAction(entry.mount_point)
            action_with_icon.setMenu(submenu)
            self.menu.addAction(action_with_icon)

            self.status_icons[entry.mount_point] = action_with_icon

        self.menu.addSeparator()
        quit_action = self.menu.addAction("Beenden")
        quit_action.triggered.connect(self.app.quit)

    def update_status(self):
        for entry in self.entries:
            is_mounted = entry.is_mounted()
            is_reachable = entry.is_reachable()

            icon = QtGui.QIcon()
            if is_mounted:
                icon = QtGui.QIcon.fromTheme("emblem-default")  # grüner Punkt

            action = self.status_icons[entry.mount_point]
            action.setIcon(icon)

            self.mount_actions[entry.mount_point].setEnabled(not is_mounted and is_reachable)
            self.unmount_actions[entry.mount_point].setEnabled(is_mounted)
            self.open_file_manager_actions[entry.mount_point].setEnabled(is_mounted)
            self.open_terminal_actions[entry.mount_point].setEnabled(is_mounted)

    def mount(self, entry):
        if entry.requires_root():
            subprocess.run(["pkexec", "mount", entry.mount_point])
        else:
            subprocess.run(["mount", entry.mount_point])
        QtCore.QTimer.singleShot(1000, self.update_status)

    def unmount(self, entry):
        if entry.requires_root():
            subprocess.run(["pkexec", "umount", entry.mount_point])
        else:
            subprocess.run(["umount", entry.mount_point])
        QtCore.QTimer.singleShot(1000, self.update_status)

    def open_file_manager(self, entry):
        if sys.platform.startswith("linux"):
            subprocess.Popen(["xdg-open", entry.mount_point])
        elif sys.platform == "darwin":
            subprocess.Popen(["open", entry.mount_point])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["explorer", entry.mount_point])

    def open_terminal(self, entry):
        if sys.platform.startswith("linux"):
            cmd = get_terminal_command()
            if cmd:
                subprocess.Popen([cmd[0], cmd[1], entry.mount_point])
            else:
                QtWidgets.QMessageBox.warning(None, "Fehler", "Kein Terminal-Emulator gefunden.")
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-a", "Terminal", entry.mount_point])
        elif sys.platform.startswith("win"):
            subprocess.Popen(["cmd", "/K", "cd", entry.mount_point])


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    entries = read_custom_fstab_entries()
    if not entries:
        QtWidgets.QMessageBox.critical(None, "Fehler", "Keine benutzerdefinierten fstab-Einträge gefunden.")
        sys.exit(1)
    tray = TrayApp(entries, app)
    sys.exit(app.exec())
