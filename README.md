# Classroom File Share

## 教室檔案分享系統

一個適合學校電腦教室區域網路 LAN 使用的輕量級檔案分享工具。

老師在 Windows 電腦執行程式後，學生只需要使用 Chrome、Edge 等瀏覽器輸入老師電腦 IP 與 Port，即可下載老師提供的檔案或上傳作業。

不需要學生安裝程式、帳號登入、Windows SMB 共用資料夾、FTP 或雲端服務。

## 功能特色

- 學生免登入，使用瀏覽器即可下載教材與上傳作業。
- 教材顯示檔名、大小、修改日期，依時間由新到舊排列。
- 學號為 4～12 位數字，支援檔案選擇、拖曳及多檔上傳。
- 中文、空白、括號等合法檔名支援，上傳自動加上學號。
- 同名檔案加入時間與隨機後綴，避免覆蓋。
- 學生無法查看或下載其他學生上傳的檔案。
- 自動偵測老師 IPv4，優先顯示常見 LAN IP；可從清單選擇或手動修改。
- Windows tkinter GUI 管理服務啟停、設定、資料夾及學生網址。
- 預設 Port 5000、單次上傳總量 500 MB，可在設定視窗調整；單次最多 100 個檔案。
- 不需要 Windows 共用資料夾；網頁資源隨程式提供，不依賴 CDN。

## 使用方式

1. 從本專案 **Releases** 下載 `ClassroomFileShare-v1.0.0-Windows.zip`。第一次公開發佈前，維護者須先依 [發佈指南](docs/PUBLISHING.md) 上傳下載包。
2. 將 ZIP **完整解壓縮** 到有寫入權限的資料夾，不要直接在壓縮檔內執行。
3. 雙擊 `教室檔案分享.exe`，老師電腦不需要安裝 Python。
4. 第一次設定老師 IP、Port、學生下載資料夾、學生上傳資料夾。不存在的資料夾會在儲存時建立。
5. 按「儲存設定」，再按「啟動服務」。
6. 告訴學生管理畫面顯示的網址，例如 `http://192.168.1.100:5000`。
7. 學生使用 Chrome／Edge 在可互通的 LAN 連線。

以上 IP 為虛構範例，請以實際電腦位址為準。不同教室可使用相同 EXE，各自保留設定。

## 老師端

- **學生下載資料夾**：老師放教材的地方，只提供最上層檔案，不開放子資料夾。
- **學生上傳資料夾**：接收學生作業，老師從管理視窗開啟本機資料夾查看。

兩個資料夾不需開啟 Windows 共用，也不可相同或互相包含。學生沒有刪除、改名、移動或編輯功能。

管理視窗提供啟動／停止服務、修改設定、開啟兩個資料夾、複製學生網址及開啟學生端網頁。修改設定前須停止服務；關閉管理視窗也會停止服務。HTTP 在背景執行，不會卡住 GUI。

「開啟學生端網頁」供老師預覽，使用 `http://localhost:所設定的Port`，未啟動時會顯示提示。

## 學生端

1. 點「下載」取得教材；老師更新後可按「重新整理」。
2. 輸入 4～12 位半形數字學號。
3. 選擇或拖曳一個或多個檔案，查看待上傳清單。
4. 按「上傳給老師」，等待成功檔名與失敗原因提示。

上傳存成 `學號_原始檔名`，同名時自動加後綴、不覆蓋舊檔。學號只是檔名標記，並非身分驗證。

## 網路需求

老師與學生必須位於可以互相連線的 LAN。伺服器固定監聽 IPv4 `0.0.0.0`；設定的老師 IP 只用於顯示網址。

學生不能用 `localhost` 或 `0.0.0.0` 連到老師電腦。若老師能開首頁而學生無法，請檢查網卡選擇、Port、防火牆、VLAN 或無線用戶端隔離。多張網卡或換電腦時需重新確認 IP。

## Windows 防火牆

第一次使用時，Windows Defender 防火牆可能詢問是否允許通訊。請允許此程式在學校電腦教室使用的區域網路環境中通訊；學校政策限制時請洽網管。

程式不會自動修改防火牆，不需關閉 Windows 防火牆或防毒軟體。日常使用不需系統管理員權限，但程式及資料夾須有適當讀寫權限。

