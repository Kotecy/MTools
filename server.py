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
import time
import traceback
import tempfile
import http.server
import socketserver
from socketserver import ThreadingMixIn
import urllib.parse
import webbrowser
import threading
import uuid
from pathlib import Path

# PyInstaller resource path
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).parent

os.chdir(BASE_DIR)
os.environ['PYTHONIOENCODING'] = 'utf-8'

ERROR_LOG_PATH = BASE_DIR / "mtools_error.log"

def log_error(context, exc):
    """Write the real exception (with traceback) to a log file and, if
    available, to stderr. Without this, exceptions raised mid-download
    (e.g. antivirus locking the file, or yt-dlp/ffmpeg failures) vanish
    silently and only show up in the browser as a vague network error."""
    msg = f"\n[{time.strftime('%Y-%m-%d %H:%M:%S')}] Error in {context}:\n"
    msg += "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        with open(ERROR_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(msg)
    except OSError:
        pass
    try:
        if sys.stderr:
            sys.stderr.write(msg)
    except Exception:
        pass

# ffmpeg for yt-dlp: use bundled in frozen EXE (if exists), else system
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys._MEIPASS)
    bundled_ffmpeg = BASE_DIR / "ffmpeg.exe"
    debug_log = BASE_DIR.parent / "mtools_debug.log"
    debug_lines = [
        f"[DEBUG] BASE_DIR: {BASE_DIR}",
        f"[DEBUG] bundled_ffmpeg: {bundled_ffmpeg}",
        f"[DEBUG] exists: {bundled_ffmpeg.exists()}",
    ]
    if not bundled_ffmpeg.exists():
        alt_paths = [
            BASE_DIR / "ffmpeg",
            BASE_DIR.parent / "ffmpeg.exe",
            Path(sys.executable).parent / "ffmpeg.exe",
        ]
        for p in alt_paths:
            debug_lines.append(f"[DEBUG] checking alt: {p} -> {p.exists()}")
            if p.exists():
                bundled_ffmpeg = p
                break
    FFMPEG_PATH = str(bundled_ffmpeg) if bundled_ffmpeg.exists() else None
    debug_lines.append(f"[DEBUG] FFMPEG_PATH: {FFMPEG_PATH}")
    # Overwrite (not append) each run — this log only exists to diagnose
    # ffmpeg-path detection on startup, so it doesn't need to grow forever.
    try:
        with open(debug_log, "w", encoding="utf-8") as f:
            f.write("\n".join(debug_lines) + "\n")
    except OSError:
        pass
    if FFMPEG_PATH:
        os.environ['PATH'] = str(BASE_DIR) + os.pathsep + os.environ.get('PATH', '')
else:
    BASE_DIR = Path(__file__).parent
    FFMPEG_PATH = None

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


# ── Content-Disposition with non-ASCII (e.g. Cyrillic) filenames ──
# HTTP header VALUES must be Latin-1 encodable. A YouTube title in
# Russian (or any non-Latin script) breaks a naive
# `filename="{title}.mp4"` header with UnicodeEncodeError, which used to
# happen mid-response (after Content-Length was already sent), corrupting
# the stream and showing up in the browser as
# net::ERR_CONTENT_LENGTH_MISMATCH. Fix: send both a plain ASCII fallback
# name and the real name percent-encoded per RFC 5987 (filename*=UTF-8'').
def content_disposition_value(filename):
    ascii_fallback = re.sub(r'[^\w\-. ]', '_', filename)
    ascii_fallback = ascii_fallback.encode('ascii', 'ignore').decode('ascii').strip() or 'download'
    encoded = urllib.parse.quote(filename, safe='')
    return f'attachment; filename="{ascii_fallback}"; filename*=UTF-8\'\'{encoded}'


# ── Progress-trackable YouTube download jobs ──────────────────
# Downloading + converting can take a while, and the user has no way to
# tell it's actually progressing vs. hung. So downloads run in a
# background thread that reports live progress (bytes downloaded, %,
# speed, ETA) via yt-dlp's progress_hooks, which the frontend polls.
DOWNLOAD_JOBS = {}
DOWNLOAD_JOBS_LOCK = threading.Lock()


