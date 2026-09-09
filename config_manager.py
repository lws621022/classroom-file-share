import ipaddress
import json
import os
import socket
from pathlib import Path
from paths import app_dir

DEFAULT_MAX_UPLOAD_MB = 500


class ConfigError(ValueError):
    pass


def detect_ips():
    candidates = set()
    try:
        for entry in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            candidates.add(entry[4][0])
    except OSError:
        pass
    lan = [ipaddress.ip_network(n) for n in ('10.0.0.0/8', '172.16.0.0/12', '192.168.0.0/16')]
    valid = [s for s in candidates if not ipaddress.ip_address(s).is_loopback and not ipaddress.ip_address(s).is_unspecified]
    return sorted(valid, key=lambda s: (not any(ipaddress.ip_address(s) in n for n in lan), s))


def defaults():
    ips = detect_ips()
    return dict(teacher_ip=ips[0] if ips else '', port=5000,
                download_folder=str(app_dir() / '學生下載'), upload_folder=str(app_dir() / '學生上傳'),
                max_upload_mb=DEFAULT_MAX_UPLOAD_MB)


def validate_config(data, create=False):
    try:
        ip = ipaddress.IPv4Address(data['teacher_ip'])
        if ip.is_loopback or ip.is_unspecified or ip.is_multicast or str(ip) == '255.255.255.255':
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise ConfigError('請輸入有效的老師 IPv4 位址（不可使用 127.0.0.1）。')
    try:
        port = int(str(data['port']))
        limit = int(str(data.get('max_upload_mb', DEFAULT_MAX_UPLOAD_MB)))
        if not 1 <= port <= 65535 or not 1 <= limit <= 102400:
            raise ValueError()
    except (KeyError, ValueError, TypeError):
        raise ConfigError('Port 必須介於 1～65535；上傳容量必須介於 1～102400 MB。')
    folders = []
    for key in ('download_folder', 'upload_folder'):
        value = data.get(key)
        if not isinstance(value, str) or not value.strip() or not Path(value).is_absolute():
            raise ConfigError('請選擇完整的資料夾路徑。')
        try:
            folders.append(Path(value).resolve())
        except (OSError, ValueError, RuntimeError) as exc:
            raise ConfigError('資料夾路徑無效，請重新選擇。') from exc
    a, b = folders
    if a == b or a in b.parents or b in a.parents:
        raise ConfigError('下載與上傳資料夾不可相同，也不可互相包含。')
    try:
        for folder in folders:
            if create:
                folder.mkdir(parents=True, exist_ok=True)
            if not folder.is_dir():
                raise ConfigError(f'資料夾不存在：{folder}，請重新設定。')
    except OSError as exc:
        raise ConfigError(f'無法存取資料夾：{exc}') from exc
    return dict(teacher_ip=str(ip), port=port, download_folder=str(a), upload_folder=str(b), max_upload_mb=limit)


def load_config(path=None):
    try:
        data = json.loads((path or app_dir() / 'config.json').read_text(encoding='utf-8-sig'))
        if not isinstance(data, dict):
            raise ValueError()
    except (OSError, ValueError) as exc:
        raise ConfigError('找不到設定檔或 JSON 格式損壞，請設定後儲存。') from exc
    return validate_config(data)


def save_config(data, path=None):
    data = validate_config(data, create=True)
    path = path or app_dir() / 'config.json'
    temp = path.with_suffix('.json.tmp')
    try:
        temp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, path)
    except OSError as exc:
        raise ConfigError('無法儲存設定，請將程式放在有寫入權限的資料夾。') from exc
    return data
