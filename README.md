<div align="center">

<img src="https://i.ibb.co/JjNq6snp/mt.jpg" width="96" alt="MTools" />

# MTools

**Медиа-инструменты прямо в браузере. Локально. Без облаков.**

Обрезка видео и аудио · Скачивание с YouTube · Создание GIF · Редактор изображений

[![Version](https://img.shields.io/badge/version-V0.810B-6ee7b7)](../../releases)
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
- Пресеты качества (64/128/256 цветов), сглаживание: Bayer / Floyd–Steinberg / Sierra-2 / нет
- Живой прогресс сборки и **предпросмотр готового GIF** прямо в превью
- Скорость 1–30 к/с, размер 10–100%, повторы, качественная палитра ffmpeg (palettegen + paletteuse)

## ✏️ Редактор изображений

- **Живой предпросмотр** каждого изменения + **зум колесом** и панорамирование мышкой
- **Кадрирование** с пропорциями: свободная, 1:1, 4:3, 16:9 (Enter — применить, Esc — отмена)
- **Текст на изображении** — добавляйте, тяните мышкой, меняйте размер и цвет
- Коррекция: яркость, контраст, насыщенность, оттенок, размытие, **тепло**, **виньетка**
- Пресеты: Оригинал, Ч/Б, Сепия, Холод, Тепло, Винтаж, Нуар, Хром, Инверсия
- Геометрия: масштаб 10–200%, поворот, отражения, **скругление углов**
- Кнопка **«Сравнить с оригиналом»** — удерживайте, чтобы увидеть до/после
- Геометрия: масштаб 10–200%, поворот, отражения, **скругление углов**
- Оценка размера результата **«до → ≈ после»** прямо под превью
- Экспорт в **PNG / JPEG / WEBP** с настройкой качества

## 🌐 Два языка

**RU / EN** — переключатель справа сверху. При первом запуске программа спрашивает язык.
Шестерёнка → настройки: тумблер сброса загруженного при выходе на главную. Всё офлайн, на встроенном словаре.

## ⬆️ Автообновление yt-dlp

YouTube часто меняет защиту — устаревший yt-dlp ломает скачивание (HTTP 403).
MTools при запуске сверяет версию с PyPI и предлагает обновление **в один клик**, без прав администратора.

## 📸 Скриншоты

<div align="center">

| Главная | Видео редактор | YouTube | GIF / Редактор |
|---|---|---|---|
| ![Главная](https://i.ibb.co/pvPqH70v/image.png) | ![Редактор](https://i.ibb.co/Z1mrpFtc/image.png) | ![YouTube](https://i.ibb.co/99b6XmjM/image.png) | *скоро* |

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
Для обрезки — нет (всё в браузере через ffmpeg.wasm). Для скачивания с YouTube — да, и MTools предложит установить его автоматически в %APPDATA%\MTools без прав администратора.
</details>

## ⚖️ Лицензия

MIT

---

<a id="english"></a>
<div align="center">

<img src="https://i.ibb.co/JjNq6snp/mt.jpg" width="80" alt="MTools" />

## MTools

**Media tools right in your browser. Local. Cloud-free.**

Trim video & audio · Download from YouTube · Make GIFs · Edit images

</div>

> [!NOTE]
> A desktop app built with Python + vanilla JS: it starts a local server and opens the UI in your browser.
> Trimming and the editor run on **ffmpeg.wasm** right in the browser; YouTube downloads use **yt-dlp** on the server side.
> No external servers, no telemetry — files never leave your computer.

### ✂️ Media Trimmer
Drag'n'drop **MP4, WEBM, MP3, WAV** · waveform / thumbnail timeline · markers, scrubbing, **Space** to pause · **fast cut** (stream copy) or **precise** re-encoding to the millisecond · `_mtools` suffix in saved names.

### ⬇️ YouTube Downloader
Link → title, channel, duration, views, thumbnail · **MP4** up to 4K or **MP3** (128–320 kbps) · honest quality list · live progress with speed & ETA · cancel anytime · bot-check bypass, network-hiccup resilience · Cyrillic filenames (RFC 5987).

### 🎞 GIF Maker
**From pictures**: drop a batch of frames, reorder with arrows · **from video**: MP4/WebM with start/length sliders and a live looping fragment preview · quality presets (64/128/256 colors), smoothing: Bayer / Floyd–Steinberg / Sierra-2 / none · live build progress and a **preview of the finished GIF** · 1–30 fps, 10–100% size, loop count, ffmpeg palettegen + paletteuse.

### ✏️ Image Editor
Live preview of every change + **wheel zoom** and drag-panning · **crop** with 1:1 / 4:3 / 16:9 / free ratios (Enter apply, Esc cancel) · **text on image** — add, drag with the mouse, resize, recolor · brightness, contrast, saturation, hue, blur, **warmth**, **vignette** · presets: Original, B&W, Sepia, Cold, Warm, Vintage, Noir, Chrome, Invert · geometry: scale 10–200%, rotate, flips, **corner radius** · hold-to-**compare with original** · **before → ≈ after** size estimate · export to **PNG / JPEG / WEBP**.

### 🌐 Two languages
**RU / EN** switcher in the top right, asked on first launch. Gear → settings: language and a "reset loaded content on going home" option. Fully offline, built-in dictionary.

### ⬆️ yt-dlp auto-update
YouTube changes its protection often — a stale yt-dlp breaks downloads (HTTP 403). On startup MTools checks PyPI and offers a **one-click update**, no admin rights needed.

### ⚙️ Install
**Windows EXE**: grab `MTools.exe` from [releases](../../releases), run it — the UI opens at `http://localhost:8000`. Everything is bundled.

**From source**:
```bash
git clone https://github.com/Kotecy/MTools && cd MTools
pip install yt-dlp
python server.py
```

**Build EXE**:
```bash
pip install yt-dlp pyinstaller
pyinstaller build.spec   # → dist/MTools.exe
```

### ⚖️ License
MIT
