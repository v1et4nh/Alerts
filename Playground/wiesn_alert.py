import os
from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from webdriver_manager.firefox import GeckoDriverManager
from selenium.webdriver.common.by import By
from Functions.telegrambot import telegram_bot_sendtext


URL = "https://www.oktoberfest-booking.com/de/reseller-angebote"
os.environ['MOZ_HEADLESS'] = '1'
if os.name == 'nt':
    driver = webdriver.Firefox(service=FirefoxService(GeckoDriverManager().install()))
else:
    driver = webdriver.Firefox()
driver.get(URL)
gesamt = driver.find_element(By.CSS_SELECTOR, "div.tw-mt-2:nth-child(2)")
data   = gesamt.text.split('\n')

dict_data = {'vormittag': [],
             'mittag':    [],
             'abend':     []}
if 'Reservierungen für Tische am Abend' in data:
    idx = data.index('Reservierungen für Tische am Abend')
    dict_data['abend'] = data[idx+1:]
    data  = data[:idx]
if 'Reservierungen für Tische am Mittag' in data:
    idx = data.index('Reservierungen für Tische am Mittag')
    dict_data['mittag'] = data[idx+1:]
    data   = data[:idx]
if 'Reservierungen für Tische am Vormittag' in data:
    dict_data['vormittag'] = data[1:]

if dict_data['abend']:
    message = dict_data['abend']
    telegram_bot_sendtext(message, bot_chatID='-1001575230467', disable_web_page_preview=True)

driver.close()