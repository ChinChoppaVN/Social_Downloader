import os
import sys
import shutil
import logging
import subprocess
import json

# Thêm đường dẫn của thư mục gốc vào sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Thiết lập môi trường khi chạy từ exe
if getattr(sys, 'frozen', False):
    # Nếu đang chạy từ exe
    application_path = os.path.dirname(sys.executable)
    
    # Thêm đường dẫn assets vào PATH - kiểm tra cả trong _internal
    assets_paths = [
        os.path.join(application_path, "assets"),                  # Thư mục assets trực tiếp
        os.path.join(application_path, "_internal", "assets"),    # Thư mục assets trong _internal
    ]
    
    # Thêm tất cả các đường dẫn assets vào PATH
    for assets_path in assets_paths:
        if os.path.exists(assets_path) and assets_path not in os.environ["PATH"]:
            print(f"Thêm đường dẫn vào PATH: {assets_path}")
            os.environ["PATH"] = assets_path + os.pathsep + os.environ["PATH"]
    
    # Tạo thư mục data trong AppData
    app_data_path = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
    data_path = os.path.join(app_data_path, "data")
    if not os.path.exists(data_path):
        os.makedirs(data_path)

# Import các module từ thư mục src
from src.ui import run_app
from src.utils import DATA_DIR  # Thêm import DATA_DIR từ utils

def setup_logging():
    """Thiết lập logging cơ bản"""
    try:
        # Nếu đang chạy từ exe, sử dụng thư mục AppData
        if getattr(sys, 'frozen', False):
            app_data_path = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
            if not os.path.exists(app_data_path):
                os.makedirs(app_data_path)
            log_file = os.path.join(app_data_path, "app.log")
        else:
            # Nếu đang chạy từ mã nguồn
            log_dir = os.path.dirname(os.path.abspath(__file__))
            log_file = os.path.join(log_dir, "app.log")
        
        # Thiết lập logging với cả file và console
        logging.basicConfig(
            level=logging.DEBUG,  # Tăng level để ghi nhiều thông tin hơn
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Thêm handler để ghi ra console
            ]
        )
        logging.info("Đã khởi tạo logging thành công")
    except Exception as e:
        print(f"Không thể thiết lập logging: {e}")
        # Cố gắng thiết lập logging cơ bản chỉ với console
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )

def check_requirements():
    """Kiểm tra các thư viện và công cụ cần thiết đã được cài đặt chưa"""
    try:
        logging.info("Đang kiểm tra các thư viện cần thiết...")
        import customtkinter
        logging.info("Đã import customtkinter thành công")
        
        import yt_dlp
        logging.info("Đã import yt_dlp thành công")
        
        # Kiểm tra ffmpeg trong PATH
        ffmpeg_in_path = shutil.which("ffmpeg")
        logging.info(f"ffmpeg trong PATH: {ffmpeg_in_path}")
        
        # Nếu đang chạy từ exe, kiểm tra ffmpeg trong các thư mục assets
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            
            # Kiểm tra cả trong thư mục assets trực tiếp và trong _internal
            assets_paths = [
                os.path.join(application_path, "assets"),
                os.path.join(application_path, "_internal", "assets")
            ]
            
            for assets_path in assets_paths:
                ffmpeg_path = os.path.join(assets_path, "ffmpeg.exe")
                logging.info(f"Kiểm tra ffmpeg tại: {ffmpeg_path}")
                logging.info(f"ffmpeg tồn tại: {os.path.exists(ffmpeg_path)}")
                
                if os.path.exists(ffmpeg_path):
                    # Nếu tìm thấy ffmpeg, thêm đường dẫn vào PATH
                    if assets_path not in os.environ["PATH"]:
                        os.environ["PATH"] = assets_path + os.pathsep + os.environ["PATH"]
                        logging.info(f"Đã thêm {assets_path} vào PATH")
                    return True
            
            # Nếu đã kiểm tra tất cả đường dẫn mà vẫn không tìm thấy
            logging.error("Không tìm thấy ffmpeg trong bất kỳ thư mục assets nào")
        
        if not ffmpeg_in_path:
            logging.error("Lỗi: FFmpeg không được cài đặt hoặc không tìm thấy trong PATH")
            from tkinter import messagebox
            messagebox.showerror("Lỗi", "FFmpeg không được cài đặt hoặc không tìm thấy. Ứng dụng có thể không hoạt động đúng.")
            return False
        
        return True
    except ImportError as e:
        logging.error(f"Lỗi: Thiếu thư viện cần thiết: {e}")
        from tkinter import messagebox
        messagebox.showerror("Lỗi", f"Thiếu thư viện cần thiết: {e}\nVui lòng cài đặt bằng cách chạy: pip install customtkinter yt-dlp")
        return False
    except Exception as e:
        logging.error(f"Lỗi không xác định khi kiểm tra yêu cầu: {e}")
        from tkinter import messagebox
        messagebox.showerror("Lỗi", f"Lỗi không xác định: {e}")
        return False

