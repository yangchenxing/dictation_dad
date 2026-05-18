import csv
import hashlib
import os
from abc import ABC, abstractmethod
from io import StringIO


class DictationStrategy(ABC):
    @abstractmethod
    def get_suffix(self) -> str:
        pass

    @abstractmethod
    def validate_csv(self, content: str) -> list[str]:
        pass

    @abstractmethod
    def get_entries(self, file_path: str) -> list[dict]:
        pass

    @abstractmethod
    def get_play_params(self) -> dict:
        pass

    def get_speech_texts(self, entries: list[dict]) -> list[str]:
        return [e["speech"] for e in entries]

    def get_audio_url(self, text: str) -> str:
        md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
        cache_path = os.path.abspath(os.path.join("./cache", f"{md5}.mp3"))
        return f"file://{cache_path}"


class ChWordStrategy(DictationStrategy):
    def get_suffix(self) -> str:
        return ".ch_word.csv"

    def validate_csv(self, content: str) -> list[str]:
        errors = []
        try:
            reader = csv.DictReader(StringIO(content))
            if reader.fieldnames is None:
                return ["无法读取CSV标题行"]
            if "speech" not in reader.fieldnames:
                errors.append("缺少必需列 'speech'")
            for i, row in enumerate(reader, start=2):
                if "speech" in row and not row["speech"].strip():
                    errors.append(f"第{i}行 'speech' 为空")
        except csv.Error as e:
            errors.append(f"CSV格式错误: {e}")
        return errors

    def get_entries(self, file_path: str) -> list[dict]:
        entries = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                speech = row.get("speech", "").strip()
                if speech:
                    entries.append({
                        "speech": speech,
                        "answer": speech,
                        "audio_url": self.get_audio_url(speech),
                    })
        return entries

    def get_play_params(self) -> dict:
        return {
            "play_count": 2,
            "interval_desc": "间隔2秒",
            "wait_time": {
                "audio_duration_factor": 1.5,
                "extra_wait_time": 3.0,
                "min_wait_time": 5.0,
            },
            "countdown_beep_count": 3,
        }


class EnWordStrategy(DictationStrategy):
    def get_suffix(self) -> str:
        return ".en_word.csv"

    def validate_csv(self, content: str) -> list[str]:
        errors = []
        try:
            reader = csv.DictReader(StringIO(content))
            if reader.fieldnames is None:
                return ["无法读取CSV标题行"]
            for col in ("speech", "answer"):
                if col not in reader.fieldnames:
                    errors.append(f"缺少必需列 '{col}'")
            for i, row in enumerate(reader, start=2):
                for col in ("speech", "answer"):
                    if col in row and not row[col].strip():
                        errors.append(f"第{i}行 '{col}' 为空")
        except csv.Error as e:
            errors.append(f"CSV格式错误: {e}")
        return errors

    def get_entries(self, file_path: str) -> list[dict]:
        entries = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                speech = row.get("speech", "").strip()
                answer = row.get("answer", "").strip()
                if speech and answer:
                    entries.append({
                        "speech": speech,
                        "answer": answer,
                        "audio_url": self.get_audio_url(speech),
                    })
        return entries

    def get_play_params(self) -> dict:
        return {
            "play_count": 2,
            "interval_desc": "间隔2秒",
            "wait_time": {
                "audio_duration_factor": 1.2,
                "extra_wait_time": 5.0,
                "min_wait_time": 10.0,
            },
            "countdown_beep_count": 3,
        }


class ChClassicalStrategy(DictationStrategy):
    def get_suffix(self) -> str:
        return ".ch_classical.csv"

    def validate_csv(self, content: str) -> list[str]:
        errors = []
        try:
            reader = csv.DictReader(StringIO(content))
            if reader.fieldnames is None:
                return ["无法读取CSV标题行"]
            for col in ("speech", "answer"):
                if col not in reader.fieldnames:
                    errors.append(f"缺少必需列 '{col}'")
            for i, row in enumerate(reader, start=2):
                for col in ("speech", "answer"):
                    if col in row and not row[col].strip():
                        errors.append(f"第{i}行 '{col}' 为空")
        except csv.Error as e:
            errors.append(f"CSV格式错误: {e}")
        return errors

    def get_entries(self, file_path: str) -> list[dict]:
        entries = []
        with open(file_path, "r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                speech = row.get("speech", "").strip()
                answer = row.get("answer", "").strip()
                if speech and answer:
                    entries.append({
                        "speech": speech,
                        "answer": answer,
                        "audio_url": self.get_audio_url(speech),
                    })
        return entries

    def get_play_params(self) -> dict:
        return {
            "play_count": 1,
            "interval_desc": "间隔3秒",
            "wait_time": {
                "audio_duration_factor": 1.5,
                "extra_wait_time": 10.0,
                "min_wait_time": 15.0,
            },
            "countdown_beep_count": 3,
        }


def get_strategy(filename_or_suffix: str) -> DictationStrategy:
    if filename_or_suffix.endswith(".ch_word.csv"):
        return ChWordStrategy()
    elif filename_or_suffix.endswith(".en_word.csv"):
        return EnWordStrategy()
    elif filename_or_suffix.endswith(".ch_classical.csv"):
        return ChClassicalStrategy()
    else:
        raise ValueError("不支持的文件类型")
