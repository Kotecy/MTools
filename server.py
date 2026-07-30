#!/usr/bin/env python3
"""
MTools — медиа-инструменты в браузере.
- Обрезка видео/аудио через ffmpeg.wasm
- YouTube Download через yt-dlp
- Всё работает локально, файлы никуда не отправляются

Запуск:  python server.py
"""
import sys
import json
import os
import re
import tempfile
import http.server
import socketserver
from socketserver import ThreadingMixIn
import urllib.parse
import webbrowser
import threading
from pathlib import Path

# PyInstaller resource path
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

os.chdir(BASE_DIR)
os.environ['PYTHONIOENCODING'] = 'utf-8'
# Redirect stderr to avoid crashes in no-console mode
if not sys.stderr:
    sys.stderr = open(os.devnull, 'w')

# ── Find free port ─────────────────────────────────────────────
def find_free_port(start=8000):
    for port in range(start, start + 100):
        try:
            s = ThreadedHTTPServer(("", port), APIHandler)
            s.server_close()
            return port
        except OSError:
            continue
    return start


# ── Formatting ─────────────────────────────────────────────────
def format_duration(seconds):
    if not seconds:
        return "\u2014"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


def format_views(count):
    if not count:
        return "\u2014"
    if count >= 1_000_000:
        return f"{count / 1_000_000:.1f}M"
    if count >= 1_000:
        return f"{count / 1_000:.1f}K"
    return str(count)


# ── HTTP Handler ───────────────────────────────────────────────
HTTPD_INSTANCE = [None]
HEARTBEAT_TIMER = [None]
SHUTDOWN_DELAY = 15  # seconds without heartbeat before shutdown

class APIHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    # Suppress logging in no-console mode (prevents crash when sys.stderr is None)
    def log_message(self, format, *args):
        pass

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/api/youtube/info":
            self._handle_youtube_info(parsed)
        elif parsed.path == "/api/youtube/download":
            self._handle_youtube_download_get(parsed)
        elif parsed.path == "/api/heartbeat":
            self._handle_heartbeat()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/youtube/download":
            self._handle_youtube_download()
        elif self.path == "/api/shutdown":
            self._handle_shutdown()
        else:
            self.send_error(404)

    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(204)
        self.end_headers()

    # ── YouTube Info ───────────────────────────────────────────
    def _handle_youtube_info(self, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        url = params.get("url", [None])[0]
        if not url:
            self._send_json({"error": "Parameter url is required"}, 400)
            return
        try:
            from yt_dlp import YoutubeDL
            ydl_opts = {"quiet": True, "no_warnings": True, "extract_flat": False}
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
            data = {
                "title": info.get("title", "\u2014"),
                "channel": info.get("channel", info.get("uploader", "\u2014")),
                "duration": format_duration(info.get("duration")),
                "duration_raw": info.get("duration"),
                "views": format_views(info.get("view_count")),
                "thumbnail": info.get("thumbnail", ""),
                "webpage_url": info.get("webpage_url", url),
            }
            self._send_json(data)
        except ImportError:
            self._send_json({"error": "yt-dlp not installed"}, 500)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    # ── YouTube Download ───────────────────────────────────────
    def _handle_youtube_download(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            ctype = self.headers.get("Content-Type", "")
            if "application/json" in ctype:
                data = json.loads(body)
            else:
                data = urllib.parse.parse_qs(body)
                data = {k: v[0] if isinstance(v, list) else v for k, v in data.items()}
        except Exception:
            self._send_json({"error": "Invalid request"}, 400)
            return
        url = data.get("url")
        fmt = data.get("format", "mp4")
        quality = data.get("quality", "best")
        if not url:
            self._send_json({"error": "Parameter url is required"}, 400)
            return
        tmp_dir = tempfile.mkdtemp(prefix="mtools_yt_")
        try:
            from yt_dlp import YoutubeDL
            if fmt == "mp3":
                format_spec = "bestaudio/best"
                postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
                outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
            else:
                quality_map = {
                    "best": "bestvideo+bestaudio/best",
                    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                }
                format_spec = quality_map.get(quality, "bestvideo+bestaudio/best")
                postprocessors = []
                outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
            ydl_opts = {
                "format": format_spec,
                "outtmpl": outtmpl,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": postprocessors,
                "merge_output_format": "mp4" if fmt == "mp4" else None,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "video")
            ext = "mp3" if fmt == "mp3" else "mp4"
            files = list(Path(tmp_dir).iterdir())
            downloaded = None
            for f in files:
                if f.suffix == f".{ext}":
                    downloaded = f
                    break
            if not downloaded:
                downloaded = files[0] if files else None
            if not downloaded or not downloaded.exists():
                self._send_json({"error": "Downloaded file not found"}, 500)
                return
            file_size = downloaded.stat().st_size
            safe_title = re.sub(r'[^\w\-_\. ]', '_', title)
            suggested_name = f"{safe_title}.{ext}"
            self.send_response(200)
            self.send_header("Content-Type", {
                "mp4": "video/mp4", "mp3": "audio/mpeg",
            }.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Disposition", f'attachment; filename="{suggested_name}"')
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()
            BUFSIZE = 65536
            with open(downloaded, "rb") as f:
                while True:
                    chunk = f.read(BUFSIZE)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            for f in Path(tmp_dir).iterdir():
                try: f.unlink()
                except: pass
            try: os.rmdir(tmp_dir)
            except: pass
        except ImportError:
            self._send_json({"error": "yt-dlp not installed"}, 500)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
            try:
                for f in Path(tmp_dir).iterdir(): f.unlink()
                os.rmdir(tmp_dir)
            except: pass

    def _handle_heartbeat(self):
        self._send_json({"ok": True})
        if HEARTBEAT_TIMER[0]:
            HEARTBEAT_TIMER[0].cancel()
        HEARTBEAT_TIMER[0] = threading.Timer(SHUTDOWN_DELAY, do_shutdown)
        HEARTBEAT_TIMER[0].daemon = True
        HEARTBEAT_TIMER[0].start()

    def _handle_youtube_download_get(self, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        url = params.get("url", [None])[0]
        fmt = params.get("format", ["mp4"])[0]
        quality = params.get("quality", ["best"])[0]
        if not url:
            self._send_json({"error": "Parameter url is required"}, 400)
            return
        tmp_dir = tempfile.mkdtemp(prefix="mtools_yt_")
        try:
            from yt_dlp import YoutubeDL
            if fmt == "mp3":
                format_spec = "bestaudio/best"
                postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
                outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
                merge = None
                ext = "mp3"
            else:
                quality_map = {
                    "best": "bestvideo+bestaudio/best",
                    "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
                    "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                    "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
                    "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                }
                format_spec = quality_map.get(quality, "bestvideo+bestaudio/best")
                postprocessors = []
                outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
                merge = "mp4"
                ext = "mp4"
            ydl_opts = {
                "format": format_spec,
                "outtmpl": outtmpl,
                "quiet": True,
                "no_warnings": True,
                "postprocessors": postprocessors,
                "merge_output_format": merge,
            }
            with YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "video")
            files = list(Path(tmp_dir).iterdir())
            downloaded = None
            for f in files:
                if f.suffix == f".{ext}":
                    downloaded = f
                    break
            if not downloaded:
                downloaded = files[0] if files else None
            if not downloaded or not downloaded.exists():
                self._send_json({"error": "Downloaded file not found"}, 500)
                return
            file_size = downloaded.stat().st_size
            safe_title = re.sub(r'[^\w\-_\. ]', '_', title)
            suggested_name = f"{safe_title}.{ext}"
            self.send_response(200)
            self.send_header("Content-Type", {
                "mp4": "video/mp4", "mp3": "audio/mpeg",
            }.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Disposition", f'attachment; filename="{suggested_name}"')
            self.end_headers()
            BUFSIZE = 65536
            with open(downloaded, "rb") as f:
                while True:
                    chunk = f.read(BUFSIZE)
                    if not chunk:
                        break
                    self.wfile.write(chunk)
            for f in Path(tmp_dir).iterdir():
                try: f.unlink()
                except: pass
            try: os.rmdir(tmp_dir)
            except: pass
        except ImportError:
            try:
                self.send_error(500, "yt-dlp not installed")
            except: pass
        except Exception as e:
            try:
                self._send_json({"error": str(e)}, 500)
            except: pass
            try:
                for f in Path(tmp_dir).iterdir(): f.unlink()
                os.rmdir(tmp_dir)
            except: pass

    def _handle_shutdown(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"shutdown")
        if HEARTBEAT_TIMER[0]:
            HEARTBEAT_TIMER[0].cancel()
        threading.Thread(target=do_shutdown, daemon=True).start()

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)


# ── Threaded HTTP Server ──────────────────────────────────────
class ThreadedHTTPServer(ThreadingMixIn, socketserver.TCPServer):
    daemon_threads = True


# ── Shutdown helper ────────────────────────────────────────────
def do_shutdown():
    httpd = HTTPD_INSTANCE[0]
    if httpd:
        httpd.shutdown()


# ── Main ───────────────────────────────────────────────────────
def open_browser(url, delay=1.5):
    def _open():
        import time
        time.sleep(delay)
        webbrowser.open(url)
    threading.Thread(target=_open, daemon=True).start()


if __name__ == "__main__":
    port = find_free_port()
    url = f"http://localhost:{port}/"

    httpd = ThreadedHTTPServer(("", port), APIHandler)
    HTTPD_INSTANCE[0] = httpd
    open_browser(url)

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    except OSError:
        pass
    finally:
        httpd.server_close()
        os._exit(0)
