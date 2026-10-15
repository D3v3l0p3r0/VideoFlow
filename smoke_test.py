"""Сетевой smoke-тест извлечения метаданных VideoFlow.

Запуск: .venv\\Scripts\\python.exe smoke_test.py [URL ...]
Скачивание медиа не выполняется.
"""
from __future__ import annotations

import sys
import tempfile
import time
import traceback
from pathlib import Path

import app  # применяет настройку системного TLS до импорта yt_dlp

MAILRU_MUSIC = "https://m.my.mail.ru/music/songs/%D0%B0-%D0%BF%D0%B0%D1%85%D0%BC%D1%83%D1%82%D0%BE%D0%B2%D0%B0-%D0%BF%D1%80%D0%BE%D1%81%D1%8C%D0%B1%D0%B0-%D1%80%D0%B0%D0%BD%D0%B5%D0%BD%D0%B0%D1%8F-%D0%BF%D1%82%D0%B8%D1%86%D0%B0-984294e0ccdf2d5f2b18fe4ca4b1eb03"

DEFAULT_URLS = [
    "https://ok.ru/video/333222905123",
    "https://rutube.ru/video/8d550691632fe82af9f98c365bdd8f1f/",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://vk.com/video-140332_456239111",
    "https://dzen.ru/video/watch/62795fd2bcf943590297af24?share_to=link",
    "https://yandex.ru/video/preview/8010645166000582981",
    MAILRU_MUSIC,
]

OPEN_TEST_VIDEO = "https://interactive-examples.mdn.mozilla.net/media/cc0-videos/flower.mp4"
OPEN_AUDIO_VIDEO = "https://download.samplelib.com/mp4/sample-5s.mp4"
YANDEX_PREVIEW_VIDEO = "https://yandex.ru/video/preview/8010645166000582981"


def check(url: str) -> bool:
    print(f"\n=== {url} ===", flush=True)
    try:
        with app.create_downloader({
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "noplaylist": True,
            "socket_timeout": 20,
        }) as downloader:
            info = downloader.extract_info(url, download=False)
        print(f"OK: {info.get('extractor')} | {info.get('title')}", flush=True)
        return True
    except Exception:
        traceback.print_exc()
        return False


def check_download_pipeline(url=OPEN_TEST_VIDEO, *, audio_only=False) -> bool:
    """Проверяет DownloadManager на небольшом открытом видео."""
    mode = "AUDIO PIPELINE" if audio_only else "VIDEO PIPELINE"
    print(f"\n=== {mode} {url} ===", flush=True)
    try:
        with tempfile.TemporaryDirectory(prefix="videoflow-test-") as folder:
            events = app.queue.Queue()
            manager = app.DownloadManager(events)
            task = app.DownloadTask(
                url=url,
                title="Open media smoke test",
                destination=folder,
                quality="480p",
                audio_only=audio_only,
                playlist=False,
            )
            manager.add(task)
            deadline = time.monotonic() + 90
            while task.status not in {"Готово", "Ошибка", "Отменено"}:
                if time.monotonic() > deadline:
                    task.cancel_event.set()
                    raise TimeoutError("download pipeline timeout")
                time.sleep(0.1)
            manager.shutdown.set()
            files = [path for path in Path(folder).iterdir() if path.is_file()]
            if task.status != "Готово":
                raise RuntimeError(f"task status: {task.status}")
            if not files or max(path.stat().st_size for path in files) < 10_000:
                raise RuntimeError("downloaded file is missing or empty")
            if audio_only and not any(path.suffix.lower() == ".mp3" for path in files):
                raise RuntimeError("FFmpeg did not produce an MP3 file")
            print(f"OK: downloaded {len(files)} file(s), temporary data cleaned", flush=True)
            return True
    except Exception:
        traceback.print_exc()
        return False


if __name__ == "__main__":
    pipeline = "--download-pipeline" in sys.argv
    yandex_download = "--yandex-download" in sys.argv
    mailru_download = "--mailru-download" in sys.argv
    flags = {"--download-pipeline", "--yandex-download", "--mailru-download"}
    urls = [arg for arg in sys.argv[1:] if arg not in flags] or DEFAULT_URLS
    results = [check(url) for url in urls]
    if pipeline:
        results.append(check_download_pipeline())
        results.append(check_download_pipeline(OPEN_AUDIO_VIDEO, audio_only=True))
    if yandex_download:
        results.append(check_download_pipeline(YANDEX_PREVIEW_VIDEO))
    if mailru_download:
        results.append(check_download_pipeline(MAILRU_MUSIC, audio_only=True))
    raise SystemExit(0 if all(results) else 1)
