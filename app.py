from __future__ import annotations

import json
import html
import os
import queue
import re
import threading
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

# На Windows Python иногда не видит корневые сертификаты из системного
# хранилища, хотя сайты нормально открываются в браузере. Truststore связывает
# стандартный модуль ssl с хранилищем Windows, не отключая проверку HTTPS.
try:
    import truststore

    truststore.inject_into_ssl()
except ImportError:
    # Резервный вариант для ручного запуска без truststore.
    try:
        import certifi

        os.environ.setdefault("SSL_CERT_FILE", certifi.where())
    except ImportError:
        pass

try:
    import yt_dlp
except ImportError:
    yt_dlp = None


if yt_dlp is not None:
    from yt_dlp.extractor.common import InfoExtractor
    from yt_dlp.utils import clean_html, parse_duration

    class MailRuMusicIE(InfoExtractor):
        IE_NAME = "mailru:music"
        IE_DESC = "Музыка Mail.ru"
        _VALID_URL = r"https?://(?:(?:m|www)\.)?my\.mail\.ru/music/songs/[^?#]*?(?P<id>[0-9a-fA-F]{32})(?:[/?#]|$)"

        def _real_extract(self, url):
            track_id = self._match_id(url).lower()
            webpage = self._download_webpage(url, track_id)
            audio_url = self._search_regex(
                r'data-audio-src=["\'](https?://[^"\']+)["\']',
                webpage, "audio URL")
            title = clean_html(self._search_regex(
                r'<span[^>]+class=["\']eventContent__audio-title["\'][^>]*>(.*?)</span>',
                webpage, "track title", default=None)) or track_id
            artist = clean_html(self._search_regex(
                r'<span[^>]+class=["\']eventContent__audio-author["\'][^>]*>(.*?)</span>',
                webpage, "artist", default=None))
            duration = parse_duration(self._search_regex(
                r'<span[^>]+class=["\']eventContent__audio-dur["\'][^>]*>(.*?)</span>',
                webpage, "duration", default=None))
            display_title = f"{artist} — {title}" if artist else title
            return {
                "id": track_id,
                "title": display_title,
                "track": title,
                "artist": artist,
                "duration": duration,
                "url": audio_url,
                "ext": "mp3",
                "vcodec": "none",
                "acodec": "mp3",
                "format_id": "http-mp3",
                "http_headers": {"Referer": url},
            }
else:
    MailRuMusicIE = None


def create_downloader(options: dict):
    """Создаёт yt-dlp с дополнительными экстракторами VideoFlow."""
    if yt_dlp is None:
        raise RuntimeError("Не установлен yt-dlp")
    downloader = yt_dlp.YoutubeDL(options)
    if MailRuMusicIE is not None:
        custom = MailRuMusicIE(downloader)
        custom_key = custom.ie_key()
        ordered_extractors = {}
        for key, extractor in downloader._ies.items():
            if key == "Generic":
                ordered_extractors[custom_key] = custom
            ordered_extractors[key] = extractor
        if custom_key not in ordered_extractors:
            ordered_extractors[custom_key] = custom
        downloader._ies = ordered_extractors
        downloader._ies_instances[custom_key] = custom
        custom.set_downloader(downloader)
    return downloader


def is_music_url(url: str) -> bool:
    return bool(re.match(
        r"https?://(?:(?:m|www)\.)?my\.mail\.ru/music/songs/", url, re.I))


def apply_extractor_compatibility_fixes() -> None:
    """Локальные адаптеры для известных регрессий сайтов/экстракторов.

    OK.ru с сентября 2026 может отдавать flashvars.metadata уже декодированным
    объектом. yt-dlp 2026.8.19 ожидает строку и вызывает json.loads повторно.
    Ограничиваем исправление только экстрактором Odnoklassniki и сохраняем
    штатное поведение для строкового JSON.
    """
    if yt_dlp is None:
        return
    try:
        from yt_dlp.extractor.odnoklassniki import OdnoklassnikiIE

        original = OdnoklassnikiIE._parse_json
        if getattr(original, "_videoflow_dict_compat", False):
            return

        def parse_json_compat(self, json_string, *args, **kwargs):
            if isinstance(json_string, (dict, list)):
                return json_string
            return original(self, json_string, *args, **kwargs)

        parse_json_compat._videoflow_dict_compat = True
        OdnoklassnikiIE._parse_json = parse_json_compat
    except (ImportError, AttributeError):
        # Новая версия yt-dlp могла переименовать или уже исправить экстрактор.
        pass

    # Yandex Video Preview перешёл с window.Ya.__inline_params__ на React
    # preloadedState. В нём остаётся канонический URL исходного видеохостинга.
    try:
        from yt_dlp.extractor.yandexvideo import YandexVideoPreviewIE
        from yt_dlp.utils import RegexNotFoundError

        original_yandex = YandexVideoPreviewIE._real_extract
        if getattr(original_yandex, "_videoflow_preloaded_state_compat", False):
            return

        def yandex_real_extract_compat(self, url):
            try:
                return original_yandex(self, url)
            except RegexNotFoundError:
                video_id = self._match_id(url)
                webpage = html.unescape(self._download_webpage(
                    url, video_id, note="Downloading current Yandex Video page"))
                target_url = self._search_regex([
                    r'"videoUrl"\s*:\s*"(https?:[^"\\]+(?:\\.[^"\\]*)*)"',
                    r'"embedUrl"\s*:\s*"(https?:[^"\\]+(?:\\.[^"\\]*)*)"',
                    r'"videoSrc"\s*:\s*"(https?:[^"\\]+(?:\\.[^"\\]*)*)"',
                ], webpage, "source video URL")
                target_url = target_url.replace(r"\/", "/").replace(r"\u002F", "/")
                return self.url_result(target_url)

        yandex_real_extract_compat._videoflow_preloaded_state_compat = True
        YandexVideoPreviewIE._real_extract = yandex_real_extract_compat
    except (ImportError, AttributeError):
        pass


apply_extractor_compatibility_fixes()


APP_NAME = "VideoFlow"
APP_DIR = Path(os.getenv("APPDATA", Path.home())) / APP_NAME
SETTINGS_FILE = APP_DIR / "settings.json"
HISTORY_FILE = APP_DIR / "history.json"


PALETTES = {
    "dark": {
        "bg": "#0b1020", "panel": "#121a2e", "panel2": "#17223b",
        "text": "#eef2ff", "muted": "#91a0bd", "accent": "#7c5cff",
        "accent2": "#9a84ff", "success": "#36d399", "danger": "#fb7185",
        "border": "#263451", "entry": "#0e1628",
    },
    "light": {
        "bg": "#f3f5fb", "panel": "#ffffff", "panel2": "#edf0fa",
        "text": "#172033", "muted": "#69758d", "accent": "#6246ea",
        "accent2": "#7c64f2", "success": "#0f9f6e", "danger": "#dc4960",
        "border": "#d8deeb", "entry": "#ffffff",
    },
}


class DownloadCancelled(Exception):
    pass


@dataclass
class DownloadTask:
    url: str
    title: str
    destination: str
    quality: str
    audio_only: bool
    playlist: bool
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    status: str = "В очереди"
    progress: float = 0.0
    speed: str = "—"
    eta: str = "—"
    cancel_event: threading.Event = field(default_factory=threading.Event, repr=False)


def load_json(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def save_json(path: Path, data) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    temp.replace(path)


def valid_url(value: str) -> bool:
    parsed = urlparse(value.strip())
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


ANSI_ESCAPE = re.compile(r"\x1b(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")


def clean_error(error: object) -> str:
    """Удаляет терминальные цвета yt-dlp и поясняет частые ошибки."""
    text = ANSI_ESCAPE.sub("", str(error)).replace("ERROR: ", "").strip()
    lowered = text.lower()
    if "certificate_verify_failed" in lowered or "certificate verify failed" in lowered:
        return (
            "Не удалось проверить HTTPS-сертификат сайта. Перезапустите программу "
            "через run.bat — он установит поддержку системных сертификатов Windows. "
            "Если ошибка останется, проверьте дату и время Windows, обновления системы, "
            "антивирус с функцией проверки HTTPS и корпоративный прокси.\n\n"
            f"Технические сведения: {text}"
        )
    if "unsupported url" in lowered:
        return "Эта ссылка пока не поддерживается установленной версией yt-dlp. Обновите зависимости через run.bat."
    if "access restricted" in lowered or "private video" in lowered:
        return "Доступ к этому видео ограничен владельцем или платформой. VideoFlow загружает только общедоступные ролики."
    if "login required" in lowered or "sign in" in lowered:
        return "Для просмотра этого ролика требуется вход на платформу. Импорт учётных данных в текущей версии не поддерживается."
    return text


def format_duration(seconds) -> str:
    if not seconds:
        return "не указана"
    seconds = int(seconds)
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}" if hours else f"{minutes:02d}:{secs:02d}"


def human_bytes(value) -> str:
    if not value:
        return "—"
    number = float(value)
    for unit in ("Б/с", "КБ/с", "МБ/с", "ГБ/с"):
        if number < 1024:
            return f"{number:.1f} {unit}"
        number /= 1024
    return f"{number:.1f} ТБ/с"


