import PyInstaller.__main__
import os
import shutil

# Đường dẫn tới thư mục hiện tại
current_dir = os.path.dirname(os.path.abspath(__file__))

# Đường dẫn tới các file cần thiết
icon_path = os.path.join(current_dir, "assets", "CH.ico")
main_script = os.path.join(current_dir, "src", "Main.py")

# Tạo thư mục dist nếu chưa tồn tại
dist_dir = os.path.join(current_dir, "dist")
if not os.path.exists(dist_dir):
    os.makedirs(dist_dir)

# Các file và thư mục cần được đóng gói cùng
additional_files = [
    (os.path.join(current_dir, "assets"), "assets"),  # Copy toàn bộ thư mục assets
    (os.path.join(current_dir, "config"), "config"),  # Copy thư mục config
    (os.path.join(current_dir, "data"), "data"),      # Copy thư mục data
]

# Tạo chuỗi dữ liệu cho additional files
datas = []
for src, dst in additional_files:
    if os.path.exists(src):
        datas.append(f"--add-data={src};{dst}")

# Cấu hình PyInstaller
PyInstaller.__main__.run([
    main_script,                        # File chính
    "--onefile",                        # Đóng gói thành 1 file
    "--noconsole",                     # Không hiển thị console
    f"--icon={icon_path}",             # Icon cho file exe
    "--name=Social Media Downloader",   # Tên file exe
    "--clean",                         # Xóa cache trước khi build
    *datas,                            # Thêm các file đi kèm
    "--hidden-import=customtkinter",    # Import ẩn các thư viện cần thiết
    "--hidden-import=yt_dlp",
    "--hidden-import=PIL",
    "--hidden-import=tkinter",
    "--hidden-import=json",
    "--hidden-import=threading",
    "--hidden-import=shutil",
    "--hidden-import=os",
    "--hidden-import=sys",
    "--hidden-import=datetime",
    "--hidden-import=re",
    "--add-binary=assets/ffmpeg.exe;.",    # Thêm ffmpeg
    "--add-binary=assets/ffprobe.exe;.",   # Thêm ffprobe
    "--add-binary=assets/ffplay.exe;.",    # Thêm ffplay
])

print("Build completed! Check the 'dist' folder for the executable.") 