def build_ydl_opts(fmt, quality, outtmpl, progress_hooks=None, postprocessor_hooks=None):
    if fmt == "mp3":
        format_spec = "bestaudio/best"
        postprocessors = [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3"}]
        merge = None
        ext = "mp3"
    else:
        quality_map = {
            "best": "bestvideo+bestaudio/best",
            "2160p": "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
            "1440p": "bestvideo[height<=1440]+bestaudio/best[height<=1440]",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p": "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p": "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "360p": "bestvideo[height<=360]+bestaudio/best[height<=360]",
        }
        format_spec = quality_map.get(quality, "bestvideo[height<=1080]+bestaudio/best[height<=1080]")
        postprocessors = []
        merge = "mp4"
        ext = "mp4"
    opts = {
        "format": format_spec,
        "outtmpl": outtmpl,
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "postprocessors": postprocessors,
        "merge_output_format": merge,
        "ffmpeg_location": FFMPEG_PATH,
        # Large/4K downloads are split into many fragments; a transient
        # network hiccup on any single fragment used to bubble up as a
        # hard failure ("Got error: timed out"). Give yt-dlp room to
        # retry instead of giving up immediately.
        "socket_timeout": 30,
        "retries": 20,
        "fragment_retries": 20,
    }
    if progress_hooks:
        opts["progress_hooks"] = progress_hooks
    if postprocessor_hooks:
        opts["postprocessor_hooks"] = postprocessor_hooks
    return opts, ext


def cleanup_tmp_dir(tmp_dir):
    try:
        for f in Path(tmp_dir).iterdir():
            try: f.unlink()
            except: pass
        os.rmdir(tmp_dir)
    except: pass


def run_download_job(job_id, url, fmt, quality):
    tmp_dir = tempfile.mkdtemp(prefix="mtools_yt_")
    with DOWNLOAD_JOBS_LOCK:
        DOWNLOAD_JOBS[job_id] = {
            "status": "starting", "downloaded": 0, "total": None, "percent": 0,
            "speed": None, "eta": None, "error": None, "tmp_dir": tmp_dir,
            "file_path": None, "filename": None, "ext": None,
        }

    def progress_hook(d):
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if not job:
                return
            if d.get("status") == "downloading":
                downloaded = d.get("downloaded_bytes") or 0
                total = d.get("total_bytes") or d.get("total_bytes_estimate")
                job["status"] = "downloading"
                job["downloaded"] = downloaded
                job["total"] = total
                job["percent"] = round(downloaded / total * 100, 1) if total else None
                job["speed"] = d.get("speed")
                job["eta"] = d.get("eta")
            elif d.get("status") == "finished":
                job["status"] = "processing"

    def pp_hook(d):
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if job and d.get("status") == "started":
                job["status"] = "processing"

    try:
        outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
        ydl_opts, ext = build_ydl_opts(
            fmt, quality, outtmpl,
            progress_hooks=[progress_hook], postprocessor_hooks=[pp_hook],
        )
        from yt_dlp import YoutubeDL
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "video")
        files = list(Path(tmp_dir).iterdir())
        candidates = [f for f in files if f.suffix == f".{ext}"]
        downloaded_file = (
            max(candidates, key=lambda f: f.stat().st_size) if candidates
            else (max(files, key=lambda f: f.stat().st_size) if files else None)
        )
        if not downloaded_file or not downloaded_file.exists():
            raise RuntimeError("Downloaded file not found")
        file_size = wait_for_stable_file(downloaded_file)
        safe_title = re.sub(r'[^\w\-_\. ]', '_', title)
        suggested_name = f"{safe_title}.{ext}"
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if job:
                job.update({
                    "status": "finished", "percent": 100,
                    "file_path": downloaded_file, "filename": suggested_name,
                    "ext": ext, "total": file_size, "downloaded": file_size,
                })
    except ImportError:
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if job:
                job["status"] = "error"
                job["error"] = "yt-dlp not installed"
        cleanup_tmp_dir(tmp_dir)
    except Exception as e:
        log_error("run_download_job", e)
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if job:
                job["status"] = "error"
                job["error"] = str(e)
        cleanup_tmp_dir(tmp_dir)


# ── Wait for a just-written file to be stable and unlocked ────
# On Windows, antivirus real-time scanning can briefly lock a file right
# after it's written, and buffered writes from ffmpeg/yt-dlp may not be
# flushed to disk the instant the process returns. If we trust stat()
# immediately, the Content-Length we send can be larger than what we can
# actually read, and the browser aborts the download with
# net::ERR_CONTENT_LENGTH_MISMATCH. So: poll until the size stops
# changing AND the file can be opened for reading before trusting it.
def wait_for_stable_file(path, tries=40, delay=0.25):
    last_size = -1
    for _ in range(tries):
        try:
            size = path.stat().st_size
        except OSError:
            time.sleep(delay)
            continue
        if size == last_size and size > 0:
            try:
                with open(path, "rb"):
                    pass
            except PermissionError:
                time.sleep(delay)
                continue
            return size
        last_size = size
        time.sleep(delay)
    # Give up waiting for stability, return whatever we last saw
    try:
        return path.stat().st_size
    except OSError:
        return last_size if last_size > 0 else 0


# ── Guaranteed full write to a (possibly unbuffered) socket file ──
# BaseHTTPRequestHandler's wfile defaults to unbuffered (wbufsize=0),
# meaning write() wraps the raw socket directly and is allowed to send
# fewer bytes than requested (a partial write). If we don't loop until
# everything is actually sent, the client receives fewer bytes than the
# Content-Length we promised, and the browser aborts the download with
# net::ERR_CONTENT_LENGTH_MISMATCH.
def send_all(wfile, data):
    view = memoryview(data)
    total_sent = 0
    while total_sent < len(view):
        sent = wfile.write(view[total_sent:])
        if not sent:
            raise ConnectionError("Socket write returned 0/None — connection likely closed")
        total_sent += sent


