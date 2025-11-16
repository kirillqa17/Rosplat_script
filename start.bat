@echo off
chcp 65001 > nul
echo ================================================
echo   Запуск Rosplat Script
echo ================================================
echo.

:: Проверяем наличие виртуального окружения
if not exist venv (
    echo [ОШИБКА] Виртуальное окружение не найдено!
    echo.
    echo Сначала запустите install.bat для установки
    echo.
    pause
    exit /b 1
)

:: Проверяем наличие .env файла
if not exist .env (
    echo [ОШИБКА] Файл .env не найден!
    echo.
    echo Скопируйте .env.example в .env и заполните ваши данные:
    echo   - LOGIN (ваш логин на RosPlat)
    echo   - PASSWORD (ваш пароль на RosPlat)
    echo   - TELEGRAM_BOT_TOKEN (токен бота от @BotFather)
    echo   - TELEGRAM_CHAT_ID (ваш Telegram ID)
    echo.
    pause
    exit /b 1
)

:: Активируем виртуальное окружение
call venv\Scripts\activate.bat

:: Запускаем бота
echo [OK] Запускаю бота...
echo.
python main.py

:: После завершения работы
echo.
echo ================================================
echo   Бот остановлен
echo ================================================
pause
