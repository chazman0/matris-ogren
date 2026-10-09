@echo off
rem Matris Ogren - bilgisayarda, internet sitesine gerek kalmadan baslatir.
rem docs klasorunu 127.0.0.1:8765 adresinden sunar ve Edge'i uygulama penceresinde acar.
rem Ilk acilista Python motoru (yaklasik 30 MB) internetten bir kez indirilir; sonra cevrimdisi calisir.
rem Kucultulmus "Matris Ogren sunucu" penceresi kapatilirsa uygulama durur.
setlocal
set "PY=%LOCALAPPDATA%\Programs\Python\Python312\python.exe"
if not exist "%PY%" set "PY=python"
start "Matris Ogren sunucu" /min "%PY%" -m http.server 8765 --bind 127.0.0.1 --directory "%~dp0docs"
timeout /t 2 /nobreak >nul
set "EDGE=%ProgramFiles(x86)%\Microsoft\Edge\Application\msedge.exe"
if not exist "%EDGE%" set "EDGE=%ProgramFiles%\Microsoft\Edge\Application\msedge.exe"
if exist "%EDGE%" (
  start "" "%EDGE%" --app=http://127.0.0.1:8765/
) else (
  start "" http://127.0.0.1:8765/
)
endlocal
