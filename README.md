# MTools <!-- V0.718 -->

**Локальные медиа-инструменты в браузере.** Всё работает на вашем компьютере — файлы никуда не отправляются.

Единое окно для обрезки видео/аудио и скачивания с YouTube. Сервер на Python, интерфейс — vanilla JS. Работает полностью локально, без интернета (кроме YouTube-качалки).

## Возможности

### ✂️ Обрезка видео/аудио
- Открыть MP4, WEBM, MP3 или WAV через drag'n'drop
- Визуальный таймлайн с формой волны (AudioContext) для аудио и превью-кадрами для видео
- Перетаскивание маркеров начала и конца; подсветка выделенного диапазона
- Быстрая обрезка (stream copy — без перекодирования) или точная с перекодированием через **ffmpeg.wasm** (в браузере)
- Встроенный плеер: клик по таймлайну — перемотка, перетаскивание — скраббинг, Space — пауза
- Ползунок громкости появляется при наведении на превью
- Плеер автоматически удерживается в границах выделения
- Результат скачивается через браузерный диалог (префикс `mtools_`)

### ⬇️ YouTube Download
- Вставьте ссылку на YouTube видео — покажет название, канал, длительность, просмотры, обложку
- Выбор формата: MP4 (360p / 480p / 720p / 1080p) или MP3
- Скачивание через **yt-dlp** на серверной стороне с индикатором прогресса
- Файл передаётся в браузер через HTTP и сохраняется через диалог скачивания
- Таймаут 10 минут, поддержка не-ASCII (кириллица) в именах файлов (RFC 5987)

## Скриншоты

