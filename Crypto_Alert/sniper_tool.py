import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from time import sleep
from Functions.file_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private


NAME        = 'Huxley'
OPENSEA     = 'huxley-comics'
SLEEP       = 15
PRICE_ALARM = 1000000  # ETH
PICKLE_FILE = '../Data/sniper.pickle'
CONTRACT    = '0x9Ca8887D13BC4591Ae36972702fDf9de2c97957f'
LIMIT       = 100
BOT_CHATID  = '-1001315234047'
load_dotenv()
OS_API_KEY = str(os.getenv('OPENSEA_API_KEY'))


def get_table(contract=''):
    time_border = time.time() - 1800  #30min
    url = f"https://api.opensea.io/api/v1/events?" \
          f"asset_contract_address={contract}&event_type=created&only_opensea=false&offset=0&limit=20&"
          # f"occurred_after={time_border}"
    headers = {
        "Accept": "application/json",
        "X-API-KEY": OS_API_KEY
    }

    response = requests.request("GET", url, headers=headers)
    data = response.json()
    dict_listing = {}
    for idx, entry in enumerate(data['asset_events']):
        current_price = int(entry['starting_price'])
        price_factor = 1000000000000000000
        current_price = current_price/price_factor
        usd_price    = round(float(entry['payment_token']['usd_price']) * current_price, 2)

        dict_listing[str(idx).rjust(2, '0')] = {'listing_time': entry['listing_time'],
                                                'currency':     entry['payment_token']['symbol'],
                                                'eth_price':    current_price,
                                                'usd_price':    usd_price}
        if entry['asset']:
            dict_listing[str(idx).rjust(2, '0')]['url'] =  entry['asset']['permalink']
            dict_listing[str(idx).rjust(2, '0')]['img'] =  entry['asset']['image_url']
            dict_listing[str(idx).rjust(2, '0')]['name'] = entry['asset']['name']
        else:
            dict_listing[str(idx).rjust(2, '0')]['url'] =  entry['asset_bundle']['permalink']
            dict_listing[str(idx).rjust(2, '0')]['img'] =  entry['asset_bundle']['assets'][0]['image_url']
            dict_listing[str(idx).rjust(2, '0')]['name'] = entry['asset_bundle']['name']

    return dict_listing


def huxley(contract=CONTRACT, price=100):
    dict_listing = get_table(contract)
    # Table
    col = []
    headers = ['Preis', 'Link', 'Datum', 'Name']
    for title in headers:
        col.append((title, []))
    for idx in dict_listing:
        entry = dict_listing[idx]
        price = round(float(entry['eth_price']), 4)
        name  = entry['name']
        if 'Issue 1' in name:
            name = 'Issue 1'
            if price > 1.2:
                continue
        elif 'Issue 2' in name:
            name = 'Issue 2'
            if price > 0.3:
                continue
        elif 'Issue 3' in name:
            name = 'Issue 3'
            if price > 0.25:
                continue
        else:
            name = 'Bundle'

        date = entry['listing_time']
        url  = entry['url']

        col[0][1].append(price)
        col[1][1].append(url)
        col[2][1].append(date)
        col[3][1].append(name)

    tmp_dict = {title: column for (title, column) in col}
    df = pd.DataFrame(tmp_dict)
    # df = df.sort_values(['Preis'])
    stats = getOSstats()
    floor_price = float(stats['floor_price'])
    print(f"{NAME}: {floor_price}")
    last_df = get_last_message()
    if not df.equals(last_df):
        stats = getOSstats()
        floor_price = float(stats['floor_price'])
        message = f"*Floor Price: {floor_price}*\n"
        message += '\nURL        |   Price   | Date'
        for row in df.itertuples():
            message += f"\n[{row.Name}]({row.Link})  |  {format(row.Preis, '.4f')}  |  {row.Datum}"
        telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)
        save_pickle(df, PICKLE_FILE)


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages
    except:
        return pd.DataFrame({'A': []})


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
        message  += '\nVolume traded: *' + str(int(stats['total_volume'])) + ' ETH*'
        message  += '\nHolders: *' + str(stats['num_owners']) + '*'
        message  += '\n\nView in [Opensea](' + url + ')'
        message  += '\n\n-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
        message  += '\nCheck out my other [Telegram-Bots](https://linktr.ee/v1et4nh)'
        telegram_bot_sendtext(message, bot_chatID=BOT_CHATID, disable_web_page_preview=True)
        dict_floor = {'floor': floor_price}
        save_pickle(dict_floor, PICKLE_FILE)


def main(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            huxley()
            sleep(time_intervall)
        except:
            print('Restart...')
            sleep(time_intervall)


if __name__ == '__main__':
    main()
