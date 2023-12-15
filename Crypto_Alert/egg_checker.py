import os
import requests
import pandas as pd
from tqdm import tqdm
from time import sleep
from dotenv import load_dotenv
from collections import defaultdict
from Functions.file_handler import save_pickle, load_pickle

# Load environment variables
load_dotenv()
OPENSEA  = 'clonex'
CONTRACT = '0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b'
OS_API   = str(os.getenv('OPENSEA_API_KEY_2'))


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


def getOSstats(collection=OPENSEA):
    url   = "https://api.opensea.io/api/v1/collection/" + collection
    data  = getData(url)
    stats = data['collection']['stats']

    return stats


def get_asset_price(token_id, contract=CONTRACT):
    url = f"https://api.opensea.io/v2/orders/ethereum/seaport/listings?" \
          f"asset_contract_address={contract}" \
          f"&token_ids={token_id}"

    data = getData(url)
    if data['orders']:
        price = int(data['orders'][0]["current_price"])
        price = str(price / 1000000000000000000)
    else:
        price = ''
    return price


def main():
    os_data = getOSstats(OPENSEA)
    total_supply = int(os_data['total_supply'])
    hex_prefix = "0xa1de6e35"
    # clone_dict = defaultdict(list)
    clone_dict = load_pickle('../Data/clonex_egg_claimed.pickle')
    for id in tqdm(range(len(clone_dict['id']) + 1, total_supply + 1)):
        if id != 1:
            clone_dict  = load_pickle('../Data/clonex_egg_claimed.pickle')
        id_hex      = hex(id).replace('0x', '')
        zero_filler = 64 - len(id_hex)
        hex_number  = hex_prefix + '0'*zero_filler + id_hex
        payload     = {"method": "eth_call",
                       "params": [{
                           "to": "0x6c410cf0b8c113dc6a7641b431390b11d5515082",
                           "data": f"{hex_number}"},
                           "latest"],
                       "id": 47,
                       "jsonrpc": "2.0"}
        url = "https://rpc.walletconnect.com/v1/?chainId=eip155:1&projectId=aaf0a53df516c2d85727e264db8586c3"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:107.0) Gecko/20100101 Firefox/107.0",
            "Accept": "*/*",
            "Accept-Language": "de,en-US;q=0.7,en;q=0.3",
            "content-type": "application/json",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "cross-site"
        }
        res  = requests.post(url=url, headers=headers, json=payload)
        data = res.json()
        egg  = not bool(int(data['result'], 16))
        clone_dict['id'].append(id)
        clone_dict['egg'].append(egg)
        clone_dict['price'].append(get_asset_price(id, CONTRACT))
        clone_dict['url'].append(f"https://opensea.io/assets/ethereum/0x49cf6f5d44e70224e2e23fdcdd2c053f30ada28b/{id}")
        save_pickle(clone_dict, '../Data/clonex_egg_claimed.pickle')
        sleep(1)

    return pd.DataFrame(clone_dict)


if __name__ == '__main__':
    df = main()
    save_pickle(df, '../Data/clonex_egg_claimed.pickle')
    print('Finished')

