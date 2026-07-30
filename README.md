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

<<<<<<< HEAD
![Главный экран](https://i.ibb.co/pvPqH70v/image.png)
![Обрезка видео](https://i.ibb.co/Z1mrpFtc/image.png)
![YouTube Download](https://i.ibb.co/99b6XmjM/image.png)
=======
![Главный экран]([https://via.placeholder.com/800x450/0D0E12/6EE7D1?text=MTools+Home](https://ibb.co/vxB9NFwx))
![Обрезка видео]([https://via.placeholder.com/800x450/171A21/E8E6E1?text=Trimmer](https://ibb.co/3Yzb9jGS))
![YouTube Download]([https://via.placeholder.com/800x450/171A21/F47174?text=YouTube+Download](https://ibb.co/ns792qSW))
>>>>>>> 881b6089585731a6609c862f4f3fc4436c111396

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
