import os

# Đường dẫn
ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(ROOT_DIR, "data")
ASSETS_DIR = os.path.join(ROOT_DIR, "assets")

# Cấu hình ứng dụng
APP_CONFIG = {
    "app_title": "Social Media Downloader",
    "app_size": "600x400",
    "max_history_display": 50,
    "font_title": ("Arial", 24, "bold"),
    "font_subtitle": ("Arial", 14),
    "font_normal": ("Arial", 14),
    "font_small": ("Arial", 12),
    "button_font": ("Arial", 16, "bold"),
    "platforms": ["YouTube", "TikTok", "Vimeo", "SoundCloud"]
}

# Cấu hình mặc định cho cột lịch sử
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