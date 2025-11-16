from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
import os
import time
import requests

# Загружаем переменные из .env файла
load_dotenv()

def send_telegram_message(message):
    """Отправляет сообщение в Telegram"""
    try:
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID")

        if not bot_token or not chat_id:
            print("⚠️  Telegram параметры не настроены в .env")
            return False

        if bot_token == "YOUR_BOT_TOKEN_HERE" or chat_id == "YOUR_CHAT_ID_HERE":
            print("⚠️  Пожалуйста, настройте TELEGRAM_BOT_TOKEN и TELEGRAM_CHAT_ID в .env файле")
            return False

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        data = {
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        response = requests.post(url, data=data, timeout=10)

        if response.status_code == 200:
            print("✅ Уведомление отправлено в Telegram")
            return True
        else:
            print(f"❌ Ошибка отправки в Telegram: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {e}")
        return False

def get_min_amount():
    """Запрашивает у пользователя минимальную сумму для проверки заявок"""
    while True:
        try:
            print("\n" + "="*50)
            amount = input("Введите минимальную сумму заявки (например, 10000 или 15000): ")
            min_amount = float(amount)
            if min_amount > 0:
                print(f"Установлена минимальная сумма: {min_amount} руб.")
                print("="*50 + "\n")
                return min_amount
            else:
                print("Сумма должна быть больше 0!")
        except ValueError:
            print("Ошибка! Введите корректное число.")

def check_page_for_requests(driver, min_amount, page_num):
    """Проверяет заявки на текущей странице"""
    try:
        time.sleep(2)  # Ждем загрузки страницы

        # Находим все строки выплат
        rows = driver.find_elements(By.CSS_SELECTOR, "div.grid.py-4.border-b")
        total_requests = len(rows)
        print(f"Страница {page_num}: найдено {total_requests} заявок")

        for idx, row in enumerate(rows, 1):
            try:
                # Все ячейки в строке
                cells = row.find_elements(By.CSS_SELECTOR, "div.w-full.min-w-\\[120px\\]")

                if len(cells) < 7:
                    continue

                # Извлекаем данные
                payout_id = cells[0].text.strip()
                bank = cells[1].text.strip().replace('\n', ' ').replace('\r', ' ')
                method = cells[2].text.strip()
                phone = cells[3].text.strip()
                amount_text = cells[4].text.strip()

                # Преобразуем сумму
                amount = float(amount_text.replace('\xa0', '').replace(' ', '').replace('₽', '').replace(',', '.'))

                print(f"  [{idx}/{total_requests}] ID: {payout_id}, Метод: {method}, Сумма: {amount} руб.")

                # Проверяем условия: метод С2С и сумма больше минимальной
                if method == "С2С" and amount >= min_amount:
                    print(f"\n✅ ПОДХОДИТ! ID: {payout_id}, Метод: {method}, Сумма: {amount} >= {min_amount}")

                    # Находим кнопку "В работу" в последней ячейке
                    button = cells[6].find_element(By.TAG_NAME, "button")
                    print(f"🔄 Нажимаю кнопку 'В работу'...")
                    button.click()

                    print(f"✅ Заявка взята в работу! ID: {payout_id}")

                    # Отправляем уведомление в Telegram
                    telegram_message = f"""
🎉 <b>Заявка взята в работу!</b>

📋 <b>ID:</b> {payout_id}
🏦 <b>Банк:</b> {bank}
💳 <b>Метод:</b> {method}
📱 <b>Телефон:</b> {phone}
💰 <b>Сумма:</b> {amount} ₽
⏰ <b>Время:</b> {time.strftime('%H:%M:%S %d.%m.%Y')}
"""
                    send_telegram_message(telegram_message)

                    time.sleep(3)
                    return True, total_requests, {"id": payout_id, "bank": bank, "method": method, "phone": phone, "amount": amount}

            except Exception as e:
                print(f"  Ошибка при обработке строки {idx}: {e}")
                continue

        return False, total_requests, None

    except Exception as e:
        print(f"Ошибка при проверке заявок на странице {page_num}: {e}")
        return False, 0, None

def check_and_process_requests(driver, wait, min_amount, first_check=False):
    """Проверяет заявки на всех страницах"""
    try:
        # Только при первой проверке переходим на страницу
        if first_check:
            driver.get("https://trade.rosplat.cash/dashboard/payoutrequests/pending")
            time.sleep(3)
        else:
            # Если не первая проверка, возвращаемся на первую страницу кликом на кнопку "1"
            # НЕ обновляем страницу! Просто переходим на первую страницу если мы не на ней
            try:
                # Ищем кнопки пагинации
                pagination_buttons = driver.find_elements(
                    By.CSS_SELECTOR,
                    "button.w-8.h-8.flex.items-center.justify-center"
                )
                # Ищем кнопку "1" чтобы вернуться на первую страницу
                for btn in pagination_buttons:
                    if btn.text.strip() == "1":
                        btn.click()
                        time.sleep(2)
                        break
            except:
                # Если не получилось найти кнопку - просто продолжаем, возможно мы уже на первой странице
                time.sleep(0.5)

        page_num = 1
        max_pages = 5  # Максимум проверяем 5 страниц (250 заявок)

        while page_num <= max_pages:
            print(f"\n{'='*50}")
            print(f"Проверяю страницу {page_num}...")
            print(f"{'='*50}")

            # Проверяем заявки на текущей странице
            found, total_requests, request_data = check_page_for_requests(driver, min_amount, page_num)

            if found:
                # Нашли подходящую заявку - выходим
                return True, request_data

            # Если на странице меньше 50 заявок - это последняя страница
            if total_requests < 50:
                print(f"\n⚠️  Это последняя страница (заявок: {total_requests})")
                break

            # Ищем кнопку "Следующая страница"
            try:
                # Находим все кнопки с нужными классами
                next_buttons = driver.find_elements(
                    By.CSS_SELECTOR,
                    "button.w-8.h-8.flex.items-center.justify-center.text-white\\/50"
                )

                # Обычно кнопка "Следующая" - это последняя кнопка или вторая
                next_button = None
                for btn in next_buttons:
                    # Проверяем, не disabled ли кнопка
                    classes = btn.get_attribute("class")
                    if "disabled:cursor-not-allowed" in classes:
                        # Проверяем, активна ли кнопка (не disabled)
                        if btn.is_enabled():
                            # Ищем стрелку вправо (обычно это >)
                            if ">" in btn.text or "›" in btn.text or btn.find_elements(By.TAG_NAME, "svg"):
                                next_button = btn
                                break

                # Если не нашли, попробуем другой способ - последняя кнопка
                if not next_button and len(next_buttons) >= 2:
                    # Берем последнюю кнопку (обычно это "следующая")
                    next_button = next_buttons[-1]

                if next_button and next_button.is_enabled():
                    print(f"\n➡️  Переход на страницу {page_num + 1}...")
                    next_button.click()
                    page_num += 1
                    time.sleep(2)
                else:
                    print(f"\n⚠️  Кнопка 'Следующая страница' недоступна - достигнут конец списка")
                    break

            except NoSuchElementException:
                print(f"\n⚠️  Кнопка 'Следующая страница' не найдена - это последняя страница")
                break
            except Exception as e:
                print(f"\n⚠️  Ошибка при переходе на следующую страницу: {e}")
                break

        print("\n⏳ Подходящих заявок не найдено на всех проверенных страницах")
        return False, None

    except Exception as e:
        print(f"Ошибка при проверке заявок: {e}")
        return False, None

def main():
    # Получаем учетные данные из .env
    login = os.getenv("LOGIN")
    password = os.getenv("PASSWORD")

    if not login or not password:
        print("ОШИБКА: Не найдены логин или пароль в .env файле!")
        return

    # Запрашиваем минимальную сумму у пользователя
    min_amount = get_min_amount()

    # Настройка опций браузера
    chrome_options = Options()
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Настройка и запуск браузера
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    wait = WebDriverWait(driver, 30)

    try:
        # Авторизация
        print("Переход на страницу авторизации...")
        driver.get("https://trade.rosplat.cash/")
        wait.until(EC.element_to_be_clickable((By.ID, "login")))

        driver.find_element(By.ID, "login").send_keys(login)
        driver.find_element(By.ID, "password").send_keys(password)

        # Пауза для ручного ввода капчи
        print("\n" + "="*50)
        print("ВНИМАНИЕ: Введите капчу вручную в браузере!")
        print("="*50)
        input("Нажмите ENTER после входа в аккаунт для продолжения...")
        print("Продолжаем выполнение скрипта...\n")

        print("Авторизация успешна!")
        print(f"Начинаю мониторинг заявок с параметрами:")
        print(f"  - Метод оплаты: С2С")
        print(f"  - Минимальная сумма: {min_amount} руб.")
        print(f"  - Интервал проверки: 10 секунд")
        print(f"  - Проверка нескольких страниц: Да")
        print(f"  - Telegram уведомления: Включены")
        print("\n" + "="*50 + "\n")

        # Бесконечный цикл проверки заявок
        check_count = 0
        first_check = True

        while True:
            check_count += 1
            print(f"\n{'#'*50}")
            print(f"[Проверка #{check_count}] {time.strftime('%H:%M:%S')}")
            print(f"{'#'*50}")

            # Проверяем и обрабатываем заявки
            request_taken, request_data = check_and_process_requests(driver, wait, min_amount, first_check)
            first_check = False  # После первой проверки больше не нужно использовать driver.get

            if request_taken:
                print("\n" + "="*50)
                print("🎉 Заявка взята в работу!")
                print("="*50 + "\n")

                # Ждем, пока пользователь завершит работу с заявкой
                print("\n" + "="*50)
                print("После завершения работы с заявкой нажмите ENTER для продолжения...")
                print("="*50)
                input()

                print("\n✅ Продолжаем работу!")
                # Спрашиваем новую минимальную сумму
                min_amount = get_min_amount()
                check_count = 0  # Сбрасываем счетчик
                first_check = True  # Нужно перезагрузить страницу после завершения работы

            # Ждем 10 секунд перед следующей проверкой
            print(f"\n⏸️  Пауза 10 секунд до следующей проверки...")
            time.sleep(10)

    except KeyboardInterrupt:
        print("\n\n⚠️  Работа бота остановлена пользователем.")
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
    finally:
        print("\nЗавершение работы браузера...")
        driver.quit()
        print("Готово!")

if __name__ == "__main__":
    main()
