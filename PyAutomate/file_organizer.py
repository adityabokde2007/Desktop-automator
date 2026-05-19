"""Watch the Downloads folder and automatically organize files.

Provides the `FileOrganizer` class which observes the user's
Downloads folder and moves new files into categorized folders
based on extensions defined in the project's `config`.
"""

import os
import shutil
import time
import logging
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import FOLDERS, FILE_TYPES
from datetime import datetime


class FileOrganizer(FileSystemEventHandler):
    def __init__(self, log_callback=None):
        self.observer = Observer()
        self.log_callback = log_callback
        self.is_running = False
        self.logs = []

        self.logger = logging.getLogger('PyAutomate.file_organizer')
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _log(self, msg):
        self.logs.append(msg)
        try:
            self.logger.info(msg)
        except Exception:
            pass
        if self.log_callback:
            try:
                self.log_callback(msg)
            except Exception:
                pass

    def on_created(self, event):
        if event.is_directory:
            return
        try:
            # small delay to allow the writing process to finish
            time.sleep(0.2)
            self.organize_file(event.src_path)
        except Exception as e:
            self._log(f"Error handling created event: {e}")

    def _choose_category(self, ext):
        ext = ext.lower()
        for category, exts in FILE_TYPES.items():
            if ext in exts:
                return category
        return 'Others'

    def _dest_folder_for_category(self, category):
        mapping = {
            'Documents': 'documents',
            'Images': 'images',
            'Videos': 'videos',
            'Music': 'music',
            'Archives': 'downloads',
            'Code': 'documents',
            'Software': 'downloads',
            'Others': 'downloads',
        }
        key = mapping.get(category, 'downloads')
        return FOLDERS.get(key, FOLDERS.get('downloads'))

    def organize_file(self, filepath):
        msgs = []
        try:
            if not os.path.exists(filepath):
                return msgs, None
            if os.path.isdir(filepath):
                return msgs, None

            filename = os.path.basename(filepath)
            name, ext = os.path.splitext(filename)
            category = self._choose_category(ext)
            dest_base = self._dest_folder_for_category(category)
            dest_folder = os.path.join(dest_base)
            os.makedirs(dest_folder, exist_ok=True)

            dest_path = os.path.join(dest_folder, filename)

            # handle file in use / transient errors by retrying
            for attempt in range(3):
                try:
                    if os.path.exists(dest_path):
                        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
                        dest_path = os.path.join(dest_folder, f"{name}_{timestamp}{ext}")
                    shutil.move(filepath, dest_path)
                    msg = f"✓ {filename} → {category}"
                    self._log(msg)
                    msgs.append(msg)
                    return msgs, category
                except PermissionError:
                    msg = f"Permission denied moving {filename}; skipping"
                    self._log(msg)
                    msgs.append(msg)
                    return msgs, None
                except (shutil.Error, OSError) as e:
                    # File in use or other transient issue
                    time.sleep(1)
                    last_exc = e
                    continue

            # if we exhausted retries
            msg = f"Failed to move {filename}: {last_exc}"
            self._log(msg)
            msgs.append(msg)
            return msgs, None

        except Exception as e:
            msg = f"Unexpected error organizing {filepath}: {e}"
            self._log(msg)
            msgs.append(msg)
            return msgs, None

    def start(self):
        downloads = FOLDERS.get('downloads')
        if not downloads or not os.path.isdir(downloads):
            self._log('Downloads folder not found; cannot start organizer')
            return self.logs

        event_handler = self
        self.observer.schedule(event_handler, downloads, recursive=False)
        self.observer.start()
        self.is_running = True
        msg = '📁 File Organizer started'
        self._log(msg)
        return self.logs

    def stop(self):
        try:
            self.observer.stop()
            self.observer.join(timeout=1)
        except Exception:
            pass
        self.is_running = False
        msg = '📁 File Organizer stopped'
        self._log(msg)
        return self.logs

    def organize_existing(self):
        downloads = FOLDERS.get('downloads')
        if not downloads or not os.path.isdir(downloads):
            self._log('Downloads folder not found; cannot organize existing files')
            return {
                'total': 0,
                'categories': {},
                'messages': [],
                'logs': self.logs,
            }
        categories = list(FILE_TYPES.keys())
        if 'Others' not in categories:
            categories.append('Others')
        counts = {c: 0 for c in categories}
        total = 0
        messages = []

        for entry in os.listdir(downloads):
            path = os.path.join(downloads, entry)
            if os.path.isfile(path):
                try:
                    msgs, cat = self.organize_file(path)
                    if msgs:
                        messages.extend(msgs)
                    if cat:
                        counts[cat] = counts.get(cat, 0) + 1
                        total += 1
                except Exception as e:
                    self._log(f"Error organizing {path}: {e}")

        return {
            'total': total,
            'categories': counts,
            'messages': messages,
            'logs': self.logs,
        }


if __name__ == '__main__':
    # simple runner for manual testing
    def printer(msg):
        print(msg)

    fo = FileOrganizer(log_callback=printer)
    fo.organize_existing()
    try:
        fo.start()
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        fo.stop()
