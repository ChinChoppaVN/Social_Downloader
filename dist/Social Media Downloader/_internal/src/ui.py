import os
import json
import logging
from datetime import datetime
import shutil
import platform
import subprocess
import re
import sys
import threading
import time
try:
    import yt_dlp
except ImportError:
    yt_dlp = None
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk, Menu
import csv
from functools import partial
import tkinter as tk  # Đảm bảo đã import tk
from urllib.parse import urlparse, parse_qs

# Thêm thư mục gốc vào sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Đường dẫn
if getattr(sys, 'frozen', False):
    application_path = os.path.dirname(sys.executable)
    # Tìm thư mục assets chứa themes/sunset_coral.json
    candidates = [
        os.path.join(application_path, "_internal", "assets"),
        os.path.join(application_path, "assets"),
        os.path.join(ROOT_DIR, "assets")
    ]
    if hasattr(sys, '_MEIPASS'):
        candidates.insert(0, os.path.join(sys._MEIPASS, "assets"))
    
    ASSETS_DIR = candidates[0]
    for c in candidates:
        if os.path.exists(os.path.join(c, "themes", "sunset_coral.json")):
            ASSETS_DIR = c
            break
            
    APP_DATA = os.path.join(os.environ.get('APPDATA', application_path), "Social Media Downloader")
    DATA_DIR = os.path.join(APP_DATA, "data")
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR, exist_ok=True)
else:
    ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
    DATA_DIR = os.path.join(ROOT_DIR, "data")

THEME_PATH = os.path.join(ASSETS_DIR, "themes", "sunset_coral.json")

# Theme 4C Tokens: Sunset Crimson & Coral with Blush Peach Cream
COLOR_PRIMARY = ("#E11D48", "#FF4757")
COLOR_PRIMARY_HOVER = ("#BE123C", "#E04050")
COLOR_INACTIVE = ("#F2E4DF", "#2B2B33")
COLOR_INACTIVE_HOVER = ("#E8D6D0", "#383844")
COLOR_TEXT_PRIMARY = ("#2E2124", "#F9FAFB")
COLOR_TEXT_MUTED = ("#8A7478", "#A1A1AA")
COLOR_TEXT_ON_PRIMARY = ("#FAF4F2", "#FAF4F2")  # Chữ màu kem trên nền đỏ
COLOR_ACCENT_ORANGE = ("#F97316", "#FB923C")
COLOR_ACCENT_ORANGE_HOVER = ("#EA580C", "#F97316")

# Tùy chỉnh CTkSegmentedButton: hiển thị chữ màu kem trên nền đỏ khi nút được chọn và loại bỏ viền/stroke
_orig_sb_select = ctk.CTkSegmentedButton._select_button_by_value
_orig_sb_unselect = ctk.CTkSegmentedButton._unselect_button_by_value

def _patched_sb_select(self, value: str):
    _orig_sb_select(self, value)
    if value in self._buttons_dict:
        self._buttons_dict[value].configure(text_color=COLOR_TEXT_ON_PRIMARY, border_width=0)

def _patched_sb_unselect(self, value: str):
    _orig_sb_unselect(self, value)
    if value in self._buttons_dict:
        self._buttons_dict[value].configure(text_color=COLOR_TEXT_PRIMARY, border_width=0)

ctk.CTkSegmentedButton._select_button_by_value = _patched_sb_select
ctk.CTkSegmentedButton._unselect_button_by_value = _patched_sb_unselect

# Import các module từ thư mục src
from src.downloader import (
    DownloaderProcess,
    download_video,
    fetch_video_title as cli_fetch_video_title,
    fetch_playlist_entries
)
from src.utils import (
    get_clean_filename, load_last_folder, save_last_folder, 
    fetch_video_title, validate_url, add_download_history, 
    get_download_history, clear_download_history,
    DATA_DIR, HISTORY_FILE
)

# Cấu hình ứng dụng
APP_CONFIG = {
    "app_title": "Social Media Downloader",
    "app_size": "600x500",
    "max_history_display": 50,
    "font_title": ("Roboto", 24, "bold"),
    "font_subtitle": ("Roboto", 14, "italic"),
    "font_normal": ("Roboto", 14),
    "font_bold": ("Roboto", 14, "bold"),
    "font_italic": ("Roboto", 14, "italic"),
    "font_small": ("Roboto", 12),
    "button_font": ("Roboto", 14, "bold"),
    "platforms": ["YouTube", "TikTok", "Vimeo", "SoundCloud"]
}

# Thứ tự cột mặc định cho bảng lịch sử
DEFAULT_COLUMNS = [
    "STT",
    "Tên file",
    "Định dạng",
    "Kích thước",
    "Thư mục lưu", 
    "Thời gian",
    "Trạng thái",
    "URL"
]