def is_admin():
    if os.name == 'nt':
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0

def check_yt_dlp_version():
    try:
        logging.info("Đang kiểm tra phiên bản yt-dlp...")
        import yt_dlp
        current_version = yt_dlp.version.__version__
        logging.info(f"Phiên bản yt-dlp hiện tại: '{current_version}'")
        if getattr(sys, 'frozen', False):
            try:
                import urllib.request
                import json
                from packaging.version import parse as parse_version
                from tkinter import messagebox
                import customtkinter as ctk
                import threading
                from src.utils import download_yt_dlp
                # Lấy version mới nhất từ PyPI
                request = urllib.request.Request("https://pypi.org/pypi/yt-dlp/json")
                response = urllib.request.urlopen(request, timeout=2)
                data = json.loads(response.read())
                latest_version = data["info"]["version"]
                logging.info(f"Phiên bản yt-dlp mới nhất: '{latest_version}'")
                current_v = parse_version(current_version)
                latest_v = parse_version(latest_version)
                if current_v < latest_v:
                    result = messagebox.askyesno(
                        "Cập nhật yt-dlp",
                        f"Có phiên bản yt-dlp mới ({latest_version}). Phiên bản hiện tại là {current_version}.\n\nBạn có muốn cập nhật không?"
                    )
                    if result:
                        if not is_admin():
                            messagebox.showinfo(
                                "Yêu cầu quyền quản trị viên",
                                "Để cập nhật yt-dlp, vui lòng khởi động lại ứng dụng bằng quyền Administrator (chuột phải vào biểu tượng ứng dụng, chọn 'Run as administrator').\n\nSau đó chọn cập nhật lại."
                            )
                            return False
                        # Nếu đã là admin thì tiến hành tải yt-dlp như cũ
                        def do_update():
                            assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
                            dest_path = os.path.join(assets_dir, "yt-dlp.exe")
                            progress_popup = ctk.CTkToplevel()
                            progress_popup.title("Đang cập nhật yt-dlp...")
                            progress_popup.geometry("400x120")
                            label = ctk.CTkLabel(progress_popup, text="Đang tải yt-dlp mới nhất...")
                            label.pack(pady=10)
                            progress = ctk.CTkProgressBar(progress_popup, width=300)
                            progress.pack(pady=10)
                            progress.set(0)
                            def progress_callback(downloaded, total):
                                percent = downloaded / total if total else 0
                                progress.set(percent)
                                label.configure(text=f"Đang tải yt-dlp: {percent*100:.1f}%")
                                progress_popup.update_idletasks()
                            def run_download():
                                ok, err = download_yt_dlp(dest_path, progress_callback)
                                progress_popup.destroy()
                                if ok:
                                    messagebox.showinfo("Thành công", "Đã cập nhật yt-dlp thành công!")
                                else:
                                    messagebox.showerror("Lỗi", f"Không thể cập nhật yt-dlp: {err}")
                            threading.Thread(target=run_download, daemon=True).start()
                        do_update()
                        return True
            except Exception as e:
                logging.error(f"Lỗi khi kiểm tra/cập nhật yt-dlp: {e}")
                return False
        return True
    except Exception as e:
        logging.error(f"Lỗi khi kiểm tra phiên bản yt-dlp: {e}")
        return False

