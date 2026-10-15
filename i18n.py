"""Interface translations. Internal download states stay language-independent."""

STRINGS = {
    "ru": {
        "downloads": "Загрузки", "history": "История", "theme": "Сменить тему",
        "language": "English", "open_folder": "Открыть папку", "paste": "Вставить",
        "download": "Скачать", "placeholder": "Ссылка на видео или музыку",
        "video": "Видео MP4", "audio": "Аудио MP3", "save_to": "Папка",
        "choose": "Выбрать", "playlist": "Весь плейлист", "queue": "Очередь",
        "clear": "Очистить", "pause": "Пауза", "resume": "Продолжить",
        "empty": "Загрузок пока нет", "empty_history": "История пуста",
        "checking": "Проверяем ссылку…", "fetching": "Получаем сведения…",
        "invalid_url": "Введите полную ссылку https://…", "clipboard_empty": "В буфере обмена нет ссылки",
        "added": "Добавлено в очередь", "paused": "Очередь на паузе", "resumed": "Загрузки продолжены",
        "items": "{count} элементов", "active": "{count} в работе", "done_count": "{count} готово",
        "remaining": "осталось {eta}", "details": "Подробнее", "untitled": "Без названия",
        "download_error": "Не удалось скачать", "source_error": "Источник вернул ошибку.",
        "folder_error": "Не удалось открыть папку", "create_folder_error": "Не удалось создать папку: {error}",
        "close_title": "Загрузка продолжается", "close_question": "Отменить текущую загрузку и закрыть VideoFlow?",
        "about": "Настройки и история хранятся на этом компьютере.\nДвижок: yt-dlp. Обработка медиа: FFmpeg.",
        "ssl_error": "Не удалось проверить HTTPS-сертификат сайта.",
        "unsupported_error": "Эта ссылка пока не поддерживается.",
        "restricted_error": "Доступ к этому материалу ограничен.",
        "login_error": "Этот материал требует входа на сайт.",
        "ffmpeg_error": "Для обработки файла требуется FFmpeg в PATH.",
        "missing_engine": "Не установлен yt-dlp. Запустите run.bat.",
        "В очереди": "В очереди", "Подготовка": "Подготовка", "Загрузка": "Загрузка",
        "Обработка": "Обработка", "Готово": "Готово", "Ошибка": "Ошибка", "Отменено": "Отменено",
    },
    "en": {
        "downloads": "Downloads", "history": "History", "theme": "Switch theme",
        "language": "Русский", "open_folder": "Open folder", "paste": "Paste",
        "download": "Download", "placeholder": "Video or music URL",
        "video": "Video MP4", "audio": "Audio MP3", "save_to": "Folder",
        "choose": "Browse", "playlist": "Entire playlist", "queue": "Queue",
        "clear": "Clear", "pause": "Pause", "resume": "Resume",
        "empty": "No downloads yet", "empty_history": "No history yet",
        "checking": "Checking URL…", "fetching": "Fetching details…",
        "invalid_url": "Enter a complete https:// URL", "clipboard_empty": "No URL in the clipboard",
        "added": "Added to queue", "paused": "Queue paused", "resumed": "Downloads resumed",
        "items": "{count} items", "active": "{count} active", "done_count": "{count} complete",
        "remaining": "{eta} left", "details": "Details", "untitled": "Untitled",
        "download_error": "Download failed", "source_error": "The source returned an error.",
        "folder_error": "Could not open folder", "create_folder_error": "Could not create folder: {error}",
        "close_title": "Download in progress", "close_question": "Cancel the current download and close VideoFlow?",
        "about": "Settings and history are stored on this computer.\nDownload engine: yt-dlp. Media processing: FFmpeg.",
        "ssl_error": "Could not verify the website's HTTPS certificate.",
        "unsupported_error": "This URL is not supported yet.",
        "restricted_error": "Access to this media is restricted.",
        "login_error": "This media requires signing in to the website.",
        "ffmpeg_error": "FFmpeg must be installed in PATH to process this file.",
        "missing_engine": "yt-dlp is missing. Run run.bat.",
        "В очереди": "Queued", "Подготовка": "Preparing", "Загрузка": "Downloading",
        "Обработка": "Processing", "Готово": "Complete", "Ошибка": "Failed", "Отменено": "Cancelled",
    },
}


def tr(language, key, **values):
    return STRINGS.get(language, STRINGS["ru"]).get(key, key).format(**values)


def file_count(language, count):
    if language == "en":
        return f"{count} file{'s' if count != 1 else ''}"
    word = "файлов" if 11 <= count % 100 <= 14 else "файл" if count % 10 == 1 else "файла" if count % 10 in {2, 3, 4} else "файлов"
    return f"{count} {word}"


def speed_text(language, value):
    if language == "en":
        for original, translated in (("ТБ/с", "TB/s"), ("ГБ/с", "GB/s"), ("МБ/с", "MB/s"), ("КБ/с", "KB/s"), ("Б/с", "B/s")):
            value = value.replace(original, translated)
    return value


def error_text(language, message):
    """Localize known engine errors; keep raw site diagnostics for troubleshooting."""
    lowered = message.lower()
    for markers, key in (
        (("https-сертификат", "certificate_verify_failed", "certificate verify failed"), "ssl_error"),
        (("не поддерживается", "unsupported url"), "unsupported_error"),
        (("доступ к этому", "access restricted", "private video"), "restricted_error"),
        (("требуется вход", "login required", "sign in"), "login_error"),
        (("ffmpeg is not installed", "ffprobe and ffmpeg not found"), "ffmpeg_error"),
        (("не установлен yt-dlp",), "missing_engine"),
    ):
        if any(marker in lowered for marker in markers):
            return tr(language, key)
    return message.removeprefix("Ошибка: ").removeprefix("ERROR: ")
