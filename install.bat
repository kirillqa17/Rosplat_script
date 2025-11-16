@echo off
chcp 65001 > nul
echo ================================================
echo   Установка Rosplat Script
echo ================================================
echo.

:: Проверяем наличие Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ОШИБКА] Python не установлен!
    echo.
    echo Пожалуйста, установите Python с сайта: https://www.python.org/downloads/
    echo ВАЖНО: При установке отметьте галочку "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [OK] Python установлен
python --version
echo.

:: Создаем виртуальное окружение
echo [1/4] Создаю виртуальное окружение...
if exist venv (
    echo Виртуальное окружение уже существует
) else (
    python -m venv venv
    if %errorlevel% neq 0 (
        echo [ОШИБКА] Не удалось создать виртуальное окружение
        pause
        exit /b 1
    )
    echo [OK] Виртуальное окружение создано
)
echo.

:: Активируем виртуальное окружение
echo [2/4] Активирую виртуальное окружение...
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось активировать виртуальное окружение
    pause
    exit /b 1
)
echo [OK] Виртуальное окружение активировано
echo.

:: Обновляем pip
echo [3/4] Обновляю pip...
python -m pip install --upgrade pip
echo.

:: Устанавливаем зависимости
echo [4/4] Устанавливаю зависимости...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [ОШИБКА] Не удалось установить зависимости
    pause
    exit /b 1
)
echo.

:: Проверяем наличие .env файла
if not exist .env (
    echo ================================================
    echo   ВАЖНО: Настройте .env файл!
    echo ================================================
    echo.
    echo Файл .env не найден.
    echo.
    echo Скопируйте .env.example в .env и заполните:
    echo   - LOGIN (ваш логин на RosPlat)
    echo   - PASSWORD (ваш пароль на RosPlat)
    echo   - TELEGRAM_BOT_TOKEN (токен бота от @BotFather)
    echo   - TELEGRAM_CHAT_ID (ваш Telegram ID)
    echo.
    echo Инструкции по настройке смотрите в README.md
    echo.
)

echo ================================================
echo   Установка завершена успешно!
echo ================================================
echo.
echo Для запуска бота используйте файл start.bat
echo.
pause
