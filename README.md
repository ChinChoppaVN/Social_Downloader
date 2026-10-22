# 🎬 Social Media Downloader v2.0

<p align="center">
  <img src="assets/CH.ico" alt="Logo" width="96" height="96" />
</p>

<p align="center">
  <b>Công cụ tải Video, Playlist & Âm thanh đa nền tảng tốc độ cao, giao diện hiện đại & trực quan</b>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Platform-Windows%2010%20%7C%2011%20(64--bit)-0078D6?logo=windows" alt="Platform" />
  <img src="https://img.shields.io/badge/Python-3.12-3776AB?logo=python" alt="Python" />
  <img src="https://img.shields.io/badge/UI-CustomTkinter-blueviolet" alt="CustomTkinter" />
  <img src="https://img.shields.io/badge/Core-yt--dlp%20%26%20FFmpeg-FF0000?logo=youtube" alt="yt-dlp" />
  <img src="https://img.shields.io/badge/Installer-Inno%20Setup%206-009688" alt="Inno Setup" />
  <img src="https://img.shields.io/badge/License-MIT-green" alt="License" />
</p>

---

## 📖 Giới thiệu

**Social Media Downloader** là phần mềm tiện ích trên Windows giúp bạn tải video, danh sách phát (playlist) và âm thanh từ các nền tảng mạng xã hội phổ biến nhất hiện nay như **YouTube, TikTok (không logo/watermark), Facebook, Instagram, Vimeo, SoundCloud, Twitter/X...**

Ứng dụng được thiết kế theo triết lý hiện đại, giao diện phẳng cao cấp, tối ưu hóa toàn bộ quá trình sử dụng cho người dùng cuối: **Tải về là dùng ngay, không cần cấu hình phức tạp, độc lập hoàn toàn và không phụ thuộc vào việc máy tính đã cài đặt Python hay FFmpeg hay chưa.**

---

## ✨ Tính năng nổi bật

### 🎨 1. Giao diện hiện đại & Cao cấp (Theme 4C)
- **Tông màu Sunset Crimson & Blush Peach Cream**:
  - **Chế độ Sáng (Light Mode)**: Nền kem nhạt dịu mắt (`#FAF4F2`), thẻ nội dung trắng ngà mềm mại, chống mỏi mắt khi sử dụng lâu.
  - **Chế độ Tối (Dark Mode)**: Nền đen Onyx sang trọng (`#121214`), các thẻ hiển thị xám tối tinh tế (`#1C1C22`).
  - **Điểm nhấn màu sắc**: Nút bấm đỏ hoàng hôn (`#E11D48` / `#FF4757`) với chữ màu kem nổi bật, độ tương phản chuẩn Accessibility.
- **Thiết kế không viền stroke**: Tối giản, không rườm rà, các khối nội dung phân tách tự nhiên và thoáng đãng.
- **Hỗ trợ đa ngôn ngữ**: Chuyển đổi linh hoạt giữa **Tiếng Việt** và **English**.

### ⚡ 2. Tải Video & Audio chất lượng cao
- **Độ phân giải video**: Lựa chọn linh hoạt giữa **Full HD (1080p)** và **4K Ultra HD**.
- **Tách âm thanh MP3**: Trích xuất audio chất lượng cao (320kbps / 256kbps), tự động gắn thẻ metadata và ảnh bìa bài hát.
- **Tự động xử lý đa luồng**: Ghép video độ phân giải cao và audio bằng công cụ FFmpeg tích hợp sẵn chỉ trong vài giây.

### 📋 3. Hàng đợi tải hàng loạt (Queue) & File danh sách `.txt`
- Hỗ trợ nạp hàng chục, hàng trăm link cùng lúc.
- Nhập danh sách link trực tiếp từ file text (`.txt`) để tải tự động nối tiếp, không cần ngồi dán từng link một.

### 📑 4. Tải trọn bộ Playlist YouTube trong 1 click
- Tự động nhận diện và phân tích toàn bộ danh sách phát.
- Đặt tên file thông minh theo số thứ tự (ví dụ: `01 - Tên video`, `02 - Tên video`).
- Hiển thị tiến trình của từng video cũng như toàn bộ danh sách, có nút **Hủy tải (Cancel)** an toàn bất cứ lúc nào.

