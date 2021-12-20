from Functions.bs4_handler import get_soup
from Functions.file_handler import save_pickle, load_pickle, load_json
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private

PICKLE_FILE = '../Data/notebooksbilliger_last_messages.pickle'


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


def run_notebooksbilliger_alert(dict_graka):
    dict_items_message = {}
    for id, item in dict_graka.items():
        # Get html source code
        soup = get_soup(item['url'])
        if soup == 'RequestsError':
            err_message = 'Error, cannot get data for ' + item['name']
            telegram_bot_sendtext(err_message, bot_chatID=bot_chatID_private)
            last_message = get_last_message(item)
            dict_items_message[item['name']] = last_message
            continue

        # Check if in stock and price triggered
        message_trigger = ''
        url_encoded = item['url'].replace('+', '%2b')
        if in_stock(soup):
            price = get_price(soup)
            if price <= item['price']:
                message = 'PRICE ALERT TRIGGERED!\n' + item['name'] + ' is in stock for ' + str(price) + '€:\n' + url_encoded
                message_trigger = message
            else:
                # message = item['name'] + ' is in stock, but not below desired price of ' + str(item['price']) + '€ (Current price: ' + str(price) + '€)\n'
                message = item['name'] + ' is not in stock any more..'
            # message += url_encoded
        else:
            message = item['name'] + ' is not in stock any more..'
        print(message)

        # Check if message is already sent
        last_message = get_last_message(item)
        if message != last_message:
            if item['flag'] == 'price' and message_trigger:
                telegram_bot_sendtext(message_trigger)
                print('Message sent...')
            else:
                message = item['name'] + ' is not in stock any more..'
                telegram_bot_sendtext(message)
            if item['flag'] == 'stock':
                telegram_bot_sendtext(message)
                print('Message sent...')

        # Save the last sent message for that item
        dict_items_message[item['name']] = message

    save_pickle(dict_items_message, PICKLE_FILE)


if __name__ == '__main__':
    dict_graka = load_json('../Data/notebooksbilliger_graka.json')
    run_notebooksbilliger_alert(dict_graka)
