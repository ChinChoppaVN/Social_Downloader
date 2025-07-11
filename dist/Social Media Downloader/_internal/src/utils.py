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
from tkinter import messagebox, filedialog
import csv

# Đường dẫn
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if getattr(sys, 'frozen', False):
    # Nếu đang chạy từ exe đã đóng gói
    APP_DATA = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
    DATA_DIR = os.path.join(APP_DATA, "data")
else:
    # Nếu đang chạy từ mã nguồn
    DATA_DIR = os.path.join(ROOT_DIR, "data")

# Thêm thư mục gốc vào sys.path
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# Đảm bảo thư mục data tồn tại
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

def get_clean_filename(name, ext):
    # Loại bỏ đuôi .mp3 hoặc .mp4 nếu đã có
    if name.lower().endswith((".mp3", ".mp4")):
        name = name.rsplit(".", 1)[0]
    
    # Loại bỏ ký tự đặc biệt (trừ # để xử lý hashtag riêng)
    invalid_chars = '<>:"/\\|?!*.-'
    for char in invalid_chars:
        name = name.replace(char, '')
    
    # Xử lý loại bỏ toàn bộ hashtag
    result = []
    i = 0
    while i < len(name):
        if name[i] == '#' and i + 1 < len(name):
            j = i + 1
            while j < len(name) and (name[j].isalnum() or name[j] == '_'):
                j += 1
            i = j
        else:
            result.append(name[i])
            i += 1
    name = ''.join(result)
    
    # Thay dấu cách bằng dấu gạch dưới
    name = name.replace(" ", "_")
    
    # Gộp các dấu _ liên tiếp thành một dấu _ (củng cố logic)
    original_name = None
    while original_name != name:  # Lặp cho đến khi không còn thay đổi
        original_name = name
        name = name.replace("__", "_")
    
    # Thêm kiểm tra bổ sung để đảm bảo không còn __
    name = name.strip("_")  # Loại bỏ _ ở đầu và cuối nếu có
    
    return f"{name}.{ext}" if name else f"video.{ext}"

def fetch_video_title(url):
    """Lấy tiêu đề video từ URL bằng yt_dlp"""
    ydl_opts = {'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video_youtube')
            # Làm sạch tiêu đề trước khi trả về
            clean_title = get_clean_filename(title, "mp3")
            return os.path.splitext(clean_title)[0]  # Loại bỏ đuôi để tránh ảnh hưởng
    except Exception as e:
        logging.error(f"Không thể lấy tiêu đề video: {e}")
        return "video_youtube"

def validate_url(url):
    from urllib.parse import urlparse, parse_qs
    try:
        result = urlparse(url)
        if result.netloc == "www.youtube.com" and result.path == "/watch":
            query = parse_qs(result.query)
            return "v" in query and all([result.scheme, result.netloc])
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def load_last_folder():
    """Tải thư mục cuối cùng được sử dụng từ file config.json"""
    default_folder = os.path.expanduser("~")
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("last_folder", config.get("folder", default_folder))
        except json.JSONDecodeError:
            logging.warning(f"File {CONFIG_FILE} bị lỗi định dạng, sử dụng thư mục mặc định.")
            return default_folder
    return default_folder

def save_last_folder(folder):
    """Lưu thư mục cuối cùng vào file config.json"""
    config = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                config = json.load(f)
        except json.JSONDecodeError:
            logging.warning(f"File {CONFIG_FILE} bị lỗi định dạng, tạo mới.")
            config = {}
    config["last_folder"] = folder
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(config, f, ensure_ascii=False, indent=4)

def get_download_history():
    """Lấy lịch sử tải xuống từ file"""
    try:
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception as e:
        logging.error(f"Lỗi khi đọc lịch sử: {e}")
    return []

def add_download_history(url, file_type, file_path, size="Không rõ", status="Thành công", folder_path="Không rõ"):
    """Thêm một mục vào lịch sử tải xuống"""
    try:
        history = get_download_history()
        history.append({
            "url": url,
            "file_type": file_type,
            "file_path": file_path,
            "size": size,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "folder_path": folder_path
        })
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Lỗi khi thêm vào lịch sử: {e}")

def clear_download_history():
    """Xóa toàn bộ lịch sử tải xuống"""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump([], f)
    except Exception as e:
        logging.error(f"Lỗi khi xóa lịch sử: {e}")

def export_download_history(export_path):
    """Xuất lịch sử tải xuống ra file CSV"""
    try:
        history = get_download_history()
        if not history:
            return False
            
        with open(export_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            writer.writerow(["URL", "Loại File", "Đường dẫn", "Kích thước", "Thời gian", "Trạng thái", "Thư mục lưu"])
            for entry in history:
                writer.writerow([
                    entry["url"],
                    entry["file_type"],
                    entry["file_path"],
                    entry.get("size", "Không rõ"),
                    entry["timestamp"],
                    entry.get("status", "Thành công"),
                    entry.get("folder_path", "Không rõ")
                ])
        return True
    except Exception as e:
        logging.error(f"Lỗi khi xuất lịch sử: {e}")
        return False

def download_yt_dlp(dest_path, progress_callback=None):
    """Tải yt-dlp.exe mới nhất từ GitHub về dest_path. Gọi progress_callback(downloaded, total) nếu có."""
    import requests
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    try:
        with requests.get(url, stream=True, timeout=60) as r:
            r.raise_for_status()
            total = int(r.headers.get('content-length', 0))
            downloaded = 0
            with open(dest_path, 'wb') as f:
                for chunk in r.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        if progress_callback:
                            progress_callback(downloaded, total)
        return True, None
    except Exception as e:
        return False, str(e)