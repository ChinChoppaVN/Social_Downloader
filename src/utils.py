import os
import json
import logging
import csv
from datetime import datetime
from tkinter import filedialog
import yt_dlp

# Sử dụng đường dẫn tương đối để import
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config.app_config import DATA_DIR

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

def add_download_history(url, file_type, file_path, size=None, status="Thành công", folder_path=None):
    history = []
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            history = json.load(f)
    
    if size is None and os.path.exists(file_path):
        size = f"{os.path.getsize(file_path) / 1024 / 1024:.2f} MB"
    
    if folder_path is None:
        folder_path = os.path.dirname(file_path)
    folder_path = os.path.normpath(folder_path).replace("/", "\\")
    
    new_entry = {
        "url": url,
        "file_type": file_type,
        "file_path": file_path,
        "size": size,
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "status": status,
        "folder_path": folder_path
    }
    
    history.append(new_entry)
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(history, f, ensure_ascii=False, indent=4)

def get_download_history():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def clear_download_history():
    if os.path.exists(HISTORY_FILE):
        os.remove(HISTORY_FILE)

def export_download_history(filename=None):
    history = get_download_history()
    if not history:
        return False
    
    if not filename:
        filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Lưu lịch sử tải dưới dạng CSV")
        if not filename:
            return False
    
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["STT", "URL", "Tên file", "Định dạng", "Kích thước", "Thời gian", "Trạng thái", "Thư mục lưu"])
        for i, entry in enumerate(reversed(history[-50:]), 1):
            writer.writerow([
                i,
                entry['url'],
                os.path.basename(entry['file_path']),
                entry['file_type'],
                entry.get('size', 'Không rõ'),
                entry['timestamp'],
                entry.get('status', 'Thành công'),
                entry.get('folder_path', 'Không rõ')
            ])
    return True