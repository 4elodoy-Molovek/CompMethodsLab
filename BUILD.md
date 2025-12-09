# Инструкция по сборке приложения в exe

## Быстрый старт

```bash
# 1. Установите зависимости
pip install -r backend/requirements.txt
pip install pyinstaller
npm install

# 2. Соберите всё
npm run build
```

## Подробная инструкция

### Шаг 1: Подготовка Python backend

1. Установите PyInstaller:
   ```bash
   pip install pyinstaller
   ```

2. Соберите backend в exe:
   ```bash
   npm run build:python
   ```
   
   Или вручную:
   ```bash
   cd backend
   pyinstaller app.spec
   ```

   Результат: `backend/dist/backend.exe`

### Шаг 2: Сборка Electron приложения

1. Установите electron-builder (если еще не установлен):
   ```bash
   npm install --save-dev electron-builder
   ```

2. Соберите приложение:
   ```bash
   npm run build:electron
   ```

   Или для конкретной платформы:
   ```bash
   npx electron-builder --win
   ```

### Шаг 3: Результат

После сборки вы найдете:

- **Установщик**: `dist/Beet Optimization Lab Setup 1.0.0.exe`
- **Распакованная версия**: `dist/win-unpacked/Beet Optimization Lab.exe`

## Структура после сборки

```
dist/
├── Beet Optimization Lab Setup 1.0.0.exe  (установщик)
└── win-unpacked/
    ├── Beet Optimization Lab.exe
    ├── resources/
    │   ├── app/
    │   │   ├── main.js
    │   │   ├── index.html
    │   │   └── ...
    │   └── backend/
    │       └── backend.exe
    └── ...
```

## Размер файла

- Установщик: ~150-200 МБ
- Распакованная версия: ~200-300 МБ

Размер большой из-за включения:
- Python runtime (~50 МБ)
- Electron (~100 МБ)
- Зависимости (numpy, flask и т.д.)

## Устранение проблем

### Ошибка "backend.exe not found"

Убедитесь, что сначала выполнили `npm run build:python`

### Ошибка при сборке Electron

Проверьте, что electron-builder установлен:
```bash
npm install --save-dev electron-builder
```

### Python backend не запускается

В режиме разработки проверьте, что Python установлен и доступен в PATH.

## Дополнительные опции

### Сборка только для разработки (без упаковки)

```bash
npm run start:electron
```

### Сборка с отладочной информацией

В `main.js` раскомментируйте:
```javascript
mainWindow.webContents.openDevTools();
```

