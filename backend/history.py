import json
import os
from datetime import datetime

_HISTORY_FILE = os.path.join(os.path.expanduser('~'), '.pc_optimizer_history.json')
_MAX_ENTRIES  = 50


def add(entry: dict) -> None:
    entries = load()
    entries.insert(0, {
        'timestamp': datetime.now().strftime('%d/%m/%Y %H:%M'),
        **entry,
    })
    entries = entries[:_MAX_ENTRIES]
    try:
        with open(_HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
    except Exception:
        pass


def load() -> list:
    try:
        with open(_HISTORY_FILE, encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []
