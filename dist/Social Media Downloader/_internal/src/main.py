import os
import sys
import shutil
import logging
import subprocess

# Thêm đường dẫn của thư mục gốc vào sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Thiết lập môi trường khi chạy từ exe
if getattr(sys, 'frozen', False):
    # Nếu đang chạy từ exe
    application_path = os.path.dirname(sys.executable)
    
    # Thêm đường dẫn assets vào PATH
    assets_path = os.path.join(application_path, "assets")
    if assets_path not in os.environ["PATH"]:
        os.environ["PATH"] = assets_path + os.pathsep + os.environ["PATH"]
    
    # Tạo thư mục data trong AppData
    app_data_path = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
    data_path = os.path.join(app_data_path, "data")
    if not os.path.exists(data_path):
        os.makedirs(data_path)

# Import các module từ thư mục src
from src.ui import run_app

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

def check_yt_dlp_version():
    try:
        import urllib.request
        import json
        from tkinter import messagebox
        import yt_dlp
        from packaging.version import parse as parse_version
        
        # Thiết lập logging nếu chưa được thiết lập
        if not logging.getLogger().handlers:
            setup_logging()
        
        # Kiểm tra phiên bản yt-dlp hiện tại
        current_version = yt_dlp.version.__version__
        
        # Kiểm tra phiên bản mới nhất từ PyPI
        response = urllib.request.urlopen("https://pypi.org/pypi/yt-dlp/json")
        data = json.loads(response.read())
        latest_version = data["info"]["version"]
        
        # Log để debug
        logging.info(f"Phiên bản yt-dlp hiện tại: '{current_version}'")
        logging.info(f"Phiên bản yt-dlp mới nhất: '{latest_version}'")
        
        # So sánh phiên bản sử dụng LooseVersion để so sánh đúng cách
        try:
            current_v = parse_version(current_version)
            latest_v = parse_version(latest_version)
            
            if current_v < latest_v:  # Chỉ cập nhật nếu phiên bản hiện tại nhỏ hơn phiên bản mới nhất
                result = messagebox.askyesno(
                    "Cập nhật yt-dlp",
                    f"Có phiên bản yt-dlp mới ({latest_version}). Phiên bản hiện tại là {current_version}.\n\nBạn có muốn cập nhật không?"
                )
                if result:
                    try:
                        # Cập nhật yt-dlp
                        application_path = os.path.dirname(sys.executable)
                        subprocess.run([sys.executable, "-m", "pip", "install", "--upgrade", "yt-dlp"], 
                                      check=True, cwd=application_path)
                        messagebox.showinfo("Thành công", "Đã cập nhật yt-dlp. Vui lòng khởi động lại ứng dụng.")
                    except Exception as update_err:
                        logging.error(f"Lỗi khi cập nhật yt-dlp: {update_err}")
                        messagebox.showerror("Lỗi", f"Không thể cập nhật yt-dlp: {update_err}")
        except Exception as version_err:
            logging.error(f"Lỗi khi so sánh phiên bản: {version_err}")
        
        return True
    except Exception as e:
        logging.error(f"Lỗi kiểm tra phiên bản yt-dlp: {e}")
        return False

def main():
    """Hàm chính để chạy ứng dụng"""
    setup_logging()
    
    if not check_requirements():
        sys.exit(1)
    
    # Kiểm tra và cập nhật yt-dlp nếu cần
    check_yt_dlp_version()
        
    try:
        run_app()
    except Exception as e:
        logging.error(f"Lỗi khởi động ứng dụng: {e}", exc_info=True)
        print(f"Có lỗi xảy ra khi khởi động ứng dụng: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()