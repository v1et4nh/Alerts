from Functions.bs4_handler import get_soup
from Functions.general_functions import price_triggered
from Functions.pickle_handler import save_pickle, load_pickle
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private

PICKLE_FILE = 'notebooksbilliger.pickle'


def in_stock(soup):
    bool_instock = True
    list_soldout = soup.findAll("div", attrs={"id": "text_no_products"})
    if not list_soldout:
        list_soldout = soup.findAll("div", attrs={"class": "soldOut"})
    if list_soldout:
        bool_instock = False
    return bool_instock


def get_price(soup):
    price_to_track = 9999999999
    list_price = soup.findAll("span", attrs={"class": "product-price__regular js-product-price"})
    for price in list_price:
        price_str = price.text.strip()
        price_to_track = min(float(price_str.replace('€', '').replace('.', '').replace(',', '.').strip()), price_to_track)
    return price_to_track


def get_last_message(item):
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages[item['name']]
    except:
        return ''


def run_notebooksbilliger_alert(list_item):
    dict_items_message = {}
    for item in list_item:
        # Get html source code
        soup = get_soup(item['url'])
        if soup == 'RequestsError':
            telegram_bot_sendtext('Error', bot_chatID=bot_chatID_private)
            break

        # Check if in stock and price triggered
        message_trigger = ''
        url_encoded = item['url'].replace('+', '%2b')
        if in_stock(soup):
            price = get_price(soup)
            if price_triggered(price, item['price']):
                message_trigger = 'PRICE ALERT TRIGGERED!\n' + item['name'] + ' is in stock for ' + str(price) + '€:\n'
                message = message_trigger
            else:
                message = item['name'] + ' is in stock, but not below desired price of ' + str(item['price']) + '€ (Current price: ' + str(price) + '€)\n'
            message += url_encoded
        else:
            message = item['name'] + ' not in stock any more..'
        print(message)

        # Check if message is already sent
        last_message = get_last_message(item)
        if message != last_message:
            if item['flag'] == 'price' and message_trigger:
                telegram_bot_sendtext(message_trigger)
                print('Message sent...')
            if item['flag'] == 'stock':
                telegram_bot_sendtext(message)
                print('Message sent...')

        # Save the last sent message for that item
        dict_items_message[item['name']] = message

    save_pickle(dict_items_message, PICKLE_FILE)


if __name__ == '__main__':
    rtx3060 = {'name': 'RTX 3060',
               'flag':  'price',
               'url':   'https://www.notebooksbilliger.de/pc+hardware/grafikkarten/nvidia/geforce+rtx+3060+nvidia',
               'price': 500}
    rtx3060ti = {'name': 'RTX 3060 Ti',
                 'flag':  'price',
                 'url':   'https://www.notebooksbilliger.de/pc+hardware/grafikkarten/nvidia/geforce+rtx+3060+ti+nvidia',
                 'price': 500}

    rtx3070_founders_edition = {'name': 'RTX 3070 Founders Edition',
                                'flag':  'stock',
                                'url':   'https://www.notebooksbilliger.de/nvidia+geforce+rtx+3070+founders+edition+714793',
                                'price': 550}
    rtx3070 = {'name': 'RTX 3070',
               'flag':  'stock',
               'url':   'https://www.notebooksbilliger.de/pc+hardware/grafikkarten/nvidia/geforce+rtx+3070+nvidia',
               'price': 550}
    rtx3070_ti = {'name': 'RTX 3070 Ti',
                  'flag':  'stock',
                  'url':   'https://www.notebooksbilliger.de/pc+hardware/grafikkarten/nvidia/geforce+rtx+3070+ti+nvidia',
                  'price': 550}

    rtx3080 = {'name': 'RTX 3080',
               'flag':  'price',
               'url':   'https://www.notebooksbilliger.de/pc+hardware/grafikkarten/nvidia/geforce+rtx+3080+nvidia',
               'price': 1200}
    rtx3080ti = {'name': 'RTX 3080 Ti',
                 'flag':  'stock',
                 'url':   'https://www.notebooksbilliger.de/pc+hardware/grafikkarten/nvidia/geforce+rtx+3080+ti+nvidia',
                 'price': 1500}

    list_graka = [rtx3060, rtx3060ti,
                  rtx3070_founders_edition, rtx3070, rtx3070_ti,
                  rtx3080, rtx3080ti]

    run_notebooksbilliger_alert(list_graka)
