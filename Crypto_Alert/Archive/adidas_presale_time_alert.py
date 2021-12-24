import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private, etherscan_api_key


NAME        = 'Adidas'
OPENSEA     = 'adidasofficial'
SLEEP       = 1
PICKLE_FILE = '../../Data/adidas_presale_last_time.pickle'
ADDRESS     = '0x28472a58a490c5e09a238847f66a68a47cc76f0f'


def getTime(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x3e8d1c07&apikey='+dict_data['key']
    data = getData(url)
    data = int(data['result'], 16)
    ts = time.ctime(data)

    return ts


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages
    except:
        return '-100000'


def getData(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    return data


def run_timer():
    dict_data       = getEtherScanData()
    last_time       = get_last_message()
    planned_time    = getTime(dict_data)
    console_output  = NAME + ': Last ' + str(last_time) + ' | Now ' + str(planned_time)
    print(console_output)
    if last_time != planned_time:
        message     = '*PRESALE*'
        message    += '\nTime changed from: ' + str(last_time)
        message    += '\nTo: *' + str(planned_time) + '*'
        message    += '\n\n-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
        message  += '\nCheck out my other [Telegram-Bots](https://linktr.ee/v1et4nh)'
        telegram_bot_sendtext(message, bot_chatID='-1001701833606', disable_web_page_preview=True)
        save_pickle(planned_time, PICKLE_FILE)


def getEtherScanData(address=ADDRESS):
    tmp_dict = {'address': address, 'key': etherscan_api_key}
    return tmp_dict


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run_timer()
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main()
