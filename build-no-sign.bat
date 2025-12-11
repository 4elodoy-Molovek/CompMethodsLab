@echo off
echo ========================================
echo Building Beet Optimization Lab (No Signing)
echo ========================================
echo.

REM Очистка кэша
echo Cleaning electron-builder cache...
if exist "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign" (
    rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache\winCodeSign"
    echo winCodeSign cache cleared.
)

REM Установка переменных окружения для отключения подписи
set CSC_IDENTITY_AUTO_DISCOVERY=false
set WIN_CSC_LINK=
set CSC_LINK=

echo.
echo Step 1: Building Python backend...
python -m PyInstaller backend/app.spec
if errorlevel 1 (
    echo ERROR: Python backend build failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Building Electron app (portable, no code signing)...
npx electron-builder --win portable --config.win.sign=false --config.win.verifyUpdateCodeSignature=false
if errorlevel 1 (
    echo.
    echo Build failed. Trying alternative method...
    echo.
    REM Альтернатива: используем electron-packager
    if not exist "node_modules\electron-packager" (
        echo Installing electron-packager...
        npm install --save-dev electron-packager
    )
    echo Using electron-packager...
    npx electron-packager . "Beet Optimization Lab" --platform=win32 --arch=x64 --out=dist --overwrite --ignore="backend/(?!dist)" --ignore="backend/__pycache__" --ignore="backend/tests"
    
    REM Копируем backend.exe
    if exist "backend\dist\backend.exe" (
        if not exist "dist\Beet Optimization Lab-win32-x64\resources" mkdir "dist\Beet Optimization Lab-win32-x64\resources"
        if not exist "dist\Beet Optimization Lab-win32-x64\resources\backend" mkdir "dist\Beet Optimization Lab-win32-x64\resources\backend"
        copy "backend\dist\backend.exe" "dist\Beet Optimization Lab-win32-x64\resources\backend\backend.exe"
        echo Backend copied successfully.
    )
)

echo.
echo ========================================
echo Build process completed!
echo Check dist folder for the application
echo ========================================
pause

