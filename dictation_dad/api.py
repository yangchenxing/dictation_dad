import asyncio
import base64
import functools
import logging
import os
import threading
from concurrent.futures import ThreadPoolExecutor

from dictation_dad.file_manager import FileManager
from dictation_dad.settings import Settings
from dictation_dad.strategies import get_strategy
from dictation_dad.tts import generate_audios, get_missing_texts, get_audio_path

logger = logging.getLogger(__name__)


def log_api_call(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        method_name = func.__name__
        logger.info("API call start: %s, args=%s, kwargs=%s", method_name, args[1:], kwargs)
        try:
            result = func(*args, **kwargs)
            logger.info("API call end: %s, success=%s", method_name, result.get("success"))
            logger.debug("API call end: %s, result=%s", method_name, result)
            return result
        except Exception as e:
            logger.error("API call error: %s, exception=%s", method_name, e)
            raise
    return wrapper


class TTSProgressTracker:
    def __init__(self):
        self.lock = threading.Lock()
        self.progress = {"current": 0, "total": 0, "text": "", "done": False, "error": None}

    def callback(self, current: int, total: int, text: str):
        with self.lock:
            self.progress["current"] = current
            self.progress["total"] = total
            self.progress["text"] = text

    def finish(self):
        with self.lock:
            self.progress["done"] = True

    def fail(self, error):
        with self.lock:
            self.progress["error"] = str(error)
            self.progress["done"] = True

    def get(self):
        with self.lock:
            return self.progress.copy()


class API:
    def __init__(self, vocabulary_root: str = "vocabulary"):
        self.file_manager = FileManager(vocabulary_root)
        self.settings = Settings()
        self.tts_tracker = None
        self.executor = ThreadPoolExecutor(max_workers=1)

    @log_api_call
    def list_directory(self, path=""):
        try:
            return {"success": True, "data": self.file_manager.list_directory(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def create_directory(self, path, name):
        try:
            self.file_manager.create_directory(path, name)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def delete_file(self, path):
        try:
            self.file_manager.delete_file(path)
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def preview_csv(self, path):
        try:
            return {"success": True, "data": self.file_manager.preview_csv(path)}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def upload_csv(self, path, filename, content, overwrite=False):
        try:
            if not any(filename.endswith(s) for s in (".ch_word.csv", ".en_word.csv", ".ch_classical.csv")):
                return {"success": False, "error": "扩展名不符合要求"}
            suffix = next(s for s in (".ch_word.csv", ".en_word.csv", ".ch_classical.csv") if filename.endswith(s))
            strategy = get_strategy(suffix)
            errors = strategy.validate_csv(content)
            if errors:
                return {"success": False, "error": "内容不合规: " + "; ".join(errors)}
            self.file_manager.save_file(path, filename, content, overwrite)
            return {"success": True}
        except FileExistsError as e:
            return {"success": False, "error": str(e), "exists": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def get_dictation_info(self, path):
        try:
            strategy = get_strategy(path)
            abs_path = self.file_manager._normalize_path(path)
            entries = strategy.get_entries(abs_path)
            missing = get_missing_texts(strategy.get_speech_texts(entries))
            play_params = strategy.get_play_params()
            wait = play_params["wait_time"].copy()
            wait["audio_duration_factor"] = self.settings.get("audio_duration_factor")
            wait["extra_wait_time"] = self.settings.get("extra_wait_time")
            wait["min_wait_time"] = self.settings.get("min_wait_time")
            play_params["wait_time"] = wait
            play_params["countdown_beep_count"] = self.settings.get("countdown_beep_count")
            return {
                "success": True,
                "data": {
                    "entries": entries,
                    "missing_count": len(missing),
                    "play_params": play_params,
                }
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def start_pre_generate(self, path):
        try:
            strategy = get_strategy(path)
            abs_path = self.file_manager._normalize_path(path)
            entries = strategy.get_entries(abs_path)
            texts = strategy.get_speech_texts(entries)
            missing = get_missing_texts(texts)
            if not missing:
                return {"success": True, "data": {"started": False}}

            self.tts_tracker = TTSProgressTracker()
            self.tts_tracker.progress["total"] = len(missing)

            def task():
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                    loop.run_until_complete(generate_audios(missing, self.tts_tracker.callback))
                    self.tts_tracker.finish()
                except Exception as e:
                    self.tts_tracker.fail(e)

            self.executor.submit(task)
            return {"success": True, "data": {"started": True, "total": len(missing)}}
        except Exception as e:
            return {"success": False, "error": str(e)}

    @log_api_call
    def get_pre_generate_progress(self):
        if self.tts_tracker is None:
            return {"success": True, "data": {"done": True}}
        return {"success": True, "data": self.tts_tracker.get()}

    @log_api_call
    def get_settings(self):
        return {"success": True, "data": self.settings.to_dict()}

    @log_api_call
    def save_settings(self, data):
        for key in ("audio_duration_factor", "extra_wait_time", "min_wait_time", "countdown_beep_count"):
            if key in data:
                self.settings.set(key, data[key])
        self.settings.save()
        return {"success": True}

    @log_api_call
    def get_audio_base64(self, speech_text):
        try:
            audio_path = get_audio_path(speech_text)
            if not os.path.isfile(audio_path):
                return {"success": False, "error": "音频文件不存在"}
            with open(audio_path, "rb") as f:
                data = base64.b64encode(f.read()).decode("ascii")
            return {"success": True, "data": data}
        except Exception as e:
            return {"success": False, "error": str(e)}
