from __future__ import print_function
import gate_api
from gate_api.exceptions import ApiException, GateApiException
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext

PICKLE_FILE = '../Data/blur_price.pickle'
SLEEP = 10

# Defining the host is optional and defaults to https://api.gateio.ws/api/v4
# See configuration.py for a list of all supported configuration parameters.
configuration = gate_api.Configuration(
    host="https://api.gateio.ws/api/v4"
)

api_client = gate_api.ApiClient(configuration)
# Create an instance of the API class
api_instance = gate_api.SpotApi(api_client)
currency_pair = 'BLUR_USDT'     # str | Currency pair (optional)
timezone = 'utc0'               # str | Timezone (optional)


def get_last_message():
    last_val = load_pickle(PICKLE_FILE)
    try:
        if 'Error' in last_val:
            last_val = 0
    except:
        pass
    try:
        return last_val
    except:
        return -100000


def get_blur_price():
    try:
        # Retrieve ticker information
        api_response = api_instance.list_tickers(currency_pair=currency_pair, timezone=timezone)
        return api_response[0].last
    except GateApiException as ex:
        print("Gate api exception, label: %s, message: %s\n" % (ex.label, ex.message))
    except ApiException as e:
        print("Exception when calling SpotApi->list_tickers: %s\n" % e)


def run():
    last_usd = get_last_message()
    usd      = float(get_blur_price())
    if abs(last_usd/usd - 1) >= 0.03:
        message = f"Blur: <b>{usd}</b> USD\n"
        message += "\n-----\nIf you have any issues or feedback, " \
                   "feel free to <a href='tg://user?id=383615621'>contact me</a> :)"
        message += "\nCheck out my other <a href='https://linktr.ee/v1et4nh'>Telegram-Bots</a>"
        telegram_bot_sendtext(message, bot_chatID='-1001863970248', disable_web_page_preview=True, parse_mode='HTML')
        save_pickle(usd, PICKLE_FILE)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run()
            sleep(time_intervall)
        except:
            print('Restart...')
            sleep(time_intervall)


if __name__ == '__main__':
    main()
