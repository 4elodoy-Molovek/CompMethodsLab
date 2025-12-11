@echo off
REM ===================================================================
REM СКРИПТ ЗАПУСКА ELECTRON ПРИЛОЖЕНИЯ
REM ===================================================================
REM 
REM НАЗНАЧЕНИЕ:
REM   Этот скрипт запускает десктопное приложение "Beet Optimization Lab"
REM   на базе Electron. Скрипт автоматически проверяет наличие всех
REM   необходимых зависимостей и устанавливает их при необходимости.
REM
REM ИСПОЛЬЗОВАНИЕ:
REM   1. Просто запустите этот файл двойным кликом
REM   2. Или запустите из командной строки: start_electron.bat
REM
REM ТРЕБОВАНИЯ:
REM   - Установленный Node.js (версия 14 или выше)
REM   - Установленный npm (обычно идёт вместе с Node.js)
REM   - Файл package.json должен находиться в той же папке
REM
REM ЧТО ДЕЛАЕТ СКРИПТ:
REM   1. Проверяет наличие папки node_modules (зависимости проекта)
REM   2. Если папки нет - автоматически устанавливает все зависимости
REM   3. Проверяет наличие Electron (основной фреймворк для десктопного приложения)
REM   4. Если Electron не найден - устанавливает его
REM   5. Запускает Electron приложение
REM   6. Если запуск через npm не удался - пытается запустить напрямую через npx
REM
REM СТРУКТУРА ПРОЕКТА:
REM   - main.js - главный файл Electron, управляет окном приложения
REM   - index.html - интерфейс пользователя
REM   - renderer.js - логика интерфейса
REM   - backend/app.py - Python backend (запускается автоматически)
REM
REM ВОЗМОЖНЫЕ ПРОБЛЕМЫ И РЕШЕНИЯ:
REM   1. Ошибка "npm не является внутренней командой"
REM      -> Установите Node.js с официального сайта nodejs.org
REM
REM   2. Ошибка при установке зависимостей
REM      -> Проверьте подключение к интернету
REM      -> Убедитесь, что у вас есть права на запись в папку проекта
REM
REM   3. Приложение не запускается
REM      -> Проверьте, что backend/app.py существует
REM      -> Убедитесь, что Python установлен и доступен в PATH
REM
REM АВТОР: [Ваше имя]
REM ДАТА СОЗДАНИЯ: [Дата]
REM ===================================================================

echo ========================================
echo Starting Beet Optimization Lab (Electron)
echo ========================================
echo.

REM ===================================================================
REM ШАГ 1: ПРОВЕРКА И УСТАНОВКА ЗАВИСИМОСТЕЙ ПРОЕКТА
REM ===================================================================
REM Проверяем наличие папки node_modules, которая содержит все
REM установленные npm-пакеты проекта. Если папки нет, значит зависимости
REM ещё не установлены, и нужно их установить.
REM
REM Важно: npm install читает package.json и устанавливает все пакеты,
REM перечисленные в секциях "dependencies" и "devDependencies"
REM ===================================================================
if not exist "node_modules\" (
    echo [INFO] Node modules not found. Installing dependencies...
    echo [INFO] This may take a few minutes on first run...
    echo.
    
    REM Вызываем npm install для установки всех зависимостей
    REM call - это команда для вызова другого bat-файла или команды
    REM в том же процессе, чтобы переменные окружения сохранились
    call npm install
    
    REM Проверяем код возврата предыдущей команды
    REM errorlevel 1 означает, что команда завершилась с ошибкой
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install dependencies!
        echo [ERROR] Please check your internet connection and try again.
        echo [ERROR] Make sure Node.js and npm are properly installed.
        pause
        REM exit /b 1 - выход из скрипта с кодом ошибки 1
        exit /b 1
    )
    echo.
    echo [SUCCESS] Dependencies installed successfully!
    echo.
)

REM ===================================================================
REM ШАГ 2: ПРОВЕРКА НАЛИЧИЯ ELECTRON
REM ===================================================================
REM Electron - это основной фреймворк, который позволяет запускать
REM веб-приложение как десктопное. Проверяем, установлен ли он.
REM
REM Если Electron не найден, устанавливаем его отдельно.
REM --save-dev означает, что пакет нужен только для разработки
REM ===================================================================
if not exist "node_modules\electron\" (
    echo [INFO] Electron not found. Installing...
    echo [INFO] This may take a few minutes...
    echo.
    
    REM Устанавливаем Electron как dev-зависимость
    call npm install electron --save-dev
    
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to install Electron!
        echo [ERROR] Please check your internet connection.
        pause
        exit /b 1
    )
    echo.
    echo [SUCCESS] Electron installed successfully!
    echo.
)

REM ===================================================================
REM ШАГ 3: ЗАПУСК ПРИЛОЖЕНИЯ
REM ===================================================================
REM Запускаем Electron приложение через npm скрипт.
REM В package.json должна быть команда "start:electron": "electron ."
REM
REM Команда "electron ." запускает Electron и указывает ему использовать
REM текущую папку как корень приложения. Electron ищет main.js и запускает его.
REM ===================================================================
echo [INFO] Starting Electron application...
echo [INFO] The application window should open shortly...
echo.

REM Запускаем через npm скрипт (предпочтительный способ)
REM Это использует команду из package.json: "start:electron": "electron ."
call npm run start:electron

REM ===================================================================
REM ШАГ 4: ОБРАБОТКА ОШИБОК ЗАПУСКА
REM ===================================================================
REM Если запуск через npm не удался, пытаемся запустить напрямую
REM через npx. npx - это утилита, которая запускает пакеты из node_modules
REM или временно устанавливает и запускает пакет, если его нет.
REM ===================================================================
if errorlevel 1 (
    echo.
    echo [WARNING] Failed to start Electron via npm script!
    echo [INFO] Trying direct electron command...
    echo.
    
    REM Пытаемся запустить напрямую через npx
    REM npx electron . - запускает Electron из node_modules/.bin/electron
    call npx electron .
    
    REM Если и это не сработало, выводим сообщение об ошибке
    if errorlevel 1 (
        echo.
        echo [ERROR] Failed to start Electron application!
        echo [ERROR] Possible reasons:
        echo [ERROR]   1. Electron is not properly installed
        echo [ERROR]   2. main.js file is missing or corrupted
        echo [ERROR]   3. Node.js version is incompatible
        echo.
        echo [INFO] Try running: npm install
        echo [INFO] Then run this script again.
    )
)

REM ===================================================================
REM ПАУЗА ПЕРЕД ЗАКРЫТИЕМ
REM ===================================================================
REM pause - останавливает выполнение скрипта и ждёт нажатия клавиши.
REM Это нужно, чтобы пользователь мог увидеть сообщения об ошибках,
REM если они возникли. Без pause окно командной строки закроется сразу.
REM ===================================================================
pause

