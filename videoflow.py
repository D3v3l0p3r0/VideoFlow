from __future__ import annotations

import os
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox
from urllib.parse import urlparse

import customtkinter as ctk
from PIL import Image, ImageDraw

import app as core
import branding
from i18n import tr, file_count, speed_text, error_text


VERSION = "1.4.1"
FONT = "Segoe UI"
ACCENT = "#8B7BF6"
ACCENT_HOVER = "#A093FF"
BG = ("#F7F7F8", "#131416")
PANEL = ("#FFFFFF", "#1B1C20")
SIDEBAR = ("#EEEEF1", "#101113")
FIELD = ("#F4F4F6", "#24252B")
BORDER = ("#E2E2E8", "#303137")
TEXT = ("#202128", "#EDEDF1")
MUTED = ("#757680", "#999AA5")
FAINT = ("#999AA4", "#64656F")
HOVER = ("#E7E7ED", "#2B2C32")
GREEN = ("#22835C", "#73CBA0")
RED = ("#BC3E56", "#F48A9D")
TERMINAL = {"Готово", "Ошибка", "Отменено"}
SELF_TEST_URLS = (
    "https://ok.ru/video/333222905123",
    "https://rutube.ru/video/8d550691632fe82af9f98c365bdd8f1f/",
    "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    "https://vk.com/video-140332_456239111",
    "https://dzen.ru/video/watch/62795fd2bcf943590297af24?share_to=link",
    "https://yandex.ru/video/preview/8010645166000582981",
    "https://m.my.mail.ru/music/songs/%D0%B0-%D0%BF%D0%B0%D1%85%D0%BC%D1%83%D1%82%D0%BE%D0%B2%D0%B0-%D0%BF%D1%80%D0%BE%D1%81%D1%8C%D0%B1%D0%B0-%D1%80%D0%B0%D0%BD%D0%B5%D0%BD%D0%B0%D1%8F-%D0%BF%D1%82%D0%B8%D1%86%D0%B0-984294e0ccdf2d5f2b18fe4ca4b1eb03",
)


def resource_path(relative):
    return Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / relative


def font(size=13, bold=False):
    return ctk.CTkFont(FONT, size, "bold" if bold else "normal")


def shorten(text, limit=76):
    return text if len(text) <= limit else text[:limit - 1].rstrip() + "…"


def source_name(url, language="ru"):
    host = (urlparse(url).hostname or "").removeprefix("www.")
    for fragment, name in (("youtu", "YouTube"), ("rutube", "Rutube"), ("vk", "VK Video" if language == "en" else "VK Видео"),
                           ("ok.ru", "OK"), ("dzen", "Dzen" if language == "en" else "Дзен"),
                           ("yandex", "Yandex Video" if language == "en" else "Яндекс Видео"),
                           ("mail.ru", "Mail.ru Music" if language == "en" else "Музыка Mail.ru")):
        if fragment in host:
            return name
    return host


def icon(name, size=18, color=None):
    """Чёткие одноцветные значки, нарисованные в одной системе линий."""
    if name == "brand":
        logo = branding.draw_brand(128)
        return ctk.CTkImage(light_image=logo, dark_image=logo, size=(size, size))
    def draw_icon(ink):
        im = Image.new("RGBA", (96, 96))
        d = ImageDraw.Draw(im)
        line = lambda xy: d.line(xy, fill=ink, width=6, joint="curve")
        if name == "download":
            line((48, 19, 48, 62)); line((29, 44, 48, 63, 67, 44))
            line((22, 65, 22, 77, 74, 77, 74, 65))
        elif name == "history":
            d.arc((18, 15, 81, 79), 210, 525, fill=ink, width=6)
            line((17, 18, 17, 38, 37, 38)); line((48, 29, 48, 49, 62, 58))
        elif name == "folder":
            d.line((16, 72, 16, 25, 39, 25, 47, 34, 80, 34, 80, 72, 16, 72), fill=ink, width=6, joint="curve")
        elif name == "settings":
            for x, y in ((25, 35), (48, 59), (71, 41)):
                line((x, 17, x, 79)); d.ellipse((x-8, y-8, x+8, y+8), fill=ink)
        elif name == "video":
            d.rounded_rectangle((15, 22, 81, 74), radius=9, outline=ink, width=5)
            d.polygon((41, 35, 41, 61, 61, 48), fill=ink)
        elif name == "audio":
            line((38, 67, 38, 25, 72, 18, 72, 59))
            d.ellipse((20, 59, 39, 76), fill=ink); d.ellipse((54, 52, 73, 69), fill=ink)
        elif name == "check":
            line((23, 48, 40, 65, 74, 31))
        elif name == "close":
            line((28, 28, 68, 68)); line((68, 28, 28, 68))
        elif name == "sun":
            d.ellipse((33, 33, 63, 63), outline=ink, width=5)
            for p in ((48, 12, 48, 23), (48, 73, 48, 84), (12, 48, 23, 48), (73, 48, 84, 48),
                      (23, 23, 30, 30), (66, 66, 73, 73), (23, 73, 30, 66), (66, 30, 73, 23)):
                line(p)
        elif name == "clipboard":
            d.rounded_rectangle((25, 24, 71, 80), radius=7, outline=ink, width=5)
            d.rounded_rectangle((36, 16, 60, 30), radius=4, fill=ink)
        elif name == "info":
            d.ellipse((16, 16, 80, 80), outline=ink, width=5)
            d.ellipse((44, 30, 52, 38), fill=ink)
            line((48, 46, 48, 66))
        elif name == "language":
            d.ellipse((16, 16, 80, 80), outline=ink, width=5)
            d.ellipse((33, 16, 63, 80), outline=ink, width=4)
            line((18, 48, 78, 48))
        return im
    return ctk.CTkImage(light_image=draw_icon(color or "#646570"),
                        dark_image=draw_icon(color or "#A3A4AE"), size=(size, size))


