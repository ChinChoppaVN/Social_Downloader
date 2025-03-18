# Social Media Downloader

Ứng dụng tải video và audio từ các nền tảng mạng xã hội phổ biến như YouTube, Facebook, TikTok, Instagram, và nhiều nền tảng khác.

## Tính năng

- Tải video với chất lượng cao nhất có thể
- Tải audio (MP3) với chất lượng tốt
- Giao diện người dùng thân thiện, chế độ tối (Dark mode)
- Hiển thị chi tiết tiến trình tải xuống:
  - Phần trăm hoàn thành
  - Tốc độ tải (MB/s)
  - Thời gian còn lại
  - Kích thước file
- Điều khiển tải xuống:
  - Tạm dừng/Tiếp tục tải
  - Hủy tải
  - Nút dán link nhanh
- Lưu lịch sử tải xuống
- Tự động lấy tên file từ tiêu đề video
- Hỗ trợ nhiều nền tảng mạng xã hội

## Cài đặt

### Người dùng
1. Tải file `Social Media Downloader.exe` từ phần [Releases](https://github.com/ChinChoppaVN/Social_Downloader/releases)
2. Chạy file `Social Media Downloader.exe`

### Nhà phát triển

1. Clone dự án:
```bash
git clone https://github.com/ChinChoppaVN/Social_Downloader.git
cd Social_Downloader
```

2. Cài đặt FFmpeg:
   - Tải FFmpeg từ: https://ffmpeg.org/download.html
   - Giải nén và copy 3 file sau vào thư mục `assets`:
     - ffmpeg.exe
     - ffprobe.exe
     - ffplay.exe

3. Tạo và kích hoạt môi trường ảo:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

4. Cài đặt các thư viện Python:
```bash
pip install -r requirements.txt
```

5. Chạy ứng dụng từ source code:
```bash
python src/Main.py
```

6. Build ứng dụng thành file exe:
```bash
python build.py
```

## Cấu trúc dự án

```
Social_Downloader/
├── src/                  # Thư mục chứa mã nguồn
│   ├── Main.py          # File chính để chạy ứng dụng
│   ├── ui.py            # Giao diện người dùng
│   ├── downloader.py    # Logic tải xuống
│   └── utils.py         # Các tiện ích
├── config/              # Thư mục cấu hình
│   ├── __init__.py
│   └── app_config.py    # Cấu hình ứng dụng
├── data/                # Thư mục chứa dữ liệu
│   ├── config.json      # Cấu hình người dùng
│   └── history.json     # Lịch sử tải xuống
├── assets/              # Thư mục chứa tài nguyên
│   ├── CH.ico          # Icon ứng dụng
│   └── ffmpeg files    # Các file FFmpeg
├── requirements.txt     # Các thư viện cần thiết
└── build.py            # Script đóng gói ứng dụng
```

## Đóng góp

Mọi đóng góp đều được hoan nghênh! Vui lòng:

1. Fork dự án
2. Tạo nhánh tính năng (`git checkout -b feature/AmazingFeature`)
3. Commit thay đổi (`git commit -m 'Add some AmazingFeature'`)
4. Push lên nhánh (`git push origin feature/AmazingFeature`)
5. Tạo Pull Request

## Giấy phép

Phân phối theo giấy phép MIT. Xem `LICENSE` để biết thêm thông tin.

## Tác giả

- **Thắng MupMip** - [GitHub](https://github.com/ChinChoppaVN) 