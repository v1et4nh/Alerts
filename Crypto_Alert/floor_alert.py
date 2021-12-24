import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private, bot_v1_floorbot_token

SLEEP               = 30
PICKLE_FILE_PROJECT = '../Data/v1_floorbot_ids_project.pickle'
PICKLE_FILE_FLOOR   = '../Data/v1_floorbot_ids_last_floor.pickle'


def get_last_floor(chat_id):
    last_floor = load_pickle(PICKLE_FILE_FLOOR)
    try:
        if 'Error' in last_floor:
            return -10000
        return last_floor[chat_id]
    except:
        return -100000


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


def getOSstats(collection):
    url = "https://api.opensea.io/api/v1/collection/" + collection
    data = getData(url)
    stats = data['collection']['stats']

    return stats


def get_current_floor_price(collection):
    stats = getOSstats(collection)
    floor_price = float(stats['floor_price'])
    eur, usd, = getETHprice()
    eur_price = int(eur * floor_price)
    usd_price = int(usd * floor_price)
    url = 'https://opensea.io/collection/' + collection
    message = f"*{collection}*\nFloor Price: *{stats['floor_price']} ETH* (*{eur_price} EUR* | *{usd_price} USD*)"
    message += '\nVolume traded: *' + str(int(stats['total_volume'])) + ' ETH*'
    message += '\nHolders: *' + str(stats['num_owners']) + '*'
    message += '\n\nView in [Opensea](' + url + ')'
    message += '\n\n-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
    message += '\nCheck out my other [Telegram-Bots](https://linktr.ee/v1et4nh)'

    return message


def run_os_stats():
    dict_user_project = load_pickle(PICKLE_FILE_PROJECT)
    for chat_id in dict_user_project:
        collection  = dict_user_project[chat_id]
        stats       = getOSstats(collection)
        last_floor  = get_last_floor(chat_id)
        floor_price = float(stats['floor_price'])
        if abs(floor_price - last_floor) > 0:
            eur, usd, = getETHprice()
            eur_price = int(eur * floor_price)
            usd_price = int(usd * floor_price)
            url       = 'https://opensea.io/collection/' + collection
            message   = f"*{collection}*\nFloor Price: *{stats['floor_price']} ETH* (*{eur_price} EUR* | *{usd_price} USD*)"
            message  += '\nVolume traded: *' + str(int(stats['total_volume'])) + ' ETH*'
            message  += '\nHolders: *' + str(stats['num_owners']) + '*'
            message  += '\n\nView in [Opensea](' + url + ')'
            message  += '\n\n-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
            message  += '\nCheck out my other [Telegram-Bots](https://linktr.ee/v1et4nh)'
            telegram_bot_sendtext(message, bot_chatID=chat_id, bot_token=bot_v1_floorbot_token, disable_web_page_preview=True)
            dict_floor = {chat_id: floor_price}
            save_pickle(dict_floor, PICKLE_FILE_FLOOR)


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
