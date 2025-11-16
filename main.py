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
            try:
                print(f"   Ответ API: {response.json()}")
            except:
                pass
            return False

    except Exception as e:
        print(f"❌ Ошибка при отправке в Telegram: {e}")
        return False

def get_price_ranges():
    """Запрашивает у пользователя ценовые диапазоны для проверки заявок"""
    ranges = []

    while True:
        try:
            print("\n" + "="*50)
            count = input("Сколько ценовых диапазонов вы хотите использовать? (например, 1, 2, 3): ")
            num_ranges = int(count)
            if num_ranges > 0:
                break
            else:
                print("Количество должно быть больше 0!")
        except ValueError:
            print("Ошибка! Введите корректное число.")

    print("="*50)
    print("\nВводите диапазоны в формате: минимум-максимум")
    print("Например: 10000-14000 или 20000-100000")
    print("="*50 + "\n")

    for i in range(num_ranges):
        while True:
            try:
                range_input = input(f"Диапазон #{i+1}: ")
                parts = range_input.strip().replace(" ", "").split("-")

                if len(parts) != 2:
                    print("Ошибка! Формат должен быть: минимум-максимум (например, 10000-15000)")
                    continue

                min_val = float(parts[0])
                max_val = float(parts[1])

                if min_val <= 0 or max_val <= 0:
                    print("Суммы должны быть больше 0!")
                    continue

                if min_val > max_val:
                    print("Минимум не может быть больше максимума!")
                    continue

                ranges.append((min_val, max_val))
                print(f"✓ Добавлен диапазон: {min_val} - {max_val} руб.")
                break

            except ValueError:
                print("Ошибка! Введите корректные числа.")

    print("\n" + "="*50)
    print("Установленные диапазоны:")
    for i, (min_val, max_val) in enumerate(ranges, 1):
        print(f"  {i}. {min_val} - {max_val} руб.")
    print("="*50 + "\n")

    return ranges

def check_price_in_ranges(amount, price_ranges):
    """Проверяет, попадает ли сумма в один из диапазонов"""
    for min_val, max_val in price_ranges:
        if min_val <= amount <= max_val:
            return True, f"{min_val}-{max_val}"
    return False, None

def check_page_for_requests(driver, price_ranges, page_num):
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

                # Проверяем условия: метод С2С и сумма в диапазонах
                in_range, matching_range = check_price_in_ranges(amount, price_ranges)

                if (method == "С2С" or method == "C2C") and in_range:
                    print(f"\n✅ ПОДХОДИТ! ID: {payout_id}, Метод: {method}, Сумма: {amount} руб. (диапазон: {matching_range})")

                    # Находим кнопку "В работу" в последней ячейке
                    button = cells[6].find_element(By.TAG_NAME, "button")
                    print(f"🔄 Нажимаю кнопку 'В работу'...")
                    button.click()

                    print(f"✅ Заявка взята в работу! ID: {payout_id}")

                    # Отправляем уведомление в Telegram
                    telegram_message = (
                        f"🎉 <b>Заявка взята в работу!</b>\n\n"
                        f"📋 <b>ID:</b> {payout_id}\n"
                        f"🏦 <b>Банк:</b> {bank}\n"
                        f"💳 <b>Метод:</b> {method}\n"
                        f"💳 <b>Карта:</b> {phone}\n"
                        f"💰 <b>Сумма:</b> {amount} ₽\n"
                        f"⏰ <b>Время:</b> {time.strftime('%H:%M:%S %d.%m.%Y')}"
                    )
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

def check_and_process_requests(driver, wait, price_ranges, first_check=False):
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
            found, total_requests, request_data = check_page_for_requests(driver, price_ranges, page_num)

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

    # Запрашиваем ценовые диапазоны у пользователя
    price_ranges = get_price_ranges()
    son = 5


    # Настройка опций браузера
    chrome_options = Options()

    # User-Agent для обхода детекции автоматизации
    chrome_options.add_argument("--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36")

    # Отключаем флаги автоматизации
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    # Дополнительные опции
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_argument("--remote-debugging-port=9222")

    # Настройка и запуск браузера
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)

    # Скрываем признаки автоматизации через JavaScript
    driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
        'source': '''
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
        '''
    })

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
        print(f"  - Ценовые диапазоны:")
        for i, (min_val, max_val) in enumerate(price_ranges, 1):
            print(f"    {i}. {min_val} - {max_val} руб.")
        print(f"  - Интервал проверки: {son} секунд")
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
            request_taken, request_data = check_and_process_requests(driver, wait, price_ranges, first_check)
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
                # Спрашиваем новые ценовые диапазоны
                price_ranges = get_price_ranges()
                check_count = 0  # Сбрасываем счетчик
                first_check = True  # Нужно перезагрузить страницу после завершения работы
            print(f"\n⏸️  Пауза {son} секунд до следующей проверки...")
            time.sleep(son)

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
