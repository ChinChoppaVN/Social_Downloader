import PyInstaller.__main__
import os
import shutil
import sys
import logging

# Thiết lập logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def check_requirements():
    """Kiểm tra các file và thư mục cần thiết"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    required_files = [
        os.path.join(current_dir, "assets", "CH.ico"),
        os.path.join(current_dir, "assets", "ffmpeg.exe"),
        os.path.join(current_dir, "assets", "ffprobe.exe"),
        os.path.join(current_dir, "assets", "ffplay.exe"),
        os.path.join(current_dir, "src", "main.py")
    ]
    
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)
    
    if missing_files:
        logging.error("Các file sau không tồn tại:")
        for file in missing_files:
            logging.error(f"- {file}")
        return False
    return True

def clean_build_dirs():
    """Xóa các thư mục build cũ"""
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dirs_to_clean = [
        os.path.join(current_dir, "build"),
        os.path.join(current_dir, "dist")
    ]
    
    for dir_path in dirs_to_clean:
        if os.path.exists(dir_path):
            try:
                shutil.rmtree(dir_path)
                logging.info(f"Đã xóa thư mục: {dir_path}")
            except Exception as e:
                logging.error(f"Không thể xóa thư mục {dir_path}: {e}")
                return False
    return True

def main():
    """Hàm chính để build ứng dụng"""
    try:
        # Kiểm tra các yêu cầu
        if not check_requirements():
            logging.error("Không thể build do thiếu file cần thiết")
            return False
            
        # Xóa các thư mục build cũ
        if not clean_build_dirs():
            logging.error("Không thể xóa thư mục build cũ")
            return False
            
        # Đường dẫn tới thư mục hiện tại
        current_dir = os.path.dirname(os.path.abspath(__file__))
        
        # Đường dẫn tới các file cần thiết
        icon_path = os.path.join(current_dir, "assets", "CH.ico")
        main_script = os.path.join(current_dir, "src", "main.py")
        
        # Các file và thư mục cần được đóng gói cùng
        additional_files = [
            (os.path.join(current_dir, "assets"), "assets"),  # Copy toàn bộ thư mục assets
            (os.path.join(current_dir, "data"), "data"),      # Copy thư mục data
            (os.path.join(current_dir, "src"), "src"),        # Copy toàn bộ thư mục src
        ]
        
        # Tạo chuỗi dữ liệu cho additional files
        datas = []
        for src, dst in additional_files:
            if os.path.exists(src):
                datas.append(f"--add-data={src};{dst}")
                logging.info(f"Thêm thư mục vào build: {src} -> {dst}")
        
        # Cấu hình PyInstaller
        build_args = [
            main_script,                        # File chính
            "--onedir",                         # Đóng gói thành 1 thư mục thay vì 1 file
            "--noconsole",                     # Không hiển thị console
            f"--icon={icon_path}",             # Icon cho file exe
            "--name=Social Media Downloader",   # Tên file exe
            "--clean",                         # Xóa cache trước khi build
            *datas,                            # Thêm các file đi kèm
            "--hidden-import=customtkinter",    # Import ẩn các thư viện cần thiết
            "--hidden-import=yt_dlp",
            "--hidden-import=PIL",
            "--hidden-import=PIL._tkinter_finder",
            "--hidden-import=PIL._imaging",
            "--hidden-import=PIL.Image",
            "--hidden-import=PIL.ImageTk",
            "--hidden-import=tkinter",
            "--hidden-import=json",
            "--hidden-import=csv",
            "--hidden-import=threading",
            "--hidden-import=shutil",
            "--hidden-import=os",
            "--hidden-import=sys",
            "--hidden-import=datetime",
            "--hidden-import=re",
            "--hidden-import=platform",
            "--hidden-import=subprocess",
            "--hidden-import=src.ui",          # Import ẩn các module từ src
            "--hidden-import=src.downloader",
            "--hidden-import=src.utils",
            "--collect-submodules=PIL",        # Thu thập tất cả submodules của PIL
            "--collect-submodules=src",        # Thu thập tất cả submodules từ src
            "--add-binary=assets/ffmpeg.exe;assets",    # Thêm ffmpeg
            "--add-binary=assets/ffprobe.exe;assets",   # Thêm ffprobe
            "--add-binary=assets/ffplay.exe;assets",    # Thêm ffplay
            "--hidden-import=packaging",
            "--hidden-import=packaging.version",
        ]
        
        logging.info("Bắt đầu quá trình build...")
        PyInstaller.__main__.run(build_args)
        
        # Kiểm tra kết quả build
        exe_path = os.path.join(current_dir, "dist", "Social Media Downloader", "Social Media Downloader.exe")
        if os.path.exists(exe_path):
            logging.info(f"Build thành công! File exe được tạo tại: {exe_path}")
            return True
        else:
            logging.error("Build thất bại! Không tìm thấy file exe")
            return False
            
    except Exception as e:
        logging.error(f"Lỗi trong quá trình build: {e}")
        return False

def create_installer():
    """Tạo file cài đặt sử dụng Inno Setup"""
    try:
        current_dir = os.path.dirname(os.path.abspath(__file__))
        inno_script = os.path.join(current_dir, "setup.iss")
        
        if not os.path.exists(inno_script):
            logging.error(f"Không tìm thấy file script Inno Setup: {inno_script}")
            return False
        
        # Đường dẫn đến Inno Setup Compiler (điều chỉnh nếu cần)
        iscc_path = r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"
        
        if not os.path.exists(iscc_path):
            logging.error(f"Không tìm thấy Inno Setup Compiler")
            return False
        
        # Chạy Inno Setup Compiler
        import subprocess
        cmd = [iscc_path, inno_script]
        logging.info(f"Đang chạy Inno Setup: {' '.join(cmd)}")
        
        process = subprocess.run(cmd, capture_output=True, text=True)
        
        if process.returncode == 0:
            logging.info("Tạo file cài đặt thành công!")
            return True
        else:
            logging.error(f"Lỗi khi tạo file cài đặt: {process.stderr}")
            return False
            
    except Exception as e:
        logging.error(f"Lỗi trong quá trình tạo file cài đặt: {e}")
        return False
if __name__ == "__main__":
    if main():
        logging.info("Quá trình build hoàn tất thành công!")
        # Tự động tạo file cài đặt
        if create_installer():
            logging.info("Đã tạo file cài đặt thành công!")
    else:
        logging.error("Quá trình build thất bại!")
        sys.exit(1)