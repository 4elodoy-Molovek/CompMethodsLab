# Исправление ошибки сборки

## Проблема
Ошибка `Cannot create symbolic link` при сборке - это проблема с правами Windows на создание символических ссылок.

## Решение 1: Отключить подпись кода (уже применено)

Конфигурация в `package.json` уже обновлена. Теперь попробуйте:

```bash
npm run build:electron
```

## Решение 2: Очистить кэш electron-builder

Если ошибка повторяется, очистите кэш:

```bash
# Удалите кэш electron-builder
rmdir /s /q "%LOCALAPPDATA%\electron-builder\Cache"
```

Или в PowerShell:
```powershell
Remove-Item -Recurse -Force "$env:LOCALAPPDATA\electron-builder\Cache"
```

Затем попробуйте снова:
```bash
npm run build:electron
```

## Решение 3: Включить Developer Mode в Windows

1. Откройте **Настройки Windows** (Win + I)
2. Перейдите в **Обновление и безопасность** → **Для разработчиков**
3. Включите **Режим разработчика**
4. Перезапустите сборку

## Решение 4: Запустить от имени администратора

1. Откройте PowerShell или CMD **от имени администратора**
2. Перейдите в папку проекта
3. Запустите:
```bash
npm run build:electron
```

## Решение 5: Использовать portable версию (без установщика)

Если ничего не помогает, можно собрать portable версию:

В `package.json` измените:
```json
"win": {
    "target": [
        {
            "target": "portable",
            "arch": ["x64"]
        }
    ],
    ...
}
```

Затем:
```bash
npm run build:electron
```

Это создаст `dist/Beet Optimization Lab.exe` без установщика.

## Проверка

После успешной сборки в папке `dist` должны появиться файлы:
- `Beet Optimization Lab Setup 1.0.0.exe` (установщик)
- Или `Beet Optimization Lab.exe` (portable версия)

