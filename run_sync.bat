@echo off
rem Median XL wiki sync - compares the newest docs and wiki snapshots in Downloads and builds an update.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  pause
  exit /b 1
)
python -c "import bs4, lxml" >nul 2>nul
if errorlevel 1 (
  echo Installing the two packages the converter needs...
  python -m pip install --user beautifulsoup4 lxml
)
python sync.py %*
if not errorlevel 1 (
  for /f "delims=" %%d in ('dir /b /ad /o-d "output\sync-*" 2^>nul') do (
    start "" "output\%%d\report.html"
    goto done
  )
)
:done
pause
