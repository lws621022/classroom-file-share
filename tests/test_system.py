import io
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from config_manager import ConfigError, load_config, save_config, validate_config
from server import create_app, ServerController


def available_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


class SystemTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.base = Path(self.temp.name)
        self.down, self.up = self.base / '下載', self.base / '上傳'
        self.down.mkdir(); self.up.mkdir()
        # Documentation-only IPv4; actual HTTP tests connect to loopback.
        self.config = dict(teacher_ip='192.0.2.100', port=available_port(), download_folder=str(self.down), upload_folder=str(self.up), max_upload_mb=1)
        self.app = create_app(self.config)
        self.client = self.app.test_client()

    def tearDown(self):
        self.temp.cleanup()

    def upload(self, names, student='413523', client=None):
        response = (client or self.client).post('/api/upload', data={'student_id': student, 'files': [(io.BytesIO(content), name) for name, content in names]})
        # The test client's multipart builder owns a separate request-body tempfile.
        response.request.environ['wsgi.input'].close()
        return response

    def test_home_and_empty(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn('教室檔案分享系統', response.get_data(as_text=True))
        self.assertEqual(self.client.get('/api/files').json, {'files': []})
        with self.client.get('/static/app.js') as response:
            self.assertEqual(response.status_code, 200)

    def test_download_names_and_sort(self):
        names = ['example.cpp', '作業 說明 (一) #&+.pdf']
        for i, name in enumerate(names):
            path = self.down / name
            path.write_bytes(b'test content')
            os.utime(path, (100 + i, 100 + i))
            with self.client.get('/download/' + urllib.parse.quote(name, safe='')) as response:
                self.assertEqual(response.data, b'test content')
                self.assertIn('attachment', response.headers['Content-Disposition'])
        self.assertEqual([f['name'] for f in self.client.get('/api/files').json['files']], list(reversed(names)))

    def test_single_multi_unicode_and_collision(self):
        self.assertEqual(self.upload([('作業 (一).cpp', b'first')]).status_code, 200)
        r = self.upload([('作業 (一).cpp', b'second'), ('homework.py', b'python')])
        self.assertEqual(len(r.json['saved']), 2)
        self.assertEqual((self.up / '413523_作業 (一).cpp').read_bytes(), b'first')
        self.assertEqual((self.up / r.json['saved'][0]).read_bytes(), b'second')
        self.assertTrue(r.json['saved'][0].endswith('.cpp'))

    def test_parallel_collision(self):
        def worker(i):
            with self.app.test_client() as client:
                return self.upload([('same.txt', str(i).encode())], client=client).json['saved'][0]
        with ThreadPoolExecutor(max_workers=8) as pool:
            names = list(pool.map(worker, range(12)))
        self.assertEqual(len(set(names)), 12)
        self.assertEqual({(self.up / n).read_bytes() for n in names}, {str(i).encode() for i in range(12)})

    def test_student_validation(self):
        for student in ['', '123', '1234567890123', '123a', '../12', '１２３４']:
            r = self.upload([('a.txt', b'a')], student)
            self.assertEqual(r.status_code, 400)
            self.assertEqual(r.json['error'], '請輸入正確的學號。')

    def test_traversal_and_private_files(self):
        (self.base / 'secret.txt').write_text('secret')
        (self.up / 'private.txt').write_text('private')
        for path in ['/download/../secret.txt', '/download/%2e%2e%2fsecret.txt', '/download/..%5csecret.txt', '/download/C:%5cWindows%5cwin.ini', '/download/a.txt:stream', '/download/private.txt', '/uploads/private.txt', '/api/uploads', '/download/missing.txt']:
            self.assertEqual(self.client.get(path).status_code, 404, path)
        for name in ['../x.txt', '..\\x.txt', 'C:\\x.txt', '/tmp/x.txt', 'a.txt:stream']:
            self.assertEqual(self.upload([(name, b'bad')]).status_code, 400)
        self.assertEqual(self.client.delete('/download/private.txt').status_code, 405)
        self.assertEqual(self.client.get('/api/files').json['files'], [])

    def test_hard_link_not_shared(self):
        secret = self.base / 'secret.txt'; secret.write_text('secret')
        os.link(secret, self.down / 'linked.txt')
        self.assertEqual(self.client.get('/api/files').json['files'], [])
        self.assertEqual(self.client.get('/download/linked.txt').status_code, 404)

    def test_limit_and_partial_failure(self):
        r = self.upload([('a.bin', b'a' * 600000), ('b.bin', b'b' * 600000)])
        self.assertEqual(r.status_code, 413)
        self.assertEqual(list(self.up.iterdir()), [])
        self.assertEqual(self.upload([('a.bin', b'a' * 3100000)]).status_code, 413)
        r = self.upload([('../bad.txt', b'x'), ('ok.txt', b'ok')])
        self.assertEqual(len(r.json['saved']), 1)
        self.assertEqual(len(r.json['failed']), 1)
        self.assertEqual(self.client.get('/').status_code, 200)
        self.assertFalse(list(self.up.glob('*.part')))

    def test_config_errors_persistence_and_paths(self):
        path = self.base / 'config.json'
        with self.assertRaises(ConfigError): load_config(path)
        path.write_text('{broken')
        with self.assertRaises(ConfigError): load_config(path)
        path.write_text('[]')
        with self.assertRaises(ConfigError): load_config(path)
        with self.assertRaises(ConfigError):
            validate_config(dict(self.config, upload_folder=str(self.base / 'invalid') + '\x00'))
        save_config(self.config, path)
        self.assertEqual(load_config(path), self.config)
        for upload in [str(self.down), str(self.down / 'nested'), str(self.base)]:
            with self.assertRaises(ConfigError): validate_config(dict(self.config, upload_folder=upload))
        missing = dict(self.config, upload_folder=str(self.base / 'new'))
        with self.assertRaises(ConfigError): validate_config(missing)
        save_config(missing, path)
        self.assertTrue((self.base / 'new').is_dir())

    def test_real_server_stop_restart_and_port_conflict(self):
        controller = ServerController()
        try:
            controller.start(self.config)
            with urllib.request.urlopen(f"http://localhost:{self.config['port']}", timeout=5) as response:
                self.assertEqual(response.status, 200)
            other = ServerController()
            with self.assertRaises(OSError): other.start(self.config)
            controller.stop()
            self.assertFalse(controller.running)
            with self.assertRaises(OSError): urllib.request.urlopen(f"http://localhost:{self.config['port']}", timeout=1)
            controller.start(self.config)
            self.assertTrue(controller.running)
        finally:
            controller.stop()

    def test_gui_remains_responsive(self):
        import tkinter as tk
        from main import TeacherApp
        root = tk.Tk(); root.withdraw()
        try:
            with patch('main.load_config', return_value=self.config):
                gui = TeacherApp(root)
            gui.start_button.invoke()
            ticks = []
            root.after(10, lambda: ticks.append(True))
            deadline = time.monotonic() + 0.4
            while time.monotonic() < deadline:
                root.update(); time.sleep(.01)
            self.assertTrue(ticks)
            self.assertTrue(gui.server.running)
            gui.copy_url()
            self.assertEqual(root.clipboard_get(), gui.url)
            gui.stop_button.invoke()
            deadline = time.monotonic() + 5
            while gui.stopping and time.monotonic() < deadline:
                root.update(); time.sleep(.02)
            self.assertFalse(gui.server.running)
            self.assertFalse(gui.stopping)
        finally:
            if 'gui' in locals(): gui.server.stop()
            for task in root.tk.call('after', 'info'): root.after_cancel(task)
            root.destroy()


if __name__ == '__main__':
    unittest.main()
