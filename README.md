<div align="center">

[🇷🇺 Русский](#russian) · [🇬🇧 English](#english-version)

<h1 id="russian"><img src="https://cdn-icons-png.flaticon.com/128/2921/2921222.png" height=28 /> MTools <sup>V0.718</sup></h1>

**Локальные медиа-инструменты в браузере.**  
Всё работает на вашем компьютере — файлы никуда не отправляются.

</div>

> [!IMPORTANT]
> Это десктопное приложение на Python + vanilla JS. Оно поднимает локальный HTTP-сервер и открывает интерфейс в браузере.  
> Для обрезки используется ffmpeg.wasm прямо в браузере. Для скачивания с YouTube — yt-dlp на серверной стороне.  
> Никаких внешних серверов, никакой телеметрии.

## ✂️ Возможности

### Обрезка видео/аудио
- Открыть **MP4, WEBM, MP3 или WAV** через drag'n'drop
- Визуальный таймлайн: форма волны (AudioContext) для аудио, превью-кадры для видео
- Перетаскивание маркеров начала и конца, подсветка выделенного диапазона
- **Быстрая обрезка** (stream copy — без перекодирования) или **точная** с перекодированием через ffmpeg.wasm
- Встроенный плеер: клик по таймлайну → перемотка, перетаскивание → скраббинг, **Space** → пауза
- Ползунок громкости по наведению на превью
- Плеер автоматически удерживается в границах выделения
- Результат скачивается через браузерный диалог (префикс `mtools_`)

### ⬇️ YouTube Download
- Вставьте ссылку — покажет название, канал, длительность, просмотры, обложку
- Формат: **MP4** (360p / 480p / 720p / 1080p) или **MP3**
- Скачивание через yt-dlp с индикатором прогресса
- Поддержка кириллицы в именах файлов (RFC 5987)
- Таймаут 10 минут

## 📸 Скриншоты

<div align="center">

**`📌 Главная`**

![Главный экран](https://i.ibb.co/pvPqH70v/image.png)

**`📌 Видео редактор`**

![Обрезка видео](https://i.ibb.co/Z1mrpFtc/image.png)

**`📌 Скачивание с YouTube`**

![YouTube Download](https://i.ibb.co/99b6XmjM/image.png)

</div>

## ⚙️ Установка

### 🪟 Готовый .exe (Windows)
1. Скачайте `MTools.exe` из [релизов](https://github.com/Kotecy/MFast-Video-Editor-in-browser/releases)
2. Запустите — откроется браузер с приложением (`http://localhost:8000`)
3. Ничего устанавливать не нужно — внутри Python, yt-dlp и ffmpeg.wasm
4. Закройте вкладку — сервер остановится сам. Либо нажмите **«Выключить сервер»**

### 🐍 Из исходников (Python)
```bash
pip install yt-dlp PyInstaller
git clone https://github.com/ваш-username/ваш-репозиторий
cd MTools
python server.py
```
Откроется `http://localhost:8000`.

## 🔧 Сборка .exe
```bash
pip install yt-dlp PyInstaller
pyinstaller build.spec
```

Исполняемый файл — `dist/MTools.exe`. В сборку входит `vendor/` (ffmpeg.wasm).

## 📁 Структура проекта
```
MTools/
├── server.py          # HTTP-сервер: YouTube API, heartbeat, статика
├── index.html         # SPA-фронтенд (vanilla JS, ~1750 строк)
├── build.spec         # Конфиг PyInstaller
├── vendor/
│   ├── ffmpeg/        # ffmpeg.wasm (обрезка в браузере)
│   └── mt.ico         # Иконка приложения
├── dist/
│   └── MTools.exe     # Собранный exe
└── README.md
```

## 🛠 Технологии
| Слой | Технология |
|------|-----------|
| **Бэкенд** | Python 3, `http.server` + `ThreadingMixIn`, yt-dlp |
| **Фронтенд** | Vanilla JS, ffmpeg.wasm, Web Audio API (форма волны) |
| **Сборка** | PyInstaller (no-console, single-file .exe, ~50 МБ) |
| **Дизайн** | Тёмная тема, Space Grotesk + Inter, кастомный CSS |

## 🌐 API endpoints
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/youtube/info?url=` | Информация о видео |
| `POST` | `/api/youtube/download/start` | Запустить скачивание (возвращает `job_id`) |
| `GET` | `/api/youtube/progress?id=` | Прогресс скачивания |
| `GET` | `/api/youtube/download/file?id=` | Скачать готовый файл |
| `GET` | `/api/heartbeat` | Продлить жизнь сервера |
| `POST` | `/api/shutdown` | Завершить сервер |

## ❓ Частые вопросы

### Не открывается страница после запуска?
Убедитесь, что порт 8000 не занят. Если занят — сервер сам найдёт свободный порт и выведет его в консоль.

### ffmpeg.wasm не загружается?
Проверьте папку `vendor/ffmpeg/` — она должна быть рядом с `index.html`. В .exe-версии всё уже встроено.

### YouTube не скачивает?
Убедитесь, что видео доступно и ссылка корректна. Проверьте `mtools_error.log` рядом с программой — там подробная информация об ошибке.

## ⭐ Поддержка

Поставьте :star: этому репозиторию, если проект оказался полезным.

## ⚖️ Лицензия
MIT

---

# <span id="english-version">🇬🇧 English version</span>

<details>
<summary><strong>English version</strong></summary>

<div align="center">

# <img src="https://cdn-icons-png.flaticon.com/128/2921/2921222.png" height=28 /> MTools <sup>V0.718</sup> <img src="https://cdn-icons-png.flaticon.com/128/686/686589.png" height=28 />

**Local media tools in your browser.**  
Everything runs on your machine — no files are sent anywhere.

</div>

> [!IMPORTANT]
> This is a desktop app built with Python + vanilla JS. It starts a local HTTP server and opens the UI in your browser.  
> Trimming uses ffmpeg.wasm in-browser. YouTube downloads use yt-dlp on the server side.  
> No external servers, no telemetry.

## ✂️ Features

### Video / Audio Trimmer
- Open **MP4, WEBM, MP3 or WAV** via drag'n'drop
- Visual timeline: audio waveform (AudioContext) or video preview frames
- Drag start/end markers, highlighted selection range
- **Fast cut** (stream copy — no re-encoding) or **precise** with ffmpeg.wasm
- Built-in player: click timeline → seek, drag → scrub, **Space** → pause
- Volume slider on preview hover
- Player stays within selection bounds
- Downloads with `mtools_` prefix

### ⬇️ YouTube Downloader
- Paste a link — shows title, channel, duration, views, thumbnail
- Format: **MP4** (360p / 480p / 720p / 1080p) or **MP3**
- Download via yt-dlp with live progress
- Non-ASCII filename support (RFC 5987)
- 10-minute timeout

## 📸 Screenshots

<div align="center">

**`📌 Home`**

![Home](https://i.ibb.co/pvPqH70v/image.png)

**`📌 Video Editor`**

![Video Editor](https://i.ibb.co/Z1mrpFtc/image.png)

**`📌 YouTube Downloader`**

![YouTube Download](https://i.ibb.co/99b6XmjM/image.png)

</div>

## ⚙️ Installation

### 🪟 Pre-built .exe (Windows)
1. Download `MTools.exe` from [releases](https://github.com/your-username/your-repo/releases)
2. Run it — a browser tab opens (`http://localhost:8000`)
3. No setup needed — bundles Python, yt-dlp and ffmpeg.wasm
4. Close the tab — server stops automatically. Or press **"Shutdown server"**

### 🐍 From source (Python)
```bash
pip install yt-dlp PyInstaller
git clone https://github.com/your-username/your-repo
cd MTools
python server.py
```
Opens at `http://localhost:8000`.

## 🔧 Building .exe
```bash
pip install yt-dlp PyInstaller
pyinstaller build.spec
```

Output: `dist/MTools.exe`. Bundles `vendor/` (ffmpeg.wasm).

## 📁 Project Structure
```
MTools/
├── server.py          # HTTP server: YouTube API, heartbeat, static files
├── index.html         # SPA frontend (vanilla JS, ~1750 lines)
├── build.spec         # PyInstaller config
├── vendor/
│   ├── ffmpeg/        # ffmpeg.wasm (in-browser trimming)
│   └── mt.ico         # App icon
├── dist/
│   └── MTools.exe     # Compiled executable
└── README.md
```

## 🛠 Tech Stack
| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3, `http.server` + `ThreadingMixIn`, yt-dlp |
| **Frontend** | Vanilla JS, ffmpeg.wasm, Web Audio API (waveform) |
| **Packaging** | PyInstaller (no-console, single-file .exe, ~50 MB) |
| **Design** | Dark theme, Space Grotesk + Inter, custom CSS |

## 🌐 API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/youtube/info?url=` | Video info |
| `POST` | `/api/youtube/download/start` | Start download (returns `job_id`) |
| `GET` | `/api/youtube/progress?id=` | Download progress |
| `GET` | `/api/youtube/download/file?id=` | Download finished file |
| `GET` | `/api/heartbeat` | Keep server alive |
| `POST` | `/api/shutdown` | Shutdown server |

## ❓ FAQ

### The page doesn't open after launch?
Check if port 8000 is free. If busy, the server auto-selects another port and shows it in the console.

### ffmpeg.wasm won't load?
Make sure `vendor/ffmpeg/` exists next to `index.html`. In the .exe version everything is pre-bundled.

### YouTube downloads fail?
Verify the video is accessible and the URL is correct. Check `mtools_error.log` next to the app for details.

## ⭐ Support

Star :star: this repo if you find it useful.

## ⚖️ License
MIT
</details>
