@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Task 4 - Fraud Detection in Applications

echo ============================================================
echo   Fraud Detection in Applications - Internee.pk Task 4
echo   Sajid Ali - Data Analyst Intern
echo ============================================================
echo.

if /I "%~1"=="server" goto SERVER

echo Opening the dashboard directly in your default browser...
if not exist "%~dp0index.html" (
  echo ERROR: index.html was not found in:
  echo %~dp0
  echo Please keep this BAT file inside the project root folder.
  echo.
  pause
  exit /b 1
)
start "" "%~dp0index.html"
echo Dashboard opened. If your browser blocks a local feature, run:
echo   OPEN_DASHBOARD.bat server
echo.
timeout /t 4 /nobreak >nul
exit /b 0

:SERVER
set "PYEXE="
set "PYARGS="
if exist "C:\Python314\python.exe" set "PYEXE=C:\Python314\python.exe"
if defined PYEXE goto PYFOUND

where python >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=python"
  goto PYFOUND
)

where py >nul 2>&1
if not errorlevel 1 (
  set "PYEXE=py"
  set "PYARGS=-3"
  goto PYFOUND
)

echo ERROR: Python could not be found.
echo Checked:
echo   1. C:\Python314\python.exe
echo   2. python command
echo   3. py launcher
echo.
echo You can still open index.html directly without Python.
echo If you want server mode, install Python or correct the installation path.
echo.
pause
exit /b 1

:PYFOUND
echo Python found: %PYEXE% %PYARGS%
echo Starting local server at http://127.0.0.1:8000/
echo Keep this window open while using server mode.
echo.
start "" http://127.0.0.1:8000/index.html
%PYEXE% %PYARGS% -m http.server 8000 --bind 127.0.0.1

echo.
echo The server stopped. Review any message above for details.
pause
endlocal
