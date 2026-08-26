<div align="center">

<img src="https://i.ibb.co/JjNq6snp/mt.jpg" width="96" alt="MTools" />

# MTools

**Медиа-инструменты прямо в браузере. Локально. Без облаков.**

Обрезка видео и аудио · Скачивание с YouTube · Создание GIF · Редактор изображений

[![Version](https://img.shields.io/badge/version-V0.810F-6ee7b7)](../../releases)
[![Platform](https://img.shields.io/badge/platform-Windows-blue)](../../releases)
[![License](https://img.shields.io/badge/license-MIT-green)](#-лицензия)
[![Engine](https://img.shields.io/badge/YouTube-yt--dlp-red)](https://github.com/yt-dlp/yt-dlp)

[🇬🇧 English](#english) · [Скачать EXE](../../releases)

</div>

---

> [!NOTE]
> Десктоп-приложение на Python + vanilla JS: поднимает локальный сервер и открывает интерфейс в браузере.
> Обрезка и редактор работают на **ffmpeg.wasm** прямо в браузере, YouTube — через **yt-dlp** на стороне сервера.
> Никаких внешних серверов, никакой телеметрии — файлы не покидают компьютер.

## ✂️ Обрезка медиа

- Drag'n'drop **MP4, WEBM, MP3, WAV**
- Визуальный таймлайн: форма волны для аудио, превью-кадры для видео
- Маркеры начала/конца, скраббинг, **Space** — пауза, ползунок громкости
- **Быстрая обрезка** (stream copy, без потери качества) или **точная** — ровно по миллисекунде
- Сохранение через диалог браузера, суффикс `_mtools` в имени файла

## ⬇️ YouTube Качалка

- Ссылка → название, канал, длительность, просмотры, обложка
- **MP4** до 4K или **MP3** (битрейт 128–320)
- Честный список качеств — только то, что реально есть у ролика
- Живой прогресс: проценты, скорость, ETA + отмена в любой момент
- Обход проверки «подтвердите, что вы не бот», устойчивость к обрывам сети
- Поддержка кириллицы в именах файлов (RFC 5987)

## 🎞 Создание GIF

- **Из картинок**: пачка кадров → анимация, порядок меняется стрелками на миниатюрах
- **Из видео**: MP4/WebM → слайдеры начала и длительности фрагмента, превью сразу крутит выбранный отрезок
- Поворот и отражения — в превью и в готовом GIF
- Пресеты качества (64/128/256 цветов), сглаживание: Bayer / Floyd–Steinberg / Sierra-2 / нет
- Живой прогресс сборки и **предпросмотр готового GIF** прямо в превью
- Скорость 1–30 к/с, размер 10–100%, повторы, качественная палитра ffmpeg (palettegen + paletteuse)

## ✏️ Редактор изображений

- **Живой предпросмотр** каждого изменения + **зум колесом** и панорамирование мышкой
- **Кадрирование** с пропорциями: свободная, 1:1, 4:3, 16:9 (Enter — применить, Esc — отмена)
- **Текст на изображении** — добавляйте, тяните мышкой, позиция кнопками (верх/центр/низ), обводка, стили «Заголовок / Подпись / Водяной знак»
- Коррекция: яркость, контраст, насыщенность, оттенок, размытие, **тепло**, **виньетка**
- Пресеты: Оригинал, Ч/Б, Сепия, Холод, Тепло, Винтаж, Нуар, Хром, Инверсия
- Геометрия: масштаб 10–200%, поворот, отражения, **скругление углов**
- Кнопка **«Сравнить с оригиналом»** — удерживайте, чтобы увидеть до/после
- Оценка размера результата **«до → ≈ после»** прямо под превью
- Экспорт в **PNG / JPEG / WEBP** с настройкой качества

## 🌐 Два языка

**RU / EN** — кнопка справа сверху. При первом запуске программа спрашивает язык.
Шестерёнка → настройки: тумблер сброса загруженного при выходе на главную. Всё офлайн, на встроенном словаре.

## ⬆️ Автообновление yt-dlp

YouTube часто меняет защиту — устаревший yt-dlp ломает скачивание (HTTP 403).
MTools при запуске сверяет версию с PyPI и предлагает обновление **в один клик**, без прав администратора.

## 📸 Скриншоты

<div align="center">

| Главная | Видео редактор | YouTube |
|---|---|---|
| ![Главная](https://i.ibb.co/pvPqH70v/image.png) | ![Редактор](https://i.ibb.co/Z1mrpFtc/image.png) | ![YouTube](https://i.ibb.co/99b6XmjM/image.png) |

</div>

## ⚙️ Установка

### 🪟 Готовый EXE

1. Скачайте `MTools.exe` со страницы [релизов](../../releases)
2. Запустите — откроется браузер с приложением (`http://localhost:8000`)
3. Внутри уже всё: Python, yt-dlp, ffmpeg.wasm. FFmpeg для YouTube доустановится сам при необходимости
4. Закройте вкладку — сервер остановится сам

### 🐍 Из исходников

```bash
git clone https://github.com/Kotecy/MTools
cd MTools
pip install yt-dlp
python server.py
```

## 🔧 Сборка EXE

```bash
pip install yt-dlp pyinstaller
pyinstaller build.spec
```

Результат: `dist/MTools.exe`

## 🛠 Технологии

| Слой | Технология |
|---|---|
| Бэкенд | Python 3, `http.server` + Threading, yt-dlp |
| Фронтенд | Vanilla JS, ffmpeg.wasm, Canvas API, Web Audio |
| Сборка | PyInstaller — single-file EXE, без консоли |

## 🌐 API

| Метод | Путь | Описание |
|---|---|---|
| GET | `/api/youtube/info?url=` | Информация о видео |
| POST | `/api/youtube/download/start` | Старт скачивания → `job_id` |
| GET | `/api/youtube/progress?id=` | Прогресс |
| POST | `/api/youtube/download/cancel` | Отмена |
| GET | `/api/youtube/download/file?id=` | Готовый файл |
| GET | `/api/ffmpeg/status` | Есть ли FFmpeg |
| POST | `/api/ffmpeg/install/start` | Автоустановка FFmpeg |
| GET | `/api/ffmpeg/install/progress` | Прогресс установки |
| GET | `/api/ytdlp/version` | Проверка обновлений yt-dlp |
| POST | `/api/ytdlp/update/start` | Обновить yt-dlp |
| GET | `/api/ytdlp/update/progress?id=` | Прогресс обновления |
| GET/POST | `/api/ui-settings` | Настройки интерфейса |
| POST | `/api/cancel-shutdown` · `/api/shutdown` | Жизненный цикл сервера |

## ❓ FAQ

<details>
<summary><b>YouTube просит подтвердить, что я не бот?</b></summary>
Перезапустите MTools — программа предложит обновить yt-dlp автоматически. Если не помогло: рядом с программой создайте <code>mtools_config.json</code> с содержимым <code>{"youtube_cookies_browser": "chrome"}</code> и перезапустите.
</details>

<details>
<summary><b>Где смотреть ошибки?</b></summary>
<code>mtools_error.log</code> рядом с программой — полная информация вместо невнятной ошибки в браузере.
</details>

<details>
<summary><b>Сервер выключается сам?</b></summary>
Да, через 10 секунд после закрытия вкладки. Перезагрузка страницы отменяет выключение.
</details>

<details>
<summary><b>Нужен ли FFmpeg?</b></summary>
Для обрезки — нет (всё в браузере через ffmpeg.wasm). Для скачивания с YouTube и сборки GIF — да, и MTools предложит установить его автоматически без прав администратора.
</details>

## ⚖️ Лицензия

MIT

---

<a id="english"></a>

<details>
<summary><h2>🇬🇧 English</h2></summary>

<div align="center">

<img src="https://i.ibb.co/JjNq6snp/mt.jpg" width="80" alt="MTools" />

**Media tools right in your browser. Local. Cloud-free.**

Trim video & audio · Download from YouTube · Make GIFs · Edit images

</div>

> A desktop app built with Python + vanilla JS: it starts a local server and opens the UI in your browser.
> Trimming and the editor run on **ffmpeg.wasm** right in the browser; YouTube downloads use **yt-dlp** on the server side.
> No external servers, no telemetry — files never leave your computer.

### ✂️ Media Trimmer

- Drag'n'drop **MP4, WEBM, MP3, WAV**
- Visual timeline: waveform for audio, preview thumbnails for video
- Start/end markers, scrubbing, **Space** to pause, volume slider on hover
- **Fast cut** (stream copy, lossless) or **precise** re-encoding to the millisecond
- Saved via browser dialog with `_mtools` suffix

### ⬇️ YouTube Downloader

- Paste a link → title, channel, duration, views, thumbnail
- **MP4** up to 4K or **MP3** (128–320 kbps)
- Honest quality list — only what the video actually has
- Live progress: percentage, speed, ETA + cancel anytime
- Bot-check bypass, resilient to network drops
- Cyrillic filenames support (RFC 5987)

### 🎞 GIF Maker

- **From pictures**: drop a batch of frames → animation, reorder with arrows on thumbnails
- **From video**: MP4/WebM → start & duration sliders, preview loops the selected fragment instantly
- Rotation & flips — in both preview and exported GIF
- Quality presets (64/128/256 colors), smoothing: Bayer / Floyd–Steinberg / Sierra-2 / none
- Live build progress and **finished GIF preview** right in the viewport
- Speed 1–30 fps, size 10–100%, loop count, quality palette via ffmpeg (palettegen + paletteuse)

### ✏️ Image Editor

- **Live preview** of every change + **mouse wheel zoom** and drag panning
- **Crop** with ratios: free, 1:1, 4:3, 16:9 (Enter — apply, Esc — cancel)
- **Text on image** — add, drag with the mouse, position buttons (top/center/bottom), outline, Heading/Caption/Watermark styles
- Adjustments: brightness, contrast, saturation, hue, blur, **warmth**, **vignette**
- Presets: Original, B&W, Sepia, Cold, Warm, Vintage, Noir, Chrome, Invert
- Geometry: scale 10–200%, rotate, flips, **corner radius**
- **Compare with original** button — hold to see before/after
- Result size estimate **"before → ≈ after"** right under the preview
- Export to **PNG / JPEG / WEBP** with quality control

### 🌐 Two Languages

**RU / EN** — round button in the top right. The app asks for your language on first launch.
Gear → settings: a "reset loaded content on going home" toggle. Fully offline, built-in dictionary.

### ⬆️ yt-dlp Auto-Update

YouTube changes its protection often — a stale yt-dlp breaks downloads (HTTP 403).
MTools checks PyPI on startup and offers a **one-click update**, no admin rights needed.

### 📸 Screenshots

<div align="center">

| Home | Video Editor | YouTube |
|---|---|---|
| ![Home](https://i.ibb.co/pvPqH70v/image.png) | ![Editor](https://i.ibb.co/Z1mrpFtc/image.png) | ![YouTube](https://i.ibb.co/99b6XmjM/image.png) |

</div>

### ⚙️ Install

**Windows EXE**: download `MTools.exe` from [releases](../../releases), run it — the UI opens at `http://localhost:8000`. Everything is bundled: Python, yt-dlp, ffmpeg.wasm. FFmpeg for YouTube auto-installs if needed. Close the tab — the server stops automatically.

**From source**:
```bash
git clone https://github.com/Kotecy/MTools
cd MTools
pip install yt-dlp
python server.py
```

### 🔧 Build EXE

```bash
pip install yt-dlp pyinstaller
pyinstaller build.spec
```

Output: `dist/MTools.exe`

### 🛠 Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3, `http.server` + Threading, yt-dlp |
| Frontend | Vanilla JS, ffmpeg.wasm, Canvas API, Web Audio |
| Packaging | PyInstaller — single-file EXE, no console |

### 🌐 API

| Method | Path | Description |
|---|---|---|
| GET | `/api/youtube/info?url=` | Video info |
| POST | `/api/youtube/download/start` | Start download → `job_id` |
| GET | `/api/youtube/progress?id=` | Progress |
| POST | `/api/youtube/download/cancel` | Cancel |
| GET | `/api/youtube/download/file?id=` | Finished file |
| GET | `/api/ffmpeg/status` | FFmpeg availability |
| POST | `/api/ffmpeg/install/start` | Auto-install FFmpeg |
| GET | `/api/ffmpeg/install/progress` | Install progress |
| GET | `/api/ytdlp/version` | Check yt-dlp updates |
| POST | `/api/ytdlp/update/start` | Update yt-dlp |
| GET | `/api/ytdlp/update/progress?id=` | Update progress |
| GET/POST | `/api/ui-settings` | UI settings |
| POST | `/api/cancel-shutdown` · `/api/shutdown` | Server lifecycle |

### ❓ FAQ

<details>
<summary><b>YouTube asks me to confirm I'm not a bot?</b></summary>
Restart MTools — it will offer to update yt-dlp automatically. If that doesn't help: create a <code>mtools_config.json</code> file next to the app with <code>{"youtube_cookies_browser": "chrome"}</code> and restart.
</details>

<details>
<summary><b>Where do I look for errors?</b></summary>
<code>mtools_error.log</code> next to the app — full details instead of a vague browser error.
</details>

<details>
<summary><b>Does the server shut down on its own?</b></summary>
Yes, 10 seconds after you close the tab. Reloading the page cancels the shutdown.
</details>

<details>
<summary><b>Do I need FFmpeg?</b></summary>
Not for trimming (it runs in-browser via ffmpeg.wasm). Yes for YouTube downloads and GIF building — MTools will offer to install it automatically, no admin rights needed.
</details>

### ⚖️ License

MIT

</details>
