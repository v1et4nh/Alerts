import time
from time import sleep
from Functions.bs4_handler import get_soup
from Functions.file_handler import save_pickle, load_pickle, load_json
from Functions.telegrambot import telegram_bot_sendtext, bot_chatID_private, etherscan_api_key

PICKLE_FILE = '../Data/impftermin_last_messages.pickle'
SLEEP = 60


def main(type=0):
    if type:
        url_type = '?type=' + str(type)
    else:
        url_type = ''
    url = "https://www.docvisit.de/kalender/blankenfeld/list" + url_type
    soup = get_soup(url)
    list_days = soup.findAll('h4')
    message = ''
    num_time = 0
    for day in reversed(list_days):
        tmp_message = '*' + day.contents[0].strip() + '*'
        list_time = day.fetchNextSiblings('a')
        len_range = len(list_time) - num_time
        for idx in range(len_range):
            tmp_url = url.replace('list', list_time[idx].attrs['href'])
            title = list_time[idx].attrs['title']
            tmp_time = list_time[idx].text
            time_message = f"[{tmp_time}h]({tmp_url}): {title}"
            tmp_message += f"\n{time_message}"
        num_time = len(list_time)
        message = tmp_message + '\n\n' + message

    if not message:
        message = 'Keine Termine mehr verfügbar\n\n'
        print(message)
    else:
        message = '*Es sind Impftermine verfügbar*: [Komplette Liste](' + url + ')\n' + message

    message += '-----\nIf you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)'
    message += '\nCheck out my other [Telegram-Bots](https://linktr.ee/v1et4nh)'
    last_message = load_pickle(PICKLE_FILE)
    if last_message != message:
        telegram_bot_sendtext(message, bot_chatID='-1001674194196', disable_web_page_preview=True)
        save_pickle(message, PICKLE_FILE)
    print(message)


def main_loop(time_intervall=SLEEP):
    while True:
        try:
            print(time.strftime('%X %x %Z'))
            main(1558164)
            main(1554376)
            sleep(time_intervall)
        except:
            print('Restart...')


if __name__ == '__main__':
    main_loop()