def quiet_button(parent, text, command, image=None, width=100, **kwargs):
    return ctk.CTkButton(parent, text=text, command=command, image=image, width=width,
                         height=34, corner_radius=8, fg_color="transparent", hover_color=HOVER,
                         text_color=MUTED, font=font(12), **kwargs)


class TaskRow(ctk.CTkFrame):
    def __init__(self, master, task, owner):
        super().__init__(master, fg_color=PANEL, corner_radius=12, height=96)
        self.task, self.owner = task, owner
        self.grid_columnconfigure(1, weight=1)
        self.symbol = ctk.CTkLabel(self, text="", image=icon("audio" if task.audio_only else "video", 22),
                                    width=44, height=44, corner_radius=10, fg_color=FIELD)
        self.symbol.grid(row=0, column=0, rowspan=2, padx=(16, 14), pady=17)
        self.title_label = ctk.CTkLabel(self, text=task.title, anchor="w", font=font(14, True), text_color=TEXT)
        self.title_label.grid(row=0, column=1, sticky="ew", pady=(15, 0))
        self.detail = ctk.CTkLabel(self, text="", anchor="w", text_color=MUTED, font=font(11))
        self.detail.grid(row=1, column=1, sticky="ew", pady=(0, 12))
        self.status_label = ctk.CTkLabel(self, text="", anchor="e", width=96, font=font(12), text_color=MUTED)
        self.status_label.grid(row=0, column=2, rowspan=2, padx=(8, 10))
        self.action = quiet_button(self, "", self.perform_action, width=32, image=icon("close", 16))
        self.action.grid(row=0, column=3, rowspan=2, padx=(0, 13))
        self.progress = ctk.CTkProgressBar(self, height=3, corner_radius=2, progress_color=ACCENT, fg_color=FIELD)
        self.progress.grid(row=2, column=0, columnspan=4, sticky="ew", padx=16, pady=(0, 10))
        self.bind("<Configure>", self.fit_title)
        self.refresh()

    def fit_title(self, _event=None):
        available = max(80, self.winfo_width() - 260)
        text = self.task.title
        f = self.title_label.cget("font")
        if f.measure(text) > available:
            while text and f.measure(text + "…") > available:
                text = text[:-1]
            text = text.rstrip() + "…"
        self.title_label.configure(text=text)

    def perform_action(self):
        if self.task.status == "Готово":
            self.owner.open_folder(self.task.destination)
        elif self.task.status == "Ошибка":
            messagebox.showerror(self.owner.tr("download_error"), error_text(self.owner.language,
                self.owner.task_errors.get(self.task.id, self.owner.tr("source_error"))))
        elif self.task.status not in TERMINAL:
            self.owner.cancel_task(self.task.id)

    def refresh(self):
        t = self.task
        base = f"{source_name(t.url, self.owner.language)}   ·   {'MP3' if t.audio_only else 'MP4  /  ' + t.quality}"
        if t.status == "Загрузка":
            base += f"   ·   {speed_text(self.owner.language, t.speed)}   ·   {self.owner.tr('remaining', eta=t.eta)}"
        self.detail.configure(text=base)
        color = GREEN if t.status == "Готово" else RED if t.status == "Ошибка" else ACCENT if t.status in {"Загрузка", "Обработка"} else MUTED
        self.status_label.configure(text=f"{t.progress:.0f}%" if t.status == "Загрузка" else self.owner.tr(t.status), text_color=color)
        self.progress.set(max(0, min(t.progress / 100, 1)))
        if t.status in TERMINAL or t.status == "В очереди":
            self.progress.grid_remove()
        else:
            self.progress.grid()
        self.action.configure(image=icon("folder" if t.status == "Готово" else "info" if t.status == "Ошибка" else "close", 16),
                              state="disabled" if t.status == "Отменено" else "normal")
        self.fit_title()


