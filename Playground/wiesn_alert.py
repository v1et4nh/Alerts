import os
import time
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from Functions.telegrambot import telegram_bot_sendtext

URL   = "https://www.oktoberfest-booking.com/de/reseller-angebote"
SLEEP = 300


def get_data(driver, label):
    try:
        element     = driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following-sibling::div")
        full_text   = element.get_attribute('textContent').replace('\xa0', ' ').strip()
        split_data  = [line.strip() for line in full_text.split('\n') if line.strip()]
        start_idx   = split_data.index('Inkludierte Leistungen')
        end_idx     = split_data.index('Summe') + 2
        food_drinks = split_data[start_idx:end_idx]
        food_drinks.remove('...')
        food_drinks_txt = food_drinks[0]
        for i in range(1, 11, 2):
            food_drinks_txt += f"\n{food_drinks[i]}: {food_drinks[i+1]}"

        dict_data = {
            'tent':    split_data[1],
            'daytime': split_data[3],
            'date':    f"{split_data[2]} {split_data[4]}",
            'person':  split_data[6],
            'tables':  split_data[7],
            'food':    food_drinks_txt
        }
        return dict_data
    except:
        return {}


def main(last_message=''):
    os.environ['MOZ_HEADLESS'] = '1'

    if os.name == 'nt':
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    else:
        driver = webdriver.Firefox()

    driver.get(URL)

    daytimes      = ['Vormittag', 'Mittag', 'Nachmittag', 'Abend']
    dict_daytimes = {daytime.lower(): get_data(driver, f'Reservierungen für Tische am {daytime}')
                     for daytime in daytimes}

    total_message = ''

    for daytime, data in dict_daytimes.items():
        msg_bool = False
        if data:
            total_message += f"*{data['tent']}*\n{data['date']} | {data['person']} | {data['tables']}\n"
            total_message += f"{data['food']}\n---\n"
            msg_bool = True
            # for i in range(0, len(data), 12):
            #     tmp_msg = ' | '.join(data[i+1:i + 11]) + '\n---\n'
            #     if 'Bodos Cafezelt' in tmp_msg:  # Blacklist
            #         continue
            #     if daytime in ['mittag', 'nachmittag', 'abend']:
            #         msg_bool = True
            #         total_message += tmp_msg
            if msg_bool:
                total_message += '\n'

    if total_message != last_message:
        last_message   = total_message
        total_message += f"Hier entlang: {URL}"
        telegram_bot_sendtext(total_message, bot_chatID='-1001575230467', disable_web_page_preview=True)

    driver.close()
    print(f"Success: {total_message}")
    return last_message


if __name__ == '__main__':
    last_message = ''
    while True:
        print('Wiesn Alert:')
        try:
            print(time.strftime('%X %x %Z'))
            last_message = main(last_message)
            sleep(SLEEP)
        except Exception as e:
            print('Restart...')
            message = f'Irgendetwas stimmt mit dem Wiesn Alert nicht. Fehlermeldung: \n{e}'
            telegram_bot_sendtext(message, bot_chatID='-1001575230467', disable_web_page_preview=True)
            sleep(SLEEP)
