import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog, ttk, Menu
import threading
import os
import json
import csv
import logging
import shutil
import platform
import subprocess

from functools import partial

from downloader import download_video
from utils import (
    get_clean_filename, load_last_folder, save_last_folder, 
    fetch_video_title, validate_url, add_download_history, 
    get_download_history, clear_download_history, export_download_history,
    DATA_DIR
)
from config.app_config import APP_CONFIG, ASSETS_DIR, DEFAULT_COLUMNS

# Tạo thư mục data nếu chưa tồn tại
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR)

CONFIG = {
    "app_title": "Social Media Downloader",
    "app_size": "600x500",
    "max_history_display": 50,
    "font_title": ("Arial", 24, "bold"),
    "font_subtitle": ("Arial", 14),
    "font_normal": ("Arial", 14),
    "font_small": ("Arial", 12),
    "button_font": ("Arial", 16, "bold"),
    "platforms": ["YouTube", "TikTok", "Vimeo", "SoundCloud"]
}

class DownloaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title(APP_CONFIG["app_title"])
        self.root.geometry(APP_CONFIG["app_size"])
        self.root.resizable(False, False)
        
        # Set icon cho ứng dụng
        icon_path = os.path.join(ASSETS_DIR, "CH.ico")
        if os.path.exists(icon_path):
            self.root.iconbitmap(icon_path)
            # Thiết lập icon cho taskbar
            try:
                from ctypes import windll
                myappid = "thangmupmip.socialdownloader.1.0"
                windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
                self.root.iconbitmap(default=icon_path)
            except Exception as e:
                logging.error(f"Không thể thiết lập icon cho taskbar: {e}")
        
        self.center_window()
        
        self.is_downloading = False
        self.mp4_selected = ctk.BooleanVar(value=True)
        self.mp3_selected = ctk.BooleanVar(value=False)
        self.download_start_time = None
        
        self.create_widgets()

    def center_window(self):
        self.root.update_idletasks()
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        x = (screen_width // 2) - (self.root.winfo_width() // 2)
        y = (screen_height // 2) - (self.root.winfo_height() // 2)
        self.root.geometry(f"{APP_CONFIG['app_size']}+{x}+{y}")

    def create_widgets(self):
        self.create_header()
        self.create_main_frame()
        self.create_buttons()
        self.create_footer()

    def create_header(self):
        header_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        header_frame.pack(fill="x", pady=10)
        
        # Tạo frame cho tiêu đề
        title_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        title_frame.pack(fill="x", padx=10)
        
        title_label = ctk.CTkLabel(title_frame, text=APP_CONFIG["app_title"], font=APP_CONFIG["font_title"])
        title_label.pack(pady=5)
        
        subtitle_label = ctk.CTkLabel(header_frame, text="Tải Video & Audio cực kỳ Pro Max", font=APP_CONFIG["font_subtitle"])
        subtitle_label.pack()

    def create_main_frame(self):
        self.main_frame = ctk.CTkFrame(self.root)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        ctk.CTkLabel(self.main_frame, text="Link video:", font=APP_CONFIG["font_normal"]).grid(row=0, column=0, sticky="w", pady=5, padx=15)
        self.url_entry = ctk.CTkEntry(self.main_frame, width=350, placeholder_text="Facebook, Instagram, TikTok, Youtube ...")
        self.url_entry.grid(row=0, column=1, pady=5, sticky="w")
        
        paste_button = ctk.CTkButton(
            self.main_frame, 
            text="Dán", 
            width=80,
            command=self.paste_url,
            font=APP_CONFIG["font_normal"]
        )
        paste_button.grid(row=0, column=2, pady=5, padx=15, sticky="w")
        
        ctk.CTkLabel(self.main_frame, text="Tên file:", font=APP_CONFIG["font_normal"]).grid(row=1, column=0, sticky="w", pady=5, padx=15)
        self.filename_entry = ctk.CTkEntry(self.main_frame, width=350, placeholder_text="Để trống để sử dụng tên mặc định")
        self.filename_entry.grid(row=1, column=1, columnspan=2, sticky="w", pady=5)
        
        ctk.CTkLabel(self.main_frame, text="Thư mục:", font=APP_CONFIG["font_normal"]).grid(row=2, column=0, sticky="w", pady=5, padx=15)
        last_folder = load_last_folder()
        self.folder_var = ctk.StringVar(value=last_folder)
        self.folder_entry = ctk.CTkEntry(self.main_frame, textvariable=self.folder_var, width=350)
        self.folder_entry.grid(row=2, column=1, pady=5, sticky="w")
        
        folder_button = ctk.CTkButton(self.main_frame, text="Chọn", command=self.select_folder, width=80)
        folder_button.grid(row=2, column=2, pady=5, padx=15, sticky="w")
        
        self.file_status_label = ctk.CTkLabel(self.main_frame, text="", text_color="red", font=APP_CONFIG["font_small"])
        self.file_status_label.grid(row=3, column=1, columnspan=2, sticky="w", pady=(0,5))
        
        ctk.CTkLabel(self.main_frame, text="Định dạng:", font=APP_CONFIG["font_normal"]).grid(row=3, column=0, sticky="w", pady=5, padx=15)
        
        mp4_button = ctk.CTkButton(self.main_frame, text="MP4", command=lambda: self.toggle_format("mp4"), width=80, fg_color=("green", "#1D6F42") if self.mp4_selected.get() else "gray", state="normal")
        mp4_button.grid(row=3, column=1, pady=5, padx=0, sticky="w")
        
        mp3_button = ctk.CTkButton(self.main_frame, text="MP3", command=lambda: self.toggle_format("mp3"), width=80, fg_color=("green", "#1D6F42") if self.mp3_selected.get() else "gray", state="normal")
        mp3_button.grid(row=3, column=1, pady=5, padx=85, sticky="w")
        
        # Progress Frame mới
        progress_frame = ctk.CTkFrame(self.main_frame)
        progress_frame.grid(row=4, column=0, columnspan=3, sticky="ew", padx=15, pady=5)
        
        # Label cho tiến trình
        self.progress_status = ctk.CTkLabel(
            progress_frame, 
            text="Sẵn sàng tải xuống", 
            font=APP_CONFIG["font_small"],
            anchor="w"
        )
        self.progress_status.pack(fill="x", padx=5, pady=(5,0))
        
        # Progress bar với màu gradient và bo góc
        self.progress_bar = ctk.CTkProgressBar(
            progress_frame,
            width=350,
            height=15,
            corner_radius=8,
            border_width=0,
            progress_color=("green", "#1D6F42"),
            fg_color=("gray85", "gray20")
        )
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", padx=5, pady=5)
        
        # Frame cho thông tin chi tiết
        info_frame = ctk.CTkFrame(progress_frame, fg_color="transparent")
        info_frame.pack(fill="x", padx=5, pady=(0,5))
        
        # Labels cho thông tin tải
        self.speed_label = ctk.CTkLabel(
            info_frame, 
            text="Tốc độ: --", 
            font=APP_CONFIG["font_small"]
        )
        self.speed_label.pack(side="left", padx=5)
        
        self.size_label = ctk.CTkLabel(
            info_frame, 
            text="| Dung lượng: --", 
            font=APP_CONFIG["font_small"]
        )
        self.size_label.pack(side="left", padx=5)
        
        self.time_label = ctk.CTkLabel(
            info_frame, 
            text="| Thời gian còn lại: --", 
            font=APP_CONFIG["font_small"]
        )
        self.time_label.pack(side="left", padx=5)
        
        self.main_frame.columnconfigure(1, weight=1)
        self.mp4_selected.trace("w", self.update_button_colors)
        self.mp3_selected.trace("w", self.update_button_colors)

    def create_buttons(self):
        button_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        button_frame.pack(pady=10)

        self.download_button = ctk.CTkButton(button_frame, text="Tải ngay", command=self.start_download, font=APP_CONFIG["button_font"])
        self.download_button.grid(row=0, column=0, padx=5, pady=0, sticky="w")

        self.history_button = ctk.CTkButton(button_frame, text="Lịch sử tải", command=self.show_download_history, font=APP_CONFIG["button_font"])
        self.history_button.grid(row=0, column=1, padx=5, pady=0, sticky="w")

    def create_footer(self):
        footer_label = ctk.CTkLabel(self.root, text="© 2025 Thắng MupMip. All rights reserved.", font=("Arial", 12))
        footer_label.pack(side="bottom", pady=10)

    def toggle_format(self, format_type):
        if format_type == "mp4":
            self.mp4_selected.set(True)
            self.mp3_selected.set(False)
        else:
            self.mp3_selected.set(True)
            self.mp4_selected.set(False)

    def update_button_colors(self, *args):
        mp4_widgets = self.main_frame.grid_slaves(row=3, column=1)
        mp4_button = None
        for widget in mp4_widgets:
            if isinstance(widget, ctk.CTkButton) and widget.grid_info()['padx'] == 0:
                mp4_button = widget
                break
        if mp4_button:
            mp4_button.configure(fg_color=("green", "#1D6F42") if self.mp4_selected.get() else "gray", state="normal")
        else:
            logging.warning("Không tìm thấy nút MP4 tại row=3, column=1 với padx=0")
        
        mp3_widgets = self.main_frame.grid_slaves(row=3, column=1)
        mp3_button = None
        for widget in mp3_widgets:
            if isinstance(widget, ctk.CTkButton) and widget.grid_info()['padx'] == 85:
                mp3_button = widget
                break
        if mp3_button:
            mp3_button.configure(fg_color=("green", "#1D6F42") if self.mp3_selected.get() else "gray", state="normal")
        else:
            logging.warning("Không tìm thấy nút MP3 tại row=3, column=1 với padx=85")

    def select_folder(self):
        folder = filedialog.askdirectory(initialdir=self.folder_var.get())
        if folder:
            self.folder_var.set(folder)
            save_last_folder(folder)

    def update_file_existence(self, *args):
        folder = self.folder_var.get().strip()
        name_input = self.filename_entry.get().strip()
        if folder and name_input:
            if self.mp4_selected.get():
                final_name = get_clean_filename(name_input, "mp4")
                final_path = os.path.join(folder, final_name)
                if os.path.exists(final_path):
                    self.file_status_label.configure(text="Tên file MP4 đã tồn tại!")
                    return
            if self.mp3_selected.get():
                final_name = get_clean_filename(name_input, "mp3")
                final_path = os.path.join(folder, final_name)
                if os.path.exists(final_path):
                    self.file_status_label.configure(text="Tên file MP3 đã tồn tại!")
                    return
            self.file_status_label.configure(text="")
        else:
            self.file_status_label.configure(text="")

    def progress_callback(self, d):
        if d['status'] == 'downloading':
            # Tính toán phần trăm
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
            downloaded = d.get('downloaded_bytes', 0)
            
            if total > 0:
                # Cập nhật progress bar
                progress = downloaded / total
                self.progress_bar.set(progress)
                
                # Hiển thị phần trăm
                percent = progress * 100
                downloaded_mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                self.progress_status.configure(
                    text=f"Đang tải: {percent:.1f}% ({downloaded_mb:.1f}MB/{total_mb:.1f}MB)"
                )
                
                # Hiển thị tốc độ
                speed = d.get('speed', 0)
                if speed:
                    speed_mb = speed / 1024 / 1024
                    self.speed_label.configure(text=f"Tốc độ: {speed_mb:.1f} MB/s")
                
                # Hiển thị thời gian còn lại
                eta = d.get('eta', 0)
                if eta:
                    if eta > 60:
                        time_left = f"{eta // 60}p {eta % 60}s"
                    else:
                        time_left = f"{eta}s"
                    self.time_label.configure(text=f"| Thời gian còn lại: {time_left}")
                
                # Hiển thị kích thước
                self.size_label.configure(
                    text=f"| Dung lượng: {downloaded_mb:.1f}MB/{total_mb:.1f}MB"
                )
                
        elif d['status'] == 'finished':
            self.progress_status.configure(text="Đang xử lý...")
            self.speed_label.configure(text="Tốc độ: --")
            self.time_label.configure(text="| Thời gian còn lại: --")
            self.size_label.configure(text="| Dung lượng: --")
            
        elif d['status'] == 'error':
            self.progress_status.configure(text="Lỗi tải xuống!")
            self.progress_bar.set(0)
            self.speed_label.configure(text="Tốc độ: --")
            self.time_label.configure(text="| Thời gian còn lại: --")
            self.size_label.configure(text="| Dung lượng: --")

    def reset_ui_state(self):
        """Reset tất cả trạng thái UI về mặc định"""
        self.progress_bar.set(0)
        self.progress_status.configure(text="Sẵn sàng tải xuống")
        self.speed_label.configure(text="Tốc độ: --")
        self.time_label.configure(text="| Thời gian còn lại: --")
        self.size_label.configure(text="| Dung lượng: --")
        self.url_entry.delete(0, ctk.END)
        self.url_entry.configure(placeholder_text="Facebook, Instagram, TikTok, Youtube ...")
        self.filename_entry.delete(0, ctk.END)
        self.filename_entry.configure(placeholder_text="Để trống để sử dụng tên mặc định")

    def download_thread(self, url, file_type, final_path, parent_window):
        try:
            downloaded_file = download_video(url, file_type, final_path, parent_window, self.progress_callback)
            
            if downloaded_file and os.path.exists(downloaded_file):
                # Tính kích thước file
                size = f"{os.path.getsize(downloaded_file) / 1024 / 1024:.2f} MB"
                folder_path = os.path.dirname(downloaded_file).replace("/", "\\")
                
                # Ghi lịch sử tải ONLY HERE
                parent_window.after(0, lambda: add_download_history(
                    url, file_type, downloaded_file, 
                    size=size,
                    status="Thành công",
                    folder_path=folder_path
                ))
                
        except Exception as e:
            # Ghi lịch sử thất bại
            parent_window.after(0, lambda: add_download_history(
                url, file_type, final_path,
                size="Không rõ",
                status="Thất bại",
                folder_path="Không rõ"
            ))
        finally:
            self.is_downloading = False
            parent_window.after(0, lambda: self.download_button.configure(state="normal"))
            parent_window.after(0, lambda: self.reset_ui_state())

    def start_download(self):
        if self.is_downloading:
            messagebox.showinfo("Thông báo", "Đang tải, vui lòng chờ!")
            return

        url = self.url_entry.get().strip()
        if not url:
            messagebox.showerror("Lỗi", "Vui lòng nhập link video!")
            return
            
        if not validate_url(url):
            messagebox.showerror("Lỗi", "Link video không hợp lệ!")
            return
            
        folder = self.folder_var.get().strip()
        if not folder:
            messagebox.showerror("Lỗi", "Vui lòng chọn thư mục lưu!")
            return
            
        if not shutil.which("ffmpeg"):
            messagebox.showerror("Lỗi", "FFmpeg không được cài đặt. Vui lòng cài FFmpeg để tải video hoặc audio.")
            return
            
        name_input = self.filename_entry.get().strip()
        if not name_input:
            name_input = fetch_video_title(url)

        # Reset thanh tiến trình và thông tin
        self.progress_bar.set(0)
        self.progress_status.configure(text="Đang chuẩn bị...")
        self.download_start_time = None

        # Chuẩn hóa tên file trước khi tạo final_path
        if self.mp4_selected.get():
            file_type = "mp4"
            clean_name = get_clean_filename(name_input, file_type)
            final_path = os.path.join(folder, clean_name)

            if os.path.exists(final_path):
                if not messagebox.askyesno("Xác nhận", f"Tên file MP4 đã tồn tại. Bạn có muốn ghi đè?"):
                    return

            self.is_downloading = True
            self.download_button.configure(state="disabled")
            threading.Thread(target=self.download_thread, args=(url, file_type, final_path, self.root), daemon=True).start()
            
        elif self.mp3_selected.get():
            file_type = "mp3"
            clean_name = get_clean_filename(name_input, file_type)
            final_path = os.path.join(folder, clean_name)

            if os.path.exists(final_path):
                if not messagebox.askyesno("Xác nhận", f"Tên file MP3 đã tồn tại. Bạn có muốn ghi đè?"):
                    return

            self.is_downloading = True
            self.download_button.configure(state="disabled")
            threading.Thread(target=self.download_thread, args=(url, file_type, final_path, self.root), daemon=True).start()
            
        else:
            messagebox.showwarning("Cảnh báo", "Vui lòng chọn một định dạng (MP4 hoặc MP3)!")
            self.is_downloading = False

    def show_download_history(self):
        history = get_download_history()
        history_window = ctk.CTkToplevel(self.root)
        history_window.title("Lịch sử tải - Social Media Downloader")
        history_window.geometry("800x500")
        history_window.resizable(True, True)
        history_window.minsize(600, 400)
        history_window.attributes("-topmost", True)

        history_window.update_idletasks()
        screen_width = history_window.winfo_screenwidth()
        screen_height = history_window.winfo_screenheight()
        x = (screen_width // 2) - (history_window.winfo_width() // 2)
        y = (screen_height // 2) - (history_window.winfo_height() // 2)
        history_window.geometry(f"800x500+{x}+{y}")

        main_frame = ctk.CTkFrame(history_window)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)

        search_entry = ctk.CTkEntry(main_frame, placeholder_text="Tìm kiếm (URL, Tên file, Thời gian)...", width=300)
        search_entry.pack(fill="x", pady=(0, 5))

        column_order = self.load_column_order()
        columns = tuple(column_order)
        tree = ttk.Treeview(main_frame, columns=columns, show="headings", height=350)
        tree.pack(fill="both", expand=True, pady=5)

        tree.configure(style="Custom.Treeview")
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Custom.Treeview", background="#2b2b2b", fieldbackground="#2b2b2b", foreground="white")
        style.map("Custom.Treeview", background=[("selected", "#0066cc")], foreground=[("selected", "white")])

        for col in columns:
            tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
            # Thiết lập kích thước cố định cho từng cột
            if col == "STT":
                tree.column(col, width=30, minwidth=30, anchor="w")
            elif col == "URL":
                tree.column(col, width=200, minwidth=30, anchor="w")
            elif col == "Tên file":
                tree.column(col, width=200, minwidth=30, anchor="w")
            elif col == "Định dạng":
                tree.column(col, width=70, minwidth=30, anchor="w")
            elif col == "Kích thước":
                tree.column(col, width=80, minwidth=30, anchor="w")
            elif col == "Thời gian":
                tree.column(col, width=120, minwidth=30, anchor="w")
            elif col == "Trạng thái":
                tree.column(col, width=80, minwidth=30, anchor="w")
            elif col == "Thư mục lưu":
                tree.column(col, width=200, minwidth=30, anchor="w")
            
            # Thêm sự kiện thay đổi kích thước cho từng cột
            def on_column_resize(event, column=col):
                if event.widget.identify_region(event.x, event.y) == "separator":
                    self.save_column_widths(tree)
            tree.bind(f'<ButtonRelease-1>', on_column_resize)

        if not history:
            empty_values = ["Chưa có lịch sử tải nào."] + [""] * (len(columns) - 1)
            tree.insert("", "end", values=empty_values)
        else:
            for i, entry in enumerate(reversed(history[-50:]), 1):
                # Tạo dictionary ánh xạ tên cột với giá trị
                values_dict = {
                    "STT": i,
                    "URL": entry['url'],
                    "Tên file": os.path.basename(entry['file_path']),
                    "Định dạng": entry['file_type'],
                    "Kích thước": entry.get('size', 'Không rõ'),
                    "Thời gian": entry['timestamp'],
                    "Trạng thái": entry.get('status', 'Thành công'),
                    "Thư mục lưu": entry.get('folder_path', 'Không rõ')
                }
                # Lấy giá trị theo thứ tự cột
                ordered_values = [values_dict[col] for col in columns]
                tree.insert("", "end", values=ordered_values)

        toolbar_frame = ctk.CTkFrame(main_frame)
        toolbar_frame.pack(fill="x", pady=5)

        btn_clear = ctk.CTkButton(toolbar_frame, text="Xóa", command=lambda: self.clear_history(tree, history_window))
        btn_clear.pack(side="left", padx=5)

        btn_delete_selected = ctk.CTkButton(toolbar_frame, text="Xóa đã chọn", command=lambda: self.delete_selected(tree, history_window))
        btn_delete_selected.pack(side="left", padx=5)

        btn_export = ctk.CTkButton(toolbar_frame, text="Xuất", command=lambda: self.export_history(history))
        btn_export.pack(side="left", padx=5)

        btn_filter = ctk.CTkButton(toolbar_frame, text="Lọc", command=lambda: self.filter_history(tree, history, search_entry.get()))
        btn_filter.pack(side="left", padx=5)

        btn_reorder = ctk.CTkButton(toolbar_frame, text="Sắp xếp cột", command=lambda: self.reorder_columns(tree))
        btn_reorder.pack(side="left", padx=5)

        btn_close = ctk.CTkButton(toolbar_frame, text="Đóng", command=history_window.destroy)
        btn_close.pack(side="left", padx=5)

        def on_search(event):
            self.filter_history(tree, history, search_entry.get())

        search_entry.bind("<KeyRelease>", on_search)
        tree.bind("<Button-3>", lambda e: self.show_context_menu(e, tree, history))

        history_window.grab_set()
        history_window.transient(self.root)

    def treeview_sort_column(self, tree, col, reverse):
        l = [(tree.set(k, col), k) for k in tree.get_children('')]
        l.sort(reverse=reverse)
        for index, (val, k) in enumerate(l):
            tree.move(k, '', index)
        tree.heading(col, command=lambda: self.treeview_sort_column(tree, col, not reverse))

    def clear_history(self, tree, history_window):
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa toàn bộ lịch sử tải?"):
            try:
                clear_download_history()
                for item in tree.get_children():
                    tree.delete(item)
                empty_values = ["Chưa có lịch sử tải nào."] + [""] * (len(self.load_column_order()) - 1)
                tree.insert("", "end", values=empty_values)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa lịch sử: {e}")
            history_window.lift()

    def delete_selected(self, tree, history_window):
        selected = tree.selection()
        if not selected:
            messagebox.showinfo("Thông báo", "Vui lòng chọn ít nhất một mục để xóa!")
            return
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn xóa các mục đã chọn?"):
            try:
                history = get_download_history()
                for item in selected:
                    values = tree.item(item, "values")
                    url = values[1]
                    new_history = [entry for entry in history if entry['url'] != url]
                    with open("history.json", "w", encoding="utf-8") as f:
                        json.dump(new_history, f, ensure_ascii=False, indent=4)
                for item in selected:
                    tree.delete(item)
                if tree.get_children():
                    for i, item in enumerate(tree.get_children(), 1):
                        tree.item(item, values=(i,) + tuple(tree.item(item, "values")[1:]))
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể xóa mục đã chọn: {e}")
            history_window.lift()

    def export_history(self, history):
        if not history:
            messagebox.showinfo("Thông báo", "Không có lịch sử để xuất!")
            return
        try:
            filename = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")], title="Lưu lịch sử tải dưới dạng CSV")
            if filename:
                with open(filename, "w", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    writer.writerow(["STT", "URL", "Tên file", "Định dạng", "Kích thước", "Thời gian", "Trạng thái", "Thư mục lưu"])
                    for i, entry in enumerate(reversed(history[-50:]), 1):
                        writer.writerow([
                            i,
                            entry['url'],
                            os.path.basename(entry['file_path']),
                            entry['file_type'],
                            entry.get('size', 'Không rõ'),
                            entry['timestamp'],
                            entry.get('status', 'Thành công'),
                            entry.get('folder_path', 'Không rõ')
                        ])
                messagebox.showinfo("Thành công", f"Lịch sử đã được xuất vào file: {filename}")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xuất lịch sử: {e}")

    def filter_history(self, tree, history, search_term):
        search_term = search_term.lower()
        for item in tree.get_children():
            tree.delete(item)
        
        column_order = self.load_column_order()
        columns = tuple(column_order)
        
        if not history:
            empty_values = ["Chưa có lịch sử tải nào."] + [""] * (len(columns) - 1)
            tree.insert("", "end", values=empty_values)
            return
        
        filtered_history = [
            entry for entry in history[-50:]
            if search_term in entry['url'].lower() or 
            search_term in os.path.basename(entry['file_path']).lower() or 
            search_term in entry.get('timestamp', '').lower()
        ]
        
        for i, entry in enumerate(reversed(filtered_history), 1):
            values_dict = {
                "STT": i,
                "URL": entry['url'],
                "Tên file": os.path.basename(entry['file_path']),
                "Định dạng": entry['file_type'],
                "Kích thước": entry.get('size', 'Không rõ'),
                "Thời gian": entry['timestamp'],
                "Trạng thái": entry.get('status', 'Thành công'),
                "Thư mục lưu": entry.get('folder_path', 'Không rõ')
            }
            ordered_values = [values_dict[col] for col in columns]
            tree.insert("", "end", values=ordered_values)

    def show_context_menu(self, event, tree, history):
        """Hiển thị menu chuột phải"""
        item = tree.identify_row(event.y)
        if item:
            tree.selection_clear()
            tree.selection_set(item)
            values = tree.item(item, "values")
            
            # Lấy thông tin file từ values theo thứ tự cột mới
            column_order = self.load_column_order()
            values_dict = dict(zip(column_order, values))
            
            file_name = values_dict["Tên file"]
            folder_path = values_dict["Thư mục lưu"]
            file_path = os.path.join(folder_path, file_name) if folder_path != "Không rõ" else None

            context_menu = Menu(self.root, tearoff=0)
            context_menu.add_command(label="Mở File", command=lambda: self.open_file(file_path))
            context_menu.add_command(label="Mở Folder", command=lambda: self.open_folder_with_highlight(file_path))
            context_menu.add_separator()
            context_menu.add_command(label="Xóa", command=lambda: self.delete_selected(tree, self.root))
            context_menu.tk_popup(event.x_root, event.y_root)

    def open_file(self, file_path):
        """Mở file được chọn"""
        if file_path and os.path.exists(file_path):
            try:
                os.startfile(file_path)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở file: {e}")
        else:
            messagebox.showerror("Lỗi", "File không tồn tại!")

    def open_folder_with_highlight(self, file_path):
        """Mở thư mục và highlight file được chọn"""
        if file_path and os.path.exists(file_path):
            try:
                if platform.system() == "Windows":
                    subprocess.run(['explorer', '/select,', file_path])
                else:
                    subprocess.run(["xdg-open", os.path.dirname(file_path)], check=True)
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể mở thư mục: {e}")
        else:
            messagebox.showerror("Lỗi", "File không tồn tại!")

    def reorder_columns(self, tree):
        current_columns = list(tree["columns"])
        new_order = simpledialog.askstring("Sắp xếp cột", "Nhập thứ tự cột (cách nhau bởi dấu phẩy, ví dụ: STT,URL,Tên file,Định dạng,Kích thước,Thời gian,Trạng thái,Thư mục lưu):", parent=self.root)
        if new_order:
            try:
                new_order = [col.strip() for col in new_order.split(",")]
                if set(new_order) == set(current_columns):
                    tree["columns"] = new_order
                    for i, col in enumerate(new_order):
                        tree.heading(col, text=col, command=lambda _col=col: self.treeview_sort_column(tree, _col, False))
                        tree.column(col, width=100, anchor="w")
                    self.save_column_order(new_order)
                else:
                    messagebox.showerror("Lỗi", "Thứ tự cột không hợp lệ!")
            except Exception as e:
                messagebox.showerror("Lỗi", f"Không thể sắp xếp cột: {e}")

    def save_column_order(self, order):
        """Lưu thứ tự cột vào config"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            config["columns"] = order
            with open("config.json", "w", encoding="utf-8") as f:
                json.dump(config, f, ensure_ascii=False, indent=4)
        except Exception as e:
            logging.error(f"Không thể lưu thứ tự cột: {e}")

    def load_column_order(self):
        """Đọc thứ tự cột từ config"""
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
                return config.get("columns", DEFAULT_COLUMNS)
        except Exception as e:
            logging.error(f"Không thể đọc thứ tự cột: {e}")
            return DEFAULT_COLUMNS

    def paste_url(self):
        """Dán link từ clipboard vào ô nhập URL"""
        try:
            url = self.root.clipboard_get()
            self.url_entry.delete(0, ctk.END)
            self.url_entry.insert(0, url)
        except Exception as e:
            logging.error(f"Không thể dán từ clipboard: {e}")
            messagebox.showerror("Lỗi", "Không thể dán từ clipboard!")

def run_app():
    ctk.set_appearance_mode("dark")  # Mặc định dark mode
    ctk.set_default_color_theme("green")

    root = ctk.CTk()
    app = DownloaderApp(root)
    root.mainloop()

if __name__ == "__main__":
    run_app()