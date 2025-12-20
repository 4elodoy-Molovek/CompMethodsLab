@echo off
REM ===================================================================
REM СКРИПТ СБОРКИ ПРИЛОЖЕНИЯ (ELECTRON + PYTHON)
REM ===================================================================

echo [INFO] Starting build process...

REM 1. ПРОВЕРКА И УСТАНОВКА PYINSTALLER
echo.
echo [STEP 1/4] Checking Python build tools...
call python -m pip install pyinstaller
if errorlevel 1 (
    echo [ERROR] Failed to install PyInstaller. Check Python installation.
    pause
    exit /b 1
)

REM 2. КОМПИЛЯЦИЯ PYTHON BACKEND
echo.
echo [STEP 2/4] Compiling Python backend...
REM --onefile: собрать в один exe
REM --noconsole: не показывать черное окно консоли при запуске (уберите, если нужен лог)
REM --distpath: куда положить результат
if exist "backend\app.py" (
    call python -m PyInstaller --clean --onefile --noconsole --distpath backend/dist --workpath backend/build --specpath backend --name backend backend/app.py
) else (
    echo [ERROR] backend/app.py not found!
    pause
    exit /b 1
)

if errorlevel 1 (
    echo [ERROR] Python compilation failed!
    pause
    exit /b 1
)

REM 3. УСТАНОВКА ELECTRON-BUILDER
echo.
echo [STEP 3/4] Installing Electron builder...
if not exist "node_modules\electron-builder\" (
    call npm install electron-builder --save-dev
)

REM 4. СБОРКА ELECTRON ПРИЛОЖЕНИЯ
echo.
echo [STEP 4/4] Building Electron app...
echo [INFO] Make sure you have configured "build" section in package.json!

REM Очистка проблемного кэша (исправляет ошибку распаковки winCodeSign)
echo [INFO] Clearing winCodeSign cache...
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" (
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign"
)

REM Запуск сборщика
REM Отключаем подпись кода и автопоиск сертификатов (решает проблемы с winCodeSign)
set CSC_IDENTITY_AUTO_DISCOVERY=false
set WIN_CSC_LINK=

call npx electron-builder --win --x64 --config.win.sign=false --config.win.verifyUpdateCodeSignature=false

if errorlevel 1 (
    echo [ERROR] Electron build failed!
    echo [HINT] If you see "Cannot create symbolic link" or "winCodeSign" error:
    echo [HINT] 1. RUN THIS SCRIPT AS ADMINISTRATOR (Right click -> Run as Administrator).
    echo [HINT] 2. Or try "npm run build:packager" manually (creates a folder instead of one exe).
    echo [HINT] Did you add the "build" configuration to package.json?
    pause
    exit /b 1
)

echo.
echo ===================================================================
echo [SUCCESS] Build complete!
echo The installer is located in the "dist" folder.
echo ===================================================================
pause