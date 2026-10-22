import logging
import os
import re
import subprocess
import threading
import sys
from src import paths

class DownloaderProcess:
    """
    Manages the execution of yt-dlp.exe as a subprocess, parsing its
    output to provide real-time progress updates.
    """
    def __init__(self, url, output_path, file_type="mp4", quality="fhd", progress_callback=None, completion_callback=None):
        self.url = url
        self.output_path = output_path
        self.file_type = file_type.lower()
        self.quality = quality.lower() if quality else "fhd"
        self.progress_callback = progress_callback
        self.completion_callback = completion_callback
        
        self.process = None
        self.thread = None
        self.cancelled = False
        self.final_file_path = output_path

    def start(self):
        """Starts the download process in a new thread."""
        self.thread = threading.Thread(target=self._run_download, daemon=True)
        self.thread.start()

    def cancel(self):
        """Cancels the running download process."""
        self.cancelled = True
        if self.process and self.process.poll() is None:
            logging.info("Terminating yt-dlp process...")
            try:
                self.process.terminate()
            except Exception as e:
                logging.warning(f"Error terminating process: {e}")
            
    def _run_download(self):
        """The main logic for building and running the yt-dlp command."""
        command = self._build_command()
        logging.info(f"Executing command: {' '.join(command)}")

        try:
            creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0

            self.process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding='utf-8',
                errors='replace',
                creationflags=creationflags
            )

            # Read stdout line by line
            for line in iter(self.process.stdout.readline, ''):
                if self.cancelled:
                    break
                self._parse_output(line)

            stdout_rest, stderr_output = self.process.communicate()

            if self.cancelled:
                logging.info("Download was cancelled by user.")
                if self.completion_callback:
                    self.completion_callback(False, "Download was cancelled.", None)
                return

            if self.process.returncode == 0:
                final_path = self._locate_final_file()
                if final_path and os.path.exists(final_path) and os.path.getsize(final_path) > 0:
                    self.final_file_path = final_path
                    if self.completion_callback:
                        self.completion_callback(True, "Download finished successfully.", final_path)
                else:
                    logging.error(f"yt-dlp exited successfully but output file is missing. Stderr: {stderr_output}")
                    if self.completion_callback:
                        self.completion_callback(False, "Output file not found after download.", None)
            else:
                logging.error(f"yt-dlp process failed with code {self.process.returncode}. Stderr: {stderr_output}")
                err_message = self._extract_error(stderr_output)
                if self.completion_callback:
                    self.completion_callback(False, err_message, None)

        except FileNotFoundError:
            logging.critical(f"Cannot find yt-dlp executable at {paths.YT_DLP_PATH}")
            if self.completion_callback:
                self.completion_callback(False, "yt-dlp executable not found.", None)
        except Exception as e:
            logging.error(f"An unexpected error occurred in downloader thread: {e}", exc_info=True)
            if self.completion_callback:
                self.completion_callback(False, f"An unexpected error occurred: {e}", None)

    def _build_command(self):
        """Constructs the command-line arguments for yt-dlp."""
        ytdlp_bin = paths.YT_DLP_PATH or "yt-dlp"
        command = [
            ytdlp_bin,
            self.url,
            '--output', self.output_path,
            '--progress',
            '--newline',
            '--no-warnings',
            '--ignore-errors',
            '--prefer-insecure'
        ]

        if paths.FFMPEG_PATH and os.path.exists(paths.FFMPEG_PATH):
            command.extend(['--ffmpeg-location', paths.FFMPEG_PATH])

        if self.file_type == 'mp3':
            command.extend([
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '192K'
            ])
        else:
            # 4K or FHD
            if self.quality == '4k':
                format_str = 'bestvideo[height<=2160]+bestaudio/best[height<=2160]/best'
            else:
                format_str = 'bestvideo[height<=1080]+bestaudio/best[height<=1080]/best'
            command.extend([
                '--format', format_str,
                '--merge-output-format', 'mp4'
            ])
        
        return command

    def _parse_output(self, line):
        """
        Parses a line of output from yt-dlp to find progress information.
        Example line: [download]  15.5% of ~101.44MiB at 790.23KiB/s ETA 02:08
        """
        if not self.progress_callback:
            return

        percent_match = re.search(r'\[download\]\s+([\d\.]+)%', line)
        if percent_match:
            try:
                percent = float(percent_match.group(1))
                size_match = re.search(r'of\s+~?([\d\.]+\w+)', line)
                speed_match = re.search(r'at\s+([\d\.]+\w+/s)', line)
                eta_match = re.search(r'ETA\s+([\d:]+)', line)

                total_size = size_match.group(1) if size_match else "--"
                speed = speed_match.group(1) if speed_match else "--"
                eta = eta_match.group(1) if eta_match else "--"

                progress_info = {
                    'status': 'downloading',
                    'progress': percent / 100.0,
                    'percent': percent,
                    'total_size': total_size,
                    'speed': speed,
                    'eta': eta
                }
                self.progress_callback(progress_info)
            except Exception as e:
                logging.debug(f"Progress parse warning: {e}")

    def _locate_final_file(self):
        """Find the exact output file on disk, handling potential container changes."""
        if os.path.exists(self.output_path):
            return self.output_path

        dir_path = os.path.dirname(self.output_path)
        base_name = os.path.splitext(os.path.basename(self.output_path))[0]

        if not os.path.exists(dir_path):
            return None

        # Look for matching base name with expected extension
        expected_ext = f".{self.file_type}"
        for fname in os.listdir(dir_path):
            if fname.startswith(base_name) and fname.lower().endswith(expected_ext):
                found = os.path.join(dir_path, fname)
                try:
                    if found != self.output_path:
                        os.rename(found, self.output_path)
                        return self.output_path
                    return found
                except Exception:
                    return found

        # Fallback: look for any file with same base name created recently
        for fname in os.listdir(dir_path):
            if fname.startswith(base_name):
                return os.path.join(dir_path, fname)

        return None

    def _extract_error(self, stderr):
        """Extract a clean, user-friendly error from stderr."""
        if not stderr:
            return "Download failed due to an unknown error."
        if "Unsupported URL" in stderr:
            return "The provided URL is not supported."
        if "HTTP Error 404" in stderr:
            return "Video not found (404 Error)."
        if "Video unavailable" in stderr:
            return "This video is unavailable."
        if "Private video" in stderr:
            return "This video is private."
        if "Sign in to confirm your age" in stderr:
            return "Age-restricted video: Login required."
        
        lines = [ln.strip() for ln in stderr.strip().split('\n') if ln.strip()]
        for ln in reversed(lines):
            if "ERROR:" in ln:
                return ln.split("ERROR:", 1)[1].strip()
        return lines[-1] if lines else "Download failed."


