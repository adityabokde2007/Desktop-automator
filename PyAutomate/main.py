import sys
import os
from gui import PyAutomateGUI
from system_commander import SystemCommander

try:
    import winreg
except Exception:
    winreg = None


def add_to_startup():
    if not winreg:
        return False
    try:
        script_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'main.py'))
        # Use Python executable so the script runs properly
        value = f'"{sys.executable}" "{script_path}"'
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, "PyAutomate", 0, winreg.REG_SZ, value)
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def remove_from_startup():
    if not winreg:
        return False
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\Run",
            0, winreg.KEY_SET_VALUE
        )
        try:
            winreg.DeleteValue(key, "PyAutomate")
        except FileNotFoundError:
            pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def hide_console():
    try:
        import ctypes
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def main():
    hide_console()
    if any(arg.lower() in ('--commander', 'commander', 'voice') for arg in sys.argv[1:]):
        commander = SystemCommander()
        commander.run()
        return

    app = PyAutomateGUI()
    app.run()


if __name__ == "__main__":
    main()
