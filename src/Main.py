import os
import sys
import shutil
import logging
from ui import run_app

def setup_logging():
    """Thiết lập logging cơ bản"""
    log_dir = os.path.dirname(os.path.abspath(__file__))
    log_file = os.path.join(log_dir, "app.log")
    
    try:
        logging.basicConfig(
            filename=log_file,
            level=logging.ERROR,
            format="%(asctime)s - %(levelname)s - %(message)s"
        )
    except Exception as e:
        print(f"Không thể thiết lập logging: {e}")

def check_requirements():
    """Kiểm tra các thư viện và công cụ cần thiết đã được cài đặt chưa"""
    try:
        import customtkinter
        import yt_dlp
        if not shutil.which("ffmpeg"):
            print("Lỗi: FFmpeg không được cài đặt. Vui lòng cài FFmpeg bằng cách xem: https://ffmpeg.org/download.html")
            return False
    except ImportError as e:
        print(f"Lỗi: Thiếu thư viện cần thiết: {e}")
        print("Vui lòng cài đặt bằng cách chạy: pip install customtkinter yt-dlp")
        return False
    return True

def main():
    """Hàm chính để chạy ứng dụng"""
    setup_logging()
    
    if not check_requirements():
        sys.exit(1)
        
    try:
        run_app()
    except Exception as e:
        logging.error(f"Lỗi khởi động ứng dụng: {e}", exc_info=True)
        print(f"Có lỗi xảy ra khi khởi động ứng dụng: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()