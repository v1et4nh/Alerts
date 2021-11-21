import requests
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private


def get_gas_prices():
    url = 'https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey=YourApiKeyToken'
    res = requests.get(url)
    if res.status_code != 200:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    data = res.json()
    safe_gas_price    = int(data['result']['SafeGasPrice'])
    propose_gas_price = int(data['result']['ProposeGasPrice'])
    fast_gas_price    = int(data['result']['FastGasPrice'])
    # suggest_base_fee  = float(data['result']['suggestBaseFee'])

    return [safe_gas_price, propose_gas_price, fast_gas_price]


def run_gas_fee_tracker():
    list_gas_prices = get_gas_prices()
    for price in list_gas_prices:
        if price <= 50:
            gas_url = 'https://etherscan.io/gastracker#historicaldata'
            message = 'Gas Price is at ' + str(price) + ' Gwei!\nCheck it out: ' + gas_url
            telegram_bot_sendtext(message, bot_chatID=bot_chatID_private)
            break
    # Debug
    print(list_gas_prices)
    print('No trigger')


if __name__ == '__main__':
    run_gas_fee_tracker()