class VideoFlowApp(ctk.CTk):
    def __init__(self):
        self.settings = core.load_json(core.SETTINGS_FILE, {})
        self.language = self.settings.get("language", "ru")
        if self.language not in {"ru", "en"}:
            self.language = "ru"
        self.appearance = self.settings.get("theme", "dark")
        ctk.set_appearance_mode(self.appearance)
        if sys.platform == "win32":
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("VideoFlow.Desktop")
        super().__init__()
        self.title(f"VideoFlow {VERSION}")
        self.geometry("1160x760")
        self.minsize(1000, 660)
        self.configure(fg_color=BG)
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self._apply_brand()
        self.events = queue.Queue()
        self.manager = core.DownloadManager(self.events)
        self.history = core.load_json(core.HISTORY_FILE, [])
        self.task_rows = {}
        self.task_errors = {}
        self.analyzed = None
        self.analyzed_url = None
        self.analysis_in_progress_url = None
        self.auto_analyze_job = None
        self.analysis_serial = 0
        self.current_page = "downloads"
        self.last_notice = ""
        self.notice_error = False
        self.url_var = ctk.StringVar()
        self.folder_var = ctk.StringVar(value=self.settings.get("folder", str(Path.home() / "Downloads")))
        self.quality_var = ctk.StringVar(value=self.settings.get("quality", "1080p"))
        self.mode_var = ctk.StringVar(value="Аудио MP3" if self.settings.get("audio_only", False) else "Видео MP4")
        self.format_var = ctk.StringVar(value=self.tr("audio") if self.mode_var.get() == "Аудио MP3" else self.tr("video"))
        self.playlist_var = ctk.BooleanVar(value=self.settings.get("playlist", False))
        self.url_var.trace_add("write", self._on_url_changed)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._build_sidebar()
        self.content = ctk.CTkFrame(self, fg_color="transparent", corner_radius=0)
        self.content.grid(row=0, column=1, sticky="nsew", padx=34, pady=(27, 19))
        self.show_downloads()
        self.bind_class("VideoFlowShortcuts", "<KeyPress>", self._handle_shortcut)
        self._install_shortcuts()
        self.after(100, self._process_events)

    def _install_shortcuts(self):
        # Bind before Tk's Entry/Text class handlers to prevent a double paste.
        def visit(widget):
            tags = widget.bindtags()
            if "VideoFlowShortcuts" not in tags:
                widget.bindtags(("VideoFlowShortcuts", *tags))
            for child in widget.winfo_children():
                visit(child)
        visit(self)

    def _handle_shortcut(self, event):
        control = bool(event.state & 0x4)
        shift = bool(event.state & 0x1)
        alt = bool(event.state & 0x20000)
        key = str(event.keysym).lower()
        # Windows virtual key codes stay the same in English/Russian layouts.
        physical_v = sys.platform == "win32" and event.keycode == 0x56
        physical_l = sys.platform == "win32" and event.keycode == 0x4C
        if control and not alt and (physical_l or key == "l"):
            return self.focus_url()
        paste = (control and not alt and (physical_v or key == "v")) or (shift and not control and key == "insert")
        if not paste:
            return None
        focused = self.focus_get()
        url_input = getattr(getattr(self, "url_entry", None), "_entry", None)
        if focused is not None and focused is not url_input and focused.winfo_class() in {"Entry", "TEntry", "Text", "TCombobox", "Spinbox"}:
            # Keep normal text insertion in the folder field and other editors.
            focused.event_generate("<<Paste>>")
        else:
            self.paste_url()
        return "break"

    def tr(self, key, **values):
        return tr(self.language, key, **values)

    def _apply_brand(self):
        if sys.platform == "win32":
            # iconbitmap also prevents CustomTkinter from setting its own icon.
            path = str(resource_path("assets/brand.ico"))
            self.iconbitmap(default=path)
            self.iconbitmap(path)
        else:
            from PIL import ImageTk
            self.window_icon = ImageTk.PhotoImage(branding.draw_brand(64))
            self.iconphoto(True, self.window_icon)

    def _build_sidebar(self):
        sidebar = self.sidebar = ctk.CTkFrame(self, width=184, corner_radius=0, fg_color=SIDEBAR)
        sidebar.grid(row=0, column=0, sticky="nsew")
        sidebar.grid_propagate(False)
        sidebar.grid_columnconfigure(0, weight=1)
        sidebar.grid_rowconfigure(4, weight=1)
        brand = ctk.CTkFrame(sidebar, fg_color="transparent")
        brand.grid(row=0, column=0, padx=21, pady=(29, 33), sticky="ew")
        ctk.CTkLabel(brand, text="", image=icon("brand", 29)).pack(side="left")
        ctk.CTkLabel(brand, text="VideoFlow", font=font(18, True), text_color=TEXT).pack(side="left", padx=(9, 0))
        self.nav_buttons = {}
        for row, (key, name, symbol, action) in enumerate((
            ("downloads", self.tr("downloads"), "download", self.show_downloads),
            ("history", self.tr("history"), "history", self.show_history),
        ), 2):
            button = ctk.CTkButton(sidebar, text=name, image=icon(symbol, 17), anchor="w", height=39,
                                   corner_radius=8, font=font(13), fg_color="transparent", hover_color=HOVER,
                                   text_color=MUTED, command=action)
            button.grid(row=row, column=0, padx=12, pady=3, sticky="ew")
            self.nav_buttons[key] = button
        quiet_button(sidebar, self.tr("theme"), self.toggle_theme, icon("sun", 16), anchor="w").grid(
            row=5, column=0, padx=16, pady=(0, 9), sticky="ew")
        self.language_button = quiet_button(sidebar, self.tr("language"), self.toggle_language, icon("language", 16), anchor="w")
        self.language_button.grid(row=6, column=0, padx=16, pady=(0, 9), sticky="ew")
        quiet_button(sidebar, f"VideoFlow  {VERSION}", self.show_about, width=145, anchor="w").grid(
            row=7, column=0, padx=17, pady=(10, 17), sticky="ew")

    def _clear_content(self, page):
        self.current_page = page
        for child in self.content.winfo_children():
            child.destroy()
        self.task_rows.clear()
        for name, button in self.nav_buttons.items():
            button.configure(fg_color=("#E0DDEC", "#27242F") if name == page else "transparent",
                             text_color=("#6352A6", "#C0B3FF") if name == page else MUTED)

    def _header(self, title):
        header = ctk.CTkFrame(self.content, fg_color="transparent")
        header.pack(fill="x", pady=(0, 23))
        copy = ctk.CTkFrame(header, fg_color="transparent")
        copy.pack(side="left")
        ctk.CTkLabel(copy, text=title, font=font(28, True), text_color=TEXT, anchor="w").pack(anchor="w")
        quiet_button(header, self.tr("open_folder"), self.open_folder, icon("folder", 17), width=139).pack(side="right", anchor="n", pady=6)

    def show_downloads(self):
        self._clear_content("downloads")
        self._header(self.tr("downloads"))
        composer = ctk.CTkFrame(self.content, fg_color=PANEL, corner_radius=15, border_width=1, border_color=BORDER)
        composer.pack(fill="x", pady=(0, 23))
        composer.grid_columnconfigure(0, weight=1)
        entry_frame = ctk.CTkFrame(composer, fg_color=FIELD, corner_radius=9)
        entry_frame.grid(row=1, column=0, columnspan=2, sticky="ew", padx=(18, 10), pady=(18, 0))
        entry_frame.grid_columnconfigure(0, weight=1)
        self.url_entry = ctk.CTkEntry(entry_frame, textvariable=self.url_var, height=46, font=font(13),
                                      placeholder_text=self.tr("placeholder"), fg_color=FIELD,
                                      text_color=TEXT, placeholder_text_color=FAINT, border_width=0)
        self.url_entry.grid(row=0, column=0, sticky="ew", padx=(7, 0))
        self.url_entry.bind("<Return>", lambda _: self.add_task())
        # CTkEntry не показывает встроенный placeholder с textvariable.
        self.url_placeholder = ctk.CTkLabel(entry_frame, text=self.tr("placeholder"),
                                            font=font(13), text_color=FAINT, fg_color=FIELD)
        self.url_placeholder.bind("<Button-1>", lambda _: self.url_entry.focus_set())
        quiet_button(entry_frame, self.tr("paste"), self.paste_url, icon("clipboard", 16), width=98).grid(row=0, column=1, padx=(2, 6))
        self.download_button = ctk.CTkButton(composer, text=self.tr("download"), image=icon("download", 17, "#17131F"),
                                              compound="right", width=132, height=46, corner_radius=9,
                                              fg_color=ACCENT, hover_color=ACCENT_HOVER, text_color="#17131F",
                                              text_color_disabled="#474052", font=font(13, True), command=self.add_task)
        self.download_button.grid(row=1, column=2, padx=(0, 18), pady=(18, 0))
        self.meta_label = ctk.CTkLabel(composer, text=self.last_notice, font=font(11), text_color=MUTED, anchor="w")
        # Статус занимает место только при анализе, результате или ошибке.
        toolbar = ctk.CTkFrame(composer, fg_color="transparent")
        toolbar.grid(row=4, column=0, columnspan=3, sticky="ew", padx=18, pady=(13, 10))
        self.format_var.set(self.tr("audio") if self.mode_var.get() == "Аудио MP3" else self.tr("video"))
        self.format_control = ctk.CTkSegmentedButton(toolbar, values=[self.tr("video"), self.tr("audio")], variable=self.format_var,
                                                      height=33, corner_radius=7, border_width=3, font=font(12),
                                                      fg_color=FIELD, selected_color=("#DDD7F8", "#3A324F"),
                                                      selected_hover_color=("#D3CAEF", "#483E62"),
                                                      text_color=TEXT, unselected_color=FIELD, unselected_hover_color=HOVER,
                                                      command=self._format_changed)
        self.format_control.pack(side="left")
        self.quality_control = ctk.CTkOptionMenu(toolbar, values=["2160p", "1440p", "1080p", "720p", "480p"],
                                                   variable=self.quality_var, width=99, height=32, font=font(12),
                                                   fg_color=PANEL, button_color=PANEL, button_hover_color=HOVER,
                                                   text_color=MUTED, dropdown_fg_color=PANEL, dropdown_text_color=TEXT,
                                                   dropdown_hover_color=HOVER)
        self.quality_control.pack(side="left", padx=(12, 0))
        self.playlist_control = ctk.CTkCheckBox(toolbar, text=self.tr("playlist"), variable=self.playlist_var,
                        checkbox_width=17, checkbox_height=17, border_width=1, corner_radius=4,
                        text_color=MUTED, border_color=FAINT, fg_color=ACCENT, hover_color=ACCENT_HOVER,
                        checkmark_color="#17131F", font=font(12))
        self.playlist_control.pack(side="right", padx=(8, 2))
        self.options_panel = ctk.CTkFrame(composer, fg_color="transparent")
        self.options_panel.grid_columnconfigure(1, weight=1)
        ctk.CTkLabel(self.options_panel, text=self.tr("save_to"), font=font(12), text_color=MUTED).grid(row=0, column=0, padx=(0, 12))
        self.folder_entry = ctk.CTkEntry(self.options_panel, textvariable=self.folder_var, height=34, border_width=0,
                                         fg_color=FIELD, text_color=TEXT, font=font(12))
        self.folder_entry.grid(row=0, column=1, sticky="ew")
        quiet_button(self.options_panel, self.tr("choose"), self.choose_folder, width=85).grid(row=0, column=2, padx=(10, 0))
        self.options_panel.grid(row=5, column=0, columnspan=3, sticky="ew", padx=21, pady=(0, 16))
        self._mode_changed()
        queue_header = ctk.CTkFrame(self.content, fg_color="transparent")
        queue_header.pack(fill="x", pady=(0, 13))
        ctk.CTkLabel(queue_header, text=self.tr("queue"), font=font(15, True), text_color=TEXT).pack(side="left")
        self.count_label = ctk.CTkLabel(queue_header, text="", font=font(11), text_color=FAINT)
        self.count_label.pack(side="left", padx=(12, 0))
        self.clear_button = quiet_button(queue_header, self.tr("clear"), self.clear_finished, width=75)
        self.clear_button.pack(side="right")
        self.pause_button = quiet_button(queue_header, self.tr("resume" if self.manager.paused.is_set() else "pause"), self.toggle_pause, width=99)
        self.pause_button.pack(side="right", padx=(0, 4))
        self.queue_area = ctk.CTkFrame(self.content, fg_color="transparent", corner_radius=0)
        self.queue_area.pack(fill="both", expand=True)
        self.queue_scroll = ctk.CTkScrollableFrame(self.queue_area, fg_color="transparent", corner_radius=0,
                                                   scrollbar_fg_color=BG, scrollbar_button_color=BORDER,
                                                   scrollbar_button_hover_color=MUTED)
        self.queue_scroll.grid_columnconfigure(0, weight=1)
        self.empty_label = ctk.CTkFrame(self.queue_area, fg_color="transparent")
        ctk.CTkLabel(self.empty_label, text="", image=icon("download", 38), width=76, height=76,
                     corner_radius=22, fg_color=FIELD).pack(pady=(0, 18))
        ctk.CTkLabel(self.empty_label, text=self.tr("empty"), font=font(16), text_color=MUTED).pack()
        for task in self.manager.tasks.values():
            self._render_task(task)
        self._update_stats()
        self._refresh_input()
        self.url_entry.focus_set()
        self._install_shortcuts()

    def _format_changed(self, value):
        self.mode_var.set("Аудио MP3" if value == self.tr("audio") else "Видео MP4")
        self._mode_changed()

    def _mode_changed(self, _value=None):
        self.format_var.set(self.tr("audio") if self.mode_var.get() == "Аудио MP3" else self.tr("video"))
        if self.mode_var.get() == "Аудио MP3":
            self.quality_control.pack_forget()
        else:
            self.quality_control.pack(side="left", padx=(12, 0), after=self.format_control)

    def show_history(self):
        self._clear_content("history")
        self._header(self.tr("history"))
        scroll = ctk.CTkScrollableFrame(self.content, fg_color="transparent", corner_radius=0,
                                       scrollbar_button_color=BORDER, scrollbar_button_hover_color=MUTED)
        scroll.pack(fill="both", expand=True)
        scroll.grid_columnconfigure(0, weight=1)
        if not self.history:
            ctk.CTkLabel(scroll, text=self.tr("empty_history"), text_color=MUTED, font=font(15)).grid(row=0, column=0, pady=90)
        for index, item in enumerate(self.history):
            row = ctk.CTkFrame(scroll, fg_color=PANEL, corner_radius=10)
            row.grid(row=index, column=0, sticky="ew", pady=(0, 7), padx=(0, 4))
            row.grid_columnconfigure(0, weight=1)
            ctk.CTkLabel(row, text=shorten(item.get("title", self.tr("untitled")), 66), anchor="w", text_color=TEXT,
                         font=font(13, True)).grid(row=0, column=0, sticky="ew", padx=17, pady=(13, 0))
            try:
                date = datetime.fromisoformat(item.get("date", "")).strftime("%d %b %Y   ·   %H:%M" if self.language == "en" else "%d.%m.%Y   ·   %H:%M")
            except ValueError:
                date = item.get("date", "").replace("T", "   ")
            detail = f"{date}   ·   {source_name(item.get('url', ''), self.language)}"
            ctk.CTkLabel(row, text=detail, anchor="w", text_color=MUTED, font=font(11)).grid(row=1, column=0, sticky="ew", padx=17, pady=(3, 13))
            result = item.get("result", "—")
            label = "Ошибка" if result.startswith("Ошибка") else result
            color = RED if label == "Ошибка" else GREEN if label == "Готово" else MUTED
            ctk.CTkLabel(row, text=self.tr(label), text_color=color, font=font(12), width=83).grid(row=0, column=1, rowspan=2, padx=10)
            if label == "Ошибка":
                quiet_button(row, self.tr("details"), lambda text=result: messagebox.showerror(self.tr("download_error"), error_text(self.language, text)), width=83).grid(row=0, column=2, rowspan=2, padx=(0, 12))
            else:
                quiet_button(row, "", lambda folder=item.get("destination"): self.open_folder(folder), icon("folder", 17), width=32).grid(row=0, column=2, rowspan=2, padx=(0, 12))
        self._install_shortcuts()

    def show_about(self):
        messagebox.showinfo("VideoFlow", f"VideoFlow {VERSION}\n\n{self.tr('about')}")

    def toggle_language(self):
        self.set_language("en" if self.language == "ru" else "ru")

    def set_language(self, language, persist=True):
        if language not in {"ru", "en"}:
            raise ValueError("Unsupported interface language")
        page = self.current_page
        self.language = language
        self.last_notice = ""
        self.sidebar.destroy()
        self._build_sidebar()
        self.show_history() if page == "history" else self.show_downloads()
        if persist:
            self._save_settings()

    def toggle_theme(self):
        self.appearance = "light" if self.appearance == "dark" else "dark"
        ctk.set_appearance_mode(self.appearance)

    def focus_url(self, _event=None):
        if self.current_page != "downloads":
            self.show_downloads()
        self.url_entry.focus_set()
        self.url_entry.select_range(0, "end")
        return "break"

    def paste_url(self):
        if self.current_page != "downloads":
            self.show_downloads()
        try:
            self.url_var.set(self.clipboard_get().strip())
            self.url_entry.focus_set()
            self.url_entry.icursor("end")
        except Exception:
            self._notify(self.tr("clipboard_empty"), error=True)

    def choose_folder(self):
        selected = filedialog.askdirectory(title=self.tr("save_to"), initialdir=self.folder_var.get() or str(Path.home()))
        if selected:
            self.folder_var.set(selected)

    def open_folder(self, folder=None):
        try:
            path = Path(folder or self.folder_var.get()).expanduser()
            path.mkdir(parents=True, exist_ok=True)
            os.startfile(str(path))
        except OSError as exc:
            messagebox.showerror(self.tr("folder_error"), str(exc))

    def _refresh_input(self):
        if self.current_page != "downloads":
            return
        valid = core.valid_url(self.url_var.get().strip())
        self.download_button.configure(state="normal" if valid else "disabled",
                                       fg_color=ACCENT if valid else ("#E6E0F4", "#332D40"),
                                       text_color_disabled=("#81758F", "#9E92B4"),
                                       image=icon("download", 17, "#17131F" if valid else "#9484A6"))
        if not self.url_var.get():
            self.url_placeholder.place(x=16, rely=0.5, anchor="w")
        else:
            self.url_placeholder.place_forget()
        self.meta_label.configure(text=shorten(self.last_notice, 103), text_color=RED if self.notice_error else MUTED)
        if self.last_notice:
            self.meta_label.grid(row=2, column=0, columnspan=3, sticky="ew", padx=21, pady=(6, 0))
        else:
            self.meta_label.grid_remove()

    def _on_url_changed(self, *_args):
        self.analysis_serial += 1
        if self.auto_analyze_job:
            self.after_cancel(self.auto_analyze_job)
            self.auto_analyze_job = None
        url = self.url_var.get().strip()
        self.analyzed = None
        self.analyzed_url = None
        self.last_notice = "" if not url else self.tr("checking") if core.valid_url(url) else self.tr("invalid_url")
        self.notice_error = False
        self._refresh_input()
        if core.valid_url(url):
            self.auto_analyze_job = self.after(650, lambda expected=url: self._auto_analyze(expected))

    def _auto_analyze(self, expected_url):
        self.auto_analyze_job = None
        if self.url_var.get().strip() == expected_url:
            self.analyze()

    def analyze(self):
        url = self.url_var.get().strip()
        if not core.valid_url(url) or core.yt_dlp is None:
            return
        self.analysis_in_progress_url = url
        self._notify(self.tr("fetching"))
        serial = self.analysis_serial
        threading.Thread(target=self._analyze_worker, args=(url, self.playlist_var.get(), serial), daemon=True).start()

    def _analyze_worker(self, url, playlist, serial):
        try:
            with core.create_downloader({"quiet": True, "no_warnings": True, "skip_download": True,
                                         "noplaylist": not playlist, "socket_timeout": 20}) as downloader:
                info = downloader.extract_info(url, download=False)
            if info.get("_type") == "playlist":
                entries = info.get("entries") or []
                summary = {"title": info.get("title") or "Плейлист", "uploader": info.get("uploader") or "",
                           "duration": None, "count": len(entries), "is_audio": False}
            else:
                audio = info.get("vcodec") == "none" or (info.get("ext") in {"mp3", "m4a", "aac", "opus", "ogg", "flac", "wav"} and not info.get("height"))
                summary = {"title": info.get("title") or "Без названия", "uploader": info.get("artist") or info.get("uploader") or info.get("channel") or "",
                           "duration": info.get("duration"), "count": None, "is_audio": audio}
            self.events.put(("analysis", "", {"ok": True, "data": summary, "url": url, "serial": serial}))
        except Exception as exc:
            self.events.put(("analysis", "", {"ok": False, "error": core.clean_error(exc), "url": url, "serial": serial}))

    def add_task(self):
        url = self.url_var.get().strip()
        if not core.valid_url(url):
            self.focus_url()
            return
        try:
            folder = Path(self.folder_var.get()).expanduser()
            folder.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self._notify(self.tr("create_folder_error", error=exc), error=True)
            return
        data = self.analyzed if self.analyzed_url == url else None
        audio = core.is_music_url(url) or bool(data and data.get("is_audio")) or self.mode_var.get() == "Аудио MP3"
        task = core.DownloadTask(url=url, title=data["title"] if data else url, destination=str(folder),
                                 quality=self.quality_var.get(), audio_only=audio, playlist=self.playlist_var.get())
        self.manager.add(task)
        self._render_task(task)
        self.url_var.set("")
        self._notify(self.tr("added"))

    def _render_task(self, task):
        if self.current_page != "downloads":
            return
        row = self.task_rows.get(task.id)
        if row:
            row.refresh()
        else:
            row = TaskRow(self.queue_scroll, task, self)
            row.grid(row=len(self.task_rows), column=0, sticky="ew", pady=(0, 8), padx=(0, 3))
            self.task_rows[task.id] = row
        self._update_stats()

    def _update_stats(self):
        if self.current_page != "downloads":
            return
        tasks = list(self.manager.tasks.values())
        active = sum(t.status in {"Подготовка", "Загрузка", "Обработка"} for t in tasks)
        done = sum(t.status == "Готово" for t in tasks)
        count = len(tasks)
        text = file_count(self.language, count) if tasks else ""
        if active:
            text += "   /   " + self.tr("active", count=active)
        elif done:
            text += "   /   " + self.tr("done_count", count=done)
        self.count_label.configure(text=text)
        self.pause_button.configure(state="normal" if any(t.status not in TERMINAL for t in tasks) else "disabled")
        self.clear_button.configure(state="normal" if any(t.status in TERMINAL for t in tasks) else "disabled")
        if tasks:
            self.empty_label.place_forget()
            self.queue_scroll.pack(fill="both", expand=True)
        else:
            self.queue_scroll.pack_forget()
            self.empty_label.place(relx=0.5, rely=0.43, anchor="center")

    def cancel_task(self, task_id):
        self.manager.cancel(task_id)

    def toggle_pause(self):
        paused = self.manager.toggle_pause()
        self.pause_button.configure(text=self.tr("resume" if paused else "pause"))
        self._notify(self.tr("paused" if paused else "resumed"))

    def clear_finished(self):
        for task_id, task in list(self.manager.tasks.items()):
            if task.status in TERMINAL:
                row = self.task_rows.pop(task_id, None)
                if row:
                    row.destroy()
                del self.manager.tasks[task_id]
        for index, row in enumerate(self.task_rows.values()):
            row.grid_configure(row=index)
        self._update_stats()

    def _notify(self, text, error=False):
        self.last_notice, self.notice_error = text, error
        self._refresh_input()

    def _process_events(self):
        try:
            # Ограничиваем порцию, чтобы большой поток событий не задерживал UI.
            for _ in range(150):
                kind, task_id, payload = self.events.get_nowait()
                if kind == "task":
                    task = self.manager.tasks.get(task_id)
                    if task:
                        self._render_task(task)
                elif kind == "analysis":
                    if payload.get("serial") != self.analysis_serial or payload.get("url") != self.url_var.get().strip():
                        continue
                    self.analysis_in_progress_url = None
                    if payload["ok"]:
                        data = self.analyzed = payload["data"]
                        self.analyzed_url = payload["url"]
                        if data.get("is_audio"):
                            self.mode_var.set("Аудио MP3")
                            if self.current_page == "downloads":
                                self._mode_changed()
                        detail = self.tr("items", count=data['count']) if data.get("count") is not None else core.format_duration(data.get("duration")) if data.get("duration") else "—"
                        self._notify(f"✓  {shorten(data['title'], 74)}   ·   {detail}")
                    else:
                        self.analyzed = None
                        self.analyzed_url = None
                        self._notify(shorten(error_text(self.language, payload["error"]).split("\n")[0], 100), error=True)
                elif kind == "history":
                    task = self.manager.tasks.get(task_id)
                    if task:
                        self.history.insert(0, {"date": datetime.now().isoformat(timespec="seconds"), "title": task.title,
                                                "url": task.url, "destination": task.destination, "result": payload["result"]})
                        self.history = self.history[:100]
                        core.save_json(core.HISTORY_FILE, self.history)
                        if self.current_page == "history":
                            self.show_history()
                elif kind == "log":
                    self.task_errors[task_id] = payload["message"]
                    self._notify(shorten(error_text(self.language, payload["message"]).split("\n")[0], 100), error=True)
        except queue.Empty:
            pass
        self.after(100, self._process_events)

    def on_close(self):
        active = self.manager.current
        if active and active.status not in TERMINAL:
            if not messagebox.askyesno(self.tr("close_title"), self.tr("close_question")):
                return
            active.cancel_event.set()
        self._save_settings()
        self.manager.shutdown.set()
        if self.auto_analyze_job:
            self.after_cancel(self.auto_analyze_job)
        self.destroy()

    def _save_settings(self):
        core.save_json(core.SETTINGS_FILE, {"theme": self.appearance, "language": self.language,
            "folder": self.folder_var.get(), "quality": self.quality_var.get(),
            "audio_only": self.mode_var.get() == "Аудио MP3", "playlist": self.playlist_var.get()})


