# Social Media Downloader

Ứng dụng tải video từ các nền tảng mạng xã hội phổ biến, được viết bằng Python với giao diện người dùng thân thiện.

## Tính năng

- **Tải video từ nhiều nền tảng:**
  - YouTube
  - TikTok
  - Vimeo
  - SoundCloud
  - Và nhiều nền tảng khác được hỗ trợ bởi yt-dlp

- **Tùy chọn tải xuống:**
  - Tải video với chất lượng cao nhất
  - Tải video với chất lượng thấp hơn
  - Tải chỉ âm thanh (MP3)
  - Tự động chọn định dạng phù hợp

- **Quản lý lịch sử tải xuống:**
  - Xem lịch sử các video đã tải
  - Xóa lịch sử
  - Xuất lịch sử ra file CSV
  - Mở nhanh file hoặc thư mục chứa file đã tải

- **Tính năng tiện ích:**
  - Tự động tạo tên file từ tiêu đề video
  - Lưu vị trí thư mục tải xuống cuối cùng
  - Nút dán URL nhanh từ clipboard
  - Hiển thị thông báo khi tải xong
  - Hỗ trợ tải xuống với FFmpeg

## Yêu cầu hệ thống

- Windows 10 trở lên
- Không cần cài đặt Python hay các thư viện
- Không cần cài đặt FFmpeg (đã được tích hợp sẵn)

## Cài đặt

1. Tải file `Social Media Downloader.exe` từ thư mục `dist`
2. Chạy file exe (không cần cài đặt)
3. Bắt đầu sử dụng

## Cách sử dụng

1. **Tải video:**
   - Copy URL video từ trình duyệt
   - Dán URL vào ô nhập liệu
   - Chọn định dạng tải xuống
   - Nhấn nút "Tải xuống"

2. **Xem lịch sử:**
   - Nhấn nút "Lịch sử" để mở cửa sổ lịch sử
   - Xem danh sách các video đã tải
   - Mở file hoặc thư mục chứa file
   - Xuất lịch sử ra file CSV

3. **Quản lý lịch sử:**
   - Chọn các mục cần xóa
   - Nhấn nút "Xóa" để xóa mục đã chọn
   - Nhấn nút "Xóa tất cả" để xóa toàn bộ lịch sử

## Lưu ý

- File tải xuống được lưu trong thư mục được chọn
- Lịch sử tải xuống được lưu trong thư mục `data`
- Có thể xuất lịch sử ra file CSV để lưu trữ

## Phát triển

Nếu bạn muốn phát triển ứng dụng:

1. Clone repository
2. Cài đặt các thư viện cần thiết:
   ```bash
   pip install -r requirements.txt
   ```
3. Chạy file `build.py` để tạo file exe:
   ```bash
   python build.py
   ```

## Giấy phép

MIT License

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

## Tác giả

- **Thắng MupMip** - [GitHub](https://github.com/ChinChoppaVN) 