# Hướng dẫn Phát triển Social Media Downloader

## Cấu trúc Dự án
```
Social_Downloader/
├── assets/           # Thư mục chứa tài nguyên
│   ├── ffmpeg.exe    # FFmpeg binary (không đẩy lên git)
│   ├── ffprobe.exe   # FFprobe binary (không đẩy lên git)
│   ├── ffplay.exe    # FFplay binary (không đẩy lên git)
│   └── CH.ico        # Icon ứng dụng
├── data/             # Thư mục dữ liệu
│   ├── config.json   # Cấu hình ứng dụng
│   └── history.json  # Lịch sử tải xuống
├── src/              # Mã nguồn chính
│   └── Main.py       # File chính của ứng dụng
├── build.py          # Script build ứng dụng
├── setup.iss         # Cấu hình Inno Setup
└── requirements.txt  # Các thư viện cần thiết
```

## Yêu cầu Phát triển
1. Python 3.8 trở lên
2. PyInstaller: `pip install pyinstaller`
3. Inno Setup (để tạo installer)
4. FFmpeg (tải từ trang chủ)

## Cài đặt Môi trường Phát triển
1. Clone repository:
```bash
git clone https://github.com/ChinChoppaVN/Social_Downloader.git
cd Social_Downloader
```

2. Cài đặt các thư viện:
```bash
pip install -r requirements.txt
```

3. Tải FFmpeg:
- Tải từ [trang chủ FFmpeg](https://ffmpeg.org/download.html)
- Giải nén và đặt các file sau vào thư mục `assets/`:
  - ffmpeg.exe
  - ffprobe.exe
  - ffplay.exe

## Quy trình Build
1. Build ứng dụng:
```bash
python build.py
```
- File exe sẽ được tạo trong thư mục `dist/`

2. Tạo installer:
- Mở file `setup.iss` với Inno Setup
- Nhấn F9 để biên dịch
- File installer sẽ được tạo trong thư mục `Installer/`

## Quy tắc Git
1. Không đẩy lên git:
- File build (`build/`, `dist/`)
- File cài đặt (`Installer/`)
- File FFmpeg (`assets/ffmpeg.exe`, `assets/ffprobe.exe`, `assets/ffplay.exe`)
- File cache và log

2. Branch:
- `main`: Branch chính, chứa code ổn định
- `develop`: Branch phát triển
- `feature/*`: Branch cho tính năng mới

3. Commit message:
- feat: Thêm tính năng mới
- fix: Sửa lỗi
- docs: Cập nhật tài liệu
- style: Thay đổi format code
- refactor: Tái cấu trúc code
- test: Thêm hoặc sửa test
- chore: Cập nhật build process, package manager

## Phát hành Phiên bản Mới
1. Tăng version trong `setup.iss`
2. Build ứng dụng và tạo installer
3. Tạo tag trên GitHub:
```bash
git tag -a v1.0.0 -m "Phiên bản 1.0.0"
git push origin v1.0.0
```
4. Tạo release trên GitHub và đính kèm file installer

## Xử lý Lỗi Thường Gặp
1. Lỗi "FFmpeg not found":
- Kiểm tra file FFmpeg trong thư mục `assets/`
- Đảm bảo tên file đúng: `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe`

2. Lỗi build:
- Xóa thư mục `build/` và `dist/` trước khi build lại
- Kiểm tra các thư viện trong `requirements.txt`

3. Lỗi installer:
- Kiểm tra đường dẫn trong `setup.iss`
- Đảm bảo file exe đã được build thành công

## Liên hệ
- Email: quyetthang.media@gmail.com
- GitHub: [ChinChoppaVN](https://github.com/ChinChoppaVN) 