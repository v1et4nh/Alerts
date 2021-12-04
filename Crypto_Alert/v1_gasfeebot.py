import os
import telebot
from telebot.types import InlineKeyboardMarkup as ikm
from telebot.types import InlineKeyboardButton as ikb
from time import sleep
from dotenv import load_dotenv
from Functions.file_handler import save_pickle, load_pickle
from eth_gas_fee_alert import get_gasfee

PICKLE_FILE = '../Data/v1_gasfeebot_ids.pickle'

# Load environment variables
load_dotenv()
bot_token = str(os.getenv('TELEGRAM_V1_GASFEEBOT_TOKEN'))   # Replace with your own bot_token

# Start Bot
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')

dict_user = load_pickle(PICKLE_FILE)
if 'Error' in dict_user:
    dict_user = {}

welcome_message = """
Hi! I am an ETH Gas Fee Alert Bot. I will send you an alert every time the gas fee falls below your predefined threshold.
\nPlease type in your desired threshold in GWEI (e.g. 80):
"""

help_message = """
/start - Set a gas fee threshold and start the alert
/stop - Stop the alert
/gas - See live gas fee now
/donate - Buy me a coffee or even better: a NFT ;)
/contact - Contact me regarding development of the bot
/help - Display this list
"""

donate_message = """
I am free of charge, but I do still have some running costs. 
My developer will be very grateful if you can support him with a little donation:

*_Ethereum-Address_*: 
0x250103C32239Dad3F31D121d75Da22353C6FF429\n
*_ENS-Address_*: 
vietanh.eth\n
*_Paypal_*: 
https://paypal.me/v1et4nh

After donating, please send a screenshot of donation to @v1et4nh. Thank you very much :)\n
"""


@bot.message_handler(commands=['start', 'home'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    if chat_id not in dict_user:
        dict_user[chat_id] = 0
    bot.send_message(message.chat.id, welcome_message)


@bot.message_handler(commands=['gas'])
def gasfee(message):
    _, gasinfo = get_gasfee()
    bot.send_message(message.chat.id, gasinfo, disable_web_page_preview=True)


@bot.message_handler(commands=['donate'])
def donate(message):
    bot.send_message(message.chat.id, donate_message)


@bot.message_handler(commands=['contact'])
def contact(message):
    mrkp = ikm()
    mrkp.add(ikb("Telegram", url="https://t.me/v1et4nh"), ikb("Twitter", url="https://twitter.com/v1et_le"))
    bot.send_message(message.chat.id, "Contact me if you have any issues or want some new features:", reply_markup=mrkp)


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, help_message)


@bot.message_handler(commands=['getUserCount'])
def getuser(message):
    if message.chat.id == 383615621:
        dict_user = load_pickle(PICKLE_FILE)
        count = len(dict_user)
        bot.send_message(message.chat.id, "Number of User using this bot: " + str(count))
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


@bot.message_handler(commands=['stop'])
def stop_alert(message):
    chat_id = str(message.chat.id)
    if chat_id in dict_user:
        dict_user[chat_id] = 0
    bot.send_message(message.chat.id, 'Alert stopped! Run alert again by typing /start')


@bot.message_handler(func=lambda message: True)
def set_threshold(message):
    try:
        threshold = int(message.text)
        chat_id   = str(message.chat.id)
        dict_user[chat_id] = threshold
        save_pickle(dict_user, PICKLE_FILE)
        bot.send_message(message.chat.id, 'Threshold set successfully to ' + str(threshold) + ' GWEI')
    except:
        bot.send_message(message.chat.id, 'Invalid input! Use /help to see all available commands.')


# Start Bot
print('Bot Listener started..')
while True:
    try:
        bot.polling(none_stop=True)
    except:
        sleep(1)
        print('Bot restart..')
