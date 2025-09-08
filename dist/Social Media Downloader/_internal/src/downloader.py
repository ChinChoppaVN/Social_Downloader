"""Download module for handling video/audio downloads from various platforms.

This module provides functionality to download videos and audio files from
supported platforms using yt-dlp, with progress tracking and error handling.
"""

import os
import sys
import json
import logging
import platform
import subprocess
import shutil
from functools import partial

import yt_dlp
import customtkinter as ctk
from tkinter import messagebox

try:
    import winsound  # For Windows sound notifications
except ImportError:
    winsound = None  # Not available on non-Windows platforms

# Add root directory to sys.path
root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root_dir not in sys.path:
    sys.path.append(root_dir)

# Import modules from root directory
from src.utils import DATA_DIR


def download_video(url, output_path, progress_callback=None):
    """Download video from URL and save to output_path.
    
    Args:
        url (str): The URL of the video to download
        output_path (str): The path where the file will be saved
        progress_callback (callable, optional): Callback function for progress updates
        
    Returns:
        bool: True if download was successful, False otherwise
    """
    try:
        # Determine file type from output path extension
        file_type = "mp3" if output_path.lower().endswith(".mp3") else "mp4"
        
        # Configure yt-dlp options
        ydl_opts = _get_download_options(output_path, progress_callback)
        
        # Add format-specific configurations
        if file_type == "mp3":
            _configure_audio_options(ydl_opts)
        else:
            _configure_video_options(ydl_opts)
        
        # Execute download
        return _execute_download(url, output_path, ydl_opts, file_type)
        
    except Exception as e:
        logging.error(f"Error during video download: {e}")
        if "Download cancelled" in str(e):
            raise Exception("Download cancelled")
        return False


def _get_download_options(output_path, progress_callback):
    """Get base download options for yt-dlp."""
    return {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,  # Set False to download full playlist
        'ignoreerrors': True,  # Skip errors and continue
        'nocheckcertificate': True,
        'prefer_insecure': True,
        'outtmpl': output_path,
        'progress_hooks': [progress_callback] if progress_callback else None,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    }


def _configure_audio_options(ydl_opts):
    """Configure yt-dlp options for audio download (MP3)."""
    ydl_opts.update({
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }]
    })


def _configure_video_options(ydl_opts):
    """Configure yt-dlp options for video download (MP4)."""
    ydl_opts.update({
        'format': 'bestvideo[ext=mp4][height<=2160]+bestaudio[ext=m4a]/best[ext=mp4]/best'  # Allow 4K H.264
    })


def _execute_download(url, output_path, ydl_opts, file_type):
    """Execute the actual download with yt-dlp."""
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Get video/playlist information
        info = ydl.extract_info(url, download=False)
        
        # Handle playlist vs single video
        if 'entries' in info:
            ydl.download([url])  # Download entire playlist
        else:
            # Handle single video
            if not info.get('formats'):
                # Fallback to best available format
                ydl_opts['format'] = 'best'
                with yt_dlp.YoutubeDL(ydl_opts) as fallback_ydl:
                    fallback_ydl.download([url])
            else:
                ydl.download([url])
    
    # Verify download success
    return _verify_download_success(output_path, file_type)


def _verify_download_success(output_path, file_type):
    """Verify that the download was successful."""
    if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
        return True
    
    # Special handling for MP3 files that might have different names
    if file_type == "mp3":
        return _find_and_rename_mp3_file(output_path)
    
    return False


def _find_and_rename_mp3_file(expected_path):
    """Find MP3 file that might have been created with a different name."""
    dir_path = os.path.dirname(expected_path)
    base_name = os.path.splitext(os.path.basename(expected_path))[0]
    
    # Look for MP3 file that might have been created with different name
    for file in os.listdir(dir_path):
        if file.startswith(base_name) and file.endswith('.mp3'):
            mp3_path = os.path.join(dir_path, file)
            # Try to rename file to expected name
            try:
                os.rename(mp3_path, expected_path)
                return True
            except OSError:
                return os.path.exists(mp3_path)
    
    return False


def show_error_on_main_thread(parent_window, message):
    """Display error message on main thread with sound notification."""
    parent_window.after(0, lambda: messagebox.showerror("Download Error", message))
    _play_system_sound("error")


def _play_system_sound(sound_type):
    """Play system sound notification."""
    if winsound is None:
        return  # Not available on non-Windows platforms
    
    try:
        sound_map = {
            "error": "SystemExclamation",
            "success": "SystemAsterisk",
            "warning": "SystemExclamation"
        }
        sound_name = sound_map.get(sound_type, "SystemAsterisk")
        winsound.PlaySound(sound_name, winsound.SND_ALIAS)
    except Exception as e:
        logging.debug(f"Could not play system sound: {e}")