### 🔄 5. Tự động & Chủ động cập nhật yt-dlp
- Thuật toán của các mạng xã hội (đặc biệt là YouTube và TikTok) thường xuyên thay đổi khiến các tool tải thông thường bị lỗi.
- **Social Media Downloader** tích hợp cơ chế tự động kiểm tra phiên bản mới của `yt-dlp` khi mở app.
- Bạn cũng có thể chủ động cập nhật bất cứ lúc nào qua menu **Cài đặt -> Cập nhật yt-dlp** với thanh tiến trình tải trực quan.

### 📂 6. Quản lý Lịch sử tải & Popup thông minh
- **Lịch sử tải chi tiết**: Tìm kiếm theo tên file, hiển thị dung lượng, ngày giờ tải, đường dẫn lưu, cho phép 1-click mở file hoặc thư mục.
- **Popup hoàn thành tiện lợi**: Tùy chọn Mở file, Mở thư mục, hoặc Đóng. Hỗ trợ tùy chọn "Không hỏi lại" để tự động mở thư mục/file theo thói quen của bạn.

---

## 🖥️ Yêu cầu hệ thống

| Thành phần | Yêu cầu tối thiểu | Khuyến nghị |
| :--- | :--- | :--- |
| **Hệ điều hành** | Windows 10 (64-bit) | Windows 10 / Windows 11 (64-bit) |
| **RAM** | 2 GB | 4 GB trở lên |
| **Dung lượng trống** | 300 MB (chứa app và cache tải) | 1 GB+ |
| **Kết nối mạng** | Kết nối Internet ổn định | Đường truyền băng thông rộng |

---

## 🚀 Hướng dẫn Cài đặt & Sử dụng

### Dành cho người dùng (Chạy file cài đặt)

1. Tải bộ cài đặt mới nhất: [SocialMediaDownloader_Setup.exe](installer/SocialMediaDownloader_Setup.exe).
2. Chạy file cài đặt và nhấn **Next** theo hướng dẫn (mặc định cài đặt vào thư mục Program Files).
3. Sau khi cài đặt, khởi chạy phần mềm từ **Desktop** hoặc **Start Menu**.

### Hướng dẫn sử dụng nhanh

```
┌────────────────────────────────────────────────────────┐
│  1. Chọn tab "Tải video/audio"                         │
│  2. Dán link video (YouTube, TikTok, Facebook...)      │
│  3. Chọn định dạng: MP4 (FHD/4K) hoặc MP3             │
│  4. Chọn thư mục lưu trữ                               │
│  5. Nhấn nút "TẢI NGAY"                                │
└────────────────────────────────────────────────────────┘
```

- **Tải Playlist**: Chuyển sang tab **"Tải playlist"**, dán link playlist YouTube và nhấn **"Tải ngay"**.
- **Tải nhiều link (Hàng đợi)**: Nhấn nút **"Hàng đợi"** bên cạnh ô link, nhập danh sách URL hoặc nhấn **"Tải từ file .txt"**, sau đó nhấn **"Áp dụng"**.
- **Cập nhật yt-dlp**: Vào thanh menu trên cùng: **Cài đặt** -> **Cập nhật yt-dlp**.

---

## 🛠️ Dành cho lập trình viên (Chạy từ mã nguồn)

Nếu bạn muốn tùy biến mã nguồn hoặc tự build lại ứng dụng:

### 1. Chuẩn bị môi trường
```bash
# Clone dự án
git clone https://github.com/ChinChoppaVN/Social_Downloader.git
cd Social_Downloader

# Tạo và kích hoạt môi trường ảo
python -m venv venv
venv\Scripts\activate

# Cài đặt các thư viện cần thiết
pip install -r requirements.txt
```

### 2. Chuẩn bị công cụ ngoại vi trong thư mục `assets/`
Đảm bảo các file sau đã có trong thư mục `assets/`:
- `ffmpeg.exe`, `ffprobe.exe`, `ffplay.exe` (từ dự án FFmpeg)
- `yt-dlp.exe` (từ dự án yt-dlp)
- `CH.ico` (biểu tượng ứng dụng)
- `themes/sunset_coral.json` (bộ cấu hình màu sắc giao diện Theme 4C)

### 3. Chạy thử nghiệm
```bash
python src/main.py
```

