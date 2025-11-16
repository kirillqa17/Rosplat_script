#!/bin/bash

echo "================================================"
echo "   Запуск Rosplat Script"
echo "================================================"
echo ""

# Проверяем наличие виртуального окружения
if [ ! -d "venv" ]; then
    echo "[ОШИБКА] Виртуальное окружение не найдено!"
    echo ""
    echo "Сначала создайте виртуальное окружение:"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    echo ""
    exit 1
fi

# Проверяем наличие .env файла
if [ ! -f ".env" ]; then
    echo "[ОШИБКА] Файл .env не найден!"
    echo ""
    echo "Скопируйте .env.example в .env и заполните ваши данные:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    echo ""
    exit 1
fi

# Активируем виртуальное окружение
source venv/bin/activate

# Запускаем бота
echo "[OK] Запускаю бота..."
echo ""
python main.py

# После завершения работы
echo ""
echo "================================================"
echo "   Бот остановлен"
echo "================================================"
