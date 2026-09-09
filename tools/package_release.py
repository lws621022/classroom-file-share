"""Package the existing onefile EXE without modifying it or including runtime data."""
import hashlib
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VERSION = 'v1.0.0'


def main():
    files = {
        '教室檔案分享.exe': ROOT / 'dist' / '教室檔案分享.exe',
        '使用說明.txt': ROOT / 'docs' / '使用說明.txt',
        'LICENSE': ROOT / 'LICENSE',
        'THIRD_PARTY_NOTICES.txt': ROOT / 'THIRD_PARTY_NOTICES.txt',
    }
    for source in files.values():
        if not source.is_file():
            raise SystemExit(f'缺少必要檔案：{source.name}')
    exe_hash = hashlib.sha256(files['教室檔案分享.exe'].read_bytes()).hexdigest()
    output = ROOT / 'release-artifacts'
    output.mkdir(exist_ok=True)
    archive = output / f'ClassroomFileShare-{VERSION}-Windows.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED) as package:
        for name, source in files.items():
            package.write(source, f'ClassroomFileShare-{VERSION}/{name}')
    with zipfile.ZipFile(archive) as package:
        assert package.testzip() is None
        assert set(package.namelist()) == {f'ClassroomFileShare-{VERSION}/{n}' for n in files}
        assert hashlib.sha256(package.read(f'ClassroomFileShare-{VERSION}/教室檔案分享.exe')).hexdigest() == exe_hash
    assert hashlib.sha256(files['教室檔案分享.exe'].read_bytes()).hexdigest() == exe_hash
    zip_hash = hashlib.sha256(archive.read_bytes()).hexdigest()
    (output / 'SHA256SUMS.txt').write_text(f'{zip_hash}  {archive.name}\n', encoding='utf-8')
    print(f'完成：{archive.name}\nEXE SHA256：{exe_hash}\nZIP SHA256：{zip_hash}')


if __name__ == '__main__':
    main()