## 設定與隨身碟

首次儲存時，`config.json` 自動建立在 EXE 同一資料夾；開發版則在 `main.py` 同一資料夾。設定不包入 EXE，老師不用編輯 JSON，因此本專案不另附預設私人設定。設定遺失、損壞或目錄不存在時會回到設定視窗。

可將程式、設定和資料放到隨身碟。**目前設定儲存絕對路徑**：換電腦或磁碟代號後，請重新確認 IP 與兩個資料夾；尚未提供自動轉換磁碟代號功能。拔除前先停止服務、關閉程式並安全退出。

錯誤記錄於程式旁的 `classroom.log`，會輪替限制大小。設定、日誌與學生檔案不應提交 GitHub。

## 開發環境

- Python 3.10 以上（實測 3.13.3）、Flask 3.1.2、Waitress 3.0.2。
- tkinter（Windows Python 安裝時需包含 Tcl/Tk）。
- HTML／CSS／JavaScript，UTF-8 繁體中文介面。
- PyInstaller 6.15.0，Windows x64 單檔、無 Console 視窗。
- 開發及 EXE 實測：Windows 11 x64。

## 從原始碼執行

在原始碼目錄開啟 PowerShell：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

執行測試：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

測試使用暫存資料夾、localhost 並包含 tkinter，需在可啟動 GUI 的 Windows 工作階段執行。詳見 [實測報告](TEST_REPORT.md)，其中也列出尚未驗證項目。

## 建立 EXE

在 Windows 開發電腦雙擊 `build.bat`。它會建立／使用 `.venv`、安裝 `requirements-build.txt`、執行測試，再以 `classroom.spec` 打包。亦可手動執行：

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-build.txt
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean classroom.spec
```

輸出為 `dist/教室檔案分享.exe`。`classroom.spec` 包含 `templates`、`static` 與執行環境；資源使用 `sys._MEIPASS` 定位，設定則使用 EXE 所在目錄。

製作一般老師下載 ZIP：

```powershell
.\.venv\Scripts\python.exe tools/package_release.py
```

腳本只讀取現有 EXE，不會重建或修改它。輸出在 `release-artifacts/ClassroomFileShare-v1.0.0-Windows.zip`，僅含 EXE、使用說明與授權文件。新版本發佈時請同步更新版本與第三方授權說明。

## 專案結構

| 檔案／目錄 | 用途 |
| --- | --- |
| `main.py` | tkinter 老師管理程式 |
| `server.py` | Flask 路由、檔案處理及 Waitress 啟停 |
| `config_manager.py`、`paths.py` | IP、設定驗證及路徑定位 |
| `templates/`、`static/` | 學生端網頁資源 |
| `tests/` | 測試程式，不含真實學生資料 |
| `requirements*.txt`、`build.bat`、`classroom.spec` | 安裝與建置 |
| `tools/package_release.py` | 從現有 EXE 製作 Release ZIP |
| `docs/` | 使用說明、Release Notes、發佈指南與盤點 |

## 安全提醒

本系統主要設計給可信任的校內 LAN 使用，**不建議直接把 Port 對 Internet 公開**。未提供 HTTPS、登入或學號身分驗證。

- 路徑穿越、任意上傳路徑及 Windows ADS 檔名會被拒絕。下載不開放符號連結、reparse point 或有其他硬連結的檔案。
- Windows 不合法字元會替換或拒絕，檔名最多 180 個 UTF-16 字元；完整路徑仍受檔案系統限制。
- 500 MB 以 1024 × 1024 bytes 計算，是單次限制，不是資料夾總配額。大型上傳會使用暫存磁碟，請保留足夠空間。
- 斷線／停止服務可能中斷未完成上傳，請確認結果再重試；突然斷電可能留下 `.upload-*.part` 暫存檔。
- EXE 未數位簽章，未在無 Python 的乾淨 Windows、各教室跨機 LAN 或整班長時間負載下實測。

## License

[MIT License](LICENSE)，Copyright (c) 2026 lws621022。

第三方元件保留各自授權條款，隨成品附上 [THIRD_PARTY_NOTICES.txt](THIRD_PARTY_NOTICES.txt)。
