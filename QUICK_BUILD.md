# Быстрая сборка в exe

## Команды (по порядку)

```bash
# 1. Установите все зависимости
pip install -r backend/requirements.txt pyinstaller
npm install

# 2. Соберите Python backend в exe
npm run build:python

# 3. Соберите Electron приложение
npm run build:electron
```

## Или одной командой

```bash
npm run build
```

## Результат

После сборки в папке `dist` будет:
- **Установщик**: `Beet Optimization Lab Setup 1.0.0.exe`
- **Распакованная версия**: `dist/win-unpacked/Beet Optimization Lab.exe`

## Запуск

Просто запустите установщик или exe файл из `win-unpacked/`

## Важно

- Первая сборка может занять 5-10 минут (скачивание зависимостей)
- Размер итогового файла: ~150-200 МБ
- Убедитесь, что у вас установлены Python и Node.js