def main():
    """Hàm chính để chạy ứng dụng"""
    try:
        # Thiết lập logging trước tiên
        setup_logging()
        logging.info("===== Bắt đầu khởi động ứng dụng =====")
        logging.info(f"Python version: {sys.version}")
        logging.info(f"Đường dẫn thực thi: {sys.executable}")
        logging.info(f"Đường dẫn hiện tại: {os.getcwd()}")
        logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")
        
        # Ghi log các biến môi trường quan trọng
        logging.info(f"PATH: {os.environ.get('PATH', 'N/A')}")
        logging.info(f"APPDATA: {os.environ.get('APPDATA', 'N/A')}")
        
        # Kiểm tra các thư mục và file quan trọng
        if getattr(sys, 'frozen', False):
            app_path = os.path.dirname(sys.executable)
            logging.info(f"Thư mục ứng dụng: {app_path}")
            
            # Kiểm tra cả thư mục assets trực tiếp và trong _internal
            assets_paths = [
                os.path.join(app_path, "assets"),
                os.path.join(app_path, "_internal", "assets")
            ]
            
            for assets_path in assets_paths:
                logging.info(f"Kiểm tra thư mục assets: {assets_path}")
                logging.info(f"Thư mục tồn tại: {os.path.exists(assets_path)}")
                if os.path.exists(assets_path):
                    logging.info(f"Nội dung thư mục: {os.listdir(assets_path)}")
                    ffmpeg_path = os.path.join(assets_path, "ffmpeg.exe")
                    logging.info(f"ffmpeg.exe tồn tại: {os.path.exists(ffmpeg_path)}")
        
        # Reset cài đặt "không hỏi lại" khi khởi động
        config_file = os.path.join(DATA_DIR, "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
                # Xóa cài đặt "không hỏi lại"
                if "dont_show_complete_popup" in config:
                    del config["dont_show_complete_popup"]
                with open(config_file, "w", encoding="utf-8") as f:
                    json.dump(config, f, ensure_ascii=False, indent=4)
                logging.info("Đã reset cài đặt 'không hỏi lại'")
            except Exception as e:
                logging.error(f"Lỗi khi reset cài đặt 'không hỏi lại': {e}")
        
        # Kiểm tra các yêu cầu
        if not check_requirements():
            logging.error("Không đáp ứng các yêu cầu cần thiết, thoát ứng dụng")
            from tkinter import messagebox
            messagebox.showerror("Lỗi", "Ứng dụng không thể khởi động do thiếu các thành phần cần thiết.")
            sys.exit(1)
        
        # Kiểm tra và cập nhật yt-dlp nếu cần
        check_yt_dlp_version()
        
        # Chạy ứng dụng chính
        logging.info("Bắt đầu chạy giao diện người dùng")
        run_app()
    except Exception as e:
        # Xử lý lỗi toàn cục
        error_msg = f"Lỗi không xử lý được khi khởi động ứng dụng: {e}"
        logging.error(error_msg, exc_info=True)
        
        try:
            # Hiển thị thông báo lỗi cho người dùng
            from tkinter import messagebox
            messagebox.showerror("Lỗi khởi động", f"Ứng dụng không thể khởi động:\n{str(e)}\n\nVui lòng kiểm tra file log để biết thêm chi tiết.")
        except:
            # Nếu không thể hiển thị messagebox, in ra console
            print(error_msg)
        
        sys.exit(1)

if __name__ == "__main__":
    main()