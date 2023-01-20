import requests
import time
from time import sleep
from Crypto.Hash import keccak
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, etherscan_api_key, bot_chatID_private
from Functions.scraping_tools import is_number_tryexcept, get_eth_price
from bot_messages import end_message

NAME        = 'A Kid Called Beast'
PICKLE_FILE = '../Data/akcb_sales_alert.pickle'
ADDRESS     = '0x77372a4cc66063575b05b44481F059BE356964A4'
OPENSEA     = 'akidcalledbeast'
TOTALSUPPLY = 'totalSupply'
MAXSUPPLY   = 'maxSupply'
MINTPRICE   = 'price'
BOT_CHATID  = '-1001839034738'
SLEEP       = 30


def get_hash(variable):
    if '()' not in variable:
        variable += '()'
    k = keccak.new(digest_bits=256)
    k.update(variable.encode('ascii'))
    k.hexdigest()
    hash_str = k.hexdigest()

    return hash_str[:8]


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages['counter']
    except:
        return -100000


def getEtherScanData(address=ADDRESS):
    tmp_dict = {'address': address, 'key': etherscan_api_key}
    return tmp_dict


def getData(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    return data


def getSalesBool(dict_data):
    """
    To get the data hash value use this website: https://emn178.github.io/online-tools/keccak_256.html
    E.g. if you look for getAmountMinted() on the readContract-site -> insert getAmountMinted() and use 0x and
    the first 8 characters -> 0xe777df20
    If there is input parameter like totalSupply(1) then use Inspection in the browser and see what data is sent
    """
    url = f"https://api.etherscan.io/api?module=proxy&action=eth_call&to={dict_data['address']}" \
          f"&data=0x{get_hash('hasSaleStarted')}" \
          f"&apikey={dict_data['key']}"
    data = getData(url)
    start_bool = int(data['result'], 16)

    return start_bool


def run_sales_alert():
    dict_data       = getEtherScanData()
    last_counter    = get_last_message()
    bool_sale_start = getSalesBool(dict_data)
    console_output  = f"{NAME}: Last {last_counter} | Now {bool_sale_start}"
    print(console_output)

    if bool_sale_start > 0:
        message = f"This is a test message: " \
                  f"{NAME} sales has started\n" \
                  f"Mint here: https://mint.akidcalledbeast.com\n"
        message += end_message
        telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)
        dict_counter = {'counter': bool_sale_start}
        save_pickle(dict_counter, PICKLE_FILE)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run_sales_alert()
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main()
