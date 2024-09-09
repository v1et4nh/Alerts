import os
import time
import difflib
from time import sleep
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from Functions.telegrambot import telegram_bot_sendtext
from Functions.telegrambot import bot_chatID_private

URL   = "https://www.oktoberfest-booking.com/de/reseller-angebote"
SLEEP = 30


def get_data(driver, label):
    try:
        element     = driver.find_element(By.XPATH, f"//*[contains(text(), '{label}')]/following-sibling::div")
        full_text   = element.get_attribute('textContent').replace('\xa0', ' ').strip()
        split_data  = [line.strip() for line in full_text.split('\n') if line.strip()]
        start_indices = [idx for idx, txt in enumerate(split_data) if txt == 'Infos zum Zelt']
        end_indices   = [idx+1 for idx, txt in enumerate(split_data) if txt == 'Details anzeigen']
        pending_txt = "Ein Käufer befindet sich derzeit im Kaufprozess für diese Reservierung"
        count_tables = 0
        dict_data = {}
        for start_idx, end_idx in zip(start_indices, end_indices):
            count_tables += 1
            sold_bool    = False
            pending_bool = False
            tmp_data = split_data[start_idx:end_idx]
            if pending_txt in tmp_data:
                pending_bool = True
                tmp_data.remove(pending_txt)
            if '.st0{fill:#78B0EE;}' in tmp_data:
                sold_bool = True
                tmp_data.remove('.st0{fill:#78B0EE;}')
            food_start_idx  = tmp_data.index('Inkludierte Leistungen')
            food_end_idx    = tmp_data.index('Summe') + 2
            food_drinks     = tmp_data[food_start_idx:food_end_idx]
            food_drinks.remove('...')
            food_drinks_txt = f"{food_drinks[0]}:"
            for i in range(1, len(food_drinks)):
                if food_drinks[i][0] == '€':
                    food_drinks_txt += f": {food_drinks[i]}"
                elif 'Summe' in food_drinks[i]:
                    food_drinks_txt += f"\n---\n{food_drinks[i]}"
                else:
                    food_drinks_txt += f"\n - {food_drinks[i]}"

            dict_data[count_tables] = {
                'sold': sold_bool,
                'pending': pending_bool,
                'tent': tmp_data[1],
                'daytime': tmp_data[3],
                'date': f"{tmp_data[2]} {tmp_data[4]}",
                'person': tmp_data[6],
                'tables': tmp_data[7],
                'food': food_drinks_txt
            }

        return dict_data
    except Exception as e:
        print(f"Error ({label}): {e}")
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
    pending_txt   = '_Ein Käufer befindet sich derzeit im Kaufprozess für diese Reservierung_\n'

    for daytime, data in dict_daytimes.items():
        msg_bool = False
        if data:
            for i in data:
                if data[i]['sold']:
                    continue
                    # total_message += '_Bereits verkauft_\n'
                if data[i]['pending']:
                    total_message += pending_txt
                total_message += f"[**{data[i]['tent']}**]({URL})\n{data[i]['date']} | {data[i]['person']} | {data[i]['tables']}\n"
                total_message += f"{data[i]['food']}\n---\n"
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

    diff_msg = difflib.ndiff(last_message, total_message)
    diff_pos = ''.join([s[-1] for s in diff_msg if s[0] == '+'])
    diff_neg = ''.join([s[-1] for s in diff_msg if s[0] == '-'])
    print(f"##########\nDiff (+):\n {diff_pos}##########\nDiff (-):\n {diff_neg}##########\n")
    disable_notification = True
    if total_message != last_message:
        last_message = total_message
        if len(diff_pos.replace(pending_txt, '')) > 0:
            disable_notification = False
        print(f'Disable notification: {disable_notification}')
        # total_message += f"[Hier entlang]({URL})"
        telegram_bot_sendtext(total_message, bot_chatID='-1001575230467', disable_web_page_preview=True,
                              disable_notification=disable_notification)
        # telegram_bot_sendtext(total_message, bot_chatID=bot_chatID_private, disable_web_page_preview=True,
        #                       disable_notification=disable_notification)

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
