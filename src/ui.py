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
import yt_dlp
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk, Menu
import csv
from functools import partial
import tkinter as tk  # Đảm bảo đã import tk

# Thêm thư mục gốc vào sys.path
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

# Đường dẫn
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")
DATA_DIR = os.path.join(ROOT_DIR, "data")

# Import các module từ thư mục src
from src.downloader import download_video, show_download_complete_popup
from src.utils import (
    get_clean_filename, load_last_folder, save_last_folder, 
    fetch_video_title, validate_url, add_download_history, 
    get_download_history, clear_download_history, export_download_history,
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
                "Thất bại": "Thất bại"
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
                "Thất bại": "Failed"
            }
        }
        self.load_settings()
        self.root.title(self.get_text("app_title"))
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
        self.download_start_time = None
        
        # Biến theo dõi trạng thái sắp xếp
        self.current_sort_reverse = False
        
        # Thêm biến trạng thái
        self.notify_download_complete = True

        self.create_widgets()

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
        label_language = self.get_text("Ngôn ngữ") if self.current_language == "Tiếng Việt" else "Language"
        label_theme = self.get_text("Giao diện") if self.current_language == "Tiếng Việt" else "Theme"
        menubar.add_command(label=label_history, command=self.show_download_history)
        language_menu = Menu(menubar, tearoff=0)
        language_menu.add_command(label="Tiếng Việt", command=lambda: self.change_language("Tiếng Việt"))
        language_menu.add_command(label="English", command=lambda: self.change_language("English"))
        menubar.add_cascade(label=label_language, menu=language_menu)
        theme_menu = Menu(menubar, tearoff=0)
        theme_menu.add_command(label="Tối" if self.current_language == "Tiếng Việt" else "Dark", command=lambda: self.change_theme("Tối" if self.current_language == "Tiếng Việt" else "Dark"))
        theme_menu.add_command(label="Sáng" if self.current_language == "Tiếng Việt" else "Light", command=lambda: self.change_theme("Sáng" if self.current_language == "Tiếng Việt" else "Light"))
        theme_menu.add_command(label="Hệ thống" if self.current_language == "Tiếng Việt" else "System", command=lambda: self.change_theme("Hệ thống" if self.current_language == "Tiếng Việt" else "System"))
        menubar.add_cascade(label=label_theme, menu=theme_menu)
        # Thông báo tải xong: submenu Bật/Tắt hoặc On/Off
        notify_menu = Menu(menubar, tearoff=0)
        notify_menu.add_radiobutton(label=self.get_text("notify_on"), value=1, variable=self.notify_var, command=lambda: self.set_notify_download_complete(True))
        notify_menu.add_radiobutton(label=self.get_text("notify_off"), value=0, variable=self.notify_var, command=lambda: self.set_notify_download_complete(False))
        menubar.add_cascade(label=self.get_text("notify_menu"), menu=notify_menu)
        self.root.config(menu=menubar)

    def create_widgets(self):
        self.create_header()
        self.create_main_frame()
        self.create_footer()

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

    def create_main_frame(self):
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(self.main_frame, text=self.get_text("link_label"), font=APP_CONFIG["font_normal"]).grid(row=0, column=0, sticky="w", pady=5, padx=15)
        self.url_entry = ctk.CTkEntry(self.main_frame, width=350, placeholder_text=self.get_text("input_url"))
        self.url_entry.grid(row=0, column=1, pady=5, sticky="w")
        
        paste_button = ctk.CTkButton(
            self.main_frame, 
            text=self.get_text("paste"), 
            width=90,
            command=self.paste_url,
            font=APP_CONFIG["font_normal"]
        )
        paste_button.grid(row=0, column=2, pady=5, padx=15, sticky="w")
        
        ctk.CTkLabel(self.main_frame, text=self.get_text("filename_label"), font=APP_CONFIG["font_normal"]).grid(row=1, column=0, sticky="w", pady=5, padx=15)
        self.filename_entry = ctk.CTkEntry(self.main_frame, width=350, placeholder_text=self.get_text("filename_placeholder"))
        self.filename_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=5)
        
        ctk.CTkLabel(self.main_frame, text=self.get_text("folder_label"), font=APP_CONFIG["font_normal"]).grid(row=2, column=0, sticky="w", pady=5, padx=15)
        last_folder = load_last_folder()
        self.folder_var = ctk.StringVar(value=last_folder)
        self.folder_entry = ctk.CTkEntry(self.main_frame, textvariable=self.folder_var, width=350)
        self.folder_entry.grid(row=2, column=1, pady=5, sticky="w")
        
        folder_button = ctk.CTkButton(self.main_frame, text=self.get_text("choose"), command=self.select_folder, width=90)
        folder_button.grid(row=2, column=2, pady=5, padx=15, sticky="w")
        
        self.file_status_label = ctk.CTkLabel(self.main_frame, text="", text_color="red", font=APP_CONFIG["font_small"])
        self.file_status_label.grid(row=3, column=1, columnspan=2, sticky="w", pady=(0,5))
        
        ctk.CTkLabel(self.main_frame, text=self.get_text("format_label"), font=APP_CONFIG["font_normal"]).grid(row=3, column=0, sticky="w", pady=5, padx=15)
        
        mp4_button = ctk.CTkButton(self.main_frame, text=self.get_text("mp4"), command=lambda: self.toggle_format("mp4"), width=80, fg_color=("green", "#1D6F42") if self.mp4_selected.get() else "gray", state="normal")
        mp4_button.grid(row=3, column=1, pady=5, padx=0, sticky="w")
        
        mp3_button = ctk.CTkButton(self.main_frame, text=self.get_text("mp3"), command=lambda: self.toggle_format("mp3"), width=80, fg_color=("green", "#1D6F42") if self.mp3_selected.get() else "gray", state="normal")
        mp3_button.grid(row=3, column=1, pady=5, padx=85, sticky="w")
        
        # Progress Frame mới
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=15, pady=5)

        # Label cho tiến trình
        self.progress_status = ctk.CTkLabel(
            progress_frame, 
            text=self.get_text("ready"), 
            font=APP_CONFIG["font_small"],
            anchor="w"
        )
        self.progress_status.pack(fill="x", padx=5, pady=(5,0))
        
        # Frame cho progress bar và nút điều khiển
        progress_control_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        progress_control_frame.pack(fill="x", padx=5, pady=5)
        
        # Progress bar với màu gradient và bo góc
        self.progress_bar = ctk.CTkProgressBar(
            progress_control_frame,
            width=350,
            height=15,
            corner_radius=8,
            border_width=0,
            progress_color=("green", "#1D6F42"),
            fg_color=("gray85", "gray20")
        )
        self.progress_bar.pack(side="left", fill="x", expand=True, padx=(0,10))
        self.progress_bar.set(0)
        
        # Frame cho các nút điều khiển
        control_buttons_frame = ctk.CTkFrame(progress_control_frame, fg_color="transparent")
        control_buttons_frame.pack(side="right")
        
        # Nút pause/play gộp
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
        
        # Nút cancel
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
        
        # Frame cho thông tin chi tiết
        info_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=5, pady=(0,5))

        # Cấu hình grid cho info_frame
        info_frame.grid_columnconfigure(0, weight=1)
        info_frame.grid_columnconfigure(1, weight=1)
        info_frame.grid_columnconfigure(2, weight=1)

        # Labels cho thông tin tải với chiều rộng cố định
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

        # Tạo frame cho các nút điều khiển
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=10)

        self.download_button = ctk.CTkButton(button_frame, text=self.get_text("download_now"), command=self.start_download, font=APP_CONFIG["button_font"])
        self.download_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        self.main_frame.columnconfigure(1, weight=1)
        self.mp4_selected.trace("w", self.update_button_colors)
        self.mp3_selected.trace("w", self.update_button_colors)

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
        mp4_widgets = self.main_frame.grid_slaves(row=3, column=1)
        mp4_button = None
        for widget in mp4_widgets:
            if isinstance(widget, ctk.CTkButton) and widget.grid_info()['padx'] == 0:
                mp4_button = widget
                break
        if mp4_button:
            mp4_button.configure(fg_color=("green", "#1D6F42") if self.mp4_selected.get() else "gray", state="normal")
        else:
            logging.warning("Không tìm thấy nút MP4 tại row=3, column=1 với padx=0")
        
        mp3_widgets = self.main_frame.grid_slaves(row=3, column=1)
        mp3_button = None
        for widget in mp3_widgets:
            if isinstance(widget, ctk.CTkButton) and widget.grid_info()['padx'] == 85:
                mp3_button = widget
                break
        if mp3_button:
            mp3_button.configure(fg_color=("green", "#1D6F42") if self.mp3_selected.get() else "gray", state="normal")
        else:
            logging.warning("Không tìm thấy nút MP3 tại row=3, column=1 với padx=85")

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
        if d['status'] == 'downloading':
            if hasattr(self, 'is_cancelled') and self.is_cancelled:
                raise Exception("Download cancelled")
                
            if hasattr(self, 'is_paused') and self.is_paused:
                while self.is_paused and not self.is_cancelled:
                    self.root.update()  # Cập nhật giao diện trong khi tạm dừng
                    self.root.after(100)  # Chờ 100ms
                if self.is_cancelled:
                    raise Exception("Download cancelled")
                return
            
            # Tính toán phần trăm
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                # Cập nhật progress bar
                progress = downloaded / total
                self.progress_bar.set(progress)
                
                # Hiển thị phần trăm
                percent = progress * 100
                self.progress_status.configure(
                    text=f"{self.get_text('downloading')} {percent:.1f}%"
                )
                
                # Hiển thị tốc độ
                speed = d.get('speed', 0)
                if speed:
                    speed_mb = speed / 1024 / 1024
                    self.speed_label.configure(text=f"Tốc độ: {speed_mb:.1f} MB/s")
                
                # Hiển thị thời gian còn lại
                eta = d.get('eta', 0)
                if eta:
                    minutes = int(eta // 60)
                    seconds = int(eta % 60)
                    time_left = f"{minutes:02d}:{seconds:02d}"
                    self.time_label.configure(text=f"Thời gian: {time_left}")
                
                # Hiển thị kích thước
                downloaded_mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                self.size_label.configure(
                    text=f"Dung lượng: {downloaded_mb:.1f}MB/{total_mb:.1f}MB"
                )
                
        elif d['status'] == 'finished':
            if not self.is_cancelled:  # Chỉ cập nhật nếu không phải do hủy
                self.progress_status.configure(text=self.get_text("download_success"))
                self.speed_label.configure(text="Tốc độ: --")
                self.time_label.configure(text="Thời gian: --")
                self.size_label.configure(text="Dung lượng: --")
                self.update_control_buttons("finished")
            
        elif d['status'] == 'error':
            if not self.is_cancelled:  # Chỉ hiển thị lỗi nếu không phải do hủy
                self.progress_status.configure(text=self.get_text("download_failed"))
                self.progress_bar.set(0)
                self.speed_label.configure(text="Tốc độ: --")
                self.time_label.configure(text="Thời gian: --")
                self.size_label.configure(text="Dung lượng: --")
                self.update_control_buttons("ready")

    def reset_ui_state(self):
        """Reset tất cả trạng thái UI về mặc định"""
        self.progress_bar.set(0)
        self.progress_status.configure(text=self.get_text("ready"))
        self.speed_label.configure(text="Tốc độ: --")
        self.time_label.configure(text="Thời gian: --")
        self.size_label.configure(text="Dung lượng: --")     
        self.url_entry.delete(0, ctk.END)
        self.url_entry.configure(placeholder_text=self.get_text("input_url"))
        self.filename_entry.delete(0, ctk.END)
        self.filename_entry.configure(placeholder_text=self.get_text("filename_placeholder"))

    def download_thread(self, url, file_type, final_path, parent_window):
        try:
            download_success = download_video(url, final_path, self.progress_callback)
            if download_success and os.path.exists(final_path):
                parent_window.after(0, lambda: add_download_history(
                    url, file_type, final_path, 
                    size=f"{os.path.getsize(final_path) / 1024 / 1024:.2f} MB",
                    status="Thành công",
                    folder_path=os.path.dirname(final_path).replace("/", "\\")
                ))
                parent_window.after(0, lambda: self.progress_status.configure(text=self.get_text("download_success")))
                parent_window.after(0, lambda: self.update_control_buttons("finished"))
                # Chỉ hiển thị popup nếu notify_download_complete đang bật
                if self.notify_download_complete:
                    parent_window.after(0, lambda: show_download_complete_popup(
                        final_path, parent_window,
                        notify_state=self.notify_download_complete,
                        on_notify_change=self.set_notify_download_complete
                    ))
        except Exception as e:
            if str(e) == "Download cancelled":
                parent_window.after(0, lambda: add_download_history(
                    url, file_type, final_path,
                    size="Không rõ",
                    status="Đã hủy",
                    folder_path="Không rõ"
                ))
                parent_window.after(0, lambda: self.progress_status.configure(text=self.get_text("download_cancelled")))
                parent_window.after(0, lambda: self.progress_bar.set(0))
                parent_window.after(0, lambda: self.speed_label.configure(text=self.get_text("speed")))
                parent_window.after(0, lambda: self.time_label.configure(text=self.get_text("time")))
                parent_window.after(0, lambda: self.size_label.configure(text=self.get_text("size")))
                parent_window.after(0, lambda: self.update_control_buttons("ready"))
                if os.path.exists(final_path):
                    try:
                        os.remove(final_path)
                    except Exception as ex:
                        print(f"Không thể xóa file tạm: {ex}")
            else:
                parent_window.after(0, lambda: add_download_history(
                    url, file_type, final_path,
                    size="Không rõ",
                    status="Thất bại",
                    folder_path="Không rõ"
                ))
                parent_window.after(0, lambda: self.progress_status.configure(text=self.get_text("download_failed")))
                parent_window.after(0, lambda: self.progress_bar.set(0))
                parent_window.after(0, lambda: self.speed_label.configure(text=self.get_text("speed")))
                parent_window.after(0, lambda: self.time_label.configure(text=self.get_text("time")))
                parent_window.after(0, lambda: self.size_label.configure(text=self.get_text("size")))
                parent_window.after(0, lambda: self.update_control_buttons("ready"))
                parent_window.after(0, lambda: messagebox.showerror(self.get_text("error"), f"Không thể tải: {str(e)}"))
        finally:
            self.is_downloading = False
            parent_window.after(0, lambda: self.download_button.configure(state="normal"))
            parent_window.after(0, lambda: self.reset_ui_state())

    def start_download(self):
        if self.is_downloading:
            self.show_message("Thông báo", "Đang tải, vui lòng chờ!")
            return

        url = self.url_entry.get().strip()
        if not url:
            self.show_message("Lỗi", self.get_text("input_url"), "error")
            return
            
        if not validate_url(url):
            self.show_message("Lỗi", self.get_text("invalid_url"), "error")
            return
            
        folder = self.folder_var.get().strip()
        if not folder:
            self.show_message("Lỗi", self.get_text("input_folder"), "error")
            return
            
        if not shutil.which("ffmpeg"):
            self.show_message("Lỗi", self.get_text("ffmpeg_missing"), "error")
            return
            
        name_input = self.filename_entry.get().strip()
        if not name_input:
            name_input = fetch_video_title(url)

        # Reset các biến điều khiển
        self.is_paused = False
        self.is_cancelled = False
        
        # Reset thanh tiến trình và thông tin
        self.progress_bar.set(0)
        self.progress_status.configure(text=self.get_text("downloading"))
        self.download_start_time = None
        
        # Kích hoạt các nút điều khiển ngay khi bắt đầu tải
        self.pause_play_button.configure(state="normal")
        self.cancel_button.configure(state="normal")

        # Chuẩn hóa tên file trước khi tạo final_path
        if self.mp4_selected.get():
            file_type = "mp4"
            clean_name = get_clean_filename(name_input, file_type)
            final_path = os.path.join(folder, clean_name)

            if os.path.exists(final_path):
                if not self.show_message(self.get_text("confirm"), self.get_text("confirm_overwrite", ext=file_type), "yesno"):
                    return

            self.is_downloading = True
            self.download_button.configure(state="disabled")
            threading.Thread(target=self.download_thread, args=(url, file_type, final_path, self.root), daemon=True).start()
            
        elif self.mp3_selected.get():
            file_type = "mp3"
            clean_name = get_clean_filename(name_input, file_type)
            final_path = os.path.join(folder, clean_name)

            if os.path.exists(final_path):
                if not self.show_message(self.get_text("confirm"), self.get_text("confirm_overwrite", ext=file_type), "yesno"):
                    return

            self.is_downloading = True
            self.download_button.configure(state="disabled")
            threading.Thread(target=self.download_thread, args=(url, file_type, final_path, self.root), daemon=True).start()
            
        else:
            self.show_message("Cảnh báo", self.get_text("select_format"), "warning")
            self.is_downloading = False

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
        main_frame = ctk.CTkFrame(history_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        top_frame = ctk.CTkFrame(main_frame)
        top_frame.pack(fill="x", pady=(0, 5))
        search_entry = ctk.CTkEntry(top_frame, placeholder_text=self.get_text("search_placeholder") if "search_placeholder" in self.translations[self.current_language] else "Tìm kiếm (URL, Tên file, Thời gian)...", width=300)
        search_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        toolbar_frame = ctk.CTkFrame(top_frame)
        toolbar_frame.pack(side="right")
        columns = tuple(DEFAULT_COLUMNS)
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=350)
        tree.pack(fill="both", expand=True, pady=5)
        tree.configure(style="Custom.Treeview")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white")
        style.map("Custom.Treeview", background=[("selected", "#0066cc")], foreground=[("selected", "white")])
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
        """Mở file được chọn"""
        if file_path and os.path.exists(file_path):
            try:
                # Nếu parent_window được truyền vào, tắt thuộc tính topmost
                if parent_window and hasattr(parent_window, 'attributes'):
                    parent_window.attributes("-topmost", False)
                
                os.startfile(file_path)
            except Exception as e:
                self.show_message("Lỗi", f"Không thể mở file: {e}", "error")
        else:
            self.show_message("Lỗi", "File không tồn tại!", "error")

    def open_folder_with_highlight(self, file_path, parent_window=None):
        """Mở thư mục và highlight file được chọn"""
        if file_path and os.path.exists(file_path):
            try:
                # Nếu parent_window được truyền vào, tắt thuộc tính topmost
                if parent_window and hasattr(parent_window, 'attributes'):
                    parent_window.attributes("-topmost", False)
                                
                if platform.system() == "Windows":
                    file_path = os.path.abspath(file_path)
                    file_path = os.path.normpath(file_path)
                    subprocess.run(['explorer', '/select,', file_path])
                else:
                    subprocess.run(["xdg-open", os.path.dirname(file_path)], check=True)
            except Exception as e:
                self.show_message("Lỗi", f"Không thể mở thư mục: {e}", "error")
        else:
            self.show_message("Lỗi", "File không tồn tại!", "error")

    def toggle_download(self):
        """Chuyển đổi giữa tạm dừng và tiếp tục tải"""
        if not hasattr(self, 'is_paused'):
            self.is_paused = False
            
        self.is_paused = not self.is_paused
        
        if self.is_paused:
            self.pause_play_button.configure(text="▶")  # Chuyển sang nút play
            self.progress_status.configure(text=self.get_text("pause"))
        else:
            self.pause_play_button.configure(text="⏸")  # Chuyển sang nút pause
            self.progress_status.configure(text=self.get_text("downloading"))

    def cancel_download(self):
        """Hủy quá trình tải xuống"""
        if self.show_message("Xác nhận", "Bạn có chắc muốn hủy tải xuống?", "yesno"):
            self.is_cancelled = True
            self.is_downloading = False
            self.progress_status.configure(text=self.get_text("download_cancelled"))
            self.progress_bar.set(0)
            self.speed_label.configure(text="Tốc độ: --")
            self.time_label.configure(text="Thời gian: --")
            self.size_label.configure(text="Dung lượng: --")
            self.update_control_buttons("ready")
            self.download_button.configure(state="normal")

    def update_control_buttons(self, status="ready"):
        """Cập nhật trạng thái các nút điều khiển"""
        if status == "ready":  # Sẵn sàng tải
            self.pause_play_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")
        elif status == "downloading":  # Đang tải
            self.pause_play_button.configure(state="normal")
            self.cancel_button.configure(state="normal")
        elif status == "finished":  # Hoàn thành
            self.pause_play_button.configure(state="disabled")
            self.cancel_button.configure(state="disabled")

    def paste_url(self):
        """Dán link từ clipboard vào ô nhập URL"""
        try:
            url = self.root.clipboard_get()
            self.url_entry.delete(0, ctk.END)
            self.url_entry.insert(0, url)
        except Exception as e:
            logging.error(f"Không thể dán từ clipboard: {e}")
            self.show_message("Lỗi", "Không thể dán từ clipboard!", "error")

    def show_message(self, title, message, type="info", parent=None):
        if parent is None:
            parent = self.root
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
        parent.lift()

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
        self.create_menubar()  # Cập nhật lại menubar khi đổi từ popup

def run_app():
    ctk.set_appearance_mode("dark")  # Mặc định dark mode
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    app = DownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()