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

import yt_dlp
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
    """Clean and sanitize filename for safe file system operations.
    
    Args:
        name (str): Original filename
        ext (str): File extension (without dot)
        
    Returns:
        str: Cleaned filename with extension
    """
    if not name:
        return f"video.{ext}"
    
    # Remove existing extension if present
    if name.lower().endswith((".mp3", ".mp4")):
        name = name.rsplit(".", 1)[0]
    
    # Remove invalid filesystem characters
    name = _remove_invalid_chars(name)
    
    # Remove hashtags completely
    name = _remove_hashtags(name)
    
    # Replace spaces with underscores and clean up
    name = _normalize_spacing(name)
    
    return f"{name}.{ext}" if name else f"video.{ext}"

def _remove_invalid_chars(name):
    """Remove characters that are invalid in filenames."""
    invalid_chars = '<>:"/\\|?!*.-'
    for char in invalid_chars:
        name = name.replace(char, '')
    return name

def _remove_hashtags(name):
    """Remove hashtags from filename."""
    result = []
    i = 0
    while i < len(name):
        if name[i] == '#' and i + 1 < len(name):
            # Skip hashtag and following alphanumeric characters
            j = i + 1
            while j < len(name) and (name[j].isalnum() or name[j] == '_'):
                j += 1
            i = j
        else:
            result.append(name[i])
            i += 1
    return ''.join(result)

def _normalize_spacing(name):
    """Normalize spaces and underscores in filename."""
    # Replace spaces with underscores
    name = name.replace(" ", "_")
    
    # Merge consecutive underscores into single underscore
    while "__" in name:
        name = name.replace("__", "_")
    
    # Remove leading and trailing underscores
    name = name.strip("_")
    
    return name

def fetch_video_title(url):
    """Fetch video title from URL using yt-dlp.
    
    Args:
        url (str): Video URL
        
    Returns:
        str: Cleaned video title or default name if extraction fails
    """
    ydl_opts = {'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            title = info.get('title', 'video_youtube')
            # Clean title before returning
            clean_title = get_clean_filename(title, "mp3")
            return os.path.splitext(clean_title)[0]  # Remove extension to avoid conflicts
    except Exception as e:
        logging.error(f"Cannot fetch video title: {e}")
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

def download_yt_dlp(dest_path, progress_callback=None):
    """Download latest yt-dlp.exe from GitHub to dest_path.
    
    Args:
        dest_path (str): Destination path for yt-dlp.exe
        progress_callback (callable, optional): Callback function for progress updates
        
    Returns:
        tuple: (success: bool, error_message: str or None)
    """
    import requests
    
    url = "https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp.exe"
    
    try:
        with requests.get(url, stream=True, timeout=60) as response:
            response.raise_for_status()
            
            total_size = int(response.headers.get('content-length', 0))
            downloaded_size = 0
            
            with open(dest_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        file.write(chunk)
                        downloaded_size += len(chunk)
                        
                        # Call progress callback if provided
                        if progress_callback:
                            progress_callback(downloaded_size, total_size)
                            
        return True, None
        
    except Exception as e:
        logging.error(f"Error downloading yt-dlp: {e}")
        return False, str(e)