import requests
import time
from time import sleep
from Crypto.Hash import keccak
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, etherscan_api_key, bot_chatID_private
from Functions.scraping_tools import is_number_tryexcept, get_eth_price
from bot_messages import end_message

NAME        = 'Surge'
PICKLE_FILE = '../Data/surge_last_counter.pickle'
ADDRESS     = '0x0632aDCab8F12edD3b06F99Dc6078FE1FEDD32B0'
OPENSEA     = 'surge-passport'
TOTALSUPPLY = 'totalSupply'
MAXSUPPLY   = 'MAX_SUPPLY'
MINTPRICE   = 'price'
BOT_CHATID  = '-1001648191786'
SLEEP       = 1


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


def getMintedAmount(dict_data):
    """
    To get the data hash value use this website: https://emn178.github.io/online-tools/keccak_256.html
    E.g. if you look for getAmountMinted() on the readContract-site -> insert getAmountMinted() and use 0x and
    the first 8 characters -> 0xe777df20
    """
    url = f"https://api.etherscan.io/api?module=proxy&action=eth_call&to={dict_data['address']}" \
          f"&data=0x{get_hash(TOTALSUPPLY)}" \
          f"&apikey={dict_data['key']}"
    data = getData(url)
    mintedAmount = int(data['result'], 16)

    return mintedAmount


def getMaxSupply(dict_data):
    if not is_number_tryexcept(str(MAXSUPPLY)):
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_call&to={dict_data['address']}" \
              f"&data=0x{get_hash(MAXSUPPLY)}" \
              f"&apikey={dict_data['key']}"
        data = getData(url)
        maxSupply = int(data['result'], 16)
    else:
        maxSupply = int(MAXSUPPLY)

    return maxSupply


def getCurrentMintPrice(dict_data):
    if not is_number_tryexcept(str(MINTPRICE)):
        url = f"https://api.etherscan.io/api?module=proxy&action=eth_call&to={dict_data['address']}" \
              f"&data=0x{get_hash(MINTPRICE)}" \
              f"&apikey={dict_data['key']}"
        data = getData(url)
        # currentPrice = float(str(int(data['result'], 16)).replace('0', ''))
        currentPrice = int(data['result'], 16)
        # price_factor = int('1' + '0'*len(str(currentPrice).replace('.', '').replace('0', '')))
        price_factor = 1000000000000000000
        currentPrice = currentPrice/price_factor
    else:
        currentPrice = float(MINTPRICE)

    return currentPrice


def getOSstats(collection=OPENSEA):
    url = "https://api.opensea.io/api/v1/collection/" + collection
    data = getData(url)
    stats = data['collection']['stats']

    return stats


def run_mint_counter():
    dict_data       = getEtherScanData()
    last_counter    = get_last_message()
    mint_counter    = getMintedAmount(dict_data)
    console_output  = f"{NAME}: Last {last_counter} | Now {mint_counter}"
    print(console_output)
    if mint_counter - last_counter > 0:
        maxSupply   = getMaxSupply(dict_data)
        amount_left = maxSupply - mint_counter
        left_perc = round(float(amount_left / maxSupply) * 100, 2)
        stats       = getOSstats()
        try:
            owner_mint_ratio = round(float(mint_counter/stats['num_owners']), 2)
        except:
            owner_mint_ratio = 0.0

        eur, usd = get_eth_price()
        try:
            floor_price = float(stats['floor_price'])
        except:
            floor_price = 0
        floor_eur   = int(floor_price * eur)
        floor_usd   = int(floor_price * usd)
        price       = getCurrentMintPrice(dict_data)
        price_x     = round(floor_price/price, 2)
        eur_price   = int(eur * price)
        usd_price   = int(usd * price)
        os_url = 'https://opensea.io/collection/' + OPENSEA

        message = f"Minted: *{mint_counter}* | Holders: *{stats['num_owners']}*\n" \
                  f"Owner-to-Mint-Ratio: *{owner_mint_ratio}*\n" \
                  f"Left: *{amount_left}* ({left_perc} %)\n\n" \
                  f"Floor Price: *{floor_price} ETH* ({floor_eur} EUR | {floor_usd} USD) *{price_x}x*\n" \
                  f"Volume traded: *{stats['total_volume']} ETH*\n\n" \
                  f"Current Mint Price: *{price} ETH* ({eur_price} EUR | {usd_price} USD)\n\n" \
                  f"View it on [Opensea]({os_url})\n"
        message += end_message
        telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)
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
