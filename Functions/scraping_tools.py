import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
API_KEY_NOMICS = str(os.getenv('NOMICS_API_KEY'))


def get_response(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    return res


def get_eth_price():
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


def is_number_tryexcept(s):
    """ Returns True is string is a number. """
    try:
        s = s.replace(',', '.')
        float(s)
        return True
    except ValueError:
        return False


def getData(url):
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    return data


def getOSstats(collection):
    url   = "https://api.opensea.io/api/v1/collection/" + collection
    data  = getData(url)
    stats = data['collection']['stats']

    return stats


def getOScollection(collection):
    url   = f"https://api.opensea.io/api/v1/collection/{collection}"
    data  = getData(url)

    return data


def get_name(collection):
    url   = "https://api.opensea.io/api/v1/collection/" + collection
    data  = getData(url)
    try:
        name  = data['collection']['name']
    except:
        name = "Error"

    return name


def get_coin(coin):
    url = f"https://api.nomics.com/v1/currencies/ticker?key={API_KEY_NOMICS}" \
          f"&ids={coin}" \
          f"&interval=1d" \
          f"&convert=EUR"
    data = requests.get(url).json()
    name = data[0]['name']
    symbol = data[0]['symbol']
    price = float(data[0]['price'])

    return name, symbol, price


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