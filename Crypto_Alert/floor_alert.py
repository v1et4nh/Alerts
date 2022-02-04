import requests
import time
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private, bot_v1_floorbot_token, bot_v1_testbot_token

SLEEP               = 45
# PICKLE_FILE_PROJECT = '../Data/v1_testbot_ids_project.pickle'
PICKLE_FILE_PROJECT = '../Data/v1_floorbot_ids_collection.pickle'
# PICKLE_FILE_FLOOR   = '../Data/v1_testbot_ids_last_floor.pickle'
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
    url   = "https://api.opensea.io/api/v1/collection/" + collection
    data  = getData(url)
    stats = data['collection']['stats']

    return stats


def get_name(collection):
    url   = "https://api.opensea.io/api/v1/collection/" + collection
    data  = getData(url)
    name  = data['collection']['name']

    return name


def get_current_floor_price(collection):
    stats = getOSstats(collection)
    floor_price = float(stats['floor_price'])
    eur, usd, = getETHprice()
    eur_price = int(eur * floor_price)
    usd_price = int(usd * floor_price)
    try:
        ratio = round(stats['count'] / stats['num_owners'], 2)
    except:
        ratio = 0
    url = 'https://opensea.io/collection/' + collection
    message = f"*{get_name(collection)}*\n" \
              f"Floor Price: *{stats['floor_price']} ETH* (*{eur_price} EUR* | *{usd_price} USD*)\n" \
              f"NFTs: *{int(stats['count'])}*\n" \
              f"Holders: *{stats['num_owners']}*\n" \
              f"NFT-to-Holders-Ratio: *{ratio}*\n" \
              f"Volume traded: *{round(stats['total_volume'], 2)} ETH*\n" \
              f"\nView on [Opensea]({url})"
    message += f"\n\n-----\n" \
               f"Issues or Feedback? -> [contact me](tg://user?id=383615621) :)\n" \
               f"Want to see more? -> [Visit my website](https://linktr.ee/v1et4nh)\n" \
               f"Love the bots? -> /donate <3"

    return message


def run_os_stats():
    dict_user          = load_pickle(PICKLE_FILE_PROJECT)
    dict_floor         = {}
    dict_current_floor = {}
    error_counter      = 0
    for chat_id in dict_user:
        try:
            collection      = dict_user[chat_id]['collection']
            floor_threshold = dict_user[chat_id]['threshold']
            try:
                alert_type  = dict_user[chat_id]['alert_type']
            except:
                dict_user[chat_id]['alert_type'] = '<'
                alert_type = dict_user[chat_id]['alert_type']
            if collection not in dict_current_floor:
                sleep(5)
                stats = getOSstats(collection)
                dict_current_floor[collection] = stats
            stats = dict_current_floor[collection]
            last_floor  = get_last_floor(chat_id)
            try:
                floor_price = float(stats['floor_price'])
            except:
                floor_price = 0
            dict_floor[chat_id] = floor_price
            trigger_bool = False
            if abs(floor_price - last_floor) > 0:
                if alert_type == '>':
                    if floor_price >= floor_threshold:
                        trigger_bool = True
                else:
                    if floor_price <= floor_threshold:
                        trigger_bool = True
                if floor_threshold == 0 or trigger_bool:
                    eur, usd, = getETHprice()
                    eur_price = int(eur * floor_price)
                    usd_price = int(usd * floor_price)
                    try:
                        ratio = round(stats['count']/stats['num_owners'], 2)
                    except:
                        ratio = 0
                    url       = 'https://opensea.io/collection/' + collection
                    message   = f"*{stats['floor_price']} ETH* - *{get_name(collection)}*\n" \
                                f"Floor Price: *{stats['floor_price']} ETH* (*{eur_price} EUR* | *{usd_price} USD*)\n" \
                                f"NFTs: *{int(stats['count'])}*\n" \
                                f"Holders: *{stats['num_owners']}*\n" \
                                f"NFT-to-Holders-Ratio: *{ratio}*\n" \
                                f"Volume traded: *{round(stats['total_volume'], 2)} ETH*\n" \
                                f"\nView on [Opensea]({url})"
                    message  += f"\n\n-----\n" \
                                f"Issues or Feedback? -> [contact me](tg://user?id=383615621) :)\n" \
                                f"Want to see more? -> [Website](https://linktr.ee/v1et4nh)\n" \
                                f"Love the bots? -> /donate <3"
                    telegram_bot_sendtext(message, bot_chatID=chat_id, bot_token=bot_v1_floorbot_token, disable_web_page_preview=True)
        except:
            try:
                if dict_user[chat_id]['collection']:
                    error_counter += 1
                    send_message = f"*Floor Bot - Error*\n" \
                                   f"{error_counter}) {chat_id} failed"
                    telegram_bot_sendtext(send_message, bot_chatID=bot_chatID_private)
            except:
                send_message = f"*Floor Bot - Collection Error*\n" \
                               f"{error_counter}) {chat_id} failed"
                telegram_bot_sendtext(send_message, bot_chatID=bot_chatID_private)
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
