import PyInstaller.__main__
import os

# Đường dẫn tới thư mục hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn tới các file cần thiết
icon_path = os.path.join(current_dir, "assets", "CH.ico")
main_script = os.path.join(current_dir, "Main.py")

# Các file và thư mục cần được đóng gói cùng
additional_files = [
    ("assets", "assets"),  # Copy toàn bộ thư mục assets vào exe
]

# Tạo chuỗi dữ liệu cho additional files
datas = [f"--add-data={src};{dst}" for src, dst in additional_files]

# Cấu hình PyInstaller
PyInstaller.__main__.run([
    main_script,                        # File chính
    "--onefile",                        # Đóng gói thành 1 file
    "--noconsole",                      # Không hiển thị console
    f"--icon={icon_path}",             # Icon cho file exe
    "--name=Social Media Downloader",   # Tên file exe
    "--clean",                          # Xóa cache trước khi build
    *datas,                            # Thêm các file đi kèm
    "--hidden-import=customtkinter",    # Import ẩn các thư viện cần thiết
    "--hidden-import=yt_dlp",
    "--hidden-import=PIL",
    "--hidden-import=tkinter",
    "--hidden-import=json",
    "--hidden-import=threading",
]) 