import requests
import time
from time import sleep
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private

NAME        = 'Clone X'
OPENSEA     = 'clonex-mintvial'
SLEEP       = 5
PRICE_ALARM = 3  # ETH


def getData(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
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
    url = "https://api.opensea.io/api/v1/collection/" + collection
    data = getData(url)
    stats = data['collection']['stats']

    return stats


def run_os_stats():
    stats = getOSstats()
    floor_price = float(stats['floor_price'])
    message  = NAME + ': ' + str(floor_price)
    print(message)
    if floor_price < PRICE_ALARM:
        eur, usd, = getETHprice()
        eur_price = int(eur * floor_price)
        usd_price = int(usd * floor_price)
        message  += '\n\nFloor Price: *' + str(stats['floor_price']) + ' ETH* (*' + str(eur_price) + ' EUR* | *' + str(usd_price) + ' USD*)'
        message  += '\nVolume traded: *' + str(int(stats['total_volume'])) + ' ETH*'
        message  += '\nHolders: *' + str(stats['num_owners']) + '*'
        telegram_bot_sendtext(message, bot_chatID=bot_chatID_private)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            run_os_stats()
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main()