def fetch_video_title(url):
    """Fetch video title using yt-dlp CLI without downloading."""
    ytdlp_bin = paths.YT_DLP_PATH or "yt-dlp"
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        cmd = [ytdlp_bin, "--print", "%(title)s", "--no-warnings", "--skip-download", url]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=creationflags, timeout=15)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip().split('\n')[0].strip()
    except Exception as e:
        logging.warning(f"Failed to fetch video title via CLI: {e}")
    return "video"


def fetch_playlist_entries(url):
    """
    Fetch all video entries (url and title) from a playlist without downloading.
    Returns: list of dicts [{'url': ..., 'title': ...}]
    """
    ytdlp_bin = paths.YT_DLP_PATH or "yt-dlp"
    entries = []
    try:
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
        cmd = [
            ytdlp_bin,
            "--flat-playlist",
            "--print", "%(url)s\t%(title)s",
            "--no-warnings",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, encoding='utf-8', errors='replace', creationflags=creationflags, timeout=30)
        if result.returncode == 0 and result.stdout.strip():
            for line in result.stdout.strip().split('\n'):
                parts = line.split('\t', 1)
                if len(parts) == 2:
                    v_url = parts[0].strip()
                    v_title = parts[1].strip()
                    if not v_url.startswith("http"):
                        v_url = f"https://www.youtube.com/watch?v={v_url}"
                    entries.append({'url': v_url, 'title': v_title})
                elif len(parts) == 1 and parts[0].strip():
                    v_url = parts[0].strip()
                    if not v_url.startswith("http"):
                        v_url = f"https://www.youtube.com/watch?v={v_url}"
                    entries.append({'url': v_url, 'title': 'video'})
    except Exception as e:
        logging.error(f"Failed to fetch playlist entries via CLI: {e}")
    return entries


def download_video(url, output_path, progress_callback=None, quality="fhd"):
    """
    Synchronous compatibility helper to download a video using DownloaderProcess.
    """
    file_type = "mp3" if output_path.lower().endswith(".mp3") else "mp4"
    done_event = threading.Event()
    result = {'success': False, 'message': ''}

    def _on_done(success, message, final_path):
        result['success'] = success
        result['message'] = message
        done_event.set()

    proc = DownloaderProcess(
        url=url,
        output_path=output_path,
        file_type=file_type,
        quality=quality,
        progress_callback=progress_callback,
        completion_callback=_on_done
    )
    proc.start()
    done_event.wait()
    return result['success']
