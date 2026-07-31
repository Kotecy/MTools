<div align="center">

[🇷🇺 Русский](#russian) · [🇬🇧 English](#english-version)

<h1 id="russian"><img src="https://cdn-icons-png.flaticon.com/128/2921/2921222.png" height=28 /> MTools <sup>V0.718E</sup></h1>

**Локальные медиа-инструменты в браузере.**  
Обрезайте видео и аудио, качайте ролики с YouTube — всё на вашем компьютере, файлы никуда не отправляются.

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
- **Быстрая обрезка** (stream copy — без перекодирования и потери качества) или **точная** с перекодированием ровно по миллисекунде
- Встроенный плеер: клик по таймлайну → перемотка, перетаскивание → скраббинг, **Space** → пауза
- Ползунок громкости по наведению на превью
- Авто-возврат в выделение: плеер не убегает за границы выбранного участка
- Результат сохраняется через диалог браузера (префикс `mtools_`), и диалог спрашивается **до** начала долгой работы — кнопка больше не «залипает» молча
- FFmpeg для обрезки **не нужен** — всё считается в браузере

### ⬇️ Скачивание с YouTube
- Вставьте ссылку — покажет название, канал, длительность, просмотры и обложку
- Формат: **MP4** (360p / 480p / 720p / 1080p / 1440p / **4K**) или **MP3**
- **Честный список качества:** предлагаются только те разрешения, которые реально есть у ролика
- **Живой прогресс:** проценты, скорость и оставшееся время — видно, что процесс идёт, а не завис
- **Отмена скачивания** в любой момент
- **Автоустановка FFmpeg** прямо из приложения, без прав администратора
- Автоматический обход проверки «Sign in to confirm you're not a bot»
- Устойчивость к сетевым обрывам на больших и 4K-видео (повторы фрагментов)
- Поддержка кириллицы в именах файлов (RFC 5987)

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
git clone https://github.com/Kotecy/MTools
cd MTools
python server.py
```
Откроется `http://localhost:8000`. Если порт занят — сервер сам возьмёт свободный и напишет его в консоль.

## 🔧 Сборка .exe
```bash
pip install yt-dlp PyInstaller
pyinstaller build.spec
```

Исполняемый файл — `dist/MTools.exe`. В сборку входит `vendor/` (ffmpeg.wasm).

## 🎬 FFmpeg

Для **обрезки** FFmpeg не нужен вообще. Он требуется только для **скачивания с YouTube** — склеить видео со звуком и вытащить MP3.

Если FFmpeg не найден, MTools покажет окно и предложит:

- **Установить автоматически** — скачает актуальную сборку с [ShareX/FFmpeg](https://github.com/ShareX/FFmpeg/releases), проверит контрольную сумму и распакует в `%APPDATA%\MTools\ffmpeg`. **Права администратора не нужны.**
- **Установить вручную** — если FFmpeg уже есть или хочется поставить самому.

Порядок поиска: встроенный в .exe → ранее автоустановленный → системный `PATH`.

## 📁 Структура проекта
```
MTools/
├── server.py          # HTTP-сервер: YouTube API, установщик FFmpeg, статика
├── index.html         # SPA-фронтенд (vanilla JS)
├── build.spec         # Конфиг PyInstaller
├── vendor/
│   ├── ffmpeg/        # ffmpeg.wasm (обрезка в браузере)
│   └── mt.ico         # Иконка приложения
├── dist/
│   └── MTools.exe     # Собранный exe
└── README.md
```

Рядом с программой при работе могут появиться `mtools_config.json` (настройки), `mtools_error.log` и `mtools_debug.log` (логи).

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
| `POST` | `/api/youtube/download/cancel` | Отменить скачивание |
| `GET` | `/api/youtube/download/file?id=` | Скачать готовый файл |
| `GET` | `/api/ffmpeg/status` | Проверить наличие FFmpeg |
| `POST` | `/api/ffmpeg/install/start` | Запустить автоустановку FFmpeg |
| `GET` | `/api/ffmpeg/install/progress` | Прогресс установки FFmpeg |
| `POST` | `/api/cancel-shutdown` | Отменить отложенное выключение (при перезагрузке страницы) |
| `POST` | `/api/shutdown` | Завершить сервер |

## ❓ Частые вопросы

### Не открывается страница после запуска?
Убедитесь, что порт 8000 не занят. Если занят — сервер сам найдёт свободный порт и выведет его в консоль.

### ffmpeg.wasm не загружается?
Проверьте папку `vendor/ffmpeg/` — она должна быть рядом с `index.html`. В .exe-версии всё уже встроено.

### YouTube просит подтвердить, что я не бот?
Обновите yt-dlp (`pip install -U yt-dlp`). Если не помогло — настройте куки, как описано [выше](#-youtube-куки-опционально).

### Скачивание обрывается или браузер ругается на длину файла?
В текущей версии это уже починено: корректные имена файлов с кириллицей, ожидание, пока файл действительно дописан на диск, и гарантированная досылка данных. Обновитесь до последней сборки.

### Где смотреть ошибки?
В `mtools_error.log` рядом с программой — там полная информация, а не невнятная ошибка в браузере.

### Сервер выключается сам?
Да, через 10 секунд после закрытия вкладки. Обычная перезагрузка страницы выключение отменяет.

## ⭐ Поддержка

Поставьте :star: этому репозиторию, если проект оказался полезным.

## ⚖️ Лицензия
MIT

---

# <span id="english-version">🇬🇧 English version</span>

<details>
<summary><strong>English version</strong></summary>

<div align="center">

# <img src="https://cdn-icons-png.flaticon.com/128/2921/2921222.png" height=28 /> MTools <sup>V0.718E</sup>

**Local media tools in your browser.**  
Trim video and audio, grab clips from YouTube — everything runs on your machine, no files are sent anywhere.

</div>

> This is a desktop app built with Python + vanilla JS. It starts a local HTTP server and opens the UI in your browser.  
> Trimming uses ffmpeg.wasm in-browser. YouTube downloads use yt-dlp on the server side.  
> No external servers, no telemetry.

## ✂️ Features

### Video / Audio Trimmer
- Open **MP4, WEBM, MP3 or WAV** via drag'n'drop
- Visual timeline: audio waveform (AudioContext) or video preview frames
- Drag start/end markers, highlighted selection range
- **Fast cut** (stream copy — no re-encoding, no quality loss) or **precise cut** re-encoded down to the millisecond
- Built-in player: click timeline → seek, drag → scrub, **Space** → pause
- Volume slider on preview hover
- Auto-return to selection: the player stays within the chosen range
- Saved through the browser dialog (`mtools_` prefix), and the dialog is requested **before** the slow work starts — no more buttons that silently do nothing
- FFmpeg is **not required** for trimming — it all runs in the browser

### ⬇️ YouTube Downloader
- Paste a link — shows title, channel, duration, views, thumbnail
- Format: **MP4** (360p / 480p / 720p / 1080p / 1440p / **4K**) or **MP3**
- **Honest quality list:** only resolutions the video actually has
- **Live progress:** percentage, speed and ETA — you can tell it's working, not hung
- **Cancel** a download at any time
- **Automatic FFmpeg installer**, no admin rights needed
- Automatic fallback around the "Sign in to confirm you're not a bot" check
- Resilient to network hiccups on large and 4K videos (fragment retries)
- Non-ASCII filename support (RFC 5987)

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
1. Download `MTools.exe` from [releases](https://github.com/Kotecy/MFast-Video-Editor-in-browser/releases)
2. Run it — a browser tab opens (`http://localhost:8000`)
3. No setup needed — bundles Python, yt-dlp and ffmpeg.wasm
4. Close the tab — the server stops automatically. Or press **"Shutdown server"**

### 🐍 From source (Python)
```bash
pip install yt-dlp PyInstaller
git clone https://github.com/Kotecy/MTools
cd MTools
python server.py
```
Opens at `http://localhost:8000`. If the port is taken, the server picks a free one and prints it to the console.

## 🔧 Building .exe
```bash
pip install yt-dlp PyInstaller
pyinstaller build.spec
```

## 🎬 FFmpeg

FFmpeg is **not** needed for trimming. It's only required for **YouTube downloads** — merging video with audio and extracting MP3.

If FFmpeg isn't found, MTools shows a dialog offering to:

- **Install automatically** — downloads the latest build from [ShareX/FFmpeg](https://github.com/ShareX/FFmpeg/releases), verifies the checksum and unpacks it into `%APPDATA%\MTools\ffmpeg`. **No admin rights required.**
- **Install manually** — if you already have FFmpeg or prefer doing it yourself.

Lookup order: bundled in the .exe → previously auto-installed → system `PATH`.

```jsonc
// Option A: read cookies from the browser where you're signed in to YouTube
{ "youtube_cookies_browser": "chrome" }   // chrome / edge / firefox / brave / opera / vivaldi

// Option B: point to an exported cookies.txt
{ "youtube_cookies_file": "C:\\path\\to\\cookies.txt" }
```

> [!WARNING]
> Cookies are sensitive data. Without this explicit setting MTools **never** touches your browser storage.



Output: `dist/MTools.exe`. Bundles `vendor/` (ffmpeg.wasm).

## 📁 Project Structure
```
MTools/
├── server.py          # HTTP server: YouTube API, FFmpeg installer, static files
├── index.html         # SPA frontend (vanilla JS)
├── build.spec         # PyInstaller config
├── vendor/
│   ├── ffmpeg/        # ffmpeg.wasm (in-browser trimming)
│   └── mt.ico         # App icon
├── dist/
│   └── MTools.exe     # Compiled executable
└── README.md
```

At runtime you may also see `mtools_config.json` (settings), `mtools_error.log` and `mtools_debug.log` (logs) next to the app.

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
| `POST` | `/api/youtube/download/cancel` | Cancel a download |
| `GET` | `/api/youtube/download/file?id=` | Download finished file |
| `GET` | `/api/ffmpeg/status` | Check whether FFmpeg is available |
| `POST` | `/api/ffmpeg/install/start` | Start the FFmpeg auto-installer |
| `GET` | `/api/ffmpeg/install/progress` | FFmpeg installation progress |
| `POST` | `/api/cancel-shutdown` | Cancel a pending shutdown (on page reload) |
| `POST` | `/api/shutdown` | Shutdown server |

## ❓ FAQ

### The page doesn't open after launch?
Check if port 8000 is free. If busy, the server auto-selects another port and shows it in the console.

### ffmpeg.wasm won't load?
Make sure `vendor/ffmpeg/` exists next to `index.html`. In the .exe version everything is pre-bundled.

### YouTube asks me to confirm I'm not a bot?
Update yt-dlp (`pip install -U yt-dlp`). If that doesn't help, set up cookies as described [above](#-youtube-cookies-optional).

### Downloads cut off, or the browser complains about content length?
Already fixed in the current version: correct Cyrillic filenames, waiting until the file is actually flushed to disk, and guaranteed full delivery of the data. Update to the latest build.

### Where do I look for errors?
In `mtools_error.log` next to the app — full details instead of a vague browser error.

### The server shuts itself down?
Yes, 10 seconds after you close the tab. A regular page reload cancels the shutdown.

## ⭐ Support

Star :star: this repo if you find it useful.

## ⚖️ License
MIT
</details>