# Tạo thư mục data nếu chưa tồn tại
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        # Khởi tạo các biến cấu hình trước khi tạo menubar
        self.config_path = os.path.join(DATA_DIR, "config.json")
        self.notify_download_complete = True
        self.notify_var = tk.IntVar(value=1 if self.notify_download_complete else 0)
        self.current_language = "Tiếng Việt"
        self.current_theme = "Tối"
        self.translations = {
            "Tiếng Việt": {
                "app_title": "Social Media Downloader",
                "subtitle": "Tải Video & Audio cực kỳ Pro Max",
                "link_label": "Link video:",
                "paste": "Dán",
                "filename_label": "Tên file:",
                "filename_placeholder": "Để trống để sử dụng tên mặc định",
                "folder_label": "Thư mục:",
                "choose": "Chọn",
                "file_exists_mp4": "Tên file MP4 đã tồn tại!",
                "file_exists_mp3": "Tên file MP3 đã tồn tại!",
                "format_label": "Định dạng:",
                "mp4": "MP4",
                "mp3": "MP3",
                "ready": "Sẵn sàng tải xuống",
                "downloading": "Đang tải...",
                "download_now": "Tải ngay",
                "history": "Lịch sử tải",
                "footer": "© 2025 Thắng MupMip. All rights reserved.",
                "success": "Đã tải xong:",
                "open_file": "Mở File",
                "open_folder": "Mở Folder",
                "close": "Đóng",
                "dont_ask_again": "Không hỏi lại",
                "confirm_overwrite": "Tên file {ext} đã tồn tại. Bạn có muốn ghi đè?",
                "confirm": "Xác nhận",
                "error": "Lỗi",
                "warning": "Cảnh báo",
                "info": "Thông báo",
                "cancel": "Hủy",
                "pause": "Tạm dừng",
                "resume": "Tiếp tục",
                "download_cancelled": "Đã hủy tải xuống",
                "download_failed": "Lỗi tải xuống!",
                "download_success": "Tải xuống hoàn tất",
                "choose_folder": "Chọn thư mục lưu!",
                "invalid_url": "Link video không hợp lệ!",
                "input_url": "Vui lòng nhập link video!",
                "input_folder": "Vui lòng chọn thư mục lưu!",
                "ffmpeg_missing": "FFmpeg không được cài đặt. Vui lòng cài FFmpeg để tải video hoặc audio.",
                "select_format": "Vui lòng chọn một định dạng (MP4 hoặc MP3)!",
                "STT": "STT",
                "Tên file": "Tên file",
                "Định dạng": "Định dạng",
                "Kích thước": "Kích thước",
                "Thư mục lưu": "Thư mục lưu",
                "Thời gian": "Thời gian",
                "Trạng thái": "Trạng thái",
                "URL": "URL",
                "Không rõ": "Không rõ",
                "Thành công": "Thành công",
                "Chưa có lịch sử tải nào.": "Chưa có lịch sử tải nào.",
                "Xóa toàn bộ": "Xóa toàn bộ",
                "Xóa đã chọn": "Xóa đã chọn",
                "Copy URL": "Copy URL",
                "Xóa": "Xóa",
                "speed": "Tốc độ: --",
                "size": "Dung lượng: --",
                "time": "Thời gian: --",
                "notify_download_complete": "Thông báo tải xong",
                "notify_menu": "Thông báo",
                "notify_on": "Bật",
                "notify_off": "Tắt",
                "Thất bại": "Thất bại",
                "quality_label": "Chất lượng:",
                "queue_btn": "📋 Queue",
                "queue_dialog_title": "Danh sách hàng đợi tải (Queue)",
                "queue_hint": "Dán danh sách link (mỗi link 1 dòng) hoặc chọn file .txt:",
                "apply": "Áp dụng",
                "load_txt": "Chọn file .txt",
                "clear_list": "Xóa hết"
            },
            "English": {
                "app_title": "Social Media Downloader",
                "subtitle": "Download Video & Audio like a Pro Max",
                "link_label": "Video link:",
                "paste": "Paste",
                "filename_label": "Filename:",
                "filename_placeholder": "Leave blank to use default name",
                "folder_label": "Folder:",
                "choose": "Browse",
                "file_exists_mp4": "MP4 file name already exists!",
                "file_exists_mp3": "MP3 file name already exists!",
                "format_label": "Format:",
                "mp4": "MP4",
                "mp3": "MP3",
                "ready": "Ready to download",
                "downloading": "Downloading...",
                "download_now": "Download now",
                "history": "History",
                "footer": "© 2025 Thang MupMip. All rights reserved.",
                "success": "Downloaded:",
                "open_file": "Open File",
                "open_folder": "Open Folder",
                "close": "Close",
                "dont_ask_again": "Don't ask again",
                "confirm_overwrite": "{ext} file name already exists. Overwrite?",
                "confirm": "Confirm",
                "error": "Error",
                "warning": "Warning",
                "info": "Info",
                "cancel": "Cancel",
                "pause": "Pause",
                "resume": "Resume",
                "download_cancelled": "Download cancelled",
                "download_failed": "Download failed!",
                "download_success": "Download completed",
                "choose_folder": "Please choose a folder!",
                "invalid_url": "Invalid video link!",
                "input_url": "Please enter a video link!",
                "input_folder": "Please choose a folder!",
                "ffmpeg_missing": "FFmpeg is not installed. Please install FFmpeg to download video or audio.",
                "select_format": "Please select a format (MP4 or MP3)!",
                "STT": "No.",
                "Tên file": "Filename",
                "Định dạng": "Type",
                "Kích thước": "Size",
                "Thư mục lưu": "Folder",
                "Thời gian": "Time",
                "Trạng thái": "Status",
                "URL": "URL",
                "Không rõ": "Unknown",
                "Thành công": "Success",
                "Chưa có lịch sử tải nào.": "No download history yet.",
                "Xóa toàn bộ": "Clear all",
                "Xóa đã chọn": "Delete selected",
                "Copy URL": "Copy URL",
                "Xóa": "Delete",
                "speed": "Speed: --",
                "size": "Size: --",
                "time": "Time: --",
                "notify_download_complete": "Download complete notification",
                "notify_menu": "Popup",
                "notify_on": "On",
                "notify_off": "Off",
                "Thất bại": "Failed",
                "quality_label": "Quality:",
                "queue_btn": "📋 Queue",
                "queue_dialog_title": "Download Queue",
                "queue_hint": "Paste links (one per line) or choose .txt file:",
                "apply": "Apply",
                "load_txt": "Browse .txt",
                "clear_list": "Clear"
            }
        }
        self.load_settings()
        app_version = "2.0"
        self.root.title(f"{self.get_text('app_title')} v{app_version}")
        self.root.geometry(APP_CONFIG["app_size"])
        self.root.resizable(False, False)
        
        # Thêm menu bar
        self.create_menubar()
        
        # Set icon cho ứng dụng
        icon_path = os.path.join(ASSETS_DIR, "CH.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
            # Thiết lập icon cho taskbar
            try:
                from ctypes import windll
                myappid = "thangmupmip.socialdownloader.1.0"
                windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                self.root.iconbitmap(default=icon_path)
            except Exception as e:
                logging.error(f"Không thể thiết lập icon cho taskbar: {e}")
        
        self.center_window()
        
        self.is_downloading = False
        self.mp4_selected = ctk.BooleanVar(value=True)
        self.mp3_selected = ctk.BooleanVar(value=False)
        self.video_quality = ctk.StringVar(value="FHD")
        self.playlist_video_quality = ctk.StringVar(value="FHD")
        self.current_downloader = None
        self.queue_urls = []
        self.is_queue_downloading = False
        self.download_start_time = None
        
        # Biến theo dõi trạng thái sắp xếp
        self.current_sort_reverse = False
        
        # Thêm biến trạng thái
        self.notify_download_complete = True
        # Thêm biến lưu hành động hoàn thành gần nhất và trạng thái không hỏi lại (chỉ trong RAM)
        self.last_complete_action = None  # 'open_file', 'open_folder', 'close'
        self.skip_complete_popup = False  # True nếu đã tick 'Không hỏi lại' trong phiên hiện tại
        
        self.create_widgets()
        
        # Tự động kiểm tra cập nhật yt-dlp sau khi giao diện đã sẵn sàng (chạy ngầm, im lặng nếu đã mới nhất)
        self.root.after(2000, lambda: self.check_ytdlp_update_dialog(silent_if_latest=True))

    def center_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (self.root.winfo_width() // 2)
        y = (screen_height // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"{APP_CONFIG['app_size']}+{x}+{y}")

    def create_menubar(self):
        menubar = Menu(self.root)
        label_history = self.get_text("history") if self.current_language == "Tiếng Việt" else "History"
        menubar.add_command(label=label_history, command=self.show_download_history)
        # Gộp các mục vào menu Cài đặt/Settings
        settings_menu = Menu(menubar, tearoff=0)
        # Ngôn ngữ
        language_menu = Menu(settings_menu, tearoff=0)
        language_menu.add_command(label="Tiếng Việt", command=lambda: self.change_language("Tiếng Việt"))
        language_menu.add_command(label="English", command=lambda: self.change_language("English"))
        settings_menu.add_cascade(label=self.get_text("Ngôn ngữ") if self.current_language == "Tiếng Việt" else "Language", menu=language_menu)
        # Giao diện
        theme_menu = Menu(settings_menu, tearoff=0)
        theme_menu.add_command(label="Tối" if self.current_language == "Tiếng Việt" else "Dark", command=lambda: self.change_theme("Tối" if self.current_language == "Tiếng Việt" else "Dark"))
        theme_menu.add_command(label="Sáng" if self.current_language == "Tiếng Việt" else "Light", command=lambda: self.change_theme("Sáng" if self.current_language == "Tiếng Việt" else "Light"))
        theme_menu.add_command(label="Hệ thống" if self.current_language == "Tiếng Việt" else "System", command=lambda: self.change_theme("Hệ thống" if self.current_language == "Tiếng Việt" else "System"))
        settings_menu.add_cascade(label=self.get_text("Giao diện") if self.current_language == "Tiếng Việt" else "Theme", menu=theme_menu)
        # Thông báo tải xong
        notify_menu = Menu(settings_menu, tearoff=0)
        notify_menu.add_radiobutton(label=self.get_text("notify_on"), value=1, variable=self.notify_var, command=lambda: self.set_notify_download_complete(True))
        notify_menu.add_radiobutton(label=self.get_text("notify_off"), value=0, variable=self.notify_var, command=lambda: self.set_notify_download_complete(False))
        settings_menu.add_cascade(label=self.get_text("notify_menu"), menu=notify_menu)
        # Thêm mục Cập nhật yt-dlp vào trong menu Cài đặt
        settings_menu.add_separator()
        label_update = "Cập nhật yt-dlp" if self.current_language == "Tiếng Việt" else "Update yt-dlp"
        settings_menu.add_command(label=label_update, command=self.check_ytdlp_update_dialog)
        # Thêm menu Cài đặt/Settings vào menubar
        menubar.add_cascade(label="Cài đặt" if self.current_language == "Tiếng Việt" else "Settings", menu=settings_menu)
        # Thêm mục Thông tin/About
        menubar.add_command(label="Thông tin" if self.current_language == "Tiếng Việt" else "About", command=self.show_about_popup)
        self.root.config(menu=menubar)

    def create_widgets(self):
        self.create_header()
        # Tạo tabview thay cho main_frame
        self.tabview = ctk.CTkTabview(self.root, border_width=0)
        self.tabview.pack(fill="both", expand=True, padx=20, pady=10)
        # Tab 1: Tải video/audio
        self.tab_download = self.tabview.add(self.get_text("Tải video/audio") if self.current_language == "Tiếng Việt" else "Download video/audio")
        self.create_main_tab(self.tab_download)
        # Tab 2: Tải playlist
        self.tab_playlist = self.tabview.add(self.get_text("Tải playlist") if self.current_language == "Tiếng Việt" else "Download playlist")
        self.create_playlist_tab(self.tab_playlist)

        # Bỏ toàn bộ stroke/viền của tab selector
        self.tabview._segmented_button.configure(border_width=0)
        for btn in self.tabview._segmented_button._buttons_dict.values():
            btn.configure(border_width=0)
        self.tabview.set(self.get_text("Tải video/audio") if self.current_language == "Tiếng Việt" else "Download video/audio")

        self.create_footer()

    def create_main_tab(self, parent):
        """Create the main download tab with form inputs and progress display"""
        self._create_url_input_section(parent)
        self._create_filename_input_section(parent) 
        self._create_folder_selection_section(parent)
        self._create_format_selection_section(parent)
        self._create_download_button_section(parent)
        self._create_progress_section(parent)
        
        parent.columnconfigure(1, weight=1)
        self.mp4_selected.trace("w", self.update_button_colors)
        self.mp3_selected.trace("w", self.update_button_colors)
    
    def _create_url_input_section(self, parent):
        """Create URL input field with paste button and queue dialog button"""
        ctk.CTkLabel(parent, text=self.get_text("link_label"), font=APP_CONFIG["font_normal"]).grid(row=0, column=0, sticky="w", pady=5, padx=15)
        self.url_entry = ctk.CTkEntry(parent, width=300, placeholder_text=self.get_text("input_url"))
        self.url_entry.grid(row=0, column=1, pady=5, sticky="w")

        btn_box = ctk.CTkFrame(parent, fg_color="transparent")
        btn_box.grid(row=0, column=2, pady=5, padx=10, sticky="w")

        paste_button = ctk.CTkButton(
            btn_box, 
            text=self.get_text("paste"), 
            width=45,
            command=self.paste_url,
            font=APP_CONFIG["font_small"],
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_ON_PRIMARY,
            border_width=0
        )
        paste_button.pack(side="left", padx=2)

        queue_button = ctk.CTkButton(
            btn_box,
            text=self.get_text("queue_btn"),
            width=65,
            command=self.open_queue_dialog,
            font=APP_CONFIG["font_small"],
            fg_color=COLOR_ACCENT_ORANGE,
            hover_color=COLOR_ACCENT_ORANGE_HOVER
        )
        queue_button.pack(side="left", padx=2)

    def open_queue_dialog(self):
        """Open popup dialog for managing multi-link download queue"""
        queue_win = ctk.CTkToplevel(self.root)
        queue_win.title(self.get_text("queue_dialog_title"))
        queue_win.geometry("520x420")
        queue_win.attributes("-topmost", True)
        queue_win.transient(self.root)
        queue_win.grab_set()

        queue_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 260
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 210
        queue_win.geometry(f"520x420+{max(0, x)}+{max(0, y)}")

        ctk.CTkLabel(queue_win, text=self.get_text("queue_hint"), font=APP_CONFIG["font_normal"]).pack(anchor="w", padx=20, pady=(15, 5))

        textbox = ctk.CTkTextbox(queue_win, width=480, height=250, border_width=0)
        textbox.pack(padx=20, pady=5, fill="both", expand=True)

        if self.queue_urls:
            textbox.insert("1.0", "\n".join(self.queue_urls))
        else:
            curr_val = self.url_entry.get().strip()
            if curr_val and not curr_val.startswith("📋"):
                textbox.insert("1.0", curr_val)

        btn_row = ctk.CTkFrame(queue_win, fg_color="transparent")
        btn_row.pack(fill="x", padx=20, pady=(10, 15))

        def load_txt():
            fpath = filedialog.askopenfilename(
                parent=queue_win,
                title="Chọn file text",
                filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
            )
            if fpath and os.path.exists(fpath):
                try:
                    with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    textbox.delete("1.0", ctk.END)
                    textbox.insert("1.0", content)
                except Exception as ex:
                    messagebox.showerror("Lỗi", f"Không thể đọc file: {ex}", parent=queue_win)

        def clear_txt():
            textbox.delete("1.0", ctk.END)

        def apply_queue():
            content = textbox.get("1.0", ctk.END).strip()
            lines = [ln.strip() for ln in content.splitlines() if ln.strip()]
            extracted = []
            for ln in lines:
                urls = re.findall(r'https?://[^\s,;]+', ln)
                if urls:
                    extracted.extend(urls)
                elif ln.startswith("http"):
                    extracted.append(ln)

            seen = set()
            valid_urls = []
            for u in extracted:
                if u not in seen:
                    seen.add(u)
                    valid_urls.append(u)

            self.queue_urls = valid_urls
            queue_win.destroy()

            if len(valid_urls) == 1:
                self.url_entry.delete(0, ctk.END)
                self.url_entry.insert(0, valid_urls[0])
                self.progress_status.configure(text=f"Đã chọn 1 link video")
            elif len(valid_urls) > 1:
                self.url_entry.delete(0, ctk.END)
                self.url_entry.insert(0, f"📋 Hàng đợi: {len(valid_urls)} videos")
                self.progress_status.configure(text=f"Đã nạp {len(valid_urls)} link vào hàng đợi tải!")
            else:
                self.progress_status.configure(text=self.get_text("ready"))

        ctk.CTkButton(btn_row, text=self.get_text("load_txt"), command=load_txt, border_width=0, width=120).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text=self.get_text("clear_list"), command=clear_txt, fg_color=COLOR_INACTIVE, text_color=COLOR_TEXT_PRIMARY, hover_color=COLOR_INACTIVE_HOVER, border_width=0, width=90).pack(side="left", padx=5)
        ctk.CTkButton(btn_row, text=self.get_text("apply"), command=apply_queue, fg_color=COLOR_PRIMARY, hover_color=COLOR_PRIMARY_HOVER, text_color=COLOR_TEXT_ON_PRIMARY, border_width=0, width=110).pack(side="right", padx=5)
    
    def _create_filename_input_section(self, parent):
        """Create filename input field"""
        ctk.CTkLabel(parent, text=self.get_text("filename_label"), font=APP_CONFIG["font_normal"]).grid(row=1, column=0, sticky="w", pady=5, padx=15)
        self.filename_entry = ctk.CTkEntry(parent, width=320, placeholder_text=self.get_text("filename_placeholder"))
        self.filename_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=5)
    
    def _create_folder_selection_section(self, parent):
        """Create folder selection field with browse button"""
        ctk.CTkLabel(parent, text=self.get_text("folder_label"), font=APP_CONFIG["font_normal"]).grid(row=2, column=0, sticky="w", pady=5, padx=15)
        last_folder = load_last_folder()
        self.folder_var = ctk.StringVar(value=last_folder)
        self.folder_entry = ctk.CTkEntry(parent, textvariable=self.folder_var, width=320)
        self.folder_entry.grid(row=2, column=1, pady=5, sticky="w")
        folder_button = ctk.CTkButton(
            parent, 
            text=self.get_text("choose"), 
            command=self.select_folder, 
            width=90,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_ON_PRIMARY,
            border_width=0
        )
        folder_button.grid(row=2, column=2, pady=5, padx=15, sticky="w")
        
        self.file_status_label = ctk.CTkLabel(parent, text="", text_color="red", font=APP_CONFIG["font_small"])
        self.file_status_label.grid(row=4, column=1, columnspan=2, sticky="w", pady=(0, 2))
    
    def _create_format_selection_section(self, parent):
        """Create format selection buttons (MP4/MP3) and Quality selector (FHD/4K)"""
        ctk.CTkLabel(parent, text=self.get_text("format_label"), font=APP_CONFIG["font_normal"]).grid(row=3, column=0, sticky="w", pady=5, padx=15)
        
        format_frame = ctk.CTkFrame(parent, fg_color="transparent")
        format_frame.grid(row=3, column=1, columnspan=2, pady=5, sticky="w")
        
        self.mp4_btn = ctk.CTkButton(
            format_frame,
            text=self.get_text("mp4"),
            command=lambda: self.toggle_format("mp4"),
            width=65,
            border_width=0,
            fg_color=COLOR_PRIMARY if self.mp4_selected.get() else COLOR_INACTIVE,
            text_color=COLOR_TEXT_ON_PRIMARY if self.mp4_selected.get() else COLOR_TEXT_MUTED,
            hover_color=COLOR_PRIMARY_HOVER if self.mp4_selected.get() else COLOR_INACTIVE_HOVER
        )
        self.mp4_btn.pack(side="left", padx=(0, 6))
        
        self.mp3_btn = ctk.CTkButton(
            format_frame,
            text=self.get_text("mp3"),
            command=lambda: self.toggle_format("mp3"),
            width=65,
            border_width=0,
            fg_color=COLOR_PRIMARY if self.mp3_selected.get() else COLOR_INACTIVE,
            text_color=COLOR_TEXT_ON_PRIMARY if self.mp3_selected.get() else COLOR_TEXT_MUTED,
            hover_color=COLOR_PRIMARY_HOVER if self.mp3_selected.get() else COLOR_INACTIVE_HOVER
        )
        self.mp3_btn.pack(side="left", padx=(0, 14))
        
        self.quality_label = ctk.CTkLabel(format_frame, text=self.get_text("quality_label"), font=APP_CONFIG["font_normal"])
        self.quality_label.pack(side="left", padx=(0, 6))
        
        self.quality_segmented = ctk.CTkSegmentedButton(
            format_frame,
            values=["FHD", "4K"],
            variable=self.video_quality,
            border_width=0,
            width=110
        )
        self.quality_segmented.pack(side="left")
    
    def _create_download_button_section(self, parent):
        """Create download button section"""
        button_frame = ctk.CTkFrame(parent, fg_color="transparent")
        button_frame.grid(row=4, column=0, columnspan=3, pady=(10, 0))
        self.download_button = ctk.CTkButton(
            button_frame, 
            text=self.get_text("download_now"), 
            command=self.start_download, 
            font=APP_CONFIG["button_font"],
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_ON_PRIMARY,
            border_width=0
        )
        self.download_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")
    
    def _create_progress_section(self, parent):
        """Create progress bar and info display section"""
        progress_frame = ctk.CTkFrame(parent, border_width=0)
        progress_frame.grid(row=5, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        
        # Progress status label
        self.progress_status = ctk.CTkLabel(
            progress_frame, 
            text=self.get_text("ready"), 
            font=APP_CONFIG["font_small"],
            anchor="w"
        )
        self.progress_status.pack(fill="x", padx=5, pady=(5,0))
        
        # Progress bar with control buttons
        self._create_progress_bar_with_controls(progress_frame)
        
        # Info labels (speed, size, time)
        self._create_progress_info_labels(progress_frame)
    
    def _create_progress_bar_with_controls(self, parent):
        """Create progress bar with pause/cancel controls"""
        progress_control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_control_frame.pack(fill="x", padx=5, pady=5)
        
        # Progress bar
        self.progress_bar = ctk.CTkProgressBar(
            progress_control_frame,
            width=350,
            height=15,
            corner_radius=8,
            border_width=0,
            progress_color=COLOR_PRIMARY,
            fg_color=COLOR_INACTIVE
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.progress_bar.set(0)
        
        # Control buttons
        control_buttons_frame = ctk.CTkFrame(progress_control_frame, fg_color="transparent")
        control_buttons_frame.pack(side="right")
        
        self.pause_play_button = ctk.CTkButton(
            control_buttons_frame,
            text="⏸",
            width=30,
            height=25,
            command=self.toggle_download,
            font=("Roboto", 14)
        )
        self.pause_play_button.pack(side="left", padx=2)
        self.pause_play_button.configure(state="disabled")
        
        self.cancel_button = ctk.CTkButton(
            control_buttons_frame,
            text="✕",
            width=30,
            height=25,
            command=self.cancel_download,
            font=("Roboto", 14)
        )
        self.cancel_button.pack(side="left", padx=2)
        self.cancel_button.configure(state="disabled")
    
    def _create_progress_info_labels(self, parent):
        """Create info labels for download progress (speed, size, time)"""
        info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        info_frame.pack(fill="x", padx=5, pady=(0,5))
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        info_frame.grid_columnconfigure(2, weight=1)
        
        self.speed_label = ctk.CTkLabel(
            info_frame, 
            text=self.get_text("speed"), 
            font=APP_CONFIG["font_small"],
            width=120,
            anchor="w"
        )
        self.speed_label.grid(row=0, column=0, padx=5)
        
        self.size_label = ctk.CTkLabel(
            info_frame, 
            text=self.get_text("size"), 
            font=APP_CONFIG["font_small"],
            width=180,
            anchor="w"
        )
        self.size_label.grid(row=0, column=1, padx=5)
        
        self.time_label = ctk.CTkLabel(
            info_frame,
            text=self.get_text("time"),
            font=APP_CONFIG["font_small"],
            width=150,
            anchor="w"
        )
        self.time_label.grid(row=0, column=2, padx=5)

    def create_playlist_tab(self, parent):
        """Create the playlist download tab with specialized UI components"""
        self._create_playlist_url_input_section(parent)
        self._create_playlist_folder_selection_section(parent)
        self._create_playlist_format_selection_section(parent)
        self._create_playlist_download_button_section(parent)
        self._create_playlist_progress_section(parent)
    
    def _create_playlist_url_input_section(self, parent):
        """Create playlist URL input with paste functionality"""
        ctk.CTkLabel(parent, text=self.get_text("Link playlist:"), font=APP_CONFIG["font_normal"]).grid(row=0, column=0, sticky="w", pady=5, padx=15)
        self.playlist_url_entry = ctk.CTkEntry(parent, width=320, placeholder_text=self.get_text("Link playlist:"))
        self.playlist_url_entry.grid(row=0, column=1, pady=5, sticky="w")
        
        paste_button = ctk.CTkButton(
            parent, 
            text=self.get_text("paste"), 
            width=90, 
            command=self._paste_playlist_url, 
            font=APP_CONFIG["font_normal"],
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_ON_PRIMARY,
            border_width=0
        )
        paste_button.grid(row=0, column=2, pady=5, padx=15, sticky="w")
    
    def _paste_playlist_url(self):
        """Paste URL from clipboard to playlist entry"""
        try:
            url = self.root.clipboard_get()
            self.playlist_url_entry.delete(0, ctk.END)
            self.playlist_url_entry.insert(0, url)
        except Exception as e:
            logging.error(f"Cannot paste from clipboard: {e}")
            self.show_message("error", "Cannot paste from clipboard!", "error")
    
    def _create_playlist_folder_selection_section(self, parent):
        """Create folder selection for playlist downloads"""
        ctk.CTkLabel(parent, text=self.get_text("folder_label"), font=APP_CONFIG["font_normal"]).grid(row=1, column=0, sticky="w", pady=5, padx=15)
        self.playlist_folder_var = ctk.StringVar(value=load_last_folder())
        self.playlist_folder_entry = ctk.CTkEntry(parent, textvariable=self.playlist_folder_var, width=320)
        self.playlist_folder_entry.grid(row=1, column=1, pady=5, sticky="w")
        
        folder_button = ctk.CTkButton(
            parent, 
            text=self.get_text("choose"), 
            command=self.select_folder, 
            width=90,
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_ON_PRIMARY,
            border_width=0
        )
        folder_button.grid(row=1, column=2, pady=5, padx=15, sticky="w")
    
    def _create_playlist_format_selection_section(self, parent):
        """Create format selection for playlist downloads"""
        ctk.CTkLabel(parent, text=self.get_text("format_label"), font=APP_CONFIG["font_normal"]).grid(row=2, column=0, sticky="w", pady=5, padx=15)
        
        # Initialize playlist format variables
        self.playlist_mp4_selected = ctk.BooleanVar(value=True)
        self.playlist_mp3_selected = ctk.BooleanVar(value=False)
        
        # Create format buttons using the common helper method
        self._create_playlist_format_buttons(parent)
    
    def _create_playlist_format_buttons(self, parent):
        """Create MP4/MP3 format buttons and Quality selector for playlist"""
        format_frame = ctk.CTkFrame(parent, fg_color="transparent")
        format_frame.grid(row=2, column=1, columnspan=2, pady=5, sticky="w")

        mp4_button = ctk.CTkButton(
            format_frame, 
            text=self.get_text("mp4"), 
            command=lambda: self._toggle_playlist_format("mp4"), 
            width=65, 
            border_width=0,
            fg_color=COLOR_PRIMARY if self.playlist_mp4_selected.get() else COLOR_INACTIVE,
            text_color=COLOR_TEXT_ON_PRIMARY if self.playlist_mp4_selected.get() else COLOR_TEXT_MUTED,
            hover_color=COLOR_PRIMARY_HOVER if self.playlist_mp4_selected.get() else COLOR_INACTIVE_HOVER
        )
        mp4_button.pack(side="left", padx=(0, 6))

        mp3_button = ctk.CTkButton(
            format_frame, 
            text=self.get_text("mp3"), 
            command=lambda: self._toggle_playlist_format("mp3"), 
            width=65, 
            border_width=0,
            fg_color=COLOR_PRIMARY if self.playlist_mp3_selected.get() else COLOR_INACTIVE,
            text_color=COLOR_TEXT_ON_PRIMARY if self.playlist_mp3_selected.get() else COLOR_TEXT_MUTED,
            hover_color=COLOR_PRIMARY_HOVER if self.playlist_mp3_selected.get() else COLOR_INACTIVE_HOVER
        )
        mp3_button.pack(side="left", padx=(0, 14))

        self.playlist_quality_label = ctk.CTkLabel(format_frame, text=self.get_text("quality_label"), font=APP_CONFIG["font_normal"])
        self.playlist_quality_label.pack(side="left", padx=(0, 6))

        self.playlist_quality_segmented = ctk.CTkSegmentedButton(
            format_frame,
            values=["FHD", "4K"],
            variable=self.playlist_video_quality,
            border_width=0,
            width=110
        )
        self.playlist_quality_segmented.pack(side="left")

        self.playlist_mp4_button = mp4_button
        self.playlist_mp3_button = mp3_button

    def _toggle_playlist_format(self, format_type):
        """Toggle playlist format selection between MP4 and MP3"""
        if format_type == "mp4":
            self.playlist_mp4_selected.set(True)
            self.playlist_mp3_selected.set(False)
        else:
            self.playlist_mp4_selected.set(False)
            self.playlist_mp3_selected.set(True)
        self._update_playlist_button_colors()

    def _update_playlist_button_colors(self):
        """Update playlist format button colors based on selection"""
        if hasattr(self, 'playlist_mp4_button') and hasattr(self, 'playlist_mp3_button'):
            is_mp4 = self.playlist_mp4_selected.get()
            self.playlist_mp4_button.configure(
                fg_color=COLOR_PRIMARY if is_mp4 else COLOR_INACTIVE,
                text_color=COLOR_TEXT_ON_PRIMARY if is_mp4 else COLOR_TEXT_MUTED,
                hover_color=COLOR_PRIMARY_HOVER if is_mp4 else COLOR_INACTIVE_HOVER
            )
            self.playlist_mp3_button.configure(
                fg_color=COLOR_PRIMARY if not is_mp4 else COLOR_INACTIVE,
                text_color=COLOR_TEXT_ON_PRIMARY if not is_mp4 else COLOR_TEXT_MUTED,
                hover_color=COLOR_PRIMARY_HOVER if not is_mp4 else COLOR_INACTIVE_HOVER
            )
        if hasattr(self, 'playlist_quality_segmented'):
            if self.playlist_mp4_selected.get():
                self.playlist_quality_segmented.configure(state="normal")
                self.playlist_quality_label.configure(text_color=COLOR_TEXT_PRIMARY)
            else:
                self.playlist_quality_segmented.configure(state="disabled")
                self.playlist_quality_label.configure(text_color=COLOR_TEXT_MUTED)

    def _create_playlist_download_button_section(self, parent):
        """Create download button for playlist"""
        self.playlist_download_button = ctk.CTkButton(
            parent, 
            text=self.get_text("download_now"), 
            font=APP_CONFIG["button_font"], 
            command=self.start_download_playlist, 
            fg_color=COLOR_PRIMARY,
            hover_color=COLOR_PRIMARY_HOVER,
            text_color=COLOR_TEXT_ON_PRIMARY,
            border_width=0,
            width=120
        )
        self.playlist_download_button.grid(row=3, column=1, pady=15)

    def _create_playlist_progress_section(self, parent):
        """Create progress display for playlist downloads"""
        playlist_progress_frame = ctk.CTkFrame(parent, border_width=0)
        playlist_progress_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        
        # Progress status label
        self.playlist_progress_status = ctk.CTkLabel(
            playlist_progress_frame,
            text=self.get_text("ready"),
            font=APP_CONFIG["font_small"],
            anchor="w"
        )
        self.playlist_progress_status.pack(fill="x", padx=5, pady=(5,0))
        
        # Progress bar
        self._create_playlist_progress_bar(playlist_progress_frame)
        
        # Info labels
        self._create_playlist_info_labels(playlist_progress_frame)

    def _create_playlist_progress_bar(self, parent):
        """Create progress bar for playlist downloads with cancel button"""
        playlist_progress_control_frame = ctk.CTkFrame(parent, fg_color="transparent")
        playlist_progress_control_frame.pack(fill="x", padx=5, pady=5)
        
        self.playlist_progress_bar = ctk.CTkProgressBar(
            playlist_progress_control_frame,
            width=320,
            height=15,
            corner_radius=8,
            border_width=0,
            progress_color=COLOR_PRIMARY,
            fg_color=COLOR_INACTIVE
        )
        self.playlist_progress_bar.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.playlist_progress_bar.set(0)

        self.playlist_cancel_button = ctk.CTkButton(
            playlist_progress_control_frame,
            text="✕",
            width=30,
            height=25,
            command=self.cancel_playlist_download,
            font=("Roboto", 14)
        )
        self.playlist_cancel_button.pack(side="right")
        self.playlist_cancel_button.configure(state="disabled")

    def cancel_playlist_download(self):
        """Cancel running playlist download"""
        if self.show_message("confirm", "Bạn có chắc muốn hủy tải playlist không?", "yesno"):
            self.is_playlist_cancelled = True
            if self.current_downloader:
                self.current_downloader.cancel()
            self.is_playlist_downloading = False
            self.playlist_progress_status.configure(text=self.get_text("download_cancelled"))
            self.playlist_progress_bar.set(0)
            self.playlist_cancel_button.configure(state="disabled")
            self.playlist_download_button.configure(state="normal")
    
    def _create_playlist_info_labels(self, parent):
        """Create info labels for playlist download progress"""
        playlist_info_frame = ctk.CTkFrame(parent, fg_color="transparent")
        playlist_info_frame.pack(fill="x", padx=5, pady=(0,5))
        playlist_info_frame.grid_columnconfigure(0, weight=1)
        playlist_info_frame.grid_columnconfigure(1, weight=1)
        playlist_info_frame.grid_columnconfigure(2, weight=1)
        
        self.playlist_speed_label = ctk.CTkLabel(
            playlist_info_frame,
            text=self.get_text("speed"),
            font=APP_CONFIG["font_small"],
            width=120,
            anchor="w"
        )
        self.playlist_speed_label.grid(row=0, column=0, padx=5)
        
        self.playlist_progress_count_label = ctk.CTkLabel(
            playlist_info_frame,
            text="Tiến trình: 0/0" if self.current_language == "Tiếng Việt" else "Progress: 0/0",
            font=APP_CONFIG["font_small"],
            width=200,
            anchor="w"
        )
        self.playlist_progress_count_label.grid(row=0, column=2, padx=5)

    def create_header(self):
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", pady=10)
        
        # Tạo frame cho tiêu đề
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10)
        
        title_label = ctk.CTkLabel(title_frame, text=self.get_text("app_title"), font=APP_CONFIG["font_title"])
        title_label.pack(pady=5)
        
        subtitle_label = ctk.CTkLabel(header_frame, text=self.get_text("subtitle"), font=APP_CONFIG["font_subtitle"])
        subtitle_label.pack()

    def create_footer(self):
        footer_label = ctk.CTkLabel(self.root, text=self.get_text("footer"), font=("Roboto", 12))
        footer_label.pack(side="bottom", pady=10)

    def toggle_format(self, format_type):
        if format_type == "mp4":
            self.mp4_selected.set(True)
            self.mp3_selected.set(False)
        else:
            self.mp3_selected.set(True)
            self.mp4_selected.set(False)

    def update_button_colors(self, *args):
        """Update format button colors and quality selector for main download tab"""
        if hasattr(self, 'mp4_btn') and hasattr(self, 'mp3_btn'):
            is_mp4 = self.mp4_selected.get()
            self.mp4_btn.configure(
                fg_color=COLOR_PRIMARY if is_mp4 else COLOR_INACTIVE,
                text_color=COLOR_TEXT_ON_PRIMARY if is_mp4 else COLOR_TEXT_MUTED,
                hover_color=COLOR_PRIMARY_HOVER if is_mp4 else COLOR_INACTIVE_HOVER
            )
            self.mp3_btn.configure(
                fg_color=COLOR_PRIMARY if not is_mp4 else COLOR_INACTIVE,
                text_color=COLOR_TEXT_ON_PRIMARY if not is_mp4 else COLOR_TEXT_MUTED,
                hover_color=COLOR_PRIMARY_HOVER if not is_mp4 else COLOR_INACTIVE_HOVER
            )
        if hasattr(self, 'quality_segmented'):
            if self.mp4_selected.get():
                self.quality_segmented.configure(state="normal")
                self.quality_label.configure(text_color=COLOR_TEXT_PRIMARY)
            else:
                self.quality_segmented.configure(state="disabled")
                self.quality_label.configure(text_color=COLOR_TEXT_MUTED)

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
            save_last_folder(folder)

    def update_file_existence(self, *args):
        folder = self.folder_var.get().strip()
        name_input = self.filename_entry.get().strip()
        if folder and name_input:
            if self.mp4_selected.get():
                final_name = get_clean_filename(name_input, "mp4")
                final_path = os.path.join(folder, final_name)
                if os.path.exists(final_path):
                    self.file_status_label.configure(text=self.get_text("file_exists_mp4"))
                    return
            if self.mp3_selected.get():
                final_name = get_clean_filename(name_input, "mp3")
                final_path = os.path.join(folder, final_name)
                if os.path.exists(final_path):
                    self.file_status_label.configure(text=self.get_text("file_exists_mp3"))
                    return
            self.file_status_label.configure(text="")
        else:
            self.file_status_label.configure(text="")

    def progress_callback(self, d):
        """Handle download progress updates from DownloaderProcess or yt-dlp"""
        if isinstance(d, dict):
            status = d.get('status')
            if status == 'downloading':
                self.root.after(0, lambda: self._apply_progress_data(d))
            elif status == 'finished':
                self.root.after(0, self._handle_finished_status)
            elif status == 'error':
                self.root.after(0, self._handle_error_status)

    def _apply_progress_data(self, d):
        """Safely update progress indicators on the main thread"""
        if not self.is_downloading or (hasattr(self, 'is_cancelled') and self.is_cancelled):
            return

        progress = d.get('progress', 0.0)
        if isinstance(progress, (int, float)):
            self.progress_bar.set(min(1.0, max(0.0, float(progress))))

        percent = d.get('percent')
        if percent is not None:
            self.progress_status.configure(text=f"{self.get_text('downloading')} {float(percent):.1f}%")
        elif isinstance(progress, (int, float)) and progress > 0:
            self.progress_status.configure(text=f"{self.get_text('downloading')} {progress*100:.1f}%")

        speed = d.get('speed')
        if speed:
            self.speed_label.configure(text=f"Speed: {speed}")

        eta = d.get('eta')
        if eta:
            self.time_label.configure(text=f"Time: {eta}")

        total_size = d.get('total_size')
        if total_size:
            self.size_label.configure(text=f"Size: {total_size}")
    
    def _handle_finished_status(self):
        """Handle download finished status"""
        if not (hasattr(self, 'is_cancelled') and self.is_cancelled):
            self.progress_status.configure(text=self.get_text("download_success"))
            self._reset_progress_labels()
            self.update_control_buttons("finished")
    
    def _handle_error_status(self):
        """Handle download error status"""
        if not (hasattr(self, 'is_cancelled') and self.is_cancelled):
            self.progress_status.configure(text=self.get_text("download_failed"))
            self.progress_bar.set(0)
            self._reset_progress_labels()
            self.update_control_buttons("ready")
    
    def _reset_progress_labels(self):
        """Reset progress info labels to default state"""
        self.speed_label.configure(text="Speed: --")
        self.time_label.configure(text="Time: --")
        self.size_label.configure(text="Size: --")

    def reset_ui_state(self):
        """Reset all UI state to default values"""
        self.progress_bar.set(0)
        self.progress_status.configure(text=self.get_text("ready"))
        self._reset_progress_labels()
        self.url_entry.delete(0, ctk.END)
        self.url_entry.configure(placeholder_text=self.get_text("input_url"))
        self.filename_entry.delete(0, ctk.END)
        self.filename_entry.configure(placeholder_text=self.get_text("filename_placeholder"))
        self.update_control_buttons("ready")

    def download_thread(self, url, file_type, final_path, parent_window, quality="fhd"):
        """Execute download in separate thread using DownloaderProcess"""
        try:
            done_event = threading.Event()
            result = {'success': False, 'msg': '', 'path': None}

            def _done(ok, msg, path):
                result['success'] = ok
                result['msg'] = msg
                result['path'] = path
                done_event.set()

            self.current_downloader = DownloaderProcess(
                url=url,
                output_path=final_path,
                file_type=file_type,
                quality=quality,
                progress_callback=self.progress_callback,
                completion_callback=_done
            )
            self.current_downloader.start()
            done_event.wait()

            if self.is_cancelled:
                self._handle_download_cancellation(url, file_type, final_path, parent_window)
            elif result['success'] and result['path'] and os.path.exists(result['path']):
                self._handle_download_success(url, file_type, result['path'], parent_window)
            else:
                err_msg = result['msg'] or "Download failed"
                self._handle_download_failure(url, file_type, final_path, parent_window, err_msg)
        except Exception as e:
            self._handle_download_exception(e, url, file_type, final_path, parent_window)
        finally:
            self._cleanup_download_state(parent_window)
    
    def _handle_download_success(self, url, file_type, final_path, parent_window):
        """Handle successful download completion"""
        file_size = f"{os.path.getsize(final_path) / 1024 / 1024:.2f} MB" if os.path.exists(final_path) else "Unknown"
        parent_window.after(0, lambda: add_download_history(
            url, file_type, final_path, 
            size=file_size,
            status="Success",
            folder_path=os.path.dirname(final_path).replace("/", "\\")
        ))
        
        parent_window.after(0, lambda: self.progress_status.configure(text=self.get_text("download_success")))
        parent_window.after(0, lambda: self.progress_bar.set(1.0))
        parent_window.after(0, lambda: self.update_control_buttons("finished"))
        
        if self.skip_complete_popup and self.last_complete_action:
            self._execute_saved_action(final_path, parent_window)
        elif self.notify_download_complete:
            self._show_completion_popup(final_path, parent_window)
    
    def _execute_saved_action(self, final_path, parent_window):
        """Execute the previously saved completion action"""
        if self.last_complete_action == "open_file":
            parent_window.after(0, lambda: self.open_file(final_path, parent_window))
        elif self.last_complete_action == "open_folder":
            parent_window.after(0, lambda: self.open_folder_with_highlight(final_path, parent_window))
    
    def _show_completion_popup(self, final_path, parent_window):
        """Show download completion popup"""
        parent_window.after(0, lambda: self.show_download_complete_popup(
            final_path, parent_window,
            notify_state=self.notify_download_complete,
            on_notify_change=self.set_notify_download_complete
        ))
    
    def _handle_download_exception(self, e, url, file_type, final_path, parent_window):
        """Handle download exceptions with specific error types"""
        err_str = str(e)
        if self._is_known_yt_dlp_error(err_str):
            parent_window.after(0, lambda: self.show_message(
                "warning",
                "Hiện không thể tải video này. Vui lòng thử lại sau!",
                "warning"
            ))
            return
        
        if str(e) == "Download cancelled":
            self._handle_download_cancellation(url, file_type, final_path, parent_window)
        else:
            self._handle_download_failure(url, file_type, final_path, parent_window, str(e))
    
    def _is_known_yt_dlp_error(self, error_str):
        """Check if error is a known yt-dlp issue"""
        known_errors = [
            'Signature extraction failed',
            'DRM protected', 
            'missing a url',
            'SSAP',
            'Some formats may be missing',
        ]
        return any(error in error_str for error in known_errors)
    
    def _handle_download_cancellation(self, url, file_type, final_path, parent_window):
        """Handle download cancellation"""
        parent_window.after(0, lambda: add_download_history(
            url, file_type, final_path,
            size="Unknown",
            status="Cancelled",
            folder_path="Unknown"
        ))
        parent_window.after(0, lambda: self.progress_status.configure(text=self.get_text("download_cancelled")))
        parent_window.after(0, lambda: self.progress_bar.set(0))
        parent_window.after(0, lambda: self._reset_progress_labels())
        parent_window.after(0, lambda: self.update_control_buttons("ready"))
        self._cleanup_partial_file(final_path)
    
    def _handle_download_failure(self, url, file_type, final_path, parent_window, error_msg):
        """Handle general download failure"""
        parent_window.after(0, lambda: add_download_history(
            url, file_type, final_path,
            size="Unknown",
            status="Failed",
            folder_path="Unknown"
        ))
        parent_window.after(0, lambda: self.progress_status.configure(text=self.get_text("download_failed")))
        parent_window.after(0, lambda: self.progress_bar.set(0))
        parent_window.after(0, lambda: self._reset_progress_labels())
        parent_window.after(0, lambda: self.update_control_buttons("ready"))
        parent_window.after(0, lambda: messagebox.showerror(self.get_text("error"), f"Không thể tải: {error_msg}"))
    
    def _cleanup_partial_file(self, file_path):
        """Remove partial download file if it exists"""
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as ex:
                logging.warning(f"Cannot remove partial file: {ex}")
    
    def _cleanup_download_state(self, parent_window):
        """Clean up download state and re-enable UI"""
        self.is_downloading = False
        parent_window.after(0, lambda: self.download_button.configure(state="normal"))
        parent_window.after(0, lambda: self.update_control_buttons("ready"))

    def is_youtube_playlist(self, url):
        parsed = urlparse(url)
        if "youtube.com" not in parsed.netloc and "youtu.be" not in parsed.netloc:
            return False
        if "/playlist" in parsed.path:
            return True
        if parsed.path == "/watch":
            qs = parse_qs(parsed.query)
            if "v" in qs:
                return False
            if "list" in qs:
                return True
        return False

    def start_download(self):
        if self.is_downloading:
            self.show_message("Thông báo", "Đang tải, vui lòng chờ!")
            return

        folder = self.folder_var.get().strip()
        if not folder:
            self.show_message("Lỗi", self.get_text("input_folder"), "error")
            return

        from src import paths
        if not paths.FFMPEG_PATH or not os.path.exists(paths.FFMPEG_PATH):
            if not shutil.which("ffmpeg"):
                self.show_message("Lỗi", self.get_text("ffmpeg_missing"), "error")
                return

        input_text = self.url_entry.get().strip()
        urls_to_download = []

        if input_text.startswith("📋") and self.queue_urls:
            urls_to_download = list(self.queue_urls)
        elif self.queue_urls and input_text in self.queue_urls:
            urls_to_download = list(self.queue_urls)
        else:
            extracted = re.findall(r'https?://[^\s,;]+', input_text)
            if len(extracted) > 1:
                urls_to_download = extracted
            elif extracted:
                urls_to_download = extracted
            elif input_text:
                urls_to_download = [input_text]

        if not urls_to_download:
            self.show_message("Lỗi", self.get_text("input_url"), "error")
            return

        if self.mp4_selected.get():
            file_type = "mp4"
        elif self.mp3_selected.get():
            file_type = "mp3"
        else:
            self.show_message("Cảnh báo", self.get_text("select_format"), "warning")
            return

        quality = self.video_quality.get().lower()

        if len(urls_to_download) > 1:
            self._start_queue_download(urls_to_download, folder, file_type, quality)
        else:
            single_url = urls_to_download[0]
            name_input = self.filename_entry.get().strip()
            self._start_single_download(single_url, folder, file_type, quality, name_input)

    def _start_single_download(self, url, folder, file_type, quality, name_input):
        if self.is_youtube_playlist(url):
            self.show_message("Thông báo", "Bạn vừa nhập link Playlist, hãy sử dụng tab Playlist để tải!", "info")
            return

        self.is_downloading = True
        self.is_paused = False
        self.is_cancelled = False
        self.download_button.configure(state="disabled")
        self.update_control_buttons("downloading")
        self.progress_bar.set(0)
        self.progress_status.configure(text=self.get_text("downloading"))

        def prepare_download():
            try:
                local_name = name_input if name_input else ""
                if not local_name:
                    local_name = cli_fetch_video_title(url)
                clean_name = get_clean_filename(local_name, file_type)
                final_path = os.path.join(folder, clean_name)

                if os.path.exists(final_path):
                    if not self.show_message(self.get_text("confirm"), self.get_text("confirm_overwrite", ext=file_type), "yesno"):
                        self.root.after(0, self.reset_ui_state)
                        return

                self.download_thread(url, file_type, final_path, self.root, quality=quality)
            except Exception as e:
                self.root.after(0, lambda: self.show_message("Lỗi", f"Không thể chuẩn bị tải xuống: {e}", "error"))
                self.root.after(0, self.reset_ui_state)

        threading.Thread(target=prepare_download, daemon=True).start()

    def _start_queue_download(self, urls, folder, file_type, quality):
        total = len(urls)
        msg = (
            f"Bạn có muốn tải {total} video trong hàng đợi bằng định dạng {file_type.upper()} ({quality.upper()}) không?"
            if self.current_language == "Tiếng Việt"
            else f"Do you want to download {total} videos in the queue as {file_type.upper()} ({quality.upper()})?"
        )
        if not self.show_message(self.get_text("confirm"), msg, "yesno"):
            return

        self.is_downloading = True
        self.is_queue_downloading = True
        self.is_cancelled = False
        self.download_button.configure(state="disabled")
        self.update_control_buttons("downloading")
        self.progress_bar.set(0)

        def queue_worker():
            success_count = 0
            last_success_path = None

            for idx, u in enumerate(urls, 1):
                if self.is_cancelled:
                    break

                self.root.after(0, lambda idx=idx: self.progress_status.configure(
                    text=f"Đang tải ({idx}/{total}): Đang lấy thông tin..."
                ))
                self.root.after(0, lambda: self.progress_bar.set(0))

                v_title = cli_fetch_video_title(u)
                clean_name = get_clean_filename(v_title, file_type)
                final_path = os.path.join(folder, clean_name)

                if os.path.exists(final_path):
                    base, ext = os.path.splitext(clean_name)
                    final_path = os.path.join(folder, f"{base}_{idx}{ext}")

                self.root.after(0, lambda idx=idx, v_title=v_title: self.progress_status.configure(
                    text=f"Đang tải ({idx}/{total}): {v_title[:35]}"
                ))

                done_event = threading.Event()
                dl_result = {'success': False, 'path': None, 'msg': ''}

                def _cb(ok, m, p):
                    dl_result['success'] = ok
                    dl_result['msg'] = m
                    dl_result['path'] = p
                    done_event.set()

                self.current_downloader = DownloaderProcess(
                    url=u,
                    output_path=final_path,
                    file_type=file_type,
                    quality=quality,
                    progress_callback=self.progress_callback,
                    completion_callback=_cb
                )
                self.current_downloader.start()
                done_event.wait()

                if self.is_cancelled:
                    break

                if dl_result['success'] and dl_result['path'] and os.path.exists(dl_result['path']):
                    success_count += 1
                    last_success_path = dl_result['path']
                    sz = f"{os.path.getsize(dl_result['path']) / 1024 / 1024:.2f} MB"
                    add_download_history(u, file_type, dl_result['path'], size=sz, status="Thành công", folder_path=folder.replace("/", "\\"))
                else:
                    add_download_history(u, file_type, final_path, size="Không rõ", status="Thất bại", folder_path=folder.replace("/", "\\"))

            self.root.after(0, lambda: self._on_queue_finished(success_count, total, last_success_path))

        threading.Thread(target=queue_worker, daemon=True).start()

    def _on_queue_finished(self, success_count, total, last_path):
        self.is_downloading = False
        self.is_queue_downloading = False
        self.download_button.configure(state="normal")
        self.update_control_buttons("ready")
        self.progress_bar.set(1.0 if success_count > 0 else 0)

        if self.is_cancelled:
            self.progress_status.configure(text=f"Đã hủy hàng đợi ({success_count}/{total} thành công)")
        else:
            self.progress_status.configure(text=f"Đã tải xong {success_count}/{total} video!")
            if last_path and os.path.exists(last_path) and self.notify_download_complete:
                self.show_download_complete_popup(last_path, self.root)

    def show_download_history(self):
        history = get_download_history()
        history_window = ctk.CTkToplevel(self.root)
        history_window.title(self.get_text("history") + " - Social Media Downloader")
        history_window.geometry("800x500")
        history_window.resizable(True, True)
        history_window.minsize(600, 400)
        history_window.attributes("-topmost", True)
        history_window.is_history_window = True
        self.topmost_var = ctk.BooleanVar(value=True)
        def on_history_window_focus(event):
            if self.topmost_var.get():
                history_window.attributes("-topmost", True)
        history_window.bind("<FocusIn>", on_history_window_focus)
        history_window.update_idletasks()
        screen_width = history_window.winfo_screenwidth()
        screen_height = history_window.winfo_screenheight()
        x = (screen_width // 2) - (history_window.winfo_width() // 2)
        y = (screen_height // 2) - (history_window.winfo_height() // 2)
        history_window.geometry(f"800x500+{x}+{y}")
        main_frame = ctk.CTkFrame(history_window, border_width=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        top_frame = ctk.CTkFrame(main_frame, border_width=0)
        top_frame.pack(fill="x", pady=(0, 5))
        search_entry = ctk.CTkEntry(top_frame, placeholder_text=self.get_text("search_placeholder") if "search_placeholder" in self.translations[self.current_language] else "Tìm kiếm (URL, Tên file, Thời gian)...", width=300)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        toolbar_frame = ctk.CTkFrame(top_frame, fg_color="transparent")
        toolbar_frame.pack(side="right")
        columns = tuple(DEFAULT_COLUMNS)
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=350)
        tree.pack(fill="both", expand=True, pady=5)
        tree.configure(style="Custom.Treeview")
        style = ttk.Style()
        style.theme_use("clam")
        is_dark = ctk.get_appearance_mode().lower() == "dark"
        tree_bg = "#1C1C22" if is_dark else "#FFFFFF"
        tree_fg = "#F9FAFB" if is_dark else "#2E2124"
        tree_sel = "#FF4757" if is_dark else "#E11D48"
        tree_head_bg = "#2B2B33" if is_dark else "#F2E4DF"
        tree_head_fg = "#F9FAFB" if is_dark else "#2E2124"
        style.configure("Custom.Treeview", background=tree_bg, fieldbackground=tree_bg, foreground=tree_fg)
        style.configure("Custom.Treeview.Heading", background=tree_head_bg, foreground=tree_head_fg)
        style.map("Custom.Treeview", background=[("selected", tree_sel)], foreground=[("selected", "#FAF4F2")])
        for col in columns:
            tree.heading(col, text=self.get_text(col), command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
            if col == "STT":
                tree.column(col, width=30, minwidth=20, anchor="w")
            elif col == "URL":
                tree.column(col, width=200, minwidth=30, anchor="w")
            elif col == "Tên file":
                tree.column(col, width=200, minwidth=30, anchor="w")
            elif col == "Định dạng":
                tree.column(col, width=70, minwidth=30, anchor="w")
            elif col == "Kích thước":
                tree.column(col, width=80, minwidth=30, anchor="w")
            elif col == "Thời gian":
                tree.column(col, width=120, minwidth=30, anchor="w")
            elif col == "Trạng thái":
                tree.column(col, width=80, minwidth=30, anchor="w")
            elif col == "Thư mục lưu":
                tree.column(col, width=100, minwidth=30, anchor="w")
        if not history:
            empty_values = [self.get_text("Chưa có lịch sử tải nào.")] + [""] * (len(columns) - 1)
            tree.insert("", "end", values=empty_values)
        else:
            for i, entry in enumerate(reversed(history[-50:]), 1):
                values_dict = {
                    "STT": i,
                    "URL": entry['url'],
                    "Tên file": os.path.basename(entry['file_path']),
                    "Định dạng": entry['file_type'],
                    "Kích thước": entry.get('size', self.get_text("Không rõ")),
                    "Thời gian": entry['timestamp'],
                    "Trạng thái": self.get_text(entry.get('status', 'Thành công')),
                    "Thư mục lưu": entry.get('folder_path', self.get_text("Không rõ"))
                }
                ordered_values = [values_dict[col] for col in columns]
                tree.insert("", "end", values=ordered_values)
        btn_clear = ctk.CTkButton(toolbar_frame, text=self.get_text("Xóa toàn bộ"), width=100, command=lambda: self.clear_history(tree, history_window))
        btn_clear.pack(side="left", padx=2)
        btn_delete_selected = ctk.CTkButton(toolbar_frame, text=self.get_text("Xóa đã chọn"), width=100, command=lambda: self.delete_selected(tree, history_window))
        btn_delete_selected.pack(side="left", padx=2)
        def on_search(event):
            self.filter_history(tree, history, search_entry.get())
        search_entry.bind("<KeyRelease>", on_search)
        tree.bind("<Button-3>", lambda e: self.show_context_menu(e, tree, history))
        history_window.grab_set()
        history_window.transient(self.root)

    def treeview_sort_column(self, tree, col, reverse):
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)
        tree.heading(col, command=lambda: self.treeview_sort_column(tree, col, not reverse))

    def clear_history(self, tree, history_window):
        if self.show_message("Xác nhận", "Bạn có chắc muốn xóa toàn bộ lịch sử tải?", "yesno", history_window):
            try:
                clear_download_history()
                for item in tree.get_children():
                    tree.delete(item)
                empty_values = ["Chưa có lịch sử tải nào."] + [""] * (len(DEFAULT_COLUMNS) - 1)
                tree.insert("", "end", values=empty_values)
            except Exception as e:
                self.show_message("Lỗi", f"Không thể xóa lịch sử: {e}", "error", history_window)
            history_window.lift()

    def delete_selected(self, tree, history_window):
        selected = tree.selection()
        if not selected:
            self.show_message("Thông báo", "Vui lòng chọn ít nhất một mục để xóa!", "info", history_window)
            return
        if self.show_message("Xác nhận", "Bạn có chắc muốn xóa các mục đã chọn?", "yesno", history_window):
            try:
                history = get_download_history()
                for item in selected:
                    values = tree.item(item, "values")
                    url = values[7]  # URL nằm ở cột thứ 8 (index 7)
                    new_history = [entry for entry in history if entry['url'] != url]
                    with open(os.path.join(DATA_DIR, "history.json"), "w", encoding="utf-8") as f:
                        json.dump(new_history, f, ensure_ascii=False, indent=4)
                    history = new_history  # Cập nhật lại history sau mỗi lần xóa
                
                # Xóa các mục đã chọn khỏi tree
                for item in selected:
                    tree.delete(item)
                
                # Cập nhật lại STT
                if tree.get_children():
                    for i, item in enumerate(tree.get_children(), 1):
                        tree.item(item, values=(i,) + tuple(tree.item(item, "values")[1:]))
                else:
                    # Nếu không còn mục nào, hiển thị thông báo trống
                    empty_values = ["Chưa có lịch sử tải nào."] + [""] * (len(DEFAULT_COLUMNS) - 1)
                    tree.insert("", "end", values=empty_values)
                    
            except Exception as e:
                self.show_message("Lỗi", f"Không thể xóa mục đã chọn: {e}", "error", history_window)
            history_window.lift()

    def filter_history(self, tree, history, search_term):
        search_term = search_term.lower()
        for item in tree.get_children():
            tree.delete(item)
        
        if not history:
            empty_values = ["Chưa có lịch sử tải nào."] + [""] * (len(DEFAULT_COLUMNS) - 1)
            tree.insert("", "end", values=empty_values)
            return
        
        filtered_history = [
            entry for entry in history[-50:]
            if search_term in entry['url'].lower() or 
            search_term in os.path.basename(entry['file_path']).lower() or 
            search_term in entry.get('timestamp', '').lower()
        ]
        
        for i, entry in enumerate(reversed(filtered_history), 1):
            values_dict = {
                "STT": i,
                "URL": entry['url'],
                "Tên file": os.path.basename(entry['file_path']),
                "Định dạng": entry['file_type'],
                "Kích thước": entry.get('size', 'Không rõ'),
                "Thời gian": entry['timestamp'],
                "Trạng thái": entry.get('status', 'Thành công'),
                "Thư mục lưu": entry.get('folder_path', 'Không rõ')
            }
            ordered_values = [values_dict[col] for col in DEFAULT_COLUMNS]
            tree.insert("", "end", values=ordered_values)

    def show_context_menu(self, event, tree, history):
        item = tree.identify_row(event.y)
        if item:
            tree.selection_clear()
            tree.selection_set(item)
            values = tree.item(item, "values")
            values_dict = dict(zip(DEFAULT_COLUMNS, values))
            file_name = values_dict["Tên file"]
            folder_path = values_dict["Thư mục lưu"]
            url = values_dict["URL"]
            file_path = os.path.join(folder_path, file_name) if folder_path != self.get_text("Không rõ") else None
            history_window = tree.master.master
            context_menu = Menu(self.root, tearoff=0)
            context_menu.add_command(label=self.get_text("open_file"), command=lambda: self.open_file(file_path, history_window))
            context_menu.add_command(label=self.get_text("open_folder"), command=lambda: self.open_folder_with_highlight(file_path, history_window))
            context_menu.add_separator()
            context_menu.add_command(label=self.get_text("Copy URL"), command=lambda: self.copy_url_from_history(url))
            context_menu.add_separator()
            context_menu.add_command(label=self.get_text("Xóa"), command=lambda: self.delete_selected(tree, history_window))
            context_menu.tk_popup(event.x_root, event.y_root)

    def copy_url_from_history(self, url):
        """Copy URL vào clipboard"""
        if url:
            self.root.clipboard_clear()
            self.root.clipboard_append(url)

    def open_file(self, file_path, parent_window=None):
        """Open the selected file using system default application"""
        if not self._validate_file_path(file_path):
            self.show_message("error", "File does not exist!", "error")
            return
            
        try:
            self._disable_parent_topmost(parent_window)
            os.startfile(file_path)
        except Exception as e:
            self.show_message("error", f"Cannot open file: {e}", "error")
    
    def _validate_file_path(self, file_path):
        """Validate if file path exists and is accessible"""
        return file_path and os.path.exists(file_path)
    
    def _disable_parent_topmost(self, parent_window):
        """Disable topmost attribute for parent window if applicable"""
        if parent_window and hasattr(parent_window, 'attributes'):
            parent_window.attributes("-topmost", False)

    def open_folder_with_highlight(self, file_path, parent_window=None):
        """Open folder and highlight the selected file"""
        if not self._validate_file_path(file_path):
            self.show_message("error", "File does not exist!", "error")
            return
            
        try:
            self._disable_parent_topmost(parent_window)
            self._open_folder_by_platform(file_path)
        except Exception as e:
            self.show_message("error", f"Cannot open folder: {e}", "error")
    
    def _open_folder_by_platform(self, file_path):
        """Open folder with file highlighted based on platform"""
        if platform.system() == "Windows":
            # Normalize path for Windows
            normalized_path = os.path.normpath(os.path.abspath(file_path))
            subprocess.run(['explorer', '/select,', normalized_path])
        else:
            # For Unix-like systems, just open the directory
            subprocess.run(["xdg-open", os.path.dirname(file_path)], check=True)

    def toggle_download(self):
        """Toggle between pause and resume download states"""
        if not hasattr(self, 'is_paused'):
            self.is_paused = False
            
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_play_button.configure(text="▶")  # Switch to play button
            self.progress_status.configure(text=self.get_text("pause"))
        else:
            self.pause_play_button.configure(text="⏸")  # Switch to pause button
            self.progress_status.configure(text=self.get_text("downloading"))

    def cancel_download(self):
        """Cancel the current download process or queue"""
        if self.show_message("confirm", "Are you sure you want to cancel the download?", "yesno"):
            self.is_cancelled = True
            if self.current_downloader:
                self.current_downloader.cancel()
            self.is_downloading = False
            self.is_queue_downloading = False
            self.progress_status.configure(text=self.get_text("download_cancelled"))
            self.progress_bar.set(0)
            self._reset_progress_labels()
            self.update_control_buttons("ready")
            self.download_button.configure(state="normal")

    def update_control_buttons(self, status="ready"):
        """Update control button states based on download status"""
        if status == "ready":  # Ready to download
            self.pause_play_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")
        elif status == "downloading":  # Currently downloading
            self.pause_play_button.configure(state="normal")
            self.cancel_button.configure(state="normal")
        elif status == "finished":  # Download completed
            self.pause_play_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")

    def paste_url(self):
        """Paste URL from clipboard into the URL entry field, auto-detecting multiple links"""
        try:
            url = self.root.clipboard_get()
            self.url_entry.delete(0, ctk.END)
            urls = re.findall(r'https?://[^\s,;]+', url)
            if len(urls) > 1:
                self.queue_urls = urls
                self.url_entry.insert(0, f"📋 Hàng đợi: {len(urls)} videos")
                self.progress_status.configure(text=f"Đã nhận diện {len(urls)} link trong bộ nhớ tạm!")
            else:
                self.queue_urls = []
                self.url_entry.insert(0, url.strip())
        except Exception as e:
            logging.error(f"Cannot paste from clipboard: {e}")
            self.show_message("error", "Cannot paste from clipboard!", "error")

    def show_message(self, title, message, msg_type="info", parent=None):
        """Show message dialog with localized text"""
        if parent is None:
            parent = self.root
            
        # Translate title and message if they exist in translations
        title = self.get_text(title) if title in self.translations[self.current_language] else title
        message = self.get_text(message) if message in self.translations[self.current_language] else message
        
        # Show appropriate message box type
        result = self._show_message_by_type(title, message, msg_type, parent)
        parent.lift()
        return result
    
    def _show_message_by_type(self, title, message, msg_type, parent):
        """Show message box based on type"""
        message_handlers = {
            "info": lambda: messagebox.showinfo(title, message, parent=parent),
            "error": lambda: messagebox.showerror(title, message, parent=parent),
            "warning": lambda: messagebox.showwarning(title, message, parent=parent),
            "yesno": lambda: messagebox.askyesno(title, message, parent=parent)
        }
        
        handler = message_handlers.get(msg_type)
        if handler:
            return handler()
        else:
            logging.warning(f"Unknown message type: {msg_type}")
            return messagebox.showinfo(title, message, parent=parent)

    def show_history_message(self, title, message, type="info", parent=None):
        title = self.get_text(title) if title in self.translations[self.current_language] else title
        message = self.get_text(message) if message in self.translations[self.current_language] else message
        if type == "info":
            messagebox.showinfo(title, message, parent=parent)
        elif type == "error":
            messagebox.showerror(title, message, parent=parent)
        elif type == "warning":
            messagebox.showwarning(title, message, parent=parent)
        elif type == "yesno":
            return messagebox.askyesno(title, message, parent=parent)
        if parent:
            parent.lift()

    def change_language(self, value):
        self.current_language = value
        self.save_settings()
        self.create_menubar()
        for widget in self.root.winfo_children():
            widget.destroy()
        self.create_menubar()
        self.create_widgets()

    def change_theme(self, value):
        self.current_theme = value
        self.save_settings()
        self.apply_theme(value)

    def apply_theme(self, value):
        if value == "Tối" or value == "Dark":
            ctk.set_appearance_mode("dark")
        elif value == "Sáng" or value == "Light":
            ctk.set_appearance_mode("light")
        else:
            ctk.set_appearance_mode("system")

    def load_settings(self):
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
                if "language" in config:
                    self.current_language = config["language"]
                if "theme" in config:
                    self.current_theme = config["theme"]
                    self.apply_theme(self.current_theme)
                if "notify_download_complete" in config:
                    self.notify_download_complete = config["notify_download_complete"]
            except Exception as e:
                print(f"Không thể đọc config: {e}")

    def save_settings(self):
        config = {}
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except:
                pass
        config["language"] = self.current_language
        config["theme"] = self.current_theme
        config["notify_download_complete"] = self.notify_download_complete
        with open(self.config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)

    def get_text(self, key):
        return self.translations[self.current_language].get(key, key)

    def set_notify_download_complete(self, value):
        self.notify_download_complete = value
        self.notify_var.set(1 if value else 0)
        self.save_settings()
        # Cập nhật lại menubar để đồng bộ trạng thái
        self.create_menubar()

    def show_download_complete_popup(self, file_path, parent_window, notify_state=True, on_notify_change=None):
        # Nếu đã tick 'Không hỏi lại', không hiển thị popup nữa
        if self.skip_complete_popup and self.last_complete_action:
            # Đã xử lý ở download_thread, không cần lặp lại ở đây
            return
        popup = ctk.CTkToplevel(parent_window)
        popup.title(self.get_text("success"))
        popup.geometry("400x110")  # Giảm chiều cao popup
        popup.resizable(False, False)
        popup.attributes("-topmost", True)
        main_frame = ctk.CTkFrame(popup, border_width=0)
        main_frame.pack(fill="both", expand=True, padx=10, pady=5)
        message_label = ctk.CTkLabel(
            main_frame,
            text=os.path.basename(file_path),  # Chỉ hiện tên file
            font=APP_CONFIG["font_normal"]
        )
        message_label.pack(pady=5)
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(pady=5)
        # Checkbox không hỏi lại (mặc định chưa chọn)
        dont_ask_var = ctk.BooleanVar(value=False)
        def on_dont_ask_change():
            self.skip_complete_popup = dont_ask_var.get()
            if dont_ask_var.get() and on_notify_change:
                on_notify_change(False)
            # Không đóng popup ở đây!
        dont_ask_checkbox = ctk.CTkCheckBox(
            main_frame,
            text=self.get_text("dont_ask_again"),
            variable=dont_ask_var,
            command=on_dont_ask_change,
            width=14,
            height=14,
            font=("Roboto", 12)
        )
        dont_ask_checkbox.pack(pady=5)
        def handle_action(action):
            # Nếu đã tick 'Không hỏi lại', nhớ hành động này cho các lần sau
            if self.skip_complete_popup:
                self.last_complete_action = action
            popup.destroy()
            if action == "open_file":
                self.open_file(file_path, parent_window)
            elif action == "open_folder":
                self.open_folder_with_highlight(file_path, parent_window)
            # Nếu là close thì chỉ đóng popup
        open_file_button = ctk.CTkButton(
            button_frame,
            text=self.get_text("open_file"),
            command=lambda: handle_action("open_file"),
            width=100
        )
        open_file_button.pack(side="left", padx=5)
        open_folder_button = ctk.CTkButton(
            button_frame,
            text=self.get_text("open_folder"),
            command=lambda: handle_action("open_folder"),
            width=100
        )
        open_folder_button.pack(side="left", padx=5)
        close_button = ctk.CTkButton(
            button_frame,
            text=self.get_text("close"),
            command=lambda: handle_action("close"),
            width=100
        )
        close_button.pack(side="left", padx=5)
        popup.update_idletasks()
        screen_width = popup.winfo_screenwidth()
        screen_height = popup.winfo_screenheight()
        x = (screen_width // 2) - (popup.winfo_width() // 2)
        y = (screen_height // 2) - (popup.winfo_height() // 2)
        popup.geometry(f"+{x}+{y}")
        popup.focus_set()
        popup.grab_set()

    def check_ytdlp_update_dialog(self, silent_if_latest=False):
        """Kiểm tra phiên bản yt-dlp mới nhất và hiển thị hộp thoại cập nhật"""
        from src import paths
        import urllib.request
        from packaging.version import parse as parse_version

        def worker():
            try:
                # 1. Lấy phiên bản yt-dlp hiện tại
                current_version = "Unknown"
                if paths.YT_DLP_PATH and os.path.exists(paths.YT_DLP_PATH):
                    creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                    res = subprocess.run([paths.YT_DLP_PATH, "--version"], capture_output=True, text=True, creationflags=creationflags, timeout=5)
                    if res.returncode == 0:
                        current_version = res.stdout.strip()
                
                # 2. Truy vấn phiên bản mới nhất từ PyPI API
                req = urllib.request.Request("https://pypi.org/pypi/yt-dlp/json", headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=7) as resp:
                    data = json.loads(resp.read().decode('utf-8'))
                latest_version = data["info"]["version"]

                current_v = parse_version(current_version) if current_version != "Unknown" else parse_version("0.0.0")
                latest_v = parse_version(latest_version)

                if current_v < latest_v:
                    msg = (
                        f"Đã có phiên bản yt-dlp mới!\n\n"
                        f"• Phiên bản hiện tại: {current_version}\n"
                        f"• Phiên bản mới nhất: {latest_version}\n\n"
                        f"Bạn có muốn cập nhật ngay bây giờ không?"
                    ) if self.current_language == "Tiếng Việt" else (
                        f"New yt-dlp version available!\n\n"
                        f"• Current version: {current_version}\n"
                        f"• Latest version: {latest_version}\n\n"
                        f"Do you want to update now?"
                    )
                    
                    def ask_update():
                        if messagebox.askyesno("Cập nhật yt-dlp", msg, parent=self.root):
                            self._perform_ytdlp_update(latest_version)
                    self.root.after(0, ask_update)

                else:
                    if not silent_if_latest:
                        def show_latest():
                            msg = (
                                f"yt-dlp đang ở phiên bản mới nhất ({current_version}).\nKhông cần cập nhật."
                            ) if self.current_language == "Tiếng Việt" else (
                                f"yt-dlp is up to date ({current_version}).\nNo update needed."
                            )
                            messagebox.showinfo("Thông báo", msg, parent=self.root)
                        self.root.after(0, show_latest)

            except Exception as e:
                if not silent_if_latest:
                    self.root.after(0, lambda: messagebox.showerror(
                        "Lỗi", f"Không thể kiểm tra cập nhật yt-dlp: {e}", parent=self.root
                    ))

        threading.Thread(target=worker, daemon=True).start()

    def _perform_ytdlp_update(self, new_version):
        """Thực hiện tải và cập nhật yt-dlp với thanh tiến trình trực quan"""
        from src import paths
        from src.utils import download_yt_dlp

        if not paths.YT_DLP_PATH:
            messagebox.showerror("Lỗi", "Không tìm thấy đường dẫn yt-dlp để cập nhật.", parent=self.root)
            return

        dest_path = paths.YT_DLP_PATH

        # Popup tiến trình cập nhật
        update_win = ctk.CTkToplevel(self.root)
        update_win.title("Cập nhật yt-dlp" if self.current_language == "Tiếng Việt" else "Update yt-dlp")
        update_win.geometry("420x150")
        update_win.resizable(False, False)
        update_win.attributes("-topmost", True)
        update_win.transient(self.root)
        update_win.grab_set()

        update_win.update_idletasks()
        x = self.root.winfo_x() + (self.root.winfo_width() // 2) - 210
        y = self.root.winfo_y() + (self.root.winfo_height() // 2) - 75
        update_win.geometry(f"420x150+{max(0, x)}+{max(0, y)}")

        lbl = ctk.CTkLabel(update_win, text=f"Đang tải yt-dlp v{new_version}...", font=APP_CONFIG["font_normal"])
        lbl.pack(pady=(20, 10))

        prog = ctk.CTkProgressBar(update_win, width=320, height=12, progress_color=COLOR_PRIMARY, fg_color=COLOR_INACTIVE, border_width=0)
        prog.pack(pady=5)
        prog.set(0)

        status_lbl = ctk.CTkLabel(update_win, text="0%", font=APP_CONFIG["font_small"], text_color=COLOR_TEXT_MUTED)
        status_lbl.pack(pady=5)

        def progress_cb(downloaded, total):
            if total > 0:
                fraction = min(1.0, max(0.0, downloaded / total))
                update_win.after(0, lambda: (
                    prog.set(fraction),
                    status_lbl.configure(text=f"{downloaded/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB ({fraction*100:.1f}%)")
                ))
            else:
                update_win.after(0, lambda: (
                    status_lbl.configure(text=f"{downloaded/(1024*1024):.1f}MB đã tải...")
                ))

        def run_update():
            try:
                ok, err = download_yt_dlp(dest_path=dest_path, progress_callback=progress_cb, new_version=new_version)
            except Exception as ex:
                ok, err = False, str(ex)

            def done():
                try:
                    update_win.destroy()
                except:
                    pass
                if ok:
                    messagebox.showinfo("Thành công", f"Đã cập nhật yt-dlp lên phiên bản {new_version} thành công!", parent=self.root)
                else:
                    messagebox.showerror("Lỗi cập nhật", f"Không thể cập nhật yt-dlp: {err}", parent=self.root)

            self.root.after(0, done)

        threading.Thread(target=run_update, daemon=True).start()

    def show_about_popup(self):
        app_version = "2.0"
        ytdlp_version = "Unknown"
        from src import paths
        if paths.YT_DLP_PATH and os.path.exists(paths.YT_DLP_PATH):
            try:
                creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
                res = subprocess.run([paths.YT_DLP_PATH, "--version"], capture_output=True, text=True, creationflags=creationflags, timeout=5)
                if res.returncode == 0:
                    ytdlp_version = res.stdout.strip()
            except Exception:
                pass
        if ytdlp_version == "Unknown" and yt_dlp is not None:
            try:
                ytdlp_version = yt_dlp.version.__version__
            except Exception:
                pass

        msg = (
            f"Social Media Downloader v{app_version}\n\n"
            f"• Phiên bản ứng dụng: {app_version}\n"
            f"• Phiên bản yt-dlp: {ytdlp_version}\n\n"
            f"© 2025 Thắng MupMip. All rights reserved.\n\n"
            f"Bạn có muốn kiểm tra cập nhật yt-dlp mới nhất không?"
        ) if self.current_language == "Tiếng Việt" else (
            f"Social Media Downloader v{app_version}\n\n"
            f"• App version: {app_version}\n"
            f"• yt-dlp version: {ytdlp_version}\n\n"
            f"© 2025 Thang MupMip. All rights reserved.\n\n"
            f"Do you want to check for yt-dlp updates now?"
        )
        if messagebox.askyesno("Thông tin" if self.current_language == "Tiếng Việt" else "About", msg, parent=self.root):
            self.check_ytdlp_update_dialog()

    def get_playlist_info(self, url):
        """Fetch playlist entries using CLI"""
        entries = fetch_playlist_entries(url)
        return len(entries), entries

    def start_download_playlist(self):
        url = self.playlist_url_entry.get().strip()
        folder = self.playlist_folder_var.get().strip()
        if not url:
            self.show_message(self.get_text("error"), self.get_text("input_url"), "error")
            return
        if not folder:
            self.show_message(self.get_text("error"), self.get_text("input_folder"), "error")
            return

        from src import paths
        if not paths.FFMPEG_PATH or not os.path.exists(paths.FFMPEG_PATH):
            if not shutil.which("ffmpeg"):
                self.show_message(self.get_text("error"), self.get_text("ffmpeg_missing"), "error")
                return

        self.playlist_progress_status.configure(text="Đang lấy danh sách playlist...")
        self.root.update_idletasks()

        num_videos, entries = self.get_playlist_info(url)
        if num_videos == 0:
            self.show_message(self.get_text("error"), "Không nhận diện được playlist hoặc playlist không có video!", "error")
            self.playlist_progress_status.configure(text=self.get_text("ready"))
            return

        fmt = "mp4" if self.playlist_mp4_selected.get() else "mp3"
        quality = self.playlist_video_quality.get().lower()

        if self.current_language == "English":
            msg = f"This playlist contains {num_videos} videos.\nDo you want to download all as {fmt.upper()} ({quality.upper()})?"
        else:
            msg = f"Playlist này có {num_videos} video.\nBạn có muốn tải toàn bộ bằng {fmt.upper()} ({quality.upper()}) không?"
        if not self.show_message(self.get_text("confirm"), msg, "yesno"):
            self.playlist_progress_status.configure(text=self.get_text("ready"))
            return

        self.playlist_progress_bar.set(0)
        self.playlist_progress_status.configure(text=self.get_text("downloading"))
        self.playlist_speed_label.configure(text=self.get_text("speed"))
        self.playlist_progress_count_label.configure(text=f"Tiến trình: 0/{num_videos}" if self.current_language == "Tiếng Việt" else f"Progress: 0/{num_videos}")
        self.is_playlist_downloading = True
        self.is_playlist_cancelled = False

        self.playlist_download_button.configure(state="disabled")
        if hasattr(self, 'playlist_cancel_button'):
            self.playlist_cancel_button.configure(state="normal")

        def playlist_download_thread():
            last_success_path = None
            try:
                for idx, entry in enumerate(entries, 1):
                    if self.is_playlist_cancelled:
                        break

                    video_url = entry.get('url')
                    title = entry.get('title', f"video_{idx}")
                    clean_title = get_clean_filename(title, fmt)
                    name_no_ext = os.path.splitext(clean_title)[0]
                    filename = f"{idx:02d} - {name_no_ext}.{fmt}"
                    final_path = os.path.join(folder, filename)

                    self.tab_playlist.after(0, lambda idx=idx: self.playlist_progress_count_label.configure(text=f"{idx}/{num_videos}"))
                    self.tab_playlist.after(0, lambda title=title: self.playlist_progress_status.configure(text=f"{self.get_text('downloading')}: {title[:35]}"))
                    self.tab_playlist.after(0, lambda: self.playlist_progress_bar.set(0))

                    done_event = threading.Event()
                    dl_result = {'success': False, 'path': None, 'msg': ''}

                    def _cb(ok, m, p):
                        dl_result['success'] = ok
                        dl_result['msg'] = m
                        dl_result['path'] = p
                        done_event.set()

                    self.current_downloader = DownloaderProcess(
                        url=video_url,
                        output_path=final_path,
                        file_type=fmt,
                        quality=quality,
                        progress_callback=self.playlist_progress_callback,
                        completion_callback=_cb
                    )
                    self.current_downloader.start()
                    done_event.wait()

                    if self.is_playlist_cancelled:
                        break

                    if dl_result['success'] and dl_result['path'] and os.path.exists(dl_result['path']):
                        last_success_path = dl_result['path']
                        sz = f"{os.path.getsize(dl_result['path']) / 1024 / 1024:.2f} MB"
                        add_download_history(
                            video_url, fmt, dl_result['path'],
                            size=sz,
                            status="Thành công",
                            folder_path=folder.replace("/", "\\")
                        )
                    else:
                        add_download_history(
                            video_url, fmt, final_path,
                            size="Không rõ",
                            status="Thất bại",
                            folder_path=folder.replace("/", "\\")
                        )

                if self.is_playlist_cancelled:
                    self.tab_playlist.after(0, lambda: self.playlist_progress_status.configure(text=self.get_text("download_cancelled")))
                    self.tab_playlist.after(0, lambda: self.playlist_progress_bar.set(0))
                else:
                    self.tab_playlist.after(0, lambda: self.playlist_progress_status.configure(text=self.get_text("download_success")))
                    self.tab_playlist.after(0, lambda: self.playlist_progress_bar.set(1.0))
                    if last_success_path and os.path.exists(last_success_path) and self.notify_download_complete:
                        self.tab_playlist.after(0, lambda: self.show_download_complete_popup(last_success_path, self.tab_playlist))

            except Exception as e:
                err_msg = str(e)
                self.tab_playlist.after(0, lambda: self.playlist_progress_status.configure(text=self.get_text("download_failed")))
                self.tab_playlist.after(0, lambda: self.playlist_progress_bar.set(0))
                self.tab_playlist.after(0, lambda: self.show_message(self.get_text("error"), f"Không thể tải playlist: {err_msg}", "error"))
            finally:
                self.is_playlist_downloading = False
                self.tab_playlist.after(0, lambda: self.playlist_download_button.configure(state="normal"))
                if hasattr(self, 'playlist_cancel_button'):
                    self.tab_playlist.after(0, lambda: self.playlist_cancel_button.configure(state="disabled"))

        threading.Thread(target=playlist_download_thread, daemon=True).start()

    def playlist_progress_callback(self, d):
        if isinstance(d, dict) and d.get('status') == 'downloading':
            progress = d.get('progress', 0.0)
            if isinstance(progress, (int, float)):
                self.tab_playlist.after(0, lambda: self.playlist_progress_bar.set(min(1.0, max(0.0, float(progress)))))
            percent = d.get('percent', progress * 100)
            speed = d.get('speed', '--')
            self.tab_playlist.after(0, lambda: self.playlist_speed_label.configure(text=f"Speed: {speed} ({percent:.1f}%)"))
        elif isinstance(d, dict) and d.get('status') == 'finished':
            self.tab_playlist.after(0, lambda: self.playlist_progress_bar.set(1.0))
            self.tab_playlist.after(0, lambda: self.playlist_speed_label.configure(text="Speed: --"))

def run_app():
    global THEME_PATH
    ctk.set_appearance_mode("dark")  # Mặc định dark mode
    if not os.path.exists(THEME_PATH):
        for candidate in [
            os.path.join(os.path.dirname(sys.executable), "_internal", "assets", "themes", "sunset_coral.json"),
            os.path.join(os.path.dirname(sys.executable), "assets", "themes", "sunset_coral.json"),
            os.path.join(ROOT_DIR, "assets", "themes", "sunset_coral.json")
        ]:
            if os.path.exists(candidate):
                THEME_PATH = candidate
                break

    logging.info(f"Using theme path: {THEME_PATH} (exists: {os.path.exists(THEME_PATH)})")
    if os.path.exists(THEME_PATH):
        ctk.set_default_color_theme(THEME_PATH)
    else:
        logging.warning("Theme file not found, falling back to dark-blue")
        ctk.set_default_color_theme("dark-blue")

    root = ctk.CTk()
    app = DownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()