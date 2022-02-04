import requests
import time
from time import sleep
from Crypto.Hash import keccak
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, etherscan_api_key, bot_chatID_private
from Functions.scraping_tools import is_number_tryexcept, get_eth_price
from bot_messages import end_message

NAME        = 'Azuki'
PICKLE_FILE = '../Data/azuki_last_counter.pickle'
ADDRESS     = '0xed5af388653567af2f388e6224dc7c4b3241c544'
OPENSEA     = 'azuki'
TOTALSUPPLY = 'totalSupply'
MAXSUPPLY   = 10000
BOT_CHATID  = '-1001754205908'
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


def getCurrentMintPrice():
    return 0.5
    # AUCTION_START_PRICE = 1
    # AUCTION_END_PRICE = 0.15
    # AUCTION_DROP_INTERVAL = 20 * 60
    # AUCTION_PRICE_CURVE_LENGTH = 340 * 60
    # AUCTION_DROP_PER_STEP = (AUCTION_START_PRICE - AUCTION_END_PRICE) / \
    #                         (AUCTION_PRICE_CURVE_LENGTH / AUCTION_DROP_INTERVAL)
    # salesStartTime = 1642010400
    #
    # currentTime = time.time()
    #
    # if currentTime < salesStartTime:
    #     return AUCTION_START_PRICE
    # elif currentTime - salesStartTime >= AUCTION_PRICE_CURVE_LENGTH:
    #     return AUCTION_END_PRICE
    # else:
    #     steps = int((currentTime - salesStartTime) / AUCTION_DROP_INTERVAL)
    #     return AUCTION_START_PRICE - (steps * AUCTION_DROP_PER_STEP)


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
        if stats['floor_price']:
            floor_price = float(stats['floor_price'])
        else:
            floor_price = 0
        owner_mint_ratio = round(float(mint_counter/stats['num_owners']), 2)

        eur, usd = get_eth_price()
        floor_eur   = int(floor_price * eur)
        floor_usd   = int(floor_price * usd)
        price       = getCurrentMintPrice()
        price_x     = round(floor_price/price, 2)
        eur_price   = int(eur * price)
        usd_price   = int(usd * price)

        message = f"Minted: *{mint_counter}* | Holders: *{stats['num_owners']}*\n" \
                  f"Owner-to-Mint-Ratio: *{owner_mint_ratio}*\n" \
                  f"Left: *{amount_left}* ({left_perc} %)\n\n" \
                  f"Floor Price: *{floor_price} ETH* ({floor_eur} EUR | {floor_usd} USD) *{price_x}x*\n" \
                  f"Volume traded: *{stats['total_volume']} ETH*\n\n" \
                  f"Current Mint Price: *{price} ETH* ({eur_price} EUR | {usd_price} USD)\n\n"
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
