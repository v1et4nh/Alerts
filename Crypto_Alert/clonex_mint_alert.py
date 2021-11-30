import requests
import json
from Functions.telegrambot import telegram_bot_sendtext


def getEtherScanData():
    with open('../Data/api_key.json', mode='r') as key_file:
        key = json.loads(key_file.read())['key']
    address = '0x348FC118bcC65a92dC033A951aF153d14D945312'
    tmp_dict = {'address': address, 'key': key}

    return tmp_dict


def getMintedAmount(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0xe777df20&apikey='+dict_data['key']
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'

    data = res.json()
    mintedAmount = int(data['result'], 16)

    return mintedAmount


def getCurrentMintPrice(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x98d5fdca&apikey='+dict_data['key']
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'

    data = res.json()
    currentPrice = float(str(int(data['result'], 16)).replace('0', ''))/10

    return currentPrice


def run_clonex_mint_counter():
    dict_data = getEtherScanData()
    mint_counter = getMintedAmount(dict_data)
    if mint_counter % 1 == 0:
        amount_left = 20000 - mint_counter
        message = 'Clone X amount minted: ' + str(mint_counter) + '\n\nOnly ' + str(amount_left) + ' Clone X NFTs left :OOO'
        price = getCurrentMintPrice(dict_data)
        eur_price = int(4000 * price)
        message += '\n\nCurrent Mint Price: ' + str(price) + ' ETH (~' + str(eur_price) + ' EUR)'
        telegram_bot_sendtext(message, bot_chatID='-1001538195190')


if __name__ == '__main__':
    run_clonex_mint_counter()