# ── HTTP Handler ───────────────────────────────────────────────
HTTPD_INSTANCE = [None]
SHUTDOWN_TIMER = [None]
SHUTDOWN_TIMER_LOCK = threading.Lock()
# How long to wait after the tab reports "closing" before actually exiting.
# A page reload also triggers the same "closing" signal (via pagehide), so
# this grace period exists purely to let a reload's fresh page cancel the
# pending shutdown before it fires — it is NOT an idle/inactivity timeout.
SHUTDOWN_GRACE_SECONDS = 10

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
        elif parsed.path == "/api/youtube/progress":
            self._handle_youtube_progress(parsed)
        elif parsed.path == "/api/youtube/download/file":
            self._handle_youtube_download_file(parsed)
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/youtube/download/start":
            self._handle_youtube_download_start()
        elif self.path == "/api/tab-closing":
            self._handle_tab_closing()
        elif self.path == "/api/cancel-shutdown":
            self._handle_cancel_shutdown()
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
            ydl_opts = {
                "quiet": True, "no_warnings": True, "extract_flat": False,
                "noplaylist": True, "socket_timeout": 30, "retries": 20,
            }
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
            log_error("_handle_youtube_info", e)
            self._send_json({"error": str(e)}, 500)

    # ── YouTube Download with progress (job-based) ─────────────
    def _handle_youtube_download_start(self):
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
        job_id = uuid.uuid4().hex
        threading.Thread(
            target=run_download_job, args=(job_id, url, fmt, quality), daemon=True,
        ).start()
        self._send_json({"job_id": job_id})

    def _handle_youtube_progress(self, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        job_id = params.get("id", [None])[0]
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if not job:
                self._send_json({"error": "Unknown job"}, 404)
                return
            self._send_json({
                "status": job["status"],
                "downloaded": job["downloaded"],
                "total": job["total"],
                "percent": job["percent"],
                "speed": job["speed"],
                "eta": job["eta"],
                "error": job["error"],
            })

    def _handle_youtube_download_file(self, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        job_id = params.get("id", [None])[0]
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
        if not job:
            self._send_json({"error": "Unknown job"}, 404)
            return
        if job["status"] == "error":
            self._send_json({"error": job["error"] or "Download failed"}, 500)
            with DOWNLOAD_JOBS_LOCK:
                DOWNLOAD_JOBS.pop(job_id, None)
            cleanup_tmp_dir(job["tmp_dir"])
            return
        if job["status"] != "finished":
            self._send_json({"error": "Not ready yet"}, 409)
            return
        downloaded_file = job["file_path"]
        file_size = job["total"]
        suggested_name = job["filename"]
        ext = job["ext"]
        headers_sent = False
        try:
            self.send_response(200)
            self.send_header("Content-Type", {
                "mp4": "video/mp4", "mp3": "audio/mpeg",
            }.get(ext, "application/octet-stream"))
            self.send_header("Content-Length", str(file_size))
            self.send_header("Content-Disposition", content_disposition_value(suggested_name))
            self.end_headers()
            headers_sent = True
            BUFSIZE = 65536
            sent = 0
            with open(downloaded_file, "rb") as f:
                while sent < file_size:
                    chunk = f.read(min(BUFSIZE, file_size - sent))
                    if not chunk:
                        break
                    send_all(self.wfile, chunk)
                    sent += len(chunk)
        except Exception as e:
            log_error("_handle_youtube_download_file (streaming)", e)
            if not headers_sent:
                self._send_json({"error": str(e)}, 500)
            return
        finally:
            with DOWNLOAD_JOBS_LOCK:
                DOWNLOAD_JOBS.pop(job_id, None)
            cleanup_tmp_dir(job["tmp_dir"])

    def _handle_tab_closing(self):
        # Fired via navigator.sendBeacon on pagehide (real tab close,
        # reload, or navigation-away). Schedule a shutdown after a short
        # grace period rather than exiting immediately, so a reload's new
        # page load (which arrives well under the grace period) can cancel
        # it via /api/cancel-shutdown.
        self._send_json({"ok": True})
        with SHUTDOWN_TIMER_LOCK:
            if SHUTDOWN_TIMER[0]:
                SHUTDOWN_TIMER[0].cancel()
            SHUTDOWN_TIMER[0] = threading.Timer(SHUTDOWN_GRACE_SECONDS, do_shutdown)
            SHUTDOWN_TIMER[0].daemon = True
            SHUTDOWN_TIMER[0].start()

    def _handle_cancel_shutdown(self):
        # Called once at page load. If a shutdown was scheduled by a
        # pagehide from the page being reloaded, cancel it — the app is
        # still in use.
        self._send_json({"ok": True})
        with SHUTDOWN_TIMER_LOCK:
            if SHUTDOWN_TIMER[0]:
                SHUTDOWN_TIMER[0].cancel()
                SHUTDOWN_TIMER[0] = None

    def _handle_shutdown(self):
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()
        self.wfile.write(b"shutdown")
        with SHUTDOWN_TIMER_LOCK:
            if SHUTDOWN_TIMER[0]:
                SHUTDOWN_TIMER[0].cancel()
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