### 4. Đóng gói thành file cài đặt Windows (.exe)
Dự án tích hợp sẵn script tự động chạy PyInstaller và Inno Setup:
```bash
python build.py
```
*File cài đặt hoàn chỉnh sẽ được tạo tại: `installer/SocialMediaDownloader_Setup.exe`.*

---

## 📁 Cấu trúc thư mục dự án

```
Social_Downloader/
├── assets/                  # Tài nguyên app (icons, themes, ffmpeg, yt-dlp)
│   ├── themes/
│   │   └── sunset_coral.json# Cấu hình màu sắc Theme 4C (Blush Peach Cream & Sunset Crimson)
│   ├── CH.ico               # Icon ứng dụng
│   ├── ffmpeg.exe           # Bộ giải mã video/audio
│   └── yt-dlp.exe           # Bộ tải stream đa nền tảng
├── data/                    # Thư mục lưu dữ liệu cục bộ (lịch sử, cài đặt)
├── installer/               # Thư mục chứa bộ cài đặt Setup đầu ra
├── src/                     # Mã nguồn ứng dụng
│   ├── main.py              # Điểm khởi chạy chính & kiểm tra phụ thuộc
│   ├── ui.py                # Toàn bộ giao diện người dùng (CustomTkinter)
│   ├── downloader.py        # Logic tải tiến trình ngầm, xử lý luồng
│   ├── utils.py             # Các hàm tiện ích (lịch sử, tải yt-dlp, config)
│   └── paths.py             # Quản lý đường dẫn môi trường
├── build.py                 # Script tự động hóa Build PyInstaller + Inno Setup
├── setup.iss                # Kịch bản đóng gói cài đặt Inno Setup Compiler
└── README.md                # Tài liệu hướng dẫn sử dụng
```

---

## ❓ Câu hỏi thường gặp (FAQ)

<details>
<summary><b>1. Vì sao một số video YouTube hoặc TikTok không tải được?</b></summary>
Có thể do:
- Video ở chế độ riêng tư (Private) hoặc giới hạn độ tuổi cần đăng nhập.
- Video được bảo vệ bằng mã hóa DRM (ví dụ: phim bản quyền).
- YouTube vừa cập nhật cơ chế bảo vệ: Hãy vào <b>Cài đặt -> Cập nhật yt-dlp</b> để cập nhật bản mới nhất và thử lại.
</details>

<details>
<summary><b>2. Ứng dụng có tự động loại bỏ logo/watermark khi tải TikTok không?</b></summary>
Có! Ứng dụng tự động chọn luồng video gốc chất lượng cao nhất không có watermark của TikTok.
</details>

<details>
<summary><b>3. Làm sao để đổi sang giao diện Sáng (Light Mode)?</b></summary>
Vào thanh menu: <b>Cài đặt</b> -> <b>Giao diện</b> -> chọn <b>Sáng</b>. Màu nền kem nhạt dịu mắt sẽ được áp dụng ngay lập tức.
</details>

<details>
<summary><b>4. Phần mềm có chứa virus hay mã độc không?</b></summary>
Hoàn toàn không. 100% mã nguồn là mã nguồn mở bằng Python. Một số phần mềm diệt virus có thể cảnh báo giả (False Positive) do file exe được đóng gói bằng PyInstaller chưa qua đăng ký chứng chỉ số đắt tiền (EV Code Signing). Bạn có thể yên tâm bấm <i>Allow</i> hoặc kiểm tra mã nguồn tại kho lưu trữ.
</details>

---

## ⚠️ Tuyên bố miễn trừ trách nhiệm (Disclaimer)

Ứng dụng **Social Media Downloader** được phát triển nhằm mục đích học tập, nghiên cứu và phục vụ nhu cầu lưu trữ ngoại tuyến cho cá nhân. Vui lòng tôn trọng quyền tác giả và tuân thủ [Điều khoản Dịch vụ](https://www.youtube.com/t/terms) của các nền tảng mạng xã hội. Tác giả không chịu trách nhiệm cho bất kỳ hành vi sử dụng sai mục đích hoặc vi phạm bản quyền nào từ phía người dùng.

---

## 👤 Tác giả

* **Thắng MupMip**
* **GitHub**: [@ChinChoppaVN](https://github.com/ChinChoppaVN)
* **Email**: quyetthang.media@gmail.com

---

<p align="center">
  Được xây dựng với sự đam mê ❤️ Chúc bạn có những trải nghiệm tải media tuyệt vời!
</p>