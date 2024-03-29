import requests
import time
import os
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private

NAME        = 'My Pet Hooligans'
OPENSEA     = 'mypethooligan'
SLEEP       = 60
PRICE_ALARM = 100000  # ETH
PICKLE_FILE = '../Data/mypethooligan_last_floor.pickle'
OS_API      = str(os.getenv('OPENSEA_API_KEY'))


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages['floor']
    except:
        return -100000


def getData(url):
    res = requests.get(url, headers={"accept": "application/json",
                                     "X-API-KEY": OS_API})
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0",
                                         "X-API-KEY": OS_API})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    return data


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

    return peur_val, pusd_val


def getOSstats(collection=OPENSEA):
    url = "https://api.opensea.io/api/v2/collections/" + collection + "/stats"
    data = getData(url)
    stats = data['total']
    try:
        url = "https://api.opensea.io/api/v2/collections/" + collection
        data = getData(url)
        total_supply = int(data["rarity"]["tokens_scored"])
    except:
        total_supply = 'unknown'
    stats['total_supply'] = total_supply

    return stats


def run_os_stats():
    stats = getOSstats()
    last_floor = get_last_message()
    floor_price = float(stats['floor_price'])
    message  = NAME + ': ' + str(floor_price)
    print(message)
    if floor_price < PRICE_ALARM and abs(floor_price - last_floor) > 0:
        eur, usd, = getETHprice()
        eur_price = int(eur * floor_price)
        usd_price = int(usd * floor_price)
        url       = 'https://opensea.io/collection/' + OPENSEA
        message   = '\n\nFloor Price: *' + str(stats['floor_price']) + ' ETH* (*' + str(eur_price) + ' EUR* | *' + str(usd_price) + ' USD*)'
        message  += '\nVolume traded: *' + str(int(stats['volume'])) + ' ETH*'
        message  += '\nHolders: *' + str(stats['num_owners']) + '*'
        message  += '\n\nView in [Opensea](' + url + ')'
        message  += '\n\n-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
        message  += '\nCheck out my other [Telegram-Bots](https://linktr.ee/v1et4nh)'
        telegram_bot_sendtext(message, bot_chatID='-1001566937584', disable_web_page_preview=True)
        dict_floor = {'floor': floor_price}
        save_pickle(dict_floor, PICKLE_FILE)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run_os_stats()
            sleep(time_intervall)
        except:
            print('Restart...')
            sleep(time_intervall)


if __name__ == '__main__':
    main()
