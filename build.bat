@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  py -3 -m venv .venv
  if errorlevel 1 goto :fail
)
".venv\Scripts\python.exe" -m pip install -r requirements-build.txt
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m unittest discover -s tests -v
if errorlevel 1 goto :fail
".venv\Scripts\python.exe" -m PyInstaller --noconfirm --clean classroom.spec
if errorlevel 1 goto :fail
echo.
echo 打包完成：%~dp0dist\教室檔案分享.exe
pause
exit /b 0
:fail
echo 建置失敗，請檢查上方錯誤訊息。
pause
exit /b 1
