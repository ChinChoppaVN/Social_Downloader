# Social Media Downloader

![Logo](assets/CH.ico)

## Giới thiệu

Social Media Downloader là ứng dụng miễn phí giúp bạn tải xuống video và âm thanh từ các nền tảng mạng xã hội phổ biến như YouTube, Facebook, TikTok và nhiều trang web khác. Với giao diện đơn giản, dễ sử dụng, ứng dụng là lựa chọn hoàn hảo cho người dùng muốn lưu trữ nội dung yêu thích để xem offline.

## Tính năng chính

- **Tải video/âm thanh từ nhiều nguồn**:
  - YouTube
  - TikTok
  - Facebook
  - Instagram
  - SoundCloud
  - Vimeo
  - Và nhiều trang web khác...

- **Hỗ trợ nhiều định dạng**:
  - MP4 (video chất lượng cao)
  - MP3 (âm thanh chất lượng cao)

- **Dễ dàng sử dụng**:
  - Chỉ cần dán liên kết
  - Tùy chọn đặt tên file theo ý muốn
  - Nhấn "Tải ngay"
  - Lưu lịch sử tải xuống

- **Tự động cập nhật công cụ tải**:
  - Luôn hoạt động ngay cả khi các trang web thay đổi

## Yêu cầu hệ thống

- Windows 7/8/10/11 (phiên bản 64-bit)
- 100MB dung lượng ổ đĩa trống
- Kết nối Internet

## Cài đặt

1. Tải xuống file cài đặt
2. Chạy file cài đặt "SocialMediaDownloader_Setup.exe"
3. Làm theo hướng dẫn trên màn hình
4. Ứng dụng sẽ tự động tạo biểu tượng trên Desktop và Start Menu

## Hướng dẫn sử dụng

### Tải xuống video:

1. Sao chép liên kết video từ trình duyệt (YouTube, Facebook, TikTok...)
2. Khởi động ứng dụng "Social Media Downloader"
3. Dán liên kết vào ô "Link video"
4. Chọn định dạng mong muốn (MP4 hoặc MP3)
5. Chọn thư mục lưu trong ô "Thư mục" 
6. Đặt tên file (tùy chọn) hoặc để trống để sử dụng tên mặc định
7. Nhấn nút "Tải ngay"
8. Đợi quá trình tải hoàn tất

### Quản lý lịch sử tải:

1. Nhấn nút "Lịch sử tải" trong giao diện chính
2. Xem danh sách các video/âm thanh đã tải xuống
3. Mở file hoặc thư mục bằng cách nhấp chuột phải vào mục trong danh sách
4. Tìm kiếm trong lịch sử bằng thanh tìm kiếm ở trên cùng

## Các vấn đề thường gặp

### Không tải được video:

- Đảm bảo liên kết hợp lệ và video không bị giới hạn (ví dụ: video riêng tư)
- Cho phép ứng dụng cập nhật công cụ tải khi được hỏi
- Kiểm tra kết nối Internet

### Lỗi khi tải xuống:

- Đảm bảo bạn có đủ dung lượng trống trên ổ đĩa
- Thử chọn thư mục lưu khác nếu gặp lỗi quyền truy cập
- Khởi động lại ứng dụng và thử lại

### Video không có âm thanh:

- Đảm bảo bạn đã chọn đúng định dạng (MP4)
- Một số video có thể không có âm thanh từ nguồn gốc

## Liên hệ & Hỗ trợ

- Email: quyetthang.media@gmail.com

---

© 2025 Thắng MupMip.

**Lưu ý**: Ứng dụng này chỉ dành cho mục đích cá nhân. Vui lòng tuân thủ các điều khoản dịch vụ của các nền tảng và tôn trọng bản quyền khi tải xuống nội dung.

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