def show_download_complete_popup(file_path, parent_window, notify_state=True, on_notify_change=None):
    """Display download completion popup with options to open file/folder."""
    # Play success sound notification
    _play_system_sound("success")
    
    # Disable topmost attribute for history windows
    _disable_history_windows_topmost(parent_window)
        
    popup = ctk.CTkToplevel(parent_window)
    popup.title("Download Complete!")
    popup.geometry("400x180")  # Increase height to accommodate additional button
    popup.attributes("-topmost", True)
    popup.resizable(False, False)

    # Center popup
    popup.update_idletasks()
    screen_width = popup.winfo_screenwidth()
    screen_height = popup.winfo_screenheight()
    x = (screen_width // 2) - (popup.winfo_width() // 2)
    y = (screen_height // 2) - (popup.winfo_height() // 2)
    popup.geometry(f"400x180+{x}+{y}")

    # Create and display filename label with length limit
    filename_label = _create_filename_label(popup, file_path)
    filename_label.pack(pady=(20, 10), padx=20)

    # Create action buttons frame
    button_frame = _create_action_buttons(popup, file_path)
    button_frame.pack(pady=(10, 5), padx=20, fill="x")

    # Add "Don't ask again" checkbox
    _create_dont_ask_checkbox(popup, notify_state, on_notify_change)

    popup.grab_set()
    popup.transient(parent_window)


def _disable_history_windows_topmost(parent_window):
    """Disable topmost attribute for any open history windows."""
    for widget in parent_window.winfo_toplevel().winfo_children():
        if isinstance(widget, ctk.CTkToplevel) and hasattr(widget, 'is_history_window'):
            widget.attributes("-topmost", False)


def _create_filename_label(popup, file_path):
    """Create filename label with truncation for long names."""
    filename = os.path.basename(file_path)
    if not filename or filename.strip() == "":
        filename = "video_youtube"  # Default if name is empty

    max_chars = 30  # Display maximum 30 characters
    if len(filename) > max_chars:
        wrapped_filename = filename[:max_chars] + "..."  # Truncate and add "..."
    else:
        wrapped_filename = filename  # Display as-is if shorter

    # Create label with limited content, centered
    return ctk.CTkLabel(
        popup, 
        text=f"Download completed:\n{wrapped_filename}", 
        font=("Helvetica", 16, "bold"), 
        justify="center"
    )


def _create_action_buttons(popup, file_path):
    """Create action buttons for the completion popup."""
    button_frame = ctk.CTkFrame(popup)
    btn_width = 100
    
    def open_file(path):
        """Open the downloaded file."""
        try:
            os.startfile(path)
            popup.destroy()
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open file: {e}")

    def open_folder_with_highlight(path):
        """Open folder containing the file and highlight it."""
        try:
            if platform.system() == "Windows":
                # Normalize path for Windows
                path = os.path.normpath(os.path.abspath(path))
                # Check if file exists
                if not os.path.exists(path):
                    raise FileNotFoundError(f"File not found: {path}")
                # Use explorer to open and highlight file
                subprocess.run(['explorer', '/select,', path])
            else:
                subprocess.run(["xdg-open", os.path.dirname(path)], check=True)
            popup.destroy()
        except FileNotFoundError as e:
            messagebox.showerror("Error", str(e))
        except Exception as e:
            messagebox.showerror("Error", f"Cannot open folder: {e}")
    
    # Create buttons
    btn_open = ctk.CTkButton(
        button_frame, 
        text="Open File", 
        command=partial(open_file, file_path), 
        width=btn_width
    )
    btn_open.pack(side="left", expand=True, fill="x", padx=5)
    
    btn_folder = ctk.CTkButton(
        button_frame, 
        text="Open Folder", 
        command=partial(open_folder_with_highlight, file_path), 
        width=btn_width
    )
    btn_folder.pack(side="left", expand=True, fill="x", padx=5)
    
    btn_close = ctk.CTkButton(
        button_frame, 
        text="Close", 
        command=popup.destroy, 
        width=btn_width
    )
    btn_close.pack(side="left", expand=True, fill="x", padx=5)
    
    return button_frame


def _create_dont_ask_checkbox(popup, notify_state, on_notify_change):
    """Create "Don't ask again" checkbox with state management."""
    dont_ask_again = ctk.BooleanVar(value=notify_state)

    def on_dont_ask_again():
        """Handle checkbox state change event."""
        # Save state to config file
        _save_dont_ask_config(dont_ask_again.get())
        
        # Call callback to sync state with UI if provided
        if on_notify_change:
            on_notify_change(dont_ask_again.get())

    checkbox = ctk.CTkCheckBox(
        popup,
        text="Don't ask again",
        variable=dont_ask_again,
        command=on_dont_ask_again,
        font=("Helvetica", 13),
        width=12,
        height=12
    )
    checkbox.place(relx=1.0, rely=1.0, anchor="se", x=-10, y=-10)


def _save_dont_ask_config(dont_ask_state):
    """Save the 'don't ask again' state to config file."""
    config = {}
    config_file = os.path.join(DATA_DIR, "config.json")
    
    if os.path.exists(config_file):
        try:
            with open(config_file, "r", encoding="utf-8") as f:
                config = json.load(f)
        except Exception as e:
            logging.warning(f"Could not read config file: {e}")
    
    config["dont_show_complete_popup"] = dont_ask_state
    
    try:
        with open(config_file, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Could not save config file: {e}")