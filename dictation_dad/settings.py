import os

import yaml

DEFAULT_SETTINGS = {
    "audio_duration_factor": 1.5,
    "extra_wait_time": 3.0,
    "min_wait_time": 5.0,
    "countdown_beep_count": 3,
}

SETTINGS_FILE = "./settings.yaml"


class Settings:
    def __init__(self, filepath: str = SETTINGS_FILE):
        self.filepath = filepath
        self._data = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    if not isinstance(data, dict):
                        data = {}
                    return {**DEFAULT_SETTINGS, **data}
            except Exception:
                return DEFAULT_SETTINGS.copy()
        return DEFAULT_SETTINGS.copy()

    def save(self) -> None:
        dirname = os.path.dirname(self.filepath)
        if dirname:
            os.makedirs(dirname, exist_ok=True)
        with open(self.filepath, "w", encoding="utf-8") as f:
            yaml.dump(self._data, f, allow_unicode=True, default_flow_style=False)

    def get(self, key: str):
        return self._data.get(key, DEFAULT_SETTINGS.get(key))

    def set(self, key: str, value) -> None:
        if key in DEFAULT_SETTINGS:
            self._data[key] = value

    def to_dict(self) -> dict:
        return self._data.copy()
