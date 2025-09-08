import os
import sys
import shutil
import logging
import subprocess
import json

# Add root directory path to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Setup environment when running from exe
if getattr(sys, 'frozen', False):
    # If running from packaged exe
    application_path = os.path.dirname(sys.executable)
    
    # Add assets paths to PATH - check both direct and _internal locations
    assets_paths = [
        os.path.join(application_path, "assets"),                  # Direct assets folder
        os.path.join(application_path, "_internal", "assets"),    # Assets folder in _internal
    ]
    
    # Add all assets paths to PATH environment variable
    for assets_path in assets_paths:
        if os.path.exists(assets_path) and assets_path not in os.environ["PATH"]:
            print(f"Adding path to PATH: {assets_path}")
            os.environ["PATH"] = assets_path + os.pathsep + os.environ["PATH"]
    
    # Create data directory in AppData
    app_data_path = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
    data_path = os.path.join(app_data_path, "data")
    if not os.path.exists(data_path):
        os.makedirs(data_path)

# Import các module từ thư mục src
from src.ui import run_app
from src.utils import DATA_DIR  # Thêm import DATA_DIR từ utils

def setup_logging():
    """Setup basic logging configuration"""
    try:
        # If running from exe, use AppData directory
        if getattr(sys, 'frozen', False):
            app_data_path = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
            if not os.path.exists(app_data_path):
                os.makedirs(app_data_path)
            log_file = os.path.join(app_data_path, "app.log")
        else:
            # If running from source code
            log_dir = os.path.dirname(os.path.abspath(__file__))
            log_file = os.path.join(log_dir, "app.log")
        
        # Setup logging with both file and console output
        logging.basicConfig(
            level=logging.DEBUG,  # Increase level to capture more information
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()  # Add handler for console output
            ]
        )
        logging.info("Logging initialized successfully")
    except Exception as e:
        print(f"Cannot setup logging: {e}")
        # Try to setup basic logging with console only
        logging.basicConfig(
            level=logging.DEBUG,
            format="%(asctime)s - %(levelname)s - %(message)s",
            handlers=[logging.StreamHandler()]
        )

def check_requirements():
    """Check if required libraries and tools are installed"""
    try:
        logging.info("Checking required libraries...")
        import customtkinter
        logging.info("Successfully imported customtkinter")
        
        import yt_dlp
        logging.info("Successfully imported yt_dlp")
        
        # Check ffmpeg in PATH
        ffmpeg_in_path = shutil.which("ffmpeg")
        logging.info(f"ffmpeg in PATH: {ffmpeg_in_path}")
        
        # If running from exe, check ffmpeg in assets directories
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
            
            # Check both direct assets folder and _internal location
            assets_paths = [
                os.path.join(application_path, "assets"),
                os.path.join(application_path, "_internal", "assets")
            ]
            
            for assets_path in assets_paths:
                ffmpeg_path = os.path.join(assets_path, "ffmpeg.exe")
                logging.info(f"Checking ffmpeg at: {ffmpeg_path}")
                logging.info(f"ffmpeg exists: {os.path.exists(ffmpeg_path)}")
                
                if os.path.exists(ffmpeg_path):
                    # If ffmpeg found, add path to PATH
                    if assets_path not in os.environ["PATH"]:
                        os.environ["PATH"] = assets_path + os.pathsep + os.environ["PATH"]
                        logging.info(f"Added {assets_path} to PATH")
                    return True
            
            # If checked all paths and still not found
            logging.error("Cannot find ffmpeg in any assets directory")
        
        if not ffmpeg_in_path:
            logging.error("Error: FFmpeg not installed or not found in PATH")
            from tkinter import messagebox
            messagebox.showerror("Error", "FFmpeg not installed or not found. Application may not work correctly.")
            return False
        
        return True
    except ImportError as e:
        logging.error(f"Error: Missing required library: {e}")
        from tkinter import messagebox
        messagebox.showerror("Error", f"Missing required library: {e}\nPlease install by running: pip install customtkinter yt-dlp")
        return False
    except Exception as e:
        logging.error(f"Unknown error during requirements check: {e}")
        from tkinter import messagebox
        messagebox.showerror("Error", f"Unknown error: {e}")
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
        logging.info("Checking yt-dlp version...")
        import yt_dlp
        current_version = yt_dlp.version.__version__
        logging.info(f"Current yt-dlp version: '{current_version}'")
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
                            # Xác định đường dẫn assets dựa trên frozen hay không
                            if getattr(sys, 'frozen', False):
                                assets_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
                            else:
                                # Khi chạy từ source code
                                root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                                assets_dir = os.path.join(root_dir, "assets")
                            
                            dest_path = os.path.join(assets_dir, "yt-dlp.exe")
                            logging.info(f"Đường dẫn tải yt-dlp: {dest_path}")
                            
                            # Tạo thư mục assets nếu chưa tồn tại
                            if not os.path.exists(assets_dir):
                                os.makedirs(assets_dir)
                                logging.info(f"Đã tạo thư mục assets: {assets_dir}")
                            
                            # Tạo progress popup đơn giản
                            import tkinter as tk
                            temp_root = tk.Tk()
                            temp_root.withdraw()  # Ẩn window chính
                            
                            progress_popup = ctk.CTkToplevel(temp_root)
                            progress_popup.title("Đang cập nhật yt-dlp...")
                            progress_popup.geometry("400x120")
                            progress_popup.attributes("-topmost", True)
                            progress_popup.resizable(False, False)
                            
                            # Căn giữa popup
                            progress_popup.update_idletasks()
                            screen_width = progress_popup.winfo_screenwidth()
                            screen_height = progress_popup.winfo_screenheight()
                            x = (screen_width // 2) - (progress_popup.winfo_width() // 2)
                            y = (screen_height // 2) - (progress_popup.winfo_height() // 2)
                            progress_popup.geometry(f"400x120+{x}+{y}")
                            
                            label = ctk.CTkLabel(progress_popup, text="Đang tải yt-dlp mới nhất...")
                            label.pack(pady=10)
                            progress = ctk.CTkProgressBar(progress_popup, width=300)
                            progress.pack(pady=10)
                            progress.set(0)
                            
                            progress_popup.grab_set()  # Lock focus vào popup
                            
                            def progress_callback(downloaded, total):
                                try:
                                    percent = downloaded / total if total else 0
                                    progress.set(percent)
                                    label.configure(text=f"Đang tải yt-dlp: {percent*100:.1f}%")
                                    progress_popup.update_idletasks()
                                except:
                                    pass  # Popup có thể đã bị đóng
                            
                            def run_download():
                                ok, err = download_yt_dlp(dest_path, progress_callback)
                                try:
                                    progress_popup.grab_release()
                                    progress_popup.destroy()
                                    temp_root.destroy()  # Đóng temp root
                                    if ok:
                                        messagebox.showinfo("Thành công", "Đã cập nhật yt-dlp thành công!")
                                        logging.info("Cập nhật yt-dlp thành công")
                                    else:
                                        messagebox.showerror("Lỗi", f"Không thể cập nhật yt-dlp: {err}")
                                        logging.error(f"Lỗi cập nhật yt-dlp: {err}")
                                except:
                                    pass  # Popup có thể đã bị đóng
                            
                            # Chạy download trong thread để không block UI
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
        
        # Kiểm tra cập nhật yt-dlp sau khi UI đã khởi tạo
        # Sẽ được gọi từ trong UI class sau khi window đã sẵn sàng
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