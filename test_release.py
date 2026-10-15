"""Offline checks for localization, shared branding and language switching."""
import json
import string
import tempfile
import unittest
from types import SimpleNamespace
from pathlib import Path
from unittest.mock import patch

from PIL import Image

import app as core
import branding
import i18n
import videoflow


def close_test_window(window):
    window.manager.shutdown.set()
    for timer in window.tk.call("after", "info"):
        window.after_cancel(timer)
    window.destroy()


class LocalizationTests(unittest.TestCase):
    def test_translation_keys_and_parameters_match(self):
        self.assertEqual(set(i18n.STRINGS["ru"]), set(i18n.STRINGS["en"]))
        formatter = string.Formatter()
        for key, value in i18n.STRINGS["ru"].items():
            ru_fields = {field for _, field, _, _ in formatter.parse(value) if field is not None}
            en_fields = {field for _, field, _, _ in formatter.parse(i18n.STRINGS["en"][key]) if field is not None}
            self.assertEqual(ru_fields, en_fields, key)

    def test_display_helpers(self):
        self.assertEqual(i18n.file_count("en", 1), "1 file")
        self.assertEqual(i18n.file_count("ru", 23), "23 файла")
        self.assertEqual(i18n.speed_text("en", "3.2 МБ/с"), "3.2 MB/s")
        self.assertEqual(i18n.error_text("en", "Доступ к этому видео ограничен владельцем"), i18n.tr("en", "restricted_error"))


class BrandingTests(unittest.TestCase):
    def test_assets_match_single_source(self):
        png = videoflow.resource_path("assets/brand.png")
        ico = videoflow.resource_path("assets/brand.ico")
        self.assertEqual(Image.open(png).convert("RGBA").tobytes(), branding.draw_brand().tobytes())
        with Image.open(ico) as image:
            self.assertTrue({(16, 16), (32, 32), (48, 48), (256, 256)}.issubset(image.ico.sizes()))

    def test_language_switch_keeps_queue_and_input(self):
        with tempfile.TemporaryDirectory(prefix="videoflow-locale-") as folder:
            settings = Path(folder) / "settings.json"
            with patch.object(core, "SETTINGS_FILE", settings), patch.object(core, "HISTORY_FILE", Path(folder) / "history.json"):
                window = videoflow.VideoFlowApp()
                window.withdraw()
                try:
                    task = core.DownloadTask(url="https://example.com/demo.mp4", title="Sample title",
                        destination=folder, quality="720p", audio_only=False, playlist=False)
                    window.manager.tasks[task.id] = task
                    window.manager.paused.set()
                    window.url_var.set("https://example.com/next.mp4")
                    window.after_cancel(window.auto_analyze_job)
                    window.auto_analyze_job = None
                    window.set_language("en")
                    window.update_idletasks()
                    self.assertEqual(window.url_var.get(), "https://example.com/next.mp4")
                    self.assertIs(window.manager.tasks[task.id], task)
                    self.assertEqual(window.task_rows[task.id].status_label.cget("text"), "Queued")
                    self.assertEqual(window.download_button.cget("text"), "Download")
                    self.assertEqual(window.pause_button.cget("text"), "Resume")
                    self.assertEqual(window.options_panel.winfo_manager(), "grid")
                    self.assertEqual(json.loads(settings.read_text(encoding="utf-8"))["language"], "en")
                    if videoflow.sys.platform == "win32":
                        self.assertTrue(window._iconbitmap_method_called)
                        # Tcl returns an empty name for native Windows ICOs.
                        # Ask the actual HWND instead of relying on that string.
                        import ctypes
                        from ctypes import wintypes
                        user32 = ctypes.windll.user32
                        user32.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
                        user32.GetAncestor.restype = wintypes.HWND
                        user32.SendMessageW.argtypes = [wintypes.HWND, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
                        user32.SendMessageW.restype = ctypes.c_void_p
                        handle = user32.GetAncestor(window.winfo_id(), 2)
                        self.assertTrue(user32.SendMessageW(handle, 0x7F, 1, 0))  # WM_GETICON, ICON_BIG
                    window.show_history()
                    window.set_language("ru", persist=False)
                    self.assertEqual(window.current_page, "history")
                    window.show_downloads()
                    self.assertEqual(window.pause_button.cget("text"), "Продолжить")
                finally:
                    close_test_window(window)


class ShortcutTests(unittest.TestCase):
    def setUp(self):
        self.window = videoflow.VideoFlowApp()
        self.window.geometry("1000x660+40+40")
        self.window.update()

    def tearDown(self):
        if self.window.auto_analyze_job:
            self.window.after_cancel(self.window.auto_analyze_job)
            self.window.auto_analyze_job = None
        close_test_window(self.window)

    def press(self, widget, keysym, keycode, state):
        widget.focus_force()
        self.window.update()
        # Let Windows map the physical key under the current keyboard layout.
        widget.event_generate("<KeyPress>", keycode=keycode, state=state)
        self.window.update()

    def test_actual_ctrl_v_shift_insert_and_history_routing(self):
        window = self.window
        url = "https://example.com/public-video.mp4"
        with patch.object(window, "clipboard_get", return_value=url) as clipboard:
            self.press(window.url_entry._entry, "v", 0x56, 0x4)
            self.assertEqual(window.url_var.get(), url)
            self.assertEqual(clipboard.call_count, 1)
            self.assertIsNotNone(window.auto_analyze_job)
            window.url_var.set("")
            self.press(window.url_entry._entry, "Insert", 0x2D, 0x1)
            self.assertEqual(window.url_var.get(), url)
            self.assertEqual(clipboard.call_count, 2)
            window.show_history()
            self.press(window, "v", 0x56, 0x4)
            self.assertEqual(window.current_page, "downloads")
            self.assertEqual(window.url_var.get(), url)

    def test_russian_layout_and_folder_native_paste(self):
        window = self.window
        window.url_entry._entry.focus_force()
        window.update()
        with patch.object(window, "clipboard_get", return_value="https://example.com/audio.mp3"):
            result = window._handle_shortcut(SimpleNamespace(keysym="Cyrillic_em", keycode=0x56, state=0x4))
            self.assertEqual(result, "break")
            self.assertEqual(window.url_var.get(), "https://example.com/audio.mp3")
        window.show_history()
        window._handle_shortcut(SimpleNamespace(keysym="Cyrillic_de", keycode=0x4C, state=0x4))
        self.assertEqual(window.current_page, "downloads")
        folder_input = window.folder_entry._entry
        folder_input.focus_force()
        window.update()
        with patch.object(folder_input, "event_generate") as native_paste, patch.object(window, "paste_url") as paste_url:
            window._handle_shortcut(SimpleNamespace(keysym="Cyrillic_em", keycode=0x56, state=0x4))
            native_paste.assert_called_once_with("<<Paste>>")
            paste_url.assert_not_called()


if __name__ == "__main__":
    unittest.main()
