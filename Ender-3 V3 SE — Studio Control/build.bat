@echo off
chcp 65001 > nul
echo [*] Завершаем процесс старого приложения, если открыто...
taskkill /f /im printer_gui.exe > nul 2>&1

echo [*] Сборка нового EXE...
pyinstaller --noconsole --onefile --clean --icon="app_icon.ico" printer_gui.py

echo.
echo [✓] Готово! Новый файл лежит в папке dist.
pause