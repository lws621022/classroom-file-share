# v1.0.0 公開分享盤點

整理日期：2026-09-09。保留現有可用程式、虛擬環境、建置產物與測試檔案；沒有刪除或重新建置正式 EXE。

## 檔案分類

| 主要檔案／資料夾 | 類型 | GitHub Source Repository |
| --- | --- | --- |
| `main.py`、`server.py`、`config_manager.py`、`paths.py` | 應用程式原始碼 | 納入 |
| `templates/index.html`、`static/style.css`、`static/app.js` | 網頁原始碼 | 納入 |
| `tests/test_system.py` | 以暫存資料生成的自動測試 | 納入，不是真實學生作業 |
| `requirements.txt`、`requirements-build.txt` | 套件清單 | 納入 |
| `classroom.spec`、`build.bat` | PyInstaller 建置設定／腳本 | 納入，保留 spec |
| `README.md`、`TEST_REPORT.md`、`docs/` | 說明、測試報告、發佈文件 | 納入 |
| `LICENSE`、`THIRD_PARTY_NOTICES.txt` | 專案與第三方授權 | 納入 |
| `.gitignore`、`.gitattributes`、`tools/package_release.py` | Git 規則、Release 製作腳本 | 納入 |
| `config.json` 及其暫存／備份 | 本機老師 IP 與資料夾設定 | 排除；本次盤點時專案及 dist 無此檔 |
| `.venv/` | 本機 Python 套件與路徑 | 排除，保留本機 |
| `__pycache__/` 及巢狀 cache、`*.pyc` | Python 執行快取 | 排除，保留本機 |
| `build/` | PyInstaller 中間產物、分析報告、含本機路徑 | 排除，保留本機 |
| `dist/教室檔案分享.exe` | PyInstaller 正式單檔成品 | 排除於來源庫，放入 Release ZIP |
| `dist/學生下載/`、`dist/學生上傳/` | 執行時資料夾（盤點時為空） | 排除 |
| `test-output/` | 開發時生成的測試教材／作業 | 排除，保留本機 |
| `release-artifacts/` | Windows ZIP 與 SHA-256 | 排除，供 Releases 附件使用 |
| `*.log`、`*.log.*`、`*.tmp`、`*.part` | 日誌與暫存檔 | 排除 |
| `.git/` | 本機版本控制資料 | 不以檔案附件上傳；commit 經 Git push 傳送 |

## 隱私與內容處理

- 沒有既有 LICENSE 或與指定作者衝突的專案作者聲明；新增 MIT，作者為 `lws621022`、年份 2026。
- 原 README 與測試採用了需求中的教室位址範例，公開 README 改為明確標示的虛構 LAN 範例；測試改用文件專用 IP，HTTP 仍只測 localhost。
- LAN 偵測網段、localhost、`0.0.0.0` 是必要技術常數，不是學校實際設定。Windows 攻擊測試中的假路徑與 `secret.txt` 是測試字串，不是私人檔案或密碼。
- 原本全域 Git 身分含學校電子郵件；本專案使用 noreply commit 位址，不改動全域設定。第三方授權中的作者及聯絡資料屬上游公開授權聲明，保持原文。
- 本機 build／虛擬環境含絕對路徑，全部排除，不刪除目前開發環境。
- EXE 內部封裝清單沒有私人 config.json、測試檔或學生資料；已檢查解壓的封裝項目及 Python archive，未發現本次已知的私人位址、使用者目錄或工作目錄標記。應用程式 code filename 為相對模組名稱。
- 掃描不等同對任意未知機密的數學保證；未來加入檔案後仍須逐次檢查。

## EXE 與 Release

`classroom.spec` 把 binaries／datas 直接傳入 EXE，沒有 COLLECT；檢查現有封裝也確認是 onefile，已含 Python、Tcl/Tk、HTML、CSS、JavaScript。原檔位於 `dist/教室檔案分享.exe`。

保留原始 SHA-256：

```text
f9dd9ed47ca6cfd2d189d25b54834c851f528ba4f483f356a4571e89b178e282
```

下載包只有以下內容，不帶預設 config.json；第一次按儲存時由程式建立設定：

```text
ClassroomFileShare-v1.0.0/
├─ 教室檔案分享.exe
├─ 使用說明.txt
├─ LICENSE
└─ THIRD_PARTY_NOTICES.txt
```

第三方授權文字來自本機實際建置依賴及 Python／Tcl/Tk 的授權檔，未將本機絕對來源路徑寫入授權文件。

本次不修改應用程式行為；僅修改文件、測試用 IP、Git 排除規則和 Release 製作工具。既有 GUI／瀏覽器驗證見 `TEST_REPORT.md`，未將未測試項目宣稱通過。
