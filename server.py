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
import urllib.request
import webbrowser
import threading
import uuid
import shutil
import zipfile
import hashlib
import platform
from pathlib import Path

try:
    from yt_dlp.utils import DownloadCancelled
except ImportError:
    DownloadCancelled = None

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
    FFMPEG_PATH = None

# Redirect stderr to avoid crashes in no-console mode
if not sys.stderr:
    sys.stderr = open(os.devnull, 'w')


# ── Optional YouTube cookies config ────────────────────────────
# YouTube increasingly requires proof of "not a bot" for some videos, which
# yt-dlp can usually satisfy either by trying a different internal player
# client (no setup needed, tried automatically below) or, if that still
# isn't enough, by using cookies from a real logged-in browser session.
# Cookie use is opt-in only — we never read a browser's cookie store
# unless the user explicitly asks for it here, since that's sensitive data.
#
# To enable: create "mtools_config.json" next to this file, e.g.:
#   {"youtube_cookies_browser": "chrome"}          (chrome/edge/firefox/brave/opera/vivaldi)
#   {"youtube_cookies_file": "C:\\path\\to\\cookies.txt"}   (exported via a browser extension)
CONFIG_PATH = BASE_DIR / "mtools_config.json"

# UI settings (language, behavior toggles) live in a fixed per-user folder —
# NOT in localStorage: the server picks a new port whenever 8000 is busy and
# localStorage is per-origin (localhost:8000 ≠ localhost:8001), so browser
# storage silently forgets everything between launches.
UI_SETTINGS_PATH = Path(os.environ.get("APPDATA", str(Path.home()))) / "MTools" / "ui_settings.json"

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return {}

def save_config(cfg):
    try:
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass

APP_CONFIG = load_config()

# Where the auto-installer puts ffmpeg — a per-user folder that never
# needs admin rights, independent of where MTools itself is installed.
FFMPEG_INSTALL_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "MTools" / "ffmpeg"


# ── yt-dlp auto-updater ───────────────────────────────────────
# YouTube constantly changes its anti-bot protection, so a stale yt-dlp
# quickly breaks downloads (e.g. HTTP 403). The frozen EXE bundles a fixed
# yt-dlp, but we let the user pull a newer one without reinstalling the whole
# app: the latest yt-dlp wheel is downloaded into a per-user folder and
# prepended to sys.path, overriding the bundled copy on the next launch.
YTDLP_PATCH_DIR = Path(os.environ.get("APPDATA", str(Path.home()))) / "MTools" / "yt_dlp_patch"
YTDLP_PYPI_API = "https://pypi.org/pypi/yt-dlp/json"

if YTDLP_PATCH_DIR.is_dir():
    # Take precedence over the bundled copy for any future `import yt_dlp`.
    sys.path.insert(0, str(YTDLP_PATCH_DIR))


def detect_ffmpeg():
    """Look for a usable ffmpeg in priority order: bundled in the frozen
    EXE, previously auto-installed by us, then the system PATH."""
    if FFMPEG_PATH and Path(FFMPEG_PATH).exists():
        return FFMPEG_PATH
    configured = APP_CONFIG.get("ffmpeg_path")
    if configured and Path(configured).exists():
        return configured
    default_installed = FFMPEG_INSTALL_DIR / "ffmpeg.exe"
    if default_installed.exists():
        return str(default_installed)
    found = shutil.which("ffmpeg")
    if found:
        return found
    return None

FFMPEG_PATH = detect_ffmpeg()


def apply_cookie_config(opts):
    """Mutate ydl_opts in place with the user's opt-in cookie settings, if any."""
    browser = APP_CONFIG.get("youtube_cookies_browser")
    cookie_file = APP_CONFIG.get("youtube_cookies_file")
    if browser:
        opts["cookiesfrombrowser"] = (browser,)
    elif cookie_file:
        opts["cookiefile"] = cookie_file
    return opts


