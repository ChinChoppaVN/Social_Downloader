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
from src.utils import DATA_DIR
from src import paths

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

def get_exe_version(exe_path):
    """Lấy phiên bản thực thi từ tham số --version."""
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        res = subprocess.run([exe_path, "--version"], capture_output=True, text=True, creationflags=creationflags, timeout=5)
        if res.returncode == 0 and res.stdout.strip():
            from packaging.version import parse as parse_v
            return parse_v(res.stdout.strip())
    except Exception:
        pass
    return None

def find_executables():
    """Tìm đường dẫn tuyệt đối cho ffmpeg.exe và yt-dlp.exe và lưu vào module paths."""
    logging.info("Searching for required executables...")
    
    # Định nghĩa các thư mục assets tiềm năng
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
        assets_dirs = [
            os.path.join(application_path, "_internal", "assets"),
            os.path.join(application_path, "assets")
        ]
    else:
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        assets_dirs = [os.path.join(root_dir, "assets")]

    executables = {
        "ffmpeg.exe": "FFMPEG_PATH",
        "yt-dlp.exe": "YT_DLP_PATH"
    }
    
    app_data_path = os.path.join(os.environ.get('APPDATA', ''), "Social Media Downloader")
    user_ytdlp = os.path.join(app_data_path, "bin", "yt-dlp.exe")

    found_all = True
    for exe_name, path_variable in executables.items():
        found = False

        # Ưu tiên kiểm tra phiên bản mới nhất giữa AppData và Bundled đối với yt-dlp.exe
        if exe_name == "yt-dlp.exe":
            bundled_ytdlp = None
            for assets_dir in assets_dirs:
                p = os.path.join(assets_dir, exe_name)
                if os.path.exists(p):
                    bundled_ytdlp = p
                    break
            
            chosen_ytdlp = None
            if bundled_ytdlp and os.path.exists(user_ytdlp):
                v_bundled = get_exe_version(bundled_ytdlp)
                v_user = get_exe_version(user_ytdlp)
                logging.info(f"So sánh phiên bản yt-dlp - Bản gốc: {v_bundled}, Bản cập nhật AppData: {v_user}")
                if v_user and v_bundled and v_user >= v_bundled:
                    chosen_ytdlp = user_ytdlp
                else:
                    chosen_ytdlp = bundled_ytdlp
            elif os.path.exists(user_ytdlp):
                chosen_ytdlp = user_ytdlp
            elif bundled_ytdlp:
                chosen_ytdlp = bundled_ytdlp

            if chosen_ytdlp:
                logging.info(f"Sử dụng yt-dlp tại: {chosen_ytdlp}")
                setattr(paths, path_variable, chosen_ytdlp)
                found = True
        else:
            for assets_dir in assets_dirs:
                exe_path = os.path.join(assets_dir, exe_name)
                logging.info(f"Checking for {exe_name} at: {exe_path}")
                if os.path.exists(exe_path):
                    logging.info(f"Found {exe_name} at: {exe_path}")
                    setattr(paths, path_variable, exe_path)
                    found = True
                    break
        
        if not found:
            # Check system PATH as fallback
            base_name = os.path.splitext(exe_name)[0]
            which_path = shutil.which(exe_name) or shutil.which(base_name)
            if which_path and os.path.exists(which_path):
                logging.info(f"Found {exe_name} in system PATH: {which_path}")
                setattr(paths, path_variable, which_path)
                found = True

        if not found and exe_name == "yt-dlp.exe":
            # Tự động tải về thư mục người dùng
            from tkinter import messagebox
            from src.utils import download_yt_dlp, get_ytdlp_update_path
            target_path = get_ytdlp_update_path()
            answer = messagebox.askyesno(
                "Tải yt-dlp",
                "Chưa tìm thấy yt-dlp.exe trên máy.\nBạn có muốn tự động tải về ngay không?"
            )
            if answer:
                ok, err = download_yt_dlp(target_path)
                if ok and os.path.exists(paths.YT_DLP_PATH or target_path):
                    setattr(paths, path_variable, paths.YT_DLP_PATH or target_path)
                    found = True
                    messagebox.showinfo("Thành công", "Đã tải yt-dlp.exe thành công!")
                else:
                    messagebox.showerror("Lỗi", f"Không thể tải yt-dlp.exe: {err}")

        if not found:
            logging.error(f"CRITICAL: Could not find {exe_name} in any assets directory.")
            from tkinter import messagebox
            messagebox.showerror("Lỗi nghiêm trọng", f"Không tìm thấy file {exe_name}. Ứng dụng không thể hoạt động.")
            found_all = False

    return found_all


def is_admin():
    if os.name == 'nt':
        import ctypes
        try:
            return ctypes.windll.shell32.IsUserAnAdmin()
        except:
            return False
    else:
        return os.geteuid() == 0



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
        
        # Kiểm tra và tìm các file thực thi cần thiết
        if not find_executables():
            logging.error("Không tìm thấy các file thực thi cần thiết, thoát ứng dụng.")
            sys.exit(1)

        # Kiểm tra các yêu cầu thư viện Python
        try:
            import customtkinter
            import PIL
            import packaging
        except ImportError as e:
            logging.error(f"Thiếu thư viện Python cần thiết: {e}")
            from tkinter import messagebox
            messagebox.showerror("Lỗi", f"Thiếu thư viện: {e.name}. Vui lòng cài đặt bằng pip.")
            sys.exit(1)
        
        # Chạy ứng dụng chính (kiểm tra cập nhật yt-dlp sẽ chạy ngầm sau khi UI sẵn sàng)
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