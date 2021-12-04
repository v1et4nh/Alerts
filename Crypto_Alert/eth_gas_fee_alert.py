import requests
from Functions.telegrambot import telegram_bot_sendtext, bot_v1_gasfeebot_token, etherscan_api_key
from Functions.file_handler import save_pickle, load_pickle

PICKLE_FILE = '../Data/v1_gasfeebot_ids.pickle'


def get_gasfee():
    getgas = "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey="
    data = requests.get(getgas + etherscan_api_key).json()

    low = data["result"]["SafeGasPrice"]
    avg = data["result"]["ProposeGasPrice"]
    fast = data["result"]["FastGasPrice"]

    gasinfo = f"""*Ethereum Live Gas Fees:*
Low:        _{low} GWEI_
Average:    _{avg} GWEI_
High/Fast:  _{fast} GWEI_

More info: [EtherScan](https://etherscan.io/gasTracker)

Donate to support the development of this bot: /donate"""

    return min([int(low), int(avg), int(fast)]), gasinfo


def run_gas_fee_tracker():
    dict_user = load_pickle(PICKLE_FILE)
    for chat_id in dict_user:
        price, gasinfo = get_gasfee()
        if price <= int(dict_user[chat_id]):
            telegram_bot_sendtext(gasinfo, bot_token=bot_v1_gasfeebot_token, bot_chatID=chat_id)


if __name__ == '__main__':
    run_gas_fee_tracker()