def executable_self_test():
    try:
        if not resource_path("assets/brand.png").is_file() or not resource_path("assets/brand.ico").is_file():
            return 2
        with core.create_downloader({"quiet": True, "no_warnings": True, "skip_download": True,
                                    "noplaylist": True, "socket_timeout": 25}) as downloader:
            for url in SELF_TEST_URLS:
                info = downloader.extract_info(url, download=False)
                if not info or not info.get("title"):
                    return 3
        return 0
    except Exception:
        return 4


def interface_self_test():
    """Проверка реальных экранов в собранном EXE, без сети и сохранения настроек."""
    window = None
    try:
        window = VideoFlowApp()
        window.withdraw()
        assert "VideoFlowShortcuts" in window.url_entry._entry.bindtags()
        assert window.bind_class("VideoFlowShortcuts", "<KeyPress>")
        assert window.options_panel.winfo_manager() == "grid"
        window.update_idletasks()
        task = core.DownloadTask(url="https://example.com/sample.mp4", title="Тест интерфейса",
                                 destination=str(Path.home()), quality="1080p", audio_only=False, playlist=False)
        window.manager.tasks[task.id] = task
        window._render_task(task)
        task.status, task.progress = "Загрузка", 42
        window._render_task(task)
        window.toggle_pause()
        window.show_history()
        window.show_downloads()
        assert window.pause_button.cget("text") == window.tr("resume")
        window.toggle_theme()
        window.set_language("en", persist=False)
        assert window.download_button.cget("text") == "Download"
        assert window.task_rows[task.id].status_label.cget("text") == "42%"
        assert window.pause_button.cget("text") == "Resume"
        window.set_language("ru", persist=False)
        window.update_idletasks()
        task.status = "Готово"
        window._render_task(task)
        window.clear_finished()
        assert not window.manager.tasks
        return 0
    except Exception:
        return 5
    finally:
        if window is not None:
            window.manager.shutdown.set()
            window.destroy()


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(executable_self_test())
    if "--ui-smoke-test" in sys.argv:
        raise SystemExit(interface_self_test())
    VideoFlowApp().mainloop()
