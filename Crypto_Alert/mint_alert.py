import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, etherscan_api_key


PICKLE_FILE = '../Data/rebelz_last_counter.pickle'


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages['counter']
    except:
        return 10000


def getEtherScanData():
    # address = '0x348FC118bcC65a92dC033A951aF153d14D945312'  # CloneX
    address = '0x074C532B1659bC47065a6c4e784F8965971C3e7c'   # Rebelz
    tmp_dict = {'address': address, 'key': etherscan_api_key}

    return tmp_dict


def getMintedAmount(dict_data):
    """
    To get the data hash value use this website: https://emn178.github.io/online-tools/keccak_256.html
    E.g. if you look for getAmountMinted() on the readContract-site -> insert getAmountMinted() and use 0x and
    the first 8 characters -> 0xe777df20
    """
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x18160ddd&apikey='+dict_data['key']
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'

    data = res.json()
    mintedAmount = int(data['result'], 16)

    return mintedAmount


def getCurrentMintPrice(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x8d859f3e&apikey='+dict_data['key']
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'

    data = res.json()
    currentPrice = float(str(int(data['result'], 16)).replace('0', ''))/1000

    return currentPrice


def getNumberOfHolders():
    url = "https://opensea.io/collection/rebelz"
    resp = requests.get(url)


def run_clonex_mint_counter():
    dict_data    = getEtherScanData()
    last_counter = get_last_message()
    mint_counter = getMintedAmount(dict_data)
    print(last_counter)
    print(mint_counter)
    if mint_counter - last_counter > 0:
        amount_left = 10000 - mint_counter
        message = 'Rebelz amount minted: *' + str(mint_counter) + '*\n\nOnly *' + str(amount_left) + '* Rebelz NFTs left :OOO'
        price = getCurrentMintPrice(dict_data)
        eur_price = int(4000 * price)
        message += '\n\nCurrent Mint Price: *' + str(price) + ' ETH* (~' + str(eur_price) + ' EUR)'
        telegram_bot_sendtext(message, bot_chatID='-1001538195190')
        # telegram_bot_sendtext(message, bot_chatID=bot_chatID_private)
        dict_counter = {'counter': mint_counter}
        save_pickle(dict_counter, PICKLE_FILE)


if __name__ == '__main__':
    while True:
        print(time.strftime('%X %x %Z'))
        run_clonex_mint_counter()
        sleep(0.5)