**Главная**
![Главный экран](https://i.ibb.co/pvPqH70v/image.png)

**Видео редактор**
![Обрезка видео](https://i.ibb.co/Z1mrpFtc/image.png)

**Скачивание с YouTube**
![YouTube Download](https://i.ibb.co/99b6XmjM/image.png)

## Установка

### Готовый .exe (Windows)
1. Скачайте `MTools.exe` из [релизов](https://github.com/ваш-username/ваш-репозиторий/releases)
2. Запустите — откроется браузер с приложением (`http://localhost:8000`)
3. Ничего устанавливать не нужно (внутри Python, yt-dlp, ffmpeg.wasm и ffmpeg)
4. Закройте вкладку — сервер остановится сам. Можно выключить вручную кнопкой "Выключить сервер"

### Из исходников (Python)
```bash
pip install yt-dlp PyInstaller
git clone https://github.com/ваш-username/ваш-репозиторий
cd MTools
python server.py
```

Откроется `http://localhost:8000`.

## Сборка .exe
```bash
pip install yt-dlp PyInstaller
pyinstaller build.spec
```

Исполняемый файл появится в `dist/MTools.exe`. Сборка включает `ffmpeg.exe` (для yt-dlp) и `vendor/` (ffmpeg.wasm для браузерной обрезки).

## Структура проекта
```
MTools/
├── server.py          # HTTP-сервер: API YouTube, heartbeat, раздача статики
├── index.html         # SPA-фронтенд (vanilla JS, ~1750 строк)
├── build.spec         # Конфиг PyInstaller для сборки .exe
├── mt.ico             # Иконка приложения
├── vendor/
│   └── ffmpeg/        # ffmpeg.wasm (обрезка в браузере)
├── dist/
│   └── MTools.exe     # Готовый исполняемый файл
└── ffmpeg.exe         # Нативный ffmpeg для yt-dlp
```

## Технологии
| Слой | Технология |
|------|-----------|
| **Бэкенд** | Python 3, `http.server` + `ThreadingMixIn`, yt-dlp, ffmpeg |
| **Фронтенд** | Vanilla JS, ffmpeg.wasm (в браузере), Web Audio API (форма волны) |
| **Сборка** | PyInstaller (no-console, single-file .exe, ~160 МБ) |
| **Дизайн** | Темная тема, Space Grotesk + Inter, кастомный CSS (без библиотек) |

## API endpoints
| Метод | Путь | Описание |
|-------|------|----------|
| `GET` | `/api/youtube/info?url=` | Информация о видео (название, длительность, просмотры) |
| `POST` | `/api/youtube/download/start` | Запустить скачивание (возвращает `job_id`) |
| `GET` | `/api/youtube/progress?id=` | Прогресс скачивания (%, скорость, ETA) |
| `GET` | `/api/youtube/download/file?id=` | Скачать готовый файл |
| `GET` | `/api/heartbeat` | Продлить жизнь сервера (сброс таймера 15 с) |
| `POST` | `/api/shutdown` | Немедленное завершение сервера |

## Лицензия
MIT

---

<br>

# MTools — English

**Local media tools in your browser.** Everything runs on your machine — no files are sent anywhere.

All-in-one tool for trimming video/audio and downloading from YouTube. Python backend, vanilla JS frontend. Fully local, no internet required (except YouTube downloader).

## Features

### ✂️ Video / Audio Trimmer
- Open MP4, WEBM, MP3 or WAV via drag'n'drop
- Visual timeline with audio waveform (AudioContext) or video preview frames
- Drag start/end markers; highlighted selection range
- Fast cut (stream copy — no re-encoding) or precise cut with **ffmpeg.wasm** (in-browser)
- Built-in player: click timeline to seek, drag to scrub, Space to pause
- Volume slider appears on hover over the preview
- Player automatically stays within selection bounds
- Result downloads via browser dialog (`mtools_` prefix)

### ⬇️ YouTube Downloader
- Paste a YouTube link — shows title, channel, duration, views, thumbnail
- Format: MP4 (360p / 480p / 720p / 1080p) or MP3
- Download via **yt-dlp** on the server with live progress indicator
- File streams to browser and saves via download dialog
- 10-minute timeout, non-ASCII filename support (RFC 5987)

## Screenshots

**Home**
![Home](https://i.ibb.co/pvPqH70v/image.png)

**Video Editor**
![Video Editor](https://i.ibb.co/Z1mrpFtc/image.png)

**YouTube Downloader**
![YouTube Download](https://i.ibb.co/99b6XmjM/image.png)

## Installation

### Pre-built .exe (Windows)
1. Download `MTools.exe` from [releases](https://github.com/your-username/your-repo/releases)
2. Run it — a browser tab opens with the app (`http://localhost:8000`)
3. No additional setup needed (bundles Python, yt-dlp, ffmpeg.wasm and ffmpeg)
4. Close the tab — the server stops automatically. Or press "Shutdown server"

### From source (Python)
```bash
pip install yt-dlp PyInstaller
git clone https://github.com/your-username/your-repo
cd MTools
python server.py
```

Opens at `http://localhost:8000`.

## Building .exe
```bash
pip install yt-dlp PyInstaller
pyinstaller build.spec
```

Output: `dist/MTools.exe`. Includes `ffmpeg.exe` (for yt-dlp) and `vendor/` (ffmpeg.wasm).

## Project Structure
```
MTools/
├── server.py          # HTTP server: YouTube API, heartbeat, static files
├── index.html         # SPA frontend (vanilla JS, ~1750 lines)
├── build.spec         # PyInstaller config
├── mt.ico             # App icon
├── vendor/
│   └── ffmpeg/        # ffmpeg.wasm (in-browser trimming)
├── dist/
│   └── MTools.exe     # Compiled executable
└── ffmpeg.exe         # Native ffmpeg for yt-dlp
```

## Tech Stack
| Layer | Technology |
|-------|-----------|
| **Backend** | Python 3, `http.server` + `ThreadingMixIn`, yt-dlp, ffmpeg |
| **Frontend** | Vanilla JS, ffmpeg.wasm, Web Audio API (waveform) |
| **Packaging** | PyInstaller (no-console, single-file .exe, ~160 MB) |
| **Design** | Dark theme, Space Grotesk + Inter, custom CSS (no libraries) |

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/youtube/info?url=` | Video info (title, duration, views) |
| `POST` | `/api/youtube/download/start` | Start download (returns `job_id`) |
| `GET` | `/api/youtube/progress?id=` | Download progress (%, speed, ETA) |
| `GET` | `/api/youtube/download/file?id=` | Download finished file |
| `GET` | `/api/heartbeat` | Keep server alive (resets 15s timer) |
| `POST` | `/api/shutdown` | Shutdown server immediately |

## License
MIT
