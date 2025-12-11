# Решение проблемы со сборкой

## Проблема
Ошибка `Cannot create symbolic link` при распаковке winCodeSign - это проблема с правами Windows.

## Решение 1: Используйте готовый скрипт (РЕКОМЕНДУЕТСЯ)

Просто запустите:
```bash
build.bat
```

Этот скрипт:
1. Соберет Python backend
2. Очистит кэш electron-builder
3. Соберет portable версию без подписи

## Решение 2: Ручная сборка с отключением подписи

В PowerShell или CMD:

```powershell
# 1. Очистите кэш
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache" -ErrorAction SilentlyContinue

# 2. Установите переменные окружения
$env:CSC_IDENTITY_AUTO_DISCOVERY = "false"
$env:WIN_CSC_LINK = ""

# 3. Соберите Python backend
python -m PyInstaller backend/app.spec

# 4. Соберите Electron (portable, без подписи)
npx electron-builder --win portable --config.win.sign=false
```

## Решение 3: Использовать electron-packager (альтернатива)

Если electron-builder не работает, используйте electron-packager:

```bash
# Установите electron-packager
npm install --save-dev electron-packager

# Соберите приложение
npx electron-packager . "Beet Optimization Lab" --platform=win32 --arch=x64 --out=dist --overwrite --ignore="backend/(?!dist)"
```

Затем вручную скопируйте `backend/dist/backend.exe` в `dist/Beet Optimization Lab-win32-x64/resources/backend/`

## Решение 4: Включить Developer Mode (если нужен установщик)

Если вам нужен именно установщик (NSIS), включите Developer Mode:

1. Win + I → Обновление и безопасность → Для разработчиков
2. Включите "Режим разработчика"
3. Перезагрузите компьютер
4. Запустите сборку от имени администратора

## Что выбрать?

- **Portable версия** (рекомендуется): `build.bat` - проще всего, не требует прав
- **Установщик**: Включите Developer Mode и запустите от администратора

## Проверка результата

После успешной сборки в `dist` будет:
- `Beet Optimization Lab.exe` (portable версия)
- Или `Beet Optimization Lab Setup 1.0.0.exe` (установщик)

