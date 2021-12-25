import os
import telebot
from telebot.types import InlineKeyboardMarkup as ikm
from telebot.types import InlineKeyboardButton as ikb
from time import sleep
from dotenv import load_dotenv
from Functions.file_handler import save_pickle, load_pickle
from floor_alert import get_current_floor_price, get_name

PICKLE_FILE = '../Data/v1_floorbot_ids_project.pickle'

# Load environment variables
load_dotenv()
bot_token = str(os.getenv('TELEGRAM_V1_FLOORBOT_TOKEN'))   # Replace with your own bot_token

# Start Bot
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')

dict_user = load_pickle(PICKLE_FILE)
if 'Error' in dict_user:
    dict_user = {}

welcome_message = """
Hi! I am an Opensea Floor Alert Bot. I will send you a message every time the floor price of your chosen collection changes. Which collection do you want to track?
\nPlease send me the opensea-url \n(e.g. https://opensea.io/collection/clonex):
"""

help_message = """
/start - Set an opensea-url and start the alert
/stop - Stop the alert
/floor - Get the current floor price
/collection - Show the current tracked collection
/donate - Buy me a coffee or even better: a NFT ;)
/contact - Contact me regarding the development of the bot
/help - Show the command list of this bot
"""

donate_message = """
I am free of charge, but I do still have some running costs. 
My developer will be very grateful if you support him by sending him a little donation:

*_Ethereum-Address_*: 
0x250103C32239Dad3F31D121d75Da22353C6FF429\n
*_ENS-Address_*: 
vietanh.eth\n
*_Paypal_*: 
https://paypal.me/v1et4nh
"""


@bot.message_handler(commands=['start', 'home'])
def send_welcome(message):
    chat_id = str(message.chat.id)
    if chat_id not in dict_user:
        dict_user[chat_id] = 0
    bot.send_message(message.chat.id, welcome_message, disable_web_page_preview=True)


@bot.message_handler(commands=['floor'])
def floor(message):
    chat_id = str(message.chat.id)
    dict_user_project = load_pickle(PICKLE_FILE)
    collection = dict_user_project[chat_id]
    message = get_current_floor_price(collection)
    bot.send_message(chat_id, message, disable_web_page_preview=True)


@bot.message_handler(commands=['collection'])
def collection(message):
    chat_id = str(message.chat.id)
    dict_user_project = load_pickle(PICKLE_FILE)
    collection = dict_user_project[chat_id]
    url = 'https://opensea.io/collection/' + collection
    message = f"You are currently tracking [{collection}]({url})"
    bot.send_message(chat_id, message)


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
    if message.chat.id == 383615621 or message.chat.id == 1899354791:
        dict_user = load_pickle(PICKLE_FILE)
        count = len(dict_user)
        bot.send_message(message.chat.id, "Number of User using this bot: " + str(count))
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


@bot.message_handler(commands=['stop'])
def stop_alert(message):
    chat_id = str(message.chat.id)
    if chat_id in dict_user:
        dict_user[chat_id] = ''
        save_pickle(dict_user, PICKLE_FILE)
    bot.send_message(message.chat.id, 'Alert stopped! Run alert again by typing /start')


@bot.message_handler(func=lambda message: True)
def set_url(message):
    try:
        url = message.text
        if "opensea.io" in url:
            project   = url[url.rfind('/')+1:]
            name      = get_name(project)
            chat_id   = str(message.chat.id)
            dict_user[chat_id] = project
            save_pickle(dict_user, PICKLE_FILE)
            bot.send_message(message.chat.id, f"Success! Floor price of the collection '{name}' will be tracked!")
        else:
            bot.send_message(message.chat.id, f"Invalid input! Please make sure it is an opensea-url and try again: ")
    except:
        bot.send_message(message.chat.id, 'Invalid input! Use /help to see all available commands.')


# Start Bot
print('Bot Listener started..')
while True:
    try:
        print('Bot started..')
        bot.polling(none_stop=True)
    except:
        sleep(2)
        print('Bot restart..')
