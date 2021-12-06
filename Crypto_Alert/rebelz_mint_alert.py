import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, etherscan_api_key, bot_chatID_private

NAME        = 'Rebelz'
PICKLE_FILE = '../Data/rebelz_last_counter.pickle'
ADDRESS     = '0x074C532B1659bC47065a6c4e784F8965971C3e7c'   # Rebelz
OPENSEA     = 'rebelz'
SLEEP       = 5


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
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x18160ddd&apikey='+dict_data['key']
    data = getData(url)
    mintedAmount = int(data['result'], 16)

    return mintedAmount


def getCurrentMintPrice(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x8d859f3e&apikey='+dict_data['key']
    data = getData(url)
    currentPrice = float(str(int(data['result'], 16)).replace('0', ''))/1000

    return currentPrice


def getMaxSupply(dict_data):
    url = 'https://api.etherscan.io/api?module=proxy&action=eth_call&to='+dict_data['address']+'&data=0x5588473c&apikey='+dict_data['key']
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
    dict_data       = getEtherScanData()
    last_counter    = get_last_message()
    mint_counter    = getMintedAmount(dict_data)
    console_output  = NAME + ': Last ' + str(last_counter) + ' | Now ' + str(mint_counter)
    print(console_output)
    if mint_counter - last_counter > 0:
        maxSupply   = getMaxSupply(dict_data)
        amount_left = maxSupply - mint_counter
        stats       = getOSstats()
        message     = 'Minted: *' + str(mint_counter) + '* | Holders: *' + str(stats['num_owners']) + '*'
        message    += '\nLeft: *' + str(amount_left) + '*'
        message    += '\n\nFloor Price: *' + str(stats['floor_price']) + ' ETH*'
        message    += '\nVolume traded: *' + str(int(stats['total_volume'])) + ' ETH*'
        price       = getCurrentMintPrice(dict_data)
        eur, usd, _ = getETHprice()
        eur_price   = int(eur * price)
        usd_price   = int(usd * price)
        message    += '\n\nCurrent Mint Price: *' + str(price) + ' ETH* (' + str(eur_price) + ' EUR | ' + str(usd_price) + ' USD)'
        message    += '\n\n-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
        message    += '\n[Join the Rebelz Discord Community](https://discord.gg/jxQdCyKeaD)'
        telegram_bot_sendtext(message, bot_chatID='-1001701186867', disable_web_page_preview=True)
        # telegram_bot_sendtext(message, bot_chatID=bot_chatID_private, disable_web_page_preview=True)
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