def friendly_youtube_error(exc):
    """yt-dlp's raw 'Sign in to confirm you're not a bot' traceback is not
    actionable for an end user. Translate it into plain guidance."""
    msg = str(exc)
    if "Sign in to confirm" in msg or "not a bot" in msg:
        return (
            "YouTube запросил подтверждение «не бот» для этого видео. "
            "Что можно сделать: 1) перезапустите MTools — программа сама "
            "предложит обновить yt-dlp до свежей версии (YouTube часто "
            "меняет защиту, и обновление обычно решает проблему); "
            "2) если не помогло, настройте куки — создайте файл "
            "mtools_config.json рядом с программой с содержимым "
            "{\"youtube_cookies_browser\": \"chrome\"} (укажите браузер, "
            "где вы залогинены в YouTube) и перезапустите сервер."
        )
    return msg


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
    apply_cookie_config(opts)
    if progress_hooks:
        opts["progress_hooks"] = progress_hooks
    if postprocessor_hooks:
        opts["postprocessor_hooks"] = postprocessor_hooks
    return opts, ext


# ── YouTube "Sign in to confirm you're not a bot" fallback ────
# The default (web) client has the fullest, most accurate format list —
# including all resolutions up to 4K — so we always try it first. Only if
# it specifically hits YouTube's bot-check do we retry with the
# android/tv clients, which dodge that check but report a much smaller
# set of formats (often capped around 360p). Forcing android/tv for
# every video would silently hide real available resolutions, so this
# is a fallback, not a default.
BOT_CHECK_CLIENT_FALLBACK = ["android", "tv"]

def extract_info_with_fallback(url, ydl_opts, download):
    from yt_dlp import YoutubeDL
    client_attempts = [None, BOT_CHECK_CLIENT_FALLBACK]
    last_exc = None
    for clients in client_attempts:
        opts = dict(ydl_opts)
        if clients:
            opts["extractor_args"] = {"youtube": {"player_client": clients}}
        try:
            with YoutubeDL(opts) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as e:
            last_exc = e
            msg = str(e)
            if "Sign in to confirm" not in msg and "not a bot" not in msg:
                raise  # a different failure — don't mask it, surface immediately
            continue  # bot-check hit — retry with the fallback client(s)
    raise last_exc


def cleanup_tmp_dir(tmp_dir):
    try:
        for f in Path(tmp_dir).iterdir():
            try: f.unlink()
            except: pass
        os.rmdir(tmp_dir)
    except: pass


# ── FFmpeg auto-installer ───────────────────────────────────────
# yt-dlp needs a real ffmpeg binary (not the in-browser ffmpeg.wasm used by
# the trimmer) to merge video+audio or extract MP3. If it's missing, offer
# to fetch a Windows build from the official ShareX/FFmpeg GitHub
# releases and install it to a per-user folder that needs no admin
# rights. We always ask GitHub for the *latest* release rather than
# hardcoding a version/filename, since new releases get published there
# over time.
FFMPEG_RELEASE_API = "https://api.github.com/repos/ShareX/FFmpeg/releases/latest"
FFMPEG_RELEASES_PAGE = "https://github.com/ShareX/FFmpeg/releases"

INSTALL_JOBS = {}
INSTALL_JOBS_LOCK = threading.Lock()


