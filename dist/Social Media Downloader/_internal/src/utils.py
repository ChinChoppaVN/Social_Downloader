"""Utility functions for Social Media Downloader.

This module provides various utility functions for file operations,
configuration management, history tracking, and system integration.
"""

import os
import sys
import json
import logging
import csv
import re
from datetime import datetime
import shutil
import platform
import subprocess
import threading
import time

try:
    import yt_dlp
except ImportError:
    yt_dlp = None
from PIL import Image, ImageTk
import customtkinter as ctk
from tkinter import messagebox, filedialog

# Path configuration
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

if getattr(sys, 'frozen', False):
    # If running from packaged exe
    APP_DATA = os.path.join(os.environ['APPDATA'], "Social Media Downloader")
    DATA_DIR = os.path.join(APP_DATA, "data")
else:
    # If running from source code
    DATA_DIR = os.path.join(ROOT_DIR, "data")

# Add root directory to sys.path
if ROOT_DIR not in sys.path:
    sys.path.append(ROOT_DIR)

CONFIG_FILE = os.path.join(DATA_DIR, "config.json")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

# Ensure data directory exists
if not os.path.exists(DATA_DIR):
    os.makedirs(DATA_DIR, exist_ok=True)

def get_clean_filename(name, ext):
    """Clean and sanitize filename for safe file system operations on Windows/macOS/Linux.
    Preserves Vietnamese accented characters and natural spaces while stripping invalid chars.
    
    Args:
        name (str): Original filename
        ext (str): File extension (without dot)
        
    Returns:
        str: Cleaned filename with extension
    """
    if not name:
        return f"video.{ext}"
    
    # Remove existing extension if present
    if name.lower().endswith((".mp3", ".mp4", f".{ext.lower()}")):
        name = name.rsplit(".", 1)[0]
    
    # 1. Replace separators that are illegal in Windows filenames (/, \, |, :) with a neat hyphen
    for ch in ['/', '\\', '|', ':']:
        name = name.replace(ch, ' - ')
    
    # 2. Remove other Windows invalid characters: < > " ? *
    for ch in '<>"?*':
        name = name.replace(ch, '')
        
    # 3. Remove hashtags completely (e.g. #shorts, #trending)
    name = re.sub(r'#\S+', '', name)
    
    # 4. Remove non-printable control characters (ASCII < 32)
    name = ''.join(c for c in name if ord(c) >= 32)
    
    # 5. Normalize spaces and hyphens (preserve natural spaces, DO NOT replace with underscores)
    name = re.sub(r'(\s*-\s*)+', ' - ', name)
    name = re.sub(r'\s+', ' ', name)
    name = name.strip(' .-_')
    
    if not name:
        name = "video"
        
    # Limit length to avoid Windows MAX_PATH issues (255 chars limit)
    if len(name) > 180:
        name = name[:180].rstrip(' .-_')
        
    return f"{name}.{ext}"

def _remove_invalid_chars(name):
    """Legacy helper maintained for backward compatibility."""
    for ch in ['/', '\\', '|', ':']:
        name = name.replace(ch, ' - ')
    for ch in '<>"?*':
        name = name.replace(ch, '')
    return name

def _remove_hashtags(name):
    """Legacy helper maintained for backward compatibility."""
    return re.sub(r'#\S+', '', name)

def _normalize_spacing(name):
    """Legacy helper maintained for backward compatibility."""
    name = re.sub(r'\s+', ' ', name)
    return name.strip(' .-_')

