"""Lightweight persistence for the PyAutomate welcome/profile flow."""

import json
import os

from config import PROFILE_FILE, ASSISTANT_NAME

DEFAULT_PROFILE = {
    'user_name': '',
    'assistant_name': ASSISTANT_NAME,
}


def load_profile():
    profile = DEFAULT_PROFILE.copy()
    try:
        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, 'r', encoding='utf-8') as handle:
                data = json.load(handle)
                if isinstance(data, dict):
                    profile.update(data)
    except Exception:
        pass

    user_name = str(profile.get('user_name', '')).strip()
    assistant_name = str(profile.get('assistant_name', ASSISTANT_NAME)).strip() or ASSISTANT_NAME

    profile['user_name'] = user_name
    profile['assistant_name'] = assistant_name
    return profile


def save_profile(user_name=None, assistant_name=None):
    profile = load_profile()

    if user_name is not None:
        cleaned_name = str(user_name).strip()
        if cleaned_name:
            profile['user_name'] = cleaned_name

    if assistant_name is not None:
        cleaned_assistant = str(assistant_name).strip()
        if cleaned_assistant:
            profile['assistant_name'] = cleaned_assistant

    directory = os.path.dirname(PROFILE_FILE)
    try:
        if directory:
            os.makedirs(directory, exist_ok=True)
        with open(PROFILE_FILE, 'w', encoding='utf-8') as handle:
            json.dump(profile, handle, indent=2)
        return profile
    except Exception:
        return profile
