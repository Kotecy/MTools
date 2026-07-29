#!/usr/bin/env python3
"""
Простой локальный сервер для запуска index.html с заголовками
Cross-Origin-Opener-Policy / Cross-Origin-Embedder-Policy.

Одно-поточное ядро ffmpeg.wasm (@ffmpeg/core), используемое в этом
проекте, обычно работает и без этих заголовков. Но если вы захотите
подключить многопоточное ядро (@ffmpeg/core-mt) для более быстрой
обработки, оно требует SharedArrayBuffer, а значит и режим
"cross-origin isolated" — который как раз включают эти заголовки.
Поэтому сервер настроен на них по умолчанию: это не мешает работе
текущей версии и сразу готово к апгрейду.

Запуск:
    python3 server.py [порт]

По умолчанию порт 8000. Затем откройте http://localhost:8000/
"""
import sys
import http.server
import socketserver

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000


class COOPCOEPHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        self.send_header("Cross-Origin-Opener-Policy", "same-origin")
        self.send_header("Cross-Origin-Embedder-Policy", "require-corp")
        self.send_header("Cross-Origin-Resource-Policy", "cross-origin")
        super().end_headers()


if __name__ == "__main__":
    with socketserver.TCPServer(("", PORT), COOPCOEPHandler) as httpd:
        print(f"Сервер запущен: http://localhost:{PORT}/")
        print("Остановить — Ctrl+C")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nОстановлено.")