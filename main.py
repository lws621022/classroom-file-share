import logging
from logging.handlers import RotatingFileHandler
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import webbrowser

from config_manager import ConfigError, defaults, detect_ips, load_config, save_config
from paths import app_dir
from server import ServerController


class TeacherApp:
    def __init__(self, root):
        self.root = root
        self.server = ServerController()
        self.settings = None
        self.closing = False
        self.stopping = False
        root.title('教室檔案分享系統')
        root.geometry('790x580')
        root.minsize(690, 530)
        root.option_add('*Font', ('Microsoft JhengHei UI', 10))
        style = ttk.Style(root)
        style.theme_use('clam')
        style.configure('TButton', padding=(12, 9))
        style.configure('Title.TLabel', font=('Microsoft JhengHei UI', 22, 'bold'))
        body = ttk.Frame(root, padding=28)
        body.pack(fill='both', expand=True)
        ttk.Label(body, text='教室檔案分享系統', style='Title.TLabel').pack(anchor='w')
        ttk.Label(body, text='老師管理介面  ·  校內區域網路專用').pack(anchor='w', pady=(5, 16))
        self.status = tk.StringVar(value='● 尚未啟動')
        ttk.Label(body, textvariable=self.status, foreground='#087c68').pack(anchor='w', pady=(0, 16))
        self.details = {}
        for key, label in [('teacher_ip', '老師 IP'), ('url', '學生網址'), ('port', 'Port'),
                           ('download_folder', '學生下載資料夾'), ('upload_folder', '學生上傳資料夾')]:
            row = ttk.Frame(body)
            row.pack(fill='x', pady=5)
            ttk.Label(row, text=label, width=18).pack(side='left')
            var = tk.StringVar(value='尚未設定')
            self.details[key] = var
            ttk.Entry(row, textvariable=var, state='readonly').pack(side='left', fill='x', expand=True)
        actions = ttk.Frame(body)
        actions.pack(fill='x', pady=(22, 8))
        self.start_button = ttk.Button(actions, text='啟動服務', command=self.start)
        self.start_button.grid(row=0, column=0, padx=(0, 8), pady=5, sticky='ew')
        self.stop_button = ttk.Button(actions, text='停止服務', command=self.stop, state='disabled')
        self.stop_button.grid(row=0, column=1, padx=8, pady=5, sticky='ew')
        self.config_button = ttk.Button(actions, text='修改設定', command=self.configure)
        self.config_button.grid(row=0, column=2, padx=8, pady=5, sticky='ew')
        for i, (text, command) in enumerate([('開啟下載資料夾', lambda: self.open_folder('download_folder')),
                                            ('開啟上傳資料夾', lambda: self.open_folder('upload_folder')),
                                            ('開啟學生端網頁', self.open_browser)]):
            ttk.Button(actions, text=text, command=command).grid(row=1, column=i, padx=(0 if i == 0 else 8, 8), pady=5, sticky='ew')
            actions.columnconfigure(i, weight=1)
        ttk.Button(body, text='複製學生網址', command=self.copy_url).pack(anchor='w', pady=5)
        ttk.Label(body, text='學生與老師須連接同一個 LAN。關閉此視窗會停止分享。').pack(anchor='w', pady=(14, 0))
        root.protocol('WM_DELETE_WINDOW', self.close)
        try:
            self.settings = load_config()
            self.refresh()
        except ConfigError as exc:
            self.start_button.configure(state='disabled')
            root.after(100, lambda reason=str(exc): self.configure(reason))
        root.after(150, self.poll)

    def refresh(self):
        if self.settings:
            for key, var in self.details.items():
                var.set(self.url if key == 'url' else str(self.settings[key]))
            self.start_button.configure(state='normal')

    @property
    def url(self):
        return f"http://{self.settings['teacher_ip']}:{self.settings['port']}"

    def configure(self, reason=''):
        if self.server.running or self.stopping:
            messagebox.showinfo('修改設定', '請先停止服務再修改設定。', parent=self.root)
            return
        dialog = tk.Toplevel(self.root)
        dialog.title('教室檔案分享 · 設定')
        dialog.geometry('760x420')
        dialog.transient(self.root)
        dialog.grab_set()
        frame = ttk.Frame(dialog, padding=24)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=reason or '設定學生連線資訊與檔案資料夾', wraplength=680).grid(row=0, column=0, columnspan=3, sticky='w', pady=(0, 18))
        values = self.settings or defaults()
        variables = {k: tk.StringVar(value=str(v)) for k, v in values.items()}
        labels = [('teacher_ip', '老師 IP'), ('port', 'Port'), ('download_folder', '學生下載資料夾'),
                  ('upload_folder', '學生上傳資料夾'), ('max_upload_mb', '單次上傳上限 (MB)')]
        for row, (key, label) in enumerate(labels, 1):
            ttk.Label(frame, text=label).grid(row=row, column=0, sticky='w', padx=(0, 16), pady=9)
            if key == 'teacher_ip':
                entry = ttk.Combobox(frame, textvariable=variables[key], values=detect_ips())
            else:
                entry = ttk.Entry(frame, textvariable=variables[key])
            entry.grid(row=row, column=1, sticky='ew', pady=9)
            if key.endswith('_folder'):
                def browse(k=key):
                    path = filedialog.askdirectory(parent=dialog, title='選擇資料夾', mustexist=False)
                    if path:
                        variables[k].set(path)
                ttk.Button(frame, text='選擇…', command=browse).grid(row=row, column=2, padx=(10, 0))
        frame.columnconfigure(1, weight=1)
        ttk.Label(frame, text='IP 可從清單選擇或手動輸入；不存在的資料夾將自動建立。').grid(row=6, column=0, columnspan=3, sticky='w', pady=12)
        def save():
            try:
                self.settings = save_config({k: v.get().strip() for k, v in variables.items()})
            except (ConfigError, OSError) as exc:
                messagebox.showerror('設定未儲存', str(exc), parent=dialog)
                return
            self.refresh()
            dialog.destroy()
        ttk.Button(frame, text='儲存設定', command=save).grid(row=7, column=1, sticky='e', pady=8)
        ttk.Button(frame, text='取消', command=dialog.destroy).grid(row=7, column=2, padx=(10, 0))

    def start(self):
        if not self.settings:
            self.configure()
            return
        try:
            self.server.start(self.settings)
        except Exception as exc:
            logging.exception('Cannot start service')
            messagebox.showerror('無法啟動服務', f'請檢查資料夾、Port 是否已被使用，以及網路權限。\n\n{exc}', parent=self.root)
            return
        self.status.set('● 服務執行中')
        self.start_button.configure(state='disabled')
        self.config_button.configure(state='disabled')
        self.stop_button.configure(state='normal')

    def stop(self):
        self.stopping = True
        self.status.set('● 正在停止服務，請稍候…')
        self.stop_button.configure(state='disabled')
        self.server.request_stop()

    def poll(self):
        if not self.server.running:
            if self.closing:
                self.root.destroy()
                return
            if self.stopping or self.status.get() == '● 服務執行中':
                self.status.set('● 服務已停止' if not self.server.error else '● 服務異常停止，請重新啟動')
                self.stopping = False
                self.start_button.configure(state='normal' if self.settings else 'disabled')
                self.config_button.configure(state='normal')
                self.stop_button.configure(state='disabled')
        self.root.after(150, self.poll)

    def open_folder(self, key):
        if not self.settings:
            return
        try:
            os.startfile(self.settings[key])
        except OSError as exc:
            messagebox.showerror('無法開啟資料夾', str(exc), parent=self.root)

    def open_browser(self):
        if not self.server.running or self.stopping:
            messagebox.showinfo('尚未啟動', '請先啟動服務。', parent=self.root)
            return
        webbrowser.open(f"http://localhost:{self.settings['port']}")

    def copy_url(self):
        if self.settings:
            self.root.clipboard_clear()
            self.root.clipboard_append(self.url)

    def close(self):
        self.closing = True
        self.stop()


def main():
    try:
        handler = RotatingFileHandler(app_dir() / 'classroom.log', maxBytes=2_000_000, backupCount=2, encoding='utf-8')
        logging.basicConfig(handlers=[handler], level=logging.WARNING, format='%(asctime)s %(levelname)s %(message)s')
    except OSError:
        logging.basicConfig(handlers=[logging.NullHandler()])
    root = tk.Tk()
    TeacherApp(root)
    root.mainloop()


if __name__ == '__main__':
    main()
