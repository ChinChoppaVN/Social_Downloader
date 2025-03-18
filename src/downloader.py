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

# Thêm thư mục gốc vào sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import các module từ thư mục gốc
def download_video(url, file_type, final_path, parent_window, progress_callback=None):
    """Tải video từ URL"""
    try:
        if file_type == 'mp3':
            # Đảm bảo final_path có đuôi .mp3
            if not final_path.endswith('.mp3'):
                final_path = final_path + '.mp3'
                
            # Cấu hình đơn giản hóa cho MP3
            ydl_opts = {
                'format': 'bestaudio',
                'outtmpl': final_path,
                'progress_hooks': [progress_callback] if progress_callback else [],
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True
            }

            # Xóa file cũ nếu tồn tại
            if os.path.exists(final_path):
                try:
                    os.remove(final_path)
                except:
                    pass

        else:
            ydl_opts = {
                'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
                'outtmpl': final_path,
                'progress_hooks': [progress_callback] if progress_callback else [],
                'quiet': True,
                'no_warnings': True
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                # Tải thông tin video trước
                info_dict = ydl.extract_info(url, download=False)
                if not info_dict:
                    raise Exception("Không thể lấy thông tin video")

                # Tiến hành tải
                ydl.download([url])
                
                if file_type == 'mp3':
                    # Kiểm tra file MP3 sau khi tải
                    if os.path.exists(final_path):
                        if os.path.getsize(final_path) > 0:
                            return final_path
                        else:
                            if os.path.exists(final_path):
                                os.remove(final_path)
                            raise Exception("File MP3 tạo ra bị lỗi (kích thước = 0)")
                    else:
                        # Kiểm tra các file tạm và file trung gian
                        dir_path = os.path.dirname(final_path)
                        base_name = os.path.splitext(os.path.basename(final_path))[0]
                        
                        # Tìm file MP3 có thể đã được tạo với tên khác
                        for file in os.listdir(dir_path):
                            if file.startswith(base_name) and file.endswith('.mp3'):
                                mp3_path = os.path.join(dir_path, file)
                                # Đổi tên file thành tên mong muốn
                                try:
                                    os.rename(mp3_path, final_path)
                                    return final_path
                                except:
                                    if os.path.exists(mp3_path):
                                        return mp3_path
                        
                        # Nếu không tìm thấy file MP3 nào
                        raise Exception("Không thể tạo file MP3. Vui lòng thử lại.")
                return final_path
                
            except Exception as e:
                if "Download cancelled" in str(e):
                    raise Exception("Download cancelled")
                else:
                    error_msg = f"Lỗi khi tải: {str(e)}"
                    logging.error(error_msg)
                    logging.error(traceback.format_exc())
                    parent_window.after(0, lambda: show_error_on_main_thread(parent_window, error_msg))
                    return None
    except Exception as e:
        if "Download cancelled" in str(e):
            raise Exception("Download cancelled")
        else:
            logging.error(f"Lỗi khi tải video: {str(e)}")
            parent_window.after(0, lambda: show_error_on_main_thread(parent_window, f"Lỗi khi tải: {str(e)}"))
            return None

def show_error_on_main_thread(parent_window, message):
    """Hiển thị thông báo lỗi trên main thread"""
    parent_window.after(0, lambda: messagebox.showerror("Lỗi tải", message))
    # Phát âm thanh lỗi
    try:
        winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
    except:
        pass

def show_download_complete_popup(file_path, parent_window):
    """Hiển thị popup thông báo tải xong"""
    # Phát âm thanh thông báo tải xong
    try:
        winsound.PlaySound("SystemAsterisk", winsound.SND_ALIAS)
    except:
        pass
        
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