def fetch_video_title(url):
    """Fetch video title from URL using yt-dlp CLI or library.
    
    Args:
        url (str): Video URL
        
    Returns:
        str: Cleaned video title or default name if extraction fails
    """
    from src import paths
    if paths.YT_DLP_PATH and os.path.exists(paths.YT_DLP_PATH):
        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            env = os.environ.copy()
            env['PYTHONIOENCODING'] = 'utf-8'
            env['PYTHONUTF8'] = '1'
            cmd = [paths.YT_DLP_PATH, "--encoding", "utf-8", "--print", "%(title)s", "--no-warnings", "--skip-download", url]
            res = subprocess.run(cmd, capture_output=True, env=env, creationflags=creationflags, timeout=15)
            if res.returncode == 0 and res.stdout:
                title = res.stdout.decode('utf-8', errors='replace').strip()
                if title:
                    clean_title = get_clean_filename(title.split('\n')[0].strip(), "mp3")
                    return os.path.splitext(clean_title)[0]
        except Exception as e:
            logging.debug(f"CLI title fetch failed: {e}")

    if yt_dlp is not None:
        ydl_opts = {'quiet': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                title = info.get('title', 'video_youtube')
                clean_title = get_clean_filename(title, "mp3")
                return os.path.splitext(clean_title)[0]
        except Exception as e:
            logging.error(f"Cannot fetch video title via yt_dlp library: {e}")

    return "video_youtube"

def validate_url(url):
    """Validate if URL is properly formatted and accessible.
    
    Args:
        url (str): URL to validate
        
    Returns:
        bool: True if URL appears valid, False otherwise
    """
    from urllib.parse import urlparse, parse_qs
    
    try:
        result = urlparse(url)
        
        # Basic URL structure validation
        if not all([result.scheme, result.netloc]):
            return False
        
        # Special validation for YouTube watch URLs
        if result.netloc == "www.youtube.com" and result.path == "/watch":
            query = parse_qs(result.query)
            return "v" in query
        
        # General URL validation
        return True
        
    except Exception as e:
        logging.debug(f"URL validation failed: {e}")
        return False

def load_last_folder():
    """Load the last used folder from config.json.
    
    Returns:
        str: Path to last used folder or user home directory as fallback
    """
    default_folder = os.path.expanduser("~")
    
    if not os.path.exists(CONFIG_FILE):
        return default_folder
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            # Try 'last_folder' first, then fallback to 'folder', then default
            return config.get("last_folder", config.get("folder", default_folder))
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Config file error, using default folder: {e}")
        return default_folder

def save_last_folder(folder):
    """Save the last used folder to config.json.
    
    Args:
        folder (str): Path to folder to save
    """
    config = _load_config_safe()
    config["last_folder"] = folder
    _save_config_safe(config)

def _load_config_safe():
    """Safely load configuration from file."""
    if not os.path.exists(CONFIG_FILE):
        return {}
        
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.warning(f"Config file error, creating new: {e}")
        return {}

def _save_config_safe(config):
    """Safely save configuration to file."""
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=4)
    except IOError as e:
        logging.error(f"Cannot save config file: {e}")

def get_download_history():
    """Get download history from file.
    
    Returns:
        list: List of download history entries
    """
    if not os.path.exists(HISTORY_FILE):
        return []
        
    try:
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError) as e:
        logging.error(f"Error reading history: {e}")
        return []

def add_download_history(url, file_type, file_path, size="Unknown", status="Success", folder_path="Unknown"):
    """Add an entry to download history.
    
    Args:
        url (str): Download URL
        file_type (str): File type (mp3/mp4)
        file_path (str): Path to downloaded file
        size (str): File size as string
        status (str): Download status
        folder_path (str): Folder containing the file
    """
    try:
        history = get_download_history()
        history.append({
            "url": url,
            "file_type": file_type,
            "file_path": file_path,
            "size": size,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "status": status,
            "folder_path": folder_path
        })
        _save_history_safe(history)
    except Exception as e:
        logging.error(f"Error adding to history: {e}")

def clear_download_history():
    """Clear all download history."""
    _save_history_safe([])

def _save_history_safe(history):
    """Safely save history to file."""
    try:
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history, f, ensure_ascii=False, indent=4)
    except IOError as e:
        logging.error(f"Error saving history: {e}")

