import datetime
import os
import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private
from bot_messages import end_message
from dotenv import load_dotenv

load_dotenv()
OS_API      = str(os.getenv('OPENSEA_API_KEY'))
NAME        = 'RTFKT Blade'
PICKLE_FILE = '../Data/rtfkt_blade.pickle'
ADDRESS     = '0x43764F5B8973F62A6f10914516131c1489E3190D'
OPENSEA     = 'rtfkt-x-tm-nyc'
BOT_CHATID  = '-1001784551695'
SLEEP       = 10


def get_transaction(occurred_after):
    url = f"https://api.opensea.io/api/v1/events?" \
          f"token_id=2" \
          f"&asset_contract_address={ADDRESS}" \
          f"&collection_slug={OPENSEA}" \
          f"&event_type=transfer" \
          f"&occurred_after={occurred_after}"

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
        "referrer": "https://api.opensea.io/api/v1",
        "Accept": "application/json",
        "X-API-KEY": OS_API
    }

    response = requests.get(url, headers=headers)
    print(f"resp_code: {response.status_code}")
    data = response.json()

    return data


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages['last_time']
    except:
        return 946681200


def getData(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    return data


def run_airdrop_checker():
    last_time  = get_last_message()
    list_transaction  = get_transaction(occurred_after=last_time)
    dict_asset = {'last_time': last_time}
    for asset in reversed(list_transaction['asset_events']):
        str_timestamp = asset['event_timestamp']
        if '.' in str_timestamp:
            str_timestamp = datetime.datetime.strptime(str_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
        else:
            str_timestamp = datetime.datetime.strptime(str_timestamp, "%Y-%m-%dT%H:%M:%S")
        # str_timestamp += datetime.timedelta(hours=2)
        current_timestamp = time.mktime(str_timestamp.timetuple()) + (str_timestamp.microsecond / 1000000.0)

        # check if timestamp is later than the last timestamp
        if current_timestamp > last_time:
            last_time  = current_timestamp
            dict_asset = {'last_time': last_time}
            if not asset['from_account']['user']:
                continue
            from_account = asset['from_account']['user']['username']
            if from_account == 'NullAddress':
                to_account = asset['to_account']['user']['username']
                if not to_account:
                    to_account = 'Unnamed'
                to_account_address = asset['to_account']['address']
                url = asset['asset']['permalink']
                readable_ts = datetime.datetime.utcfromtimestamp(current_timestamp).strftime('%Y-%m-%d %H:%M:%S')
                message = f"*New RTFKT Blade Airdrop*\n" \
                          f"To: *{to_account}*\n" \
                          f"Wallet: *{to_account_address}\n*" \
                          f"Time: *{readable_ts}* UTC\n\n" \
                          f"View it on [OpenSea]({url})\n"
                message += end_message
                telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)

    save_pickle(dict_asset, PICKLE_FILE)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            print(NAME)
            run_airdrop_checker()
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main()
