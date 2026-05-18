import asyncio
import hashlib
import os

import edge_tts

CACHE_DIR = "./cache"


def _get_log_file() -> str:
    return os.path.join(CACHE_DIR, "generate.log")


def _get_cache_path(text: str) -> str:
    md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
    return os.path.join(CACHE_DIR, f"{md5}.mp3")


def _get_voice(text: str) -> str:
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            return "zh-CN-XiaoxiaoNeural"
    return "en-US-JennyNeural"


def _get_rate() -> str:
    return "-10%"


def check_cache(text: str) -> bool:
    return os.path.exists(_get_cache_path(text))


def get_missing_texts(texts: list[str]) -> list[str]:
    return [t for t in texts if not check_cache(t)]


async def _generate_one(text: str) -> None:
    cache_path = _get_cache_path(text)
    if os.path.exists(cache_path):
        return
    os.makedirs(CACHE_DIR, exist_ok=True)
    voice = _get_voice(text)
    rate = _get_rate()
    communicate = edge_tts.Communicate(text, voice, rate=rate)
    await communicate.save(cache_path)

    md5 = hashlib.md5(text.encode("utf-8")).hexdigest()
    try:
        with open(_get_log_file(), "a", encoding="utf-8") as f:
            f.write(f"{md5}\t{text}\n")
    except OSError as e:
        raise RuntimeError(f"写入生成日志失败: {e}")


async def generate_audios(texts: list[str], progress_callback=None) -> None:
    total = len(texts)
    for i, text in enumerate(texts):
        if progress_callback:
            progress_callback(i, total, text)
        await _generate_one(text)
    if progress_callback:
        progress_callback(total, total, "")


def get_audio_url(text: str) -> str:
    return f"file://{os.path.abspath(_get_cache_path(text))}"


def get_audio_path(text: str) -> str:
    return os.path.abspath(_get_cache_path(text))