def export_download_history(export_path):
    """Export download history to CSV file.
    
    Args:
        export_path (str): Path where CSV file will be saved
        
    Returns:
        bool: True if export successful, False otherwise
    """
    try:
        history = get_download_history()
        if not history:
            return False
            
        with open(export_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.writer(f)
            # Write CSV headers
            writer.writerow(["URL", "File Type", "File Path", "Size", "Timestamp", "Status", "Folder Path"])
            
            # Write history entries
            for entry in history:
                writer.writerow([
                    entry["url"],
                    entry["file_type"],
                    entry["file_path"],
                    entry.get("size", "Unknown"),
                    entry["timestamp"],
                    entry.get("status", "Success"),
                    entry.get("folder_path", "Unknown")
                ])
        return True
    except Exception as e:
        logging.error(f"Error exporting history: {e}")
        return False

def is_path_writable(path):
    """Check if a file or directory path is genuinely writable on Windows."""
    try:
        if not path:
            return False
        d = path if os.path.isdir(path) else os.path.dirname(path)
        if not d:
            d = "."
        if not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        test_file = os.path.join(d, f".write_test_{os.getpid()}_{int(time.time()*1000)}.tmp")
        with open(test_file, "w") as f:
            f.write("test")
        try:
            os.remove(test_file)
        except Exception:
            pass
        return True
    except Exception:
        return False

def get_user_bin_ytdlp_path():
    """Get the user-writable path for yt-dlp in AppData."""
    app_data = os.environ.get('APPDATA', '')
    if not app_data:
        app_data = os.path.expanduser("~")
    user_bin = os.path.join(app_data, "Social Media Downloader", "bin")
    try:
        os.makedirs(user_bin, exist_ok=True)
    except Exception:
        pass
    return os.path.join(user_bin, "yt-dlp.exe")

def get_ytdlp_update_path(preferred_path=None):
    """Determine the optimal writable destination for yt-dlp.exe.
    
    If preferred_path is provided and its directory is writable, returns preferred_path.
    Otherwise, falls back to AppData/bin which is always writable without Admin rights.
    """
    if preferred_path and is_path_writable(preferred_path):
        return preferred_path
    return get_user_bin_ytdlp_path()

def download_yt_dlp(dest_path=None, progress_callback=None, new_version=None):
    """Download latest yt-dlp.exe from GitHub with fallbacks and auto-privilege handling.
    
    Args:
        dest_path (str, optional): Target destination. If not provided or not writable,
                                   falls back to user AppData/bin automatically.
        progress_callback (callable, optional): (downloaded_bytes, total_bytes) -> None
        new_version (str, optional): Version tag if known (e.g. '2026.10.21')
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    target_path = get_ytdlp_update_path(dest_path)
    logging.info(f"Downloading yt-dlp to: {target_path} (requested: {dest_path})")

    # List candidate URLs to try in order
    urls = [
        "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    ]
    if new_version:
        urls.insert(0, f"https://github.com/yt-dlp/yt-dlp/releases/download/{new_version}/yt-dlp.exe")
    urls.append("https://github.com/yt-dlp/yt-dlp-nightly-builds/releases/latest/download/yt-dlp.exe")

    target_dir = os.path.dirname(target_path)
    os.makedirs(target_dir, exist_ok=True)
    temp_path = target_path + f".tmp_{int(time.time()*1000)}"

    import urllib.request
    import ssl

    last_error = None
    success = False

    for url in urls:
        logging.info(f"Trying download from URL: {url}")
        for use_unverified_ssl in (False, True):
            try:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Accept": "*/*"
                }
                req = urllib.request.Request(url, headers=headers)
                
                ssl_context = None
                if use_unverified_ssl:
                    ssl_context = ssl._create_unverified_context()

                with urllib.request.urlopen(req, timeout=45, context=ssl_context) as response:
                    total_size = int(response.headers.get('Content-Length', 0))
                    downloaded_size = 0
                    
                    with open(temp_path, 'wb') as file:
                        while True:
                            chunk = response.read(65536)
                            if not chunk:
                                break
                            file.write(chunk)
                            downloaded_size += len(chunk)
                            if progress_callback:
                                try:
                                    progress_callback(downloaded_size, total_size)
                                except Exception:
                                    pass

                # Check if download is valid (> 5MB)
                if os.path.exists(temp_path) and os.path.getsize(temp_path) > 5 * 1024 * 1024:
                    success = True
                    break
                else:
                    if os.path.exists(temp_path):
                        try:
                            os.remove(temp_path)
                        except Exception:
                            pass
                    last_error = "File tải về dung lượng không hợp lệ."
            except Exception as e:
                last_error = str(e)
                logging.warning(f"Download attempt failed from {url} (unverified_ssl={use_unverified_ssl}): {e}")
                if os.path.exists(temp_path):
                    try:
                        os.remove(temp_path)
                    except Exception:
                        pass
        if success:
            break

    if not success:
        return False, f"Không thể tải yt-dlp từ máy chủ: {last_error}"

    # Replace target_path with temp_path safely
    try:
        if os.path.exists(target_path):
            old_backup = target_path + f".old_{int(time.time()*1000)}"
            try:
                os.replace(target_path, old_backup)
                try:
                    os.remove(old_backup)
                except Exception:
                    pass
            except Exception:
                try:
                    os.remove(target_path)
                except Exception:
                    pass
        os.replace(temp_path, target_path)
    except Exception as e:
        try:
            shutil.copy2(temp_path, target_path)
            try:
                os.remove(temp_path)
            except Exception:
                pass
        except Exception as copy_e:
            return False, f"Không thể lưu file yt-dlp: {copy_e}"

    # Update runtime paths
    from src import paths
    paths.YT_DLP_PATH = target_path
    bin_dir = os.path.dirname(target_path)
    if bin_dir not in os.environ.get("PATH", ""):
        os.environ["PATH"] = bin_dir + os.pathsep + os.environ.get("PATH", "")

    logging.info(f"yt-dlp successfully updated to: {target_path} ({os.path.getsize(target_path)} bytes)")
    return True, None