def _github_get_json(url):
    req = urllib.request.Request(
        url, headers={"User-Agent": "MTools", "Accept": "application/vnd.github+json"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _score_ffmpeg_asset(name, want_arm):
    name = name.lower()
    if not name.endswith(".zip"):
        return -1
    if any(bad in name for bad in ("macos", "darwin", "linux", "-mac")):
        return -1  # this repo is Windows-only, but be defensive anyway
    has_arm = "arm64" in name or "aarch64" in name
    has_x64 = "x64" in name or "amd64" in name or "win64" in name
    has_x86 = ("x86" in name or "i686" in name or "win32" in name) and not has_x64 and not has_arm
    is_win_labeled = "win" in name or "windows" in name
    bonus = 5 if is_win_labeled else 0  # prefer explicitly-labeled builds when available
    if want_arm:
        if has_arm:
            return bonus + 10
        if has_x64:
            return bonus + 3  # x64 builds still run on arm64 Windows via emulation
        return -1
    if has_x64:
        return bonus + 10
    if has_x86:
        return bonus + 5
    return -1


def find_ffmpeg_release_asset():
    release = _github_get_json(FFMPEG_RELEASE_API)
    assets = release.get("assets", [])
    machine = platform.machine().lower()
    want_arm = "arm" in machine or "aarch64" in machine
    scored = [(_score_ffmpeg_asset(a.get("name") or "", want_arm), a) for a in assets]
    scored = [t for t in scored if t[0] > 0]
    scored.sort(key=lambda t: t[0], reverse=True)
    chosen = scored[0][1] if scored else None
    if not chosen:
        available = ", ".join(a.get("name", "?") for a in assets) or "нет файлов вообще"
        raise RuntimeError(
            "Не удалось найти подходящий архив FFmpeg для Windows в последнем "
            f"релизе ({FFMPEG_RELEASES_PAGE}). Доступные файлы в релизе: {available}. "
            "Установите вручную."
        )
    # Best-effort: the release notes sometimes list a "File / SHA256" table
    # as plain text. If we can find a 64-char hex string right after this
    # asset's filename, use it to verify the download; if not, just skip
    # verification rather than failing the whole install over it.
    sha256 = None
    body = release.get("body") or ""
    m = re.search(re.escape(chosen["name"]) + r"[^\n]{0,80}?([a-fA-F0-9]{64})", body)
    if m:
        sha256 = m.group(1).lower()
    return {
        "download_url": chosen["browser_download_url"],
        "name": chosen["name"],
        "size": chosen.get("size"),
        "sha256": sha256,
        "release_tag": release.get("tag_name"),
    }


def run_ffmpeg_install_job(job_id):
    with INSTALL_JOBS_LOCK:
        INSTALL_JOBS[job_id] = {
            "status": "starting", "downloaded": 0, "total": None,
            "percent": 0, "error": None, "path": None,
        }
    zip_path = None
    try:
        asset = find_ffmpeg_release_asset()
        with INSTALL_JOBS_LOCK:
            job = INSTALL_JOBS.get(job_id)
            if job:
                job["status"] = "downloading"
                job["total"] = asset.get("size")

        FFMPEG_INSTALL_DIR.mkdir(parents=True, exist_ok=True)
        zip_path = FFMPEG_INSTALL_DIR / asset["name"]
        req = urllib.request.Request(asset["download_url"], headers={"User-Agent": "MTools"})
        hasher = hashlib.sha256()
        with urllib.request.urlopen(req, timeout=30) as resp:
            total = int(resp.headers.get("Content-Length") or asset.get("size") or 0) or None
            downloaded = 0
            with open(zip_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    with INSTALL_JOBS_LOCK:
                        job = INSTALL_JOBS.get(job_id)
                        if not job:
                            return  # job was dismissed/cancelled client-side
                        job["downloaded"] = downloaded
                        job["total"] = total
                        job["percent"] = round(downloaded / total * 100, 1) if total else None

        if asset["sha256"] and hasher.hexdigest().lower() != asset["sha256"]:
            raise RuntimeError(
                "Контрольная сумма скачанного файла не совпала — похоже, "
                "файл повреждён при загрузке. Попробуйте ещё раз."
            )

        with INSTALL_JOBS_LOCK:
            job = INSTALL_JOBS.get(job_id)
            if job:
                job["status"] = "extracting"

        with zipfile.ZipFile(zip_path) as zf:
            wanted = ("ffmpeg.exe", "ffprobe.exe")
            extracted_any = False
            for member in zf.namelist():
                base = Path(member).name.lower()
                if base in wanted:
                    with zf.open(member) as src, open(FFMPEG_INSTALL_DIR / base, "wb") as dst:
                        shutil.copyfileobj(src, dst)
                    extracted_any = True
        if not extracted_any:
            raise RuntimeError("В скачанном архиве не нашлось ffmpeg.exe")

        ffmpeg_exe = FFMPEG_INSTALL_DIR / "ffmpeg.exe"
        if not ffmpeg_exe.exists():
            raise RuntimeError("Распаковка прошла, но ffmpeg.exe не появился на диске")

        global FFMPEG_PATH
        FFMPEG_PATH = str(ffmpeg_exe)
        cfg = load_config()
        cfg["ffmpeg_path"] = str(ffmpeg_exe)
        save_config(cfg)
        global APP_CONFIG
        APP_CONFIG = cfg

        with INSTALL_JOBS_LOCK:
            job = INSTALL_JOBS.get(job_id)
            if job:
                job["status"] = "finished"
                job["percent"] = 100
                job["path"] = str(ffmpeg_exe)
    except Exception as e:
        log_error("run_ffmpeg_install_job", e)
        with INSTALL_JOBS_LOCK:
            job = INSTALL_JOBS.get(job_id)
            if job:
                job["status"] = "error"
                job["error"] = str(e)
    finally:
        if zip_path:
            try: zip_path.unlink()
            except OSError: pass


# ── yt-dlp auto-updater ───────────────────────────────────────
# Mirrors the FFmpeg auto-installer: check PyPI for a newer yt-dlp than the
# one currently in use, then (on request) download the wheel and unpack the
# `yt_dlp` package into YTDLP_PATCH_DIR so it overrides the bundled copy.
YTDLP_JOBS = {}
YTDLP_JOBS_LOCK = threading.Lock()


def get_current_ytdlp_version():
    try:
        from yt_dlp import version as _v
        return _v.__version__
    except Exception:
        return None


def _parse_ver(v):
    """Best-effort version tuple for comparison. yt-dlp uses date-based
    versions like 2026.8.19; split on '.' and take leading ints."""
    out = []
    for part in (v or "").split("."):
        m = re.match(r"\d+", part)
        out.append(int(m.group(0)) if m else 0)
    return tuple(out)


def get_latest_ytdlp_release():
    req = urllib.request.Request(
        YTDLP_PYPI_API, headers={"User-Agent": "MTools"},
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latest = data["info"]["version"]
    wheel = None
    for u in data.get("urls", []):
        if u.get("packagetype") == "bdist_wheel":
            wheel = u
            break
    if not wheel:
        for u in data.get("urls", []):
            if u.get("packagetype") == "sdist":
                wheel = u
                break
    if not wheel:
        raise RuntimeError("Не удалось найти пакет yt-dlp на PyPI.")
    return {
        "version": latest,
        "url": wheel.get("url"),
        "filename": wheel.get("filename"),
        "size": wheel.get("size"),
    }


def check_ytdlp_update():
    current = get_current_ytdlp_version()
    try:
        rel = get_latest_ytdlp_release()
    except Exception as e:
        return {
            "current": current, "latest": None,
            "update_available": False, "error": str(e),
        }
    latest = rel["version"]
    available = bool(current and latest and _parse_ver(latest) > _parse_ver(current))
    return {
        "current": current, "latest": latest,
        "update_available": available, "url": rel["url"],
    }


def run_ytdlp_update_job(job_id):
    with YTDLP_JOBS_LOCK:
        YTDLP_JOBS[job_id] = {
            "status": "starting", "downloaded": 0, "total": None,
            "percent": 0, "error": None, "version": None,
        }
    wheel_path = None
    try:
        rel = get_latest_ytdlp_release()
        if not rel["url"]:
            raise RuntimeError("Не удалось найти пакет yt-dlp на PyPI.")
        with YTDLP_JOBS_LOCK:
            job = YTDLP_JOBS.get(job_id)
            if job:
                job["status"] = "downloading"
                job["total"] = rel.get("size")
                job["version"] = rel["version"]

        YTDLP_PATCH_DIR.mkdir(parents=True, exist_ok=True)
        wheel_path = YTDLP_PATCH_DIR / (rel["filename"] or "yt_dlp_update.whl")
        req = urllib.request.Request(rel["url"], headers={"User-Agent": "MTools"})
        hasher = hashlib.sha256()
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length") or rel.get("size") or 0) or None
            downloaded = 0
            with open(wheel_path, "wb") as f:
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
                    hasher.update(chunk)
                    downloaded += len(chunk)
                    with YTDLP_JOBS_LOCK:
                        job = YTDLP_JOBS.get(job_id)
                        if not job:
                            return  # job dismissed client-side
                        job["downloaded"] = downloaded
                        job["total"] = total
                        job["percent"] = round(downloaded / total * 100, 1) if total else None

        with YTDLP_JOBS_LOCK:
            job = YTDLP_JOBS.get(job_id)
            if job:
                job["status"] = "extracting"

        # The wheel is a zip; unpack only the `yt_dlp/` package folder into
        # YTDLP_PATCH_DIR so `import yt_dlp` resolves to the fresh copy.
        target_pkg = YTDLP_PATCH_DIR / "yt_dlp"
        if target_pkg.exists():
            shutil.rmtree(target_pkg)
        with zipfile.ZipFile(wheel_path) as zf:
            for member in zf.namelist():
                if not member.startswith("yt_dlp/") or member.endswith("/"):
                    continue
                dest = target_pkg / member[len("yt_dlp/"):]
                dest.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as src, open(dest, "wb") as dst:
                    shutil.copyfileobj(src, dst)

        try:
            wheel_path.unlink()
        except OSError:
            pass
        try:
            (YTDLP_PATCH_DIR / "version.txt").write_text(rel["version"], encoding="utf-8")
        except OSError:
            pass

        with YTDLP_JOBS_LOCK:
            job = YTDLP_JOBS.get(job_id)
            if job:
                job["status"] = "finished"
                job["percent"] = 100
    except Exception as e:
        log_error("run_ytdlp_update_job", e)
        with YTDLP_JOBS_LOCK:
            job = YTDLP_JOBS.get(job_id)
            if job:
                job["status"] = "error"
                job["error"] = str(e)
    finally:
        if wheel_path:
            try:
                wheel_path.unlink()
            except OSError:
                pass


def run_download_job(job_id, url, fmt, quality):
    tmp_dir = tempfile.mkdtemp(prefix="mtools_yt_")
    with DOWNLOAD_JOBS_LOCK:
        DOWNLOAD_JOBS[job_id] = {
            "status": "starting", "downloaded": 0, "total": None, "percent": 0,
            "speed": None, "eta": None, "error": None, "tmp_dir": tmp_dir,
            "file_path": None, "filename": None, "ext": None,
            "cancel_requested": False,
        }

    def check_cancel(job):
        if job.get("cancel_requested"):
            raise DownloadCancelled("Cancelled by user")

    def progress_hook(d):
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if not job:
                return
            check_cancel(job)
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
            if not job:
                return
            check_cancel(job)
            if d.get("status") == "started":
                job["status"] = "processing"

    try:
        outtmpl = os.path.join(tmp_dir, "%(title)s.%(ext)s")
        ydl_opts, ext = build_ydl_opts(
            fmt, quality, outtmpl,
            progress_hooks=[progress_hook], postprocessor_hooks=[pp_hook],
        )
        info = extract_info_with_fallback(url, ydl_opts, download=True)
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
                if job.get("cancel_requested"):
                    raise DownloadCancelled("Cancelled by user")
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
        if DownloadCancelled is not None and isinstance(e, DownloadCancelled):
            with DOWNLOAD_JOBS_LOCK:
                job = DOWNLOAD_JOBS.get(job_id)
                if job:
                    job["status"] = "cancelled"
                DOWNLOAD_JOBS.pop(job_id, None)
            cleanup_tmp_dir(tmp_dir)
            return
        log_error("run_download_job", e)
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if job:
                job["status"] = "error"
                job["error"] = friendly_youtube_error(e)
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
        elif parsed.path == "/api/ffmpeg/status":
            self._handle_ffmpeg_status()
        elif parsed.path == "/api/ffmpeg/install/progress":
            self._handle_ffmpeg_install_progress(parsed)
        elif parsed.path == "/api/ytdlp/version":
            self._handle_ytdlp_version()
        elif parsed.path == "/api/ytdlp/update/progress":
            self._handle_ytdlp_update_progress(parsed)
        elif parsed.path == "/api/ui-settings":
            self._handle_ui_settings_get()
        else:
            super().do_GET()

    def do_POST(self):
        if self.path == "/api/youtube/download/start":
            self._handle_youtube_download_start()
        elif self.path == "/api/youtube/download/cancel":
            self._handle_youtube_download_cancel()
        elif self.path == "/api/ffmpeg/install/start":
            self._handle_ffmpeg_install_start()
        elif self.path == "/api/ytdlp/update/start":
            self._handle_ytdlp_update_start()
        elif self.path == "/api/ui-settings":
            self._handle_ui_settings_post()
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
            ydl_opts = {
                "quiet": True, "no_warnings": True, "extract_flat": False,
                "noplaylist": True, "socket_timeout": 30, "retries": 20,
            }
            apply_cookie_config(ydl_opts)
            info = extract_info_with_fallback(url, ydl_opts, download=False)
            formats = info.get("formats") or []
            heights = [
                f.get("height") for f in formats
                if f.get("height") and f.get("vcodec") not in (None, "none")
            ]
            max_height = max(heights) if heights else None
            quality_tiers = [("2160p", 2160), ("1440p", 1440), ("1080p", 1080),
                              ("720p", 720), ("480p", 480), ("360p", 360)]
            if max_height:
                # Only offer resolutions this video actually has — a
                # tier "available" if the video has something at or
                # above it (yt-dlp/ffmpeg will just use the closest
                # match under the requested cap, same as normal).
                available_qualities = [q for q, h in quality_tiers if max_height >= h]
                if not available_qualities:
                    available_qualities = ["360p"]
            else:
                # Couldn't determine resolution (e.g. unusual format
                # list) — don't hide anything, safer default.
                available_qualities = [q for q, _ in quality_tiers]
            data = {
                "title": info.get("title", "\u2014"),
                "channel": info.get("channel", info.get("uploader", "\u2014")),
                "duration": format_duration(info.get("duration")),
                "duration_raw": info.get("duration"),
                "views": format_views(info.get("view_count")),
                "thumbnail": info.get("thumbnail", ""),
                "webpage_url": info.get("webpage_url", url),
                "max_height": max_height,
                "available_qualities": available_qualities,
            }
            self._send_json(data)
        except ImportError:
            self._send_json({"error": "yt-dlp not installed"}, 500)
        except Exception as e:
            log_error("_handle_youtube_info", e)
            self._send_json({"error": friendly_youtube_error(e)}, 500)

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

    def _handle_youtube_download_cancel(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length).decode("utf-8")
            data = json.loads(body) if body else {}
        except Exception:
            data = {}
        job_id = data.get("job_id")
        tmp_dir_to_clean = None
        with DOWNLOAD_JOBS_LOCK:
            job = DOWNLOAD_JOBS.get(job_id)
            if job:
                job["cancel_requested"] = True
                # If the file was already fully downloaded by the time the
                # cancel arrived, the download thread has no more hook
                # calls left to catch it — honor the cancel here instead.
                if job["status"] == "finished":
                    job["status"] = "cancelled"
                    tmp_dir_to_clean = job["tmp_dir"]
                    DOWNLOAD_JOBS.pop(job_id, None)
        if tmp_dir_to_clean:
            cleanup_tmp_dir(tmp_dir_to_clean)
        self._send_json({"ok": True})

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
        if job["status"] == "cancelled":
            self._send_json({"error": "Download was cancelled"}, 410)
            with DOWNLOAD_JOBS_LOCK:
                DOWNLOAD_JOBS.pop(job_id, None)
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

    # ── FFmpeg auto-installer ───────────────────────────────────
    def _handle_ffmpeg_status(self):
        self._send_json({
            "available": bool(FFMPEG_PATH),
            "path": FFMPEG_PATH,
        })

    def _handle_ffmpeg_install_start(self):
        job_id = uuid.uuid4().hex
        threading.Thread(
            target=run_ffmpeg_install_job, args=(job_id,), daemon=True,
        ).start()
        self._send_json({"job_id": job_id})

    def _handle_ffmpeg_install_progress(self, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        job_id = params.get("id", [None])[0]
        with INSTALL_JOBS_LOCK:
            job = INSTALL_JOBS.get(job_id)
            if not job:
                self._send_json({"error": "Unknown job"}, 404)
                return
            self._send_json({
                "status": job["status"],
                "downloaded": job["downloaded"],
                "total": job["total"],
                "percent": job["percent"],
                "error": job["error"],
                "path": job["path"],
            })

    def _handle_ytdlp_version(self):
        self._send_json(check_ytdlp_update())

    def _handle_ytdlp_update_start(self):
        job_id = uuid.uuid4().hex
        threading.Thread(
            target=run_ytdlp_update_job, args=(job_id,), daemon=True,
        ).start()
        self._send_json({"job_id": job_id})

    def _handle_ytdlp_update_progress(self, parsed):
        params = urllib.parse.parse_qs(parsed.query)
        job_id = params.get("id", [None])[0]
        with YTDLP_JOBS_LOCK:
            job = YTDLP_JOBS.get(job_id)
            if not job:
                self._send_json({"error": "Unknown job"}, 404)
                return
            self._send_json({
                "status": job["status"],
                "downloaded": job["downloaded"],
                "total": job["total"],
                "percent": job["percent"],
                "error": job["error"],
                "version": job["version"],
            })

    def _handle_ui_settings_get(self):
        try:
            with open(UI_SETTINGS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            data = {}
        self._send_json(data if isinstance(data, dict) else {})

    def _handle_ui_settings_post(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            data = json.loads(self.rfile.read(length).decode("utf-8"))
            if not isinstance(data, dict):
                raise ValueError("not an object")
        except Exception:
            self._send_json({"error": "Invalid request"}, 400)
            return
        try:
            UI_SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(UI_SETTINGS_PATH, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except OSError:
            pass
        self._send_json({"ok": True})

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