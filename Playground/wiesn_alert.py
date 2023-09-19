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
        element = driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following-sibling::div")
        return element.text.split('\n')
    except:
        return []


def main(last_message=''):
    os.environ['MOZ_HEADLESS'] = '1'

    if os.name == 'nt':
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    else:
        driver = webdriver.Firefox()

    driver.get(URL)

    labels    = ['Vormittag', 'Mittag', 'Nachmittag', 'Abend']
    dict_data = {label.lower(): get_data(driver, f'Reservierungen für Tische am {label}') for label in labels}

    total_message = ''

    for label, data in dict_data.items():
        msg_bool = False
        if data:
            for i in range(0, len(data), 12):
                tmp_msg = ' | '.join(data[i+1:i + 11]) + '\n---\n'
                if label == 'abend' or any(day in tmp_msg for day in ['Freitag', 'Samstag', 'Sonntag']):
                    msg_bool = True
                    total_message += tmp_msg
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
