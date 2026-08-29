import os
import re
import time
import difflib
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from Functions.telegrambot import telegram_bot_sendtext
from Functions.telegrambot import bot_chatID_private

# Wichtig: Der Fragment-Anker #ticket-shop wird gebraucht, damit die
# Angebote beim Laden bereits im HTML stehen.
URL = "https://www.oktoberfest-booking.com/de#ticket-shop"
SLEEP = 300

PENDING_TEXT = "Ein Käufer befindet sich derzeit im Kaufprozess für diese Reservierung"
PENDING_MSG = f'_{PENDING_TEXT}_\n'


def clean_text(text):
    """Mehrfache Whitespaces/Zeilenumbrüche zu einem einzigen Leerzeichen zusammenfassen."""
    return re.sub(r'\s+', ' ', text).strip()


def parse_entry(entry_div, daytime_fallback):
    result = {'items': [], 'total': ''}

    # Wenn gerade jemand anderes den Kaufprozess für diesen Tisch durchläuft,
    # ist der Reservieren-Button ausgegraut/deaktiviert, bleibt aber im DOM.
    # Wir zeigen den Eintrag trotzdem an, aber mit einem Pending-Hinweis.
    result['pending'] = PENDING_TEXT in entry_div.get_text()

    name_tag = entry_div.find('h2', class_='tw-font-semibold')
    result['tent'] = clean_text(name_tag.get_text()) if name_tag else ''

    link_tag = entry_div.find('a', href=True)
    result['tent_url'] = f"https://www.oktoberfest-booking.com{link_tag['href']}" if link_tag else ''

    columns = entry_div.select('div.tw-grid > div.tw-flex.tw-space-x-2')

    # Spalte 1: Datum / Tageszeit / Uhrzeit
    if len(columns) > 0:
        texts = [clean_text(s.get_text()) for s in columns[0].find_all('span') if s.get_text(strip=True)]
        result['date']       = texts[0] if len(texts) > 0 else ''
        result['daytime']    = texts[1] if len(texts) > 1 else daytime_fallback
        result['time_range'] = texts[2] if len(texts) > 2 else ''

    # Spalte 2: Personen / Tische
    if len(columns) > 1:
        texts = [clean_text(s.get_text()) for s in columns[1].find_all('span') if s.get_text(strip=True)]
        result['persons'] = texts[0] if len(texts) > 0 else ''
        result['tables']  = texts[1] if len(texts) > 1 else ''

    # Spalte 3: Inkludierte Leistungen + Summe
    if len(columns) > 2:
        for line in columns[2].select('div.tw-flex.tw-justify-between'):
            spans = line.find_all('span', recursive=False)
            label = clean_text(spans[0].get_text(' ')) if len(spans) > 0 else ''
            price = clean_text(spans[1].get_text(' ')) if len(spans) > 1 else ''
            if label == 'Summe':
                result['total'] = price
            elif label:
                result['items'].append((label, price))

    # Reservieren-Button auslesen. Bei einem laufenden Kaufprozess (pending)
    # ist der Button zwar deaktiviert, aber weiterhin im DOM vorhanden.
    button = entry_div.find('button')
    if button:
        wire_click = button.get('wire:click', '')
        match = re.search(r'reserve\("([\w-]+)"\)', wire_click)
        result['id'] = match.group(1) if match else ''
        result['button_price'] = clean_text(button.get_text())
    else:
        result['id'] = ''
        result['button_price'] = ''

    return result


def wait_for_entries(driver, timeout=20, poll=1):
    """Wartet, bis mindestens ein Angebot geladen ist, oder bis die Zeit abläuft.

    Der Container .ticket-shop-entries existiert schon leer im DOM, bevor
    Livewire/Alpine die eigentlichen Angebote nachlädt. Ein reines
    "Element vorhanden"-Warten (z. B. via WebDriverWait) reicht daher nicht -
    wir müssen aktiv pollen, bis wirklich ein Angebot im Container steckt.
    Läuft die Zeit ab, geben wir False zurück und parsen trotzdem mit dem,
    was da ist (z. B. wenn es aktuell wirklich keine Angebote gibt).
    """
    end_time = time.time() + timeout
    while time.time() < end_time:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        container = soup.find('div', class_='ticket-shop-entries')
        if container and container.find('div', attrs={'x-data': True}):
            return True
        time.sleep(poll)
    return False


def get_data(driver):
    soup = BeautifulSoup(driver.page_source, 'html.parser')
    container = soup.find('div', class_='ticket-shop-entries')
    if not container:
        return {}

    dict_data = {}
    current_daytime = ''
    count = 0

    for child in container.find_all(['h2', 'div'], recursive=False):
        if child.name == 'h2':
            current_daytime = re.sub(r'^Reservierungen für Tische am\s*', '', child.get_text(strip=True))
        elif 'tw-space-y-6' in (child.get('class') or []):
            for entry_div in child.find_all('div', attrs={'x-data': True}, recursive=False):
                count += 1
                dict_data[count] = parse_entry(entry_div, current_daytime)

    return dict_data


def format_entry(e):
    lines = [f"[**{e['tent']}**]({e['tent_url']})"]
    lines.append(f"{e.get('date', '')} | {e.get('daytime', '')} | {e.get('time_range', '')}")
    lines.append(f"{e.get('persons', '')} | {e.get('tables', '')}")
    for label, price in e['items']:
        lines.append(f" - {label}" + (f": {price}" if price else ""))
    lines.append(f"---\nSumme: {e['total']}")
    return "\n".join(lines)


def main(last_message=''):
    os.environ['MOZ_HEADLESS'] = '1'

    if os.name == 'nt':
        driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
    else:
        driver = webdriver.Firefox()

    driver.get(URL)
    wait_for_entries(driver)

    data = get_data(driver)

    total_message = ''
    for i in sorted(data):
        entry = data[i]
        if entry['pending']:
            total_message += PENDING_MSG
        total_message += format_entry(entry) + '\n\n'

    diff_msg = difflib.ndiff(last_message, total_message)
    diff_pos = ''.join([s[-1] for s in diff_msg if s[0] == '+'])
    diff_neg = ''.join([s[-1] for s in diff_msg if s[0] == '-'])
    print(f"##########\nDiff (+):\n{diff_pos}##########\nDiff (-):\n{diff_neg}##########\n")

    disable_notification = True
    if total_message != last_message:
        if len(diff_pos.replace(PENDING_MSG, '')) > 0 and last_message != '':
            disable_notification = False
        print(f'Disable notification: {disable_notification}')
        telegram_bot_sendtext(total_message, bot_chatID='-1001575230467', disable_web_page_preview=True,
                               disable_notification=disable_notification)
        # telegram_bot_sendtext(total_message, bot_chatID=bot_chatID_private, disable_web_page_preview=True,
        #                       disable_notification=disable_notification)
        last_message = total_message

    driver.close()
    print(f"Success: {total_message}")
    return last_message


if __name__ == '__main__':
    last_message = ''
    while True:
        print('Wiesn Alert:')
        try:
            print(time.strftime('%X %x %Z'))
            last_message = main(last_message)
            time.sleep(SLEEP)
        except Exception as e:
            print('Restart...')
            message = f'Irgendetwas stimmt mit dem Wiesn Alert nicht. Fehlermeldung: \n{e}'
            telegram_bot_sendtext(message, bot_chatID='-1001575230467', disable_web_page_preview=True)
            time.sleep(SLEEP)