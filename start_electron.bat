@echo off
echo ========================================
echo Starting Beet Optimization Lab (Electron)
echo ========================================
echo.

REM Проверка наличия node_modules
if not exist "node_modules\" (
    echo Node modules not found. Installing dependencies...
    call npm install
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies!
        pause
        exit /b 1
    )
    echo.
)

REM Проверка наличия electron
if not exist "node_modules\electron\" (
    echo Electron not found. Installing...
    call npm install electron --save-dev
    if errorlevel 1 (
        echo ERROR: Failed to install Electron!
        pause
        exit /b 1
    )
    echo.
)

echo Starting Electron application...
echo.

REM Запуск Electron
call npm run start:electron

if errorlevel 1 (
    echo.
    echo ERROR: Failed to start Electron!
    echo Trying direct electron command...
    call npx electron .
)

pause

