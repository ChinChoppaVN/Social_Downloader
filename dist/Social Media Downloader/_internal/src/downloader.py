import os
import yt_dlp
import customtkinter as ctk
from tkinter import messagebox
import traceback
import platform
import subprocess
import shutil
from functools import partial
import logging
import winsound  # Thêm import winsound để phát âm thanh trên Windows
import sys
import json

# Thêm thư mục gốc vào sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import các module từ thư mục gốc
from src.utils import DATA_DIR  # Thêm import DATA_DIR

def download_video(url, output_path, progress_callback=None):
    """Tải video từ URL và lưu vào output_path"""
    try:
        # Xác định định dạng từ đường dẫn đầu ra
        file_type = "mp3" if output_path.lower().endswith(".mp3") else "mp4"
        
        # Cấu hình yt-dlp
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'ignoreerrors': True,  # Bỏ qua lỗi và tiếp tục
            'nocheckcertificate': True,
            'prefer_insecure': True,
            'outtmpl': output_path,
            'progress_hooks': [progress_callback] if progress_callback else None,
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
        }
        
        # Nếu là MP3, thêm cấu hình chuyển đổi âm thanh
        if file_type == "mp3":
            ydl_opts.update({
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }]
            })
        else:  # MP4
            ydl_opts.update({
                'format': 'bestvideo[ext=mp4][vcodec^=avc1]+bestaudio[ext=m4a]/best[ext=mp4][vcodec^=avc1]/best'  # Chỉ định codec H.264
            })
        
        # Tải video
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # Lấy thông tin video
            info = ydl.extract_info(url, download=False)
            
            # Nếu không tìm thấy định dạng phù hợp, thử tải định dạng mặc định
            if not info.get('formats'):
                ydl_opts['format'] = 'best'
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            else:
                ydl.download([url])
                
        # Kiểm tra file tải xuống
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            return True
        else:
            # Kiểm tra trường hợp file MP3 có thể đã được tạo với tên khác
            if file_type == "mp3":
                dir_path = os.path.dirname(output_path)
                base_name = os.path.splitext(os.path.basename(output_path))[0]
                
                # Tìm file MP3 có thể đã được tạo với tên khác
                for file in os.listdir(dir_path):
                    if file.startswith(base_name) and file.endswith('.mp3'):
                        mp3_path = os.path.join(dir_path, file)
                        # Đổi tên file thành tên mong muốn
                        try:
                            os.rename(mp3_path, output_path)
                            return True
                        except:
                            return os.path.exists(mp3_path)
            
            return False
            
    except Exception as e:
        logging.error(f"Lỗi khi tải video: {e}")
        if "Download cancelled" in str(e):
            raise Exception("Download cancelled")
        return False

def show_error_on_main_thread(parent_window, message):
    """Hiển thị thông báo lỗi trên main thread"""
    parent_window.after(0, lambda: messagebox.showerror("Lỗi tải", message))
    # Phát âm thanh lỗi
    try:
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
    except:
        pass

def show_download_complete_popup(file_path, parent_window, notify_state=True, on_notify_change=None):
    """Hiển thị popup thông báo tải xong"""
    # Phát âm thanh thông báo tải xong
    try:
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except:
        pass
    
    # Tắt thuộc tính topmost của các cửa sổ lịch sử
    for widget in parent_window.winfo_toplevel().winfo_children():
        if isinstance(widget, ctk.CTkToplevel) and hasattr(widget, 'is_history_window'):
            widget.attributes("-topmost", False)
        
    popup = ctk.CTkToplevel(parent_window)
    popup.title("Tải xong!")
    popup.geometry("400x180")  # Tăng chiều cao để chứa thêm nút
    popup.attributes("-topmost", True)
    popup.resizable(False, False)

    # Căn giữa popup
    popup.update_idletasks()
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = (screen_width // 2) - (popup.winfo_width() // 2)
    y = (screen_height // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"400x180+{x}+{y}")

    # Lấy tên file và giới hạn số ký tự
    filename = os.path.basename(file_path)
    if not filename or filename.strip() == "":
        filename = "video_youtube"  # Mặc định nếu tên rỗng

    max_chars = 30  # Hiển thị tối đa 30 ký tự
    if len(filename) > max_chars:
        wrapped_filename = filename[:max_chars] + "..."  # Cắt ngắn và thêm "..."
    else:
        wrapped_filename = filename  # Hiển thị nguyên văn nếu ngắn hơn

    # Tạo label với nội dung đã giới hạn, căn giữa
    label = ctk.CTkLabel(popup, text=f"Đã tải xong:\n{wrapped_filename}", 
                         font=("Helvetica", 16, "bold"), 
                         justify="center")
    label.pack(pady=(20, 10), padx=20)

    # Tạo frame chứa 3 nút xếp hàng ngang
    button_frame = ctk.CTkFrame(popup)
    button_frame.pack(pady=(10, 5), padx=20, fill="x")
    btn_width = 100

    def open_file(path):
        """Mở file vừa tải"""
        try:
            os.startfile(path)
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở file: {e}")

    def open_folder_with_highlight(path):
        """Mở thư mục chứa file và highlight file"""
        try:
            if platform.system() == "Windows":
                # Chuẩn hóa đường dẫn sang định dạng Windows
                path = os.path.abspath(path)  # Chuyển đổi thành đường dẫn tuyệt đối
                path = os.path.normpath(path)  # Chuẩn hóa đường dẫn
                # Kiểm tra xem file có tồn tại không
                if not os.path.exists(path):
                    raise FileNotFoundError(f"Không tìm thấy file: {path}")
                # Sử dụng explorer để mở và highlight file
                subprocess.run(['explorer', '/select,', path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(path)], check=True)
            popup.destroy()
        except FileNotFoundError as e:
            messagebox.showerror("Lỗi", str(e))
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}")

    # Tạo biến để lưu trạng thái "không hỏi lại"
    dont_ask_again = ctk.BooleanVar(value=notify_state)

    def on_dont_ask_again():
        """Xử lý sự kiện khi checkbox thay đổi"""
        # Lưu trạng thái vào file config
        config = {}
        config_file = os.path.join(DATA_DIR, "config.json")
        if os.path.exists(config_file):
            try:
                with open(config_file, "r", encoding="utf-8") as f:
                    config = json.load(f)
            except:
                pass
        config["dont_show_complete_popup"] = dont_ask_again.get()
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
        # Gọi callback đồng bộ trạng thái với UI nếu có
        if on_notify_change:
            on_notify_change(dont_ask_again.get())

    btn_open = ctk.CTkButton(button_frame, text="Mở File", 
                            command=partial(open_file, file_path), 
                            width=btn_width)
    btn_open.pack(side="left", expand=True, fill="x", padx=5)
    
    btn_folder = ctk.CTkButton(button_frame, text="Mở Folder", 
                            command=partial(open_folder_with_highlight, file_path), 
                            width=btn_width)
    btn_folder.pack(side="left", expand=True, fill="x", padx=5)
    
    btn_close = ctk.CTkButton(button_frame, text="Đóng", 
                            command=popup.destroy, 
                            width=btn_width)
    btn_close.pack(side="left", expand=True, fill="x", padx=5)

    # Thêm checkbox "Không hỏi lại" nhỏ hơn và sát cạnh dưới popup
    checkbox = ctk.CTkCheckBox(
        popup,
        text="Không hỏi lại",
        variable=dont_ask_again,
        command=on_dont_ask_again,
        font=("Helvetica", 13),
        width=12,
        height=12
    )
    checkbox.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)

    popup.grab_set()
    popup.transient(parent_window)