from Functions.bs4_handler import get_soup
from Functions.file_handler import save_pickle, load_pickle, load_json
from Functions.telegrambot import telegram_bot_sendtext
from Crypto_Alert.bot_messages import end_message

PICKLE_FILE = '../Data/monopoly_dice_links.pickle'


def get_pickle():
    dict_pickle = load_pickle(PICKLE_FILE)
    if 'Error' in dict_pickle:
        dict_pickle = {'url': []}
    return dict_pickle


if __name__ == '__main__':
    url  = 'https://www.vg247.com/monopoly-go-dice-links'
    soup = get_soup(url)
    dict_links = get_pickle()
    list_url   = soup.findAll("a", href=True)

    for item in list_url:
        if "mply.io" in item.attrs['href'] and item.attrs['href'] not in dict_links['url']:
            dict_links['url'].append(item.attrs['href'])
            message = f"New Dice Link: {item.attrs['href']}\n\n{end_message}"
            telegram_bot_sendtext(message, bot_chatID='-1002041563125', disable_web_page_preview=True)
            save_pickle(dict_links, PICKLE_FILE)