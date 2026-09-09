import logging
import os
import re
import shutil
import socket
import stat
import tempfile
import threading
import unicodedata
import uuid
from datetime import datetime
from pathlib import Path

from flask import Flask, abort, jsonify, render_template, request, send_file
from werkzeug.exceptions import HTTPException, RequestEntityTooLarge
from waitress import create_server
from waitress import wasyncore
from waitress.task import ThreadedTaskDispatcher
from config_manager import validate_config
from paths import resource_dir


def safe_name(name):
    name = unicodedata.normalize('NFC', name or '')
    if not name or name in ('.', '..') or any(c in name for c in '/\\:') or any(ord(c) < 32 for c in name):
        raise ValueError('檔名包含不允許的路徑或控制字元。')
    name = re.sub(r'[<>"|?*]', '_', name).rstrip(' .')
    if not name or len(name.encode('utf-16-le')) > 360:
        raise ValueError('檔名為空或過長（最多 180 個 UTF-16 字元）。')
    return name


def plain_file(path, root):
    """Reject Windows reparse points, symbolic links and external hard links."""
    try:
        info = path.lstat()
        return (path.parent.resolve() == root and path.resolve().parent == root
                and stat.S_ISREG(info.st_mode) and not path.is_symlink()
                and not getattr(info, 'st_file_attributes', 0) & 0x400 and info.st_nlink == 1)
    except OSError:
        return False


def create_app(settings):
    settings = validate_config(settings)
    assets = resource_dir()
    app = Flask(__name__, template_folder=str(assets / 'templates'), static_folder=str(assets / 'static'))
    limit = settings['max_upload_mb'] * 1024 * 1024
    # Multipart envelope allowance; actual file bytes are checked separately.
    app.config.update(MAX_CONTENT_LENGTH=limit + 1024 * 1024, MAX_FORM_PARTS=200, MAX_FORM_MEMORY_SIZE=1024 * 1024)
    downloads = Path(settings['download_folder']).resolve()
    uploads = Path(settings['upload_folder']).resolve()

    @app.after_request
    def headers(response):
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['Content-Security-Policy'] = "default-src 'self'; style-src 'self'; script-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
        response.headers['Cache-Control'] = 'no-store'
        return response

    @app.get('/')
    def index():
        return render_template('index.html', max_upload_mb=settings['max_upload_mb'])

    @app.get('/api/files')
    def files():
        result = []
        try:
            for path in downloads.iterdir():
                if plain_file(path, downloads):
                    try:
                        info = path.stat()
                        result.append(dict(name=path.name, size=info.st_size, modified=info.st_mtime))
                    except OSError:
                        continue
        except OSError:
            return jsonify(error='無法讀取老師的下載資料夾，請通知老師。'), 503
        return jsonify(files=sorted(result, key=lambda f: (-f['modified'], f['name'])))

    @app.get('/download/<path:name>')
    def download(name):
        try:
            if safe_name(name) != name:
                abort(404)
        except ValueError:
            abort(404)
        target = downloads / name
        if not plain_file(target, downloads):
            abort(404)
        try:
            return send_file(target, as_attachment=True, download_name=name, mimetype='application/octet-stream')
        except OSError:
            abort(404)

    @app.post('/api/upload')
    def upload():
        student = request.form.get('student_id', '')
        if not re.fullmatch(r'[0-9]{4,12}', student):
            return jsonify(error='請輸入正確的學號。'), 400
        incoming = request.files.getlist('files')
        if not incoming or all(not f.filename for f in incoming):
            return jsonify(error='請先選擇檔案。'), 400
        if len(incoming) > 100:
            return jsonify(error='單次最多上傳 100 個檔案。'), 400
        # Check total before saving any files (Flask spools large parts to disk).
        total = 0
        for item in incoming:
            item.stream.seek(0, 2)
            total += item.stream.tell()
            item.stream.seek(0)
        if total > limit:
            raise RequestEntityTooLarge()
        saved, failed = [], []
        for item in incoming:
            staging = None
            try:
                name = f'{student}_{safe_name(item.filename)}'
                with tempfile.NamedTemporaryFile(dir=uploads, prefix='.upload-', suffix='.part', delete=False) as out:
                    staging = Path(out.name)
                    shutil.copyfileobj(item.stream, out, length=1024 * 1024)
                # Hard-link creation is atomic and never replaces an existing file.
                # A completed staging file is published only after writing succeeds.
                target = uploads / name
                for attempt in range(20):
                    try:
                        if os.name == 'nt':
                            os.rename(staging, target)  # Windows rename never overwrites.
                        else:
                            os.link(staging, target)
                            staging.unlink()
                        staging = None
                        saved.append(target.name)
                        break
                    except FileExistsError:
                        base = Path(name)
                        target = uploads / f'{base.stem}_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}{base.suffix}'
                else:
                    raise OSError('無法建立唯一檔名')
            except ValueError as exc:
                failed.append(dict(name=item.filename, reason=str(exc)))
            except OSError:
                app.logger.exception('Upload failed')
                failed.append(dict(name=item.filename, reason='無法儲存檔案，請通知老師檢查空間與資料夾權限。'))
            finally:
                if staging is not None:
                    try:
                        staging.unlink(missing_ok=True)
                    except OSError:
                        app.logger.exception('Cannot remove incomplete upload')
        return jsonify(saved=saved, failed=failed), (200 if saved else 400)

    @app.errorhandler(413)
    def too_large(error):
        return jsonify(error='檔案過大，無法上傳。'), 413

    @app.errorhandler(Exception)
    def errors(error):
        if isinstance(error, HTTPException):
            return jsonify(error={404: '找不到檔案或頁面。', 405: '不允許此操作。'}.get(error.code, '請求格式不正確。')), error.code
        app.logger.exception('Request failed')
        return jsonify(error='處理失敗，請稍後重試或通知老師。'), 500

    return app


class ServerController:
    def __init__(self):
        self.thread = None
        self.stop_event = threading.Event()
        self.error = None

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, settings):
        if self.running:
            return
        app = create_app(settings)
        self.stop_event.clear()
        self.error = None
        dispatcher = ThreadedTaskDispatcher()
        dispatcher.set_thread_count(8)
        sockets = {}
        listener = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            if os.name == 'nt':
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            else:
                listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            listener.bind(('0.0.0.0', settings['port']))
            listener.listen(128)
            server = create_server(app, sockets=[listener], map=sockets,
                                   _dispatcher=dispatcher, max_request_body_size=app.config['MAX_CONTENT_LENGTH'] + 1024 * 1024,
                                   channel_timeout=120, connection_limit=128)
        except Exception:
            listener.close()
            dispatcher.shutdown()
            for channel in list(sockets.values()):
                channel.close()
            raise
        self.port = server.effective_port

        def run():
            try:
                while not self.stop_event.is_set():
                    wasyncore.loop(timeout=0.1, count=1, map=sockets)
            except Exception as exc:
                self.error = str(exc)
                logging.exception('Server stopped unexpectedly')
            finally:
                server.close()
                dispatcher.shutdown(timeout=30)
                for channel in list(sockets.values()):
                    channel.close()
        self.thread = threading.Thread(target=run, name='classroom-server', daemon=True)
        self.thread.start()

    def request_stop(self):
        self.stop_event.set()

    def stop(self, timeout=35):
        self.request_stop()
        if self.thread:
            self.thread.join(timeout)
            if self.thread.is_alive():
                raise RuntimeError('服務仍在完成檔案處理，請稍後再試。')
