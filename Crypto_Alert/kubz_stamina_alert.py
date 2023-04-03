import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext
from bot_messages import end_message

PICKLE_FILE = '../Data/kubzStamina.pickle'
TOKENID     = 3043
BOT_CHATID  = '-800629298'
SLEEP       = 60
DEBUG       = False


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages['counter']
    except:
        return -100000


def getData(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    return data


def getStamina(tokenID):
    url     = f"https://genesis-api.keungz.com/kubz/info/{str(tokenID)}"
    data    = getData(url)
    stamina = data['kubzStamina'][str(tokenID)] / 100

    return stamina


def run_kubz_stamina_checker():
    lastStamina    = get_last_message()
    currentStamina = getStamina(TOKENID)
    console_output = f"Kubz Stamina: Last {lastStamina} | Now {currentStamina}"
    dict_counter   = {'counter': currentStamina}
    save_pickle(dict_counter, PICKLE_FILE)
    print(console_output)
    if currentStamina >= 7 or DEBUG:
        message = f"Kubz has full stamina\n" \
                  f"Go to [keungz.com](https://keungz.com) to craft!\n\n"
        message += end_message
        print(message)
        telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)
    if currentStamina >= 3 > lastStamina:
        message = f"Kubz has half full stamina\n" \
                  f"Go to [keungz.com](https://keungz.com) to craft!\n\n"
        message += end_message
        print(message)
        telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run_kubz_stamina_checker()
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main()
