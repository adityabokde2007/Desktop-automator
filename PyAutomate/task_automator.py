"""Scheduled task runner for PyAutomate.

Provides `TaskAutomator` to run periodic tasks such as
taking screenshots, cleaning up downloads and monitoring system.
"""

import os
import schedule
import time
import threading
import subprocess
from datetime import datetime
from PIL import ImageGrab
import psutil
from config import TASK_SCHEDULE, FOLDERS


class TaskAutomator:
    def __init__(self, log_callback=None, main_window=None, on_complete=None, screenshot_popup=None):
        self.main_window = main_window
        self.log_callback = log_callback
        self.on_complete = on_complete
        self.screenshot_popup = screenshot_popup
        self.tasks_run = 0
        self.is_running = False
        self.thread = None
        self.logs = []

    def _log(self, msg):
        self.logs.append(msg)
        try:
            if self.log_callback:
                self.log_callback(msg)
        except Exception:
            pass

    def take_screenshot(self):
        try:
            if self.main_window:
                self.main_window.withdraw()
                import time
                time.sleep(0.8)

            screenshots_dir = r"C:\Users\kinga\OneDrive\Desktop\Screenshots"
            os.makedirs(
                screenshots_dir,
                exist_ok=True
            )
            screenshot = ImageGrab.grab()
            timestamp = datetime.now().strftime(
                "%Y%m%d_%H%M%S"
            )
            filename = f"screenshot_{timestamp}.png"
            filepath = os.path.join(
                screenshots_dir, filename
            )
            screenshot.save(filepath)
            self.tasks_run += 1

            if self.main_window:
                self.main_window.deiconify()

            if self.log_callback:
                self.log_callback(
                    f"📸 Screenshot saved: {filename}"
                )

            # Show screenshot success popup
            if self.screenshot_popup:
                try:
                    self.main_window.after(0, lambda: self.screenshot_popup(filename))
                except Exception:
                    pass

            if self.on_complete:
                self.on_complete()
        except Exception as e:
            if self.main_window:
                self.main_window.deiconify()
            if self.log_callback:
                self.log_callback(
                    f"❌ Screenshot error: {str(e)}"
                )
            if self.on_complete:
                self.on_complete()

    def cleanup_downloads(self):
        try:
            downloads = FOLDERS.get('downloads')
            days = TASK_SCHEDULE.get('cleanup_days', 30)
            cutoff = time.time() - (days * 24 * 3600)
            deleted = 0
            if not downloads or not os.path.isdir(downloads):
                msg = 'Downloads folder not found; cleanup skipped'
                self._log(msg)
                return [msg]

            for entry in os.listdir(downloads):
                path = os.path.join(downloads, entry)
                try:
                    if os.path.isfile(path):
                        mtime = os.path.getmtime(path)
                        if mtime < cutoff:
                            try:
                                os.remove(path)
                                deleted += 1
                            except PermissionError:
                                self._log(f"Permission denied deleting {path}")
                                continue
                except Exception as e:
                    self._log(f"Error inspecting {path}: {e}")
                    continue

            msg = f"🗑️ Deleted {deleted} old files"
            self._log(msg)
            self.tasks_run += 1
            return [msg]
        except Exception as e:
            msg = f"Error during cleanup: {e}"
            self._log(msg)
            return [msg]

    def system_monitor(self):
        try:
            cpu = psutil.cpu_percent(interval=1)
            mem = psutil.virtual_memory().percent
            msg = f"System monitor — CPU: {cpu}%, RAM: {mem}%"
            self._log(msg)
            if cpu > 90:
                self.send_notification('High CPU usage', f'CPU at {cpu}%')
            if mem > 90:
                self.send_notification('High memory usage', f'RAM at {mem}%')

            self.tasks_run += 1
            return [msg]
        except Exception as e:
            msg = f"Error in system monitor: {e}"
            self._log(msg)
            return [msg]

    def send_notification(self, title, message):
        try:
            from plyer import notification
            notification.notify(title=title, message=message, timeout=5)
            msg = f"Notification sent: {title} — {message}"
            self._log(msg)
            return [msg]
        except Exception as e:
            msg = f"Failed to send notification: {e}"
            self._log(msg)
            return [msg]

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        if self.log_callback:
            self.log_callback("⚡ Taking screenshot...")
        thread = threading.Thread(
            target=self.take_screenshot,
            daemon=True
        )
        thread.start()

    def stop(self):
        self.is_running = False
        return self.logs

    def run_pending(self):
        try:
            while self.is_running:
                try:
                    schedule.run_pending()
                except Exception as e:
                    self._log(f"Error running scheduled jobs: {e}")
                time.sleep(1)
        finally:
            self.is_running = False


if __name__ == '__main__':
    def printer(m):
        print(m)

    ta = TaskAutomator(log_callback=printer)
    ta.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        ta.stop()
