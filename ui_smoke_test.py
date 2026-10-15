"""Проверка построения всех экранов CustomTkinter без действий пользователя."""
from __future__ import annotations

import tempfile
import time

import videoflow
import app as core


def main() -> None:
    window = videoflow.VideoFlowApp()
    window.withdraw()
    window.update_idletasks()

    # Проверяем автоматический анализ после изменения поля ссылки.
    mailru_url = (
        "https://m.my.mail.ru/music/songs/"
        "%D0%B0-%D0%BF%D0%B0%D1%85%D0%BC%D1%83%D1%82%D0%BE%D0%B2%D0%B0-"
        "%D0%BF%D1%80%D0%BE%D1%81%D1%8C%D0%B1%D0%B0-"
        "%D1%80%D0%B0%D0%BD%D0%B5%D0%BD%D0%B0%D1%8F-"
        "%D0%BF%D1%82%D0%B8%D1%86%D0%B0-984294e0ccdf2d5f2b18fe4ca4b1eb03"
    )
    window.url_var.set(mailru_url)
    deadline = time.monotonic() + 25
    while window.analyzed_url != mailru_url and time.monotonic() < deadline:
        window.update()
        time.sleep(0.03)
    assert window.analyzed_url == mailru_url, "automatic URL analysis did not finish"
    assert window.mode_var.get() == "Аудио MP3", "audio mode was not selected automatically"
    window.url_var.set("")

    task = core.DownloadTask(
        url="https://example.com/video.mp4",
        title="Тестовая строка очереди VideoFlow",
        destination=tempfile.gettempdir(),
        quality="1080p",
        audio_only=False,
        playlist=False,
    )
    window.manager.tasks[task.id] = task
    window._render_task(task)
    task.status = "Загрузка"
    task.progress = 42.5
    task.speed = "2.4 МБ/с"
    task.eta = "00:12"
    window._render_task(task)
    window.update_idletasks()

    window.show_history()
    window.update_idletasks()
    window.show_downloads()
    assert window.options_panel.winfo_manager() == "grid"
    window.update_idletasks()
    window.toggle_pause()
    assert window.manager.paused.is_set()
    window.show_history()
    window.show_downloads()
    assert window.pause_button.cget("text") == window.tr("resume")
    language = window.language
    window.set_language("en", persist=False)
    assert window.download_button.cget("text") == "Download"
    assert window.options_panel.winfo_manager() == "grid"
    assert task.id in window.task_rows
    window.set_language(language, persist=False)
    window.toggle_pause()
    window.update_idletasks()
    window.toggle_theme()
    window.update_idletasks()
    task.status = "Готово"
    window._render_task(task)
    window.clear_finished()
    assert not window.manager.tasks

    window.manager.shutdown.set()
    window.destroy()
    print("UI_SMOKE_OK")


if __name__ == "__main__":
    main()
