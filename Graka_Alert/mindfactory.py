from Functions.bs4_handler import get_soup
from Functions.telegrambot import telegram_bot_sendtext


def get_list_item():
    url = 'https://www.mindfactory.de/Hardware/Grafikkarten+(VGA)/GeForce+RTX+fuer+Gaming.html'
    soup = get_soup(url)

    list_url_raw   = soup.findAll("a", attrs={"class": "phover-complete-link"})
    list_name_raw  = soup.findAll("div", attrs={"class": "pname"})
    list_price_raw = soup.findAll("div", attrs={"class": "pprice"})

    tmp_url = []
    for item in list_url_raw:
        tmp_url.append(item.attrs['href'])

    tmp_name = []
    for item in list_name_raw:
        tmp_name.append(item.text.strip())

    tmp_price = []
    for item in list_price_raw:
        tmp_price.append(float(
            item.text.replace('€', '').replace('.', '').replace('-', '').replace('*', '').replace(',', '.').strip()))

    list_item = zip(tmp_url, tmp_name, tmp_price)

    return list_item


def check_price(is_list_price, should_list_price):
    for url, name, price in is_list_price:
        current_idx = name.find('Ti')
        if current_idx != -1:
            start = current_idx - 5
            end = current_idx + 2
        else:
            current_idx = name.find('30')
            start = current_idx
            end = current_idx + 4
        short_name = name[start:end]

        try:
            debug_txt = short_name + ': ' + str(price) + ' | ' + str(should_list_price[short_name])
            print(debug_txt)
            if price <= should_list_price[short_name]:
                message = name + '\n' + str(price) + ' Euro' + '\n' + url
                telegram_bot_sendtext(message)
        except:
            print(short_name + ' is not listed in the scraper')


def main(dict_price):
    list_item = get_list_item()
    check_price(list_item, dict_price)


if __name__ == '__main__':
    dict_price = {'3060':    550,
                  '3060 Ti': 750,
                  '3070':    850,
                  '3070 Ti': 950,
                  '3080':    1350,
                  '3080 Ti': 1550}
    main(dict_price)
