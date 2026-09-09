# GitHub 發佈指南

## 專案資料

- Repository：`classroom-file-share`
- 顯示名稱（README）：`Classroom File Share - 教室檔案分享系統`
- Description：`A lightweight LAN file sharing tool for computer classrooms. Teachers can share files and receive student uploads through a web browser.`
- 版本標籤：`v1.0.0`
- Release 標題：`Classroom File Share v1.0.0`

GitHub Repository 名稱使用 `classroom-file-share`；較長的中英文名稱用於 README／對外介紹。

## 建立 GitHub Repository 並推送

本次僅準備本機 Git commit，沒有建立遠端或 push。到 GitHub 登入自己的帳號，建立名稱為 `classroom-file-share` 的 Public 空白 Repository。**不要另外勾選建立 README、.gitignore 或 License**，本機已包含這些檔案，避免產生另一段歷史。

複製 GitHub 顯示的實際遠端網址，在本機專案目錄執行下列命令。先將文字佔位符換成剛建立的 Repository URL：

```powershell
git remote add origin "貼上實際的GitHub遠端網址"
git remote -v
git push -u origin main
```

登入請使用 GitHub 支援的驗證流程，不要將權杖寫入遠端 URL、原始碼或文件。流程參考 [GitHub：加入本機原始碼](https://docs.github.com/en/migrations/importing-source-code/using-the-command-line-to-import-source-code/adding-locally-hosted-code-to-github)。

本專案 commit 使用 `lws621022` 及 noreply 位址，避免帶入開發電腦的學校信箱。若需要 commit 正確連結到 GitHub 帳號，請在 GitHub 的 Emails 設定確認自己的 noreply 位址，再設定本專案 Git 身分；不需公開真實信箱。

## 建立 Release

1. 在已推送的 Repository 開啟 Releases，建立新 Release。
2. 建立標籤 `v1.0.0`，指向本次 `Initial release v1.0.0` commit。
3. 標題填入 `Classroom File Share v1.0.0`。
4. 將 [Release Notes](releases/v1.0.0.md) 的內文貼入說明。
5. 加入 `release-artifacts/ClassroomFileShare-v1.0.0-Windows.zip` 及旁邊的 `SHA256SUMS.txt` 作為附件。
6. 檢查檔案與說明後發佈。

GitHub 自動產生的 Source code ZIP 只有原始碼，**不是老師使用的 Windows 下載包**。請引導老師下載名稱含 `Windows.zip` 的附件。參考 [GitHub：管理 Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)。

## 更新下載包

```powershell
.\.venv\Scripts\python.exe tools/package_release.py
```

腳本依明確清單打包，不遞迴收集 `dist` 的其他檔案。即使程式使用後新增設定或學生資料，也不會一起放入 ZIP。它驗證 ZIP CRC、檔案清單、ZIP 內與原始 EXE 的 SHA-256，並產生 ZIP 的 `SHA256SUMS.txt`。

重新執行會更新 ZIP 與校驗碼，不會修改現有 EXE。發佈前請使用最後產生的一對 ZIP／校驗碼。正式版本發佈後，不要隨意替換同版本下載包；變更程式請建立新版本。

## 每次 commit／發佈前

```powershell
git status --short
git diff --cached --stat
git diff --cached
git ls-files
```

逐一確認沒有 `config.json`、學生資料、真實 IP／私人路徑、API Key、密碼、日誌或建置快取。`.gitignore` 不能隱藏已經追蹤的檔案，也無法防止手動放進 ZIP 的資料；不要以 `git add -f` 加入這些內容。

來源檔案應以 `git push` 上傳；EXE／ZIP 使用 Releases 附件，不要整個工作資料夾拖曳上傳。