def human_eta(value) -> str:
    if value is None:
        return "—"
    value = int(value)
    minutes, seconds = divmod(value, 60)
    hours, minutes = divmod(minutes, 60)
    return f"{hours:d}:{minutes:02d}:{seconds:02d}" if hours else f"{minutes:02d}:{seconds:02d}"


class DownloadManager:
    def __init__(self, events: queue.Queue):
        self.events = events
        self.tasks: dict[str, DownloadTask] = {}
        self.pending: queue.Queue[DownloadTask] = queue.Queue()
        self.paused = threading.Event()
        self.shutdown = threading.Event()
        self.current: DownloadTask | None = None
        self.worker = threading.Thread(target=self._run, daemon=True, name="download-worker")
        self.worker.start()

    def add(self, task: DownloadTask) -> None:
        self.tasks[task.id] = task
        self.pending.put(task)
        self.events.put(("task", task.id, {}))

    def toggle_pause(self) -> bool:
        if self.paused.is_set():
            self.paused.clear()
            return False
        self.paused.set()
        return True

    def cancel(self, task_id: str) -> None:
        task = self.tasks.get(task_id)
        if task and task.status not in {"Готово", "Ошибка", "Отменено"}:
            task.cancel_event.set()
            if task is not self.current:
                task.status = "Отменено"
                self.events.put(("task", task.id, {}))

    def _run(self) -> None:
        while not self.shutdown.is_set():
            try:
                task = self.pending.get(timeout=0.25)
            except queue.Empty:
                continue
            while self.paused.is_set() and not self.shutdown.is_set():
                time.sleep(0.2)
            if task.cancel_event.is_set():
                self.pending.task_done()
                continue
            self.current = task
            try:
                self._download(task)
            except DownloadCancelled:
                self._update(task, status="Отменено")
                self.events.put(("history", task.id, {"result": "Отменено"}))
            except Exception as exc:
                clean = clean_error(exc)
                self._update(task, status="Ошибка")
                self.events.put(("history", task.id, {"result": f"Ошибка: {clean}"}))
                self.events.put(("log", task.id, {"message": clean}))
            finally:
                self.current = None
                self.pending.task_done()

    def _update(self, task: DownloadTask, **changes) -> None:
        for key, value in changes.items():
            setattr(task, key, value)
        self.events.put(("task", task.id, changes))

    def _download(self, task: DownloadTask) -> None:
        if yt_dlp is None:
            raise RuntimeError("Не установлен yt-dlp. Запустите run.bat или pip install -r requirements.txt")

        height = int(task.quality.rstrip("p"))
        if task.audio_only:
            format_rule = "bestaudio/best"
        else:
            format_rule = (
                f"bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/"
                f"bestvideo[height<={height}]+bestaudio/best[height<={height}]/best"
            )

        def progress_hook(data):
            if task.cancel_event.is_set():
                raise DownloadCancelled()
            state = data.get("status")
            if state == "downloading":
                total = data.get("total_bytes") or data.get("total_bytes_estimate") or 0
                downloaded = data.get("downloaded_bytes") or 0
                percent = (downloaded / total * 100) if total else task.progress
                self._update(
                    task, status="Загрузка", progress=min(percent, 99.8),
                    speed=human_bytes(data.get("speed")), eta=human_eta(data.get("eta")),
                )
            elif state == "finished":
                self._update(task, status="Обработка", progress=99.9, speed="—", eta="—")

        output = str(Path(task.destination) / ("%(playlist_index)03d - %(title)s [%(id)s].%(ext)s" if task.playlist else "%(title)s [%(id)s].%(ext)s"))
        options = {
            "format": format_rule,
            "outtmpl": output,
            "noplaylist": not task.playlist,
            "windowsfilenames": True,
            "continuedl": True,
            "overwrites": False,
            "retries": 3,
            "fragment_retries": 3,
            "socket_timeout": 20,
            "progress_hooks": [progress_hook],
            "quiet": True,
            "noprogress": True,
            "no_warnings": True,
            "merge_output_format": "mp4",
        }
        if task.audio_only:
            options["postprocessors"] = [{
                "key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"
            }]

        self._update(task, status="Подготовка")
        with create_downloader(options) as downloader:
            downloader.download([task.url])
        if task.cancel_event.is_set():
            raise DownloadCancelled()
        self._update(task, status="Готово", progress=100.0, speed="—", eta="—")
        self.events.put(("history", task.id, {"result": "Готово"}))


