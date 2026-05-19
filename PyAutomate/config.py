"""Configuration for the PyAutomate project.

This module defines folders, file type groups, profile storage,
and task schedule defaults.
"""

import os
import getpass

USERNAME = getpass.getuser()
HOME = os.path.expanduser('~')

def _norm(path):
    return os.path.normpath(path)

PROFILE_FILE = os.path.join(HOME, '.pyautomate_profile.json')
ASSISTANT_NAME = 'Nova'

# Common user folders (resolved from the current user's home)
FOLDERS = {
    'downloads': r'C:\Users\kinga\Downloads',
    'documents': r'C:\Users\kinga\Documents',
    'images': r'C:\Users\kinga\Pictures',
    'music': r'C:\Users\kinga\Music',
    'videos': r'C:\Users\kinga\Videos',
    'software': r'C:\Users\kinga\Downloads\Software',
    'archives': r'C:\Users\kinga\Downloads\Archives',
    'code': r'C:\Users\kinga\Documents\Code',
    'others': r'C:\Users\kinga\Downloads\Others',
}

FILE_TYPES = {
    'Documents': ['.pdf', '.docx', '.doc',
                  '.txt', '.xlsx', '.pptx',
                  '.csv'],
    'Images': ['.jpg', '.jpeg', '.png',
               '.gif', '.bmp', '.svg',
               '.webp'],
    'Videos': ['.mp4', '.mkv', '.avi',
               '.mov', '.wmv'],
    'Music': ['.mp3', '.wav', '.flac',
              '.aac', '.m4a'],
    'Archives': ['.zip', '.rar', '.7z',
                 '.tar', '.gz'],
    'Code': ['.py', '.js', '.html',
             '.css', '.java', '.cpp',
             '.c', '.json'],
    'Software': ['.exe', '.msi', '.apk'],
    'Others': []
}

TASK_SCHEDULE = {
    'screenshot_interval': 60,
    'cleanup_days': 30,
    'startup': True,
}

__all__ = [
    'USERNAME', 'HOME', 'PROFILE_FILE', 'ASSISTANT_NAME',
    'FOLDERS', 'FILE_TYPES', 'TASK_SCHEDULE'
]
