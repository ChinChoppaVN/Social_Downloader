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

from utils import add_download_history

def download_video(url, file_type, final_path, parent_window, progress_callback=None):
    """Tải video từ URL"""
    try:
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best' if file_type == 'mp4' else 'bestaudio/best',
            'outtmpl': final_path,
            'progress_hooks': [progress_callback] if progress_callback else [],
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }] if file_type == 'mp3' else [],
            'quiet': True,
            'no_warnings': True
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info_dict = ydl.extract_info(url, download=True)
                return final_path
            except Exception as e:
                if "Download cancelled" in str(e):
                    raise Exception("Download cancelled")
                else:
                    logging.error(f"Lỗi khi tải video: {e}")
                    return None
    except Exception as e:
        if "Download cancelled" in str(e):
            raise Exception("Download cancelled")
        else:
            logging.error(f"Lỗi khi tải video: {e}")
            return None

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