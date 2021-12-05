import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, etherscan_api_key, bot_chatID_private

NAME        = 'Alpha Girl Club'
PICKLE_FILE = '../Data/agc_last_counter.pickle'
ADDRESS     = '0x8c5029957bf42c61d19a29075dc4e00b626e5022'   # Alpha Girl Club
OPENSEA     = 'alphagirlclub'
SLEEP       = 1


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


def getMintedAmount(dict_data):
    """
    To get the data hash value use this website: https://emn178.github.io/online-tools/keccak_256.html
    E.g. if you look for getAmountMinted() on the readContract-site -> insert getAmountMinted() and use 0x and
    the first 8 characters -> 0xe777df20
    """
    url = 'https://api.etherscan.io/api?module=account&action=balance&address='+dict_data['address']+'&tag=latest&apikey='+dict_data['key']
    data = getData(url)
    mintedAmount = int(int(data['result'])/0.08/1000000000000000000)

    return mintedAmount


def getCurrentMintPrice(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x33039c7c&apikey='+dict_data['key']
    data = getData(url)
    currentPrice = float(str(int(data['result'], 16)).replace('0', ''))/100

    return currentPrice


def getMaxSupply(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0xa62ee636&apikey='+dict_data['key']
    data = getData(url)
    maxSupply = int(data['result'], 16)

    return maxSupply


def getETHprice():
    url_eur = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=eur%2Cbtc&include_market_cap=true&include_24hr_change=true"
    url_usd = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd%2Cbtc&include_market_cap=true&include_24hr_change=true"
    data_eur = requests.get(url_eur).json()
    peur = round(data_eur["ethereum"]["eur"], 2)
    peur = format(peur, ",")
    peur_val = float(peur.replace(',', ''))
    data = requests.get(url_usd).json()
    pusd = round(data["ethereum"]["usd"], 2)
    pusd = format(pusd, ",")
    pusd_val = float(pusd.replace(',', ''))
    pbtc = round(data["ethereum"]["btc"], 8)
    pchange = round(data["ethereum"]["usd_24h_change"], 2)
    market = round(data["ethereum"]["usd_market_cap"])
    market = format(market, ",")

    priceinfo = f"""<b><ins><a href='https://coingecko.com/en/coins/ethereum/'>Ethereum | $ETH</a> Price:</ins></b>
<b>💰 EUR:</b> €{peur}
<b>💰 USD:</b> ${pusd}
<b>🗿 BTC:</b> ฿{pbtc}
<b>📈 24h change:</b> {pchange}%
<b>💎 Market Cap:</b> ${market}
"""

    return peur_val, pusd_val, priceinfo


def getOSstats(collection=OPENSEA):
    url = "https://api.opensea.io/api/v1/collection/" + collection
    data = getData(url)
    stats = data['collection']['stats']

    return stats


def run_mint_counter():
    dict_data    = getEtherScanData()
    last_counter = get_last_message()
    mint_counter = getMintedAmount(dict_data) + 500  # 500 for the team
    print(last_counter)
    print(mint_counter)
    if mint_counter - last_counter > 0:
        maxSupply = getMaxSupply(dict_data)
        amount_left = maxSupply - mint_counter
        stats = getOSstats()
        message  = 'Minted: *' + str(mint_counter) + '* | Holders: *' + str(stats['num_owners']) + '*'
        message += '\nLeft: *' + str(amount_left) + '*'
        message += '\n\nFloor Price: *' + str(stats['floor_price']) + ' ETH*'
        message += '\nVolume traded: *' + str(int(stats['total_volume'])) + ' ETH*'
        price = getCurrentMintPrice(dict_data)
        eur, usd, _ = getETHprice()
        eur_price = int(eur * price)
        usd_price = int(usd * price)
        message += '\n\nCurrent Mint Price: *' + str(price) + ' ETH* (' + str(eur_price) + ' EUR | ' + str(usd_price) + ' USD)'
        telegram_bot_sendtext(message, bot_chatID='-1001655992736')
        dict_counter = {'counter': mint_counter}
        save_pickle(dict_counter, PICKLE_FILE)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run_mint_counter()
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main()
