import os
import yt_dlp
import customtkinter as ctk
from tkinter import messagebox
import traceback
import platform
import subprocess
import shutil
from functools import partial

from utils import add_download_history

def download_video(url, file_type, output_path, parent_window, progress_callback=None):
    """
    Tải video/audio từ URL và lưu vào output_path
    
    Args:
        url: URL của video
        file_type: 'mp4' hoặc 'mp3'
        output_path: Đường dẫn lưu file (không bao gồm đuôi)
        parent_window: Cửa sổ gốc để hiển thị thông báo
        progress_callback: Hàm callback cập nhật tiến trình
    """
    # Đảm bảo output_path không có đuôi
    folder = os.path.dirname(output_path)
    filename = os.path.basename(output_path)
    if filename.lower().endswith((".mp3", ".mp4")):
        filename = filename.rsplit(".", 1)[0]
    outtmpl = os.path.join(folder, filename)

    ydl_opts = {
        'outtmpl': outtmpl + ".%(ext)s",  # Cho phép yt_dlp thêm đuôi tự động
        'noplaylist': True,
    }
    if progress_callback is not None:
        ydl_opts['progress_hooks'] = [progress_callback]

    if file_type == "mp3":
        if not shutil.which("ffmpeg"):
            raise Exception("FFmpeg không được cài đặt. Vui lòng cài FFmpeg để tải mp3.")
        ydl_opts.update({
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })
    else:  # mp4
        ydl_opts.update({
            'format': 'bestvideo+bestaudio/best',
            'merge_output_format': 'mp4'
        })

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            downloaded_filename = ydl.prepare_filename(info_dict)
            base, downloaded_ext = os.path.splitext(downloaded_filename)
            
            # Chuẩn hóa tên file để chỉ giữ một đuôi
            final_filename = f"{base}.{file_type}"
            if os.path.exists(downloaded_filename) and downloaded_filename != final_filename:
                try:
                    os.rename(downloaded_filename, final_filename)
                except OSError as e:
                    show_error_on_main_thread(parent_window, f"Không thể đổi tên file: {e}")

        # Lưu lịch sử tải và hiển thị popup hoàn thành
        parent_window.after(0, lambda: add_download_history(url, file_type, final_filename))
        parent_window.after(0, lambda: show_download_complete_popup(final_filename, parent_window))

    except Exception as e:
        error_msg = f"Có lỗi xảy ra:\n{traceback.format_exc()}"
        show_error_on_main_thread(parent_window, error_msg)

def show_error_on_main_thread(parent_window, message):
    """Hiển thị thông báo lỗi trên main thread"""
    parent_window.after(0, lambda: messagebox.showerror("Lỗi tải", message))

def show_download_complete_popup(file_path, parent_window):
    """Hiển thị popup thông báo tải xong"""
    popup = ctk.CTkToplevel(parent_window)
    popup.title("Tải xong!")
    popup.geometry("400x150") 
    popup.attributes("-topmost", True)
    popup.resizable(False, False)

    # Căn giữa popup
    popup.update_idletasks()
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = (screen_width // 2) - (popup.winfo_width() // 2)
    y = (screen_height // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"400x150+{x}+{y}")

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
    button_frame.pack(pady=(10, 20), padx=20, fill="x")
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
                subprocess.run(['explorer', '/select,', path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(path)], check=True)
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}")


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

    popup.grab_set()
    popup.transient(parent_window)