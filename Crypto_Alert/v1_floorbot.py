import os
import time
import telebot
from time import sleep
from bot_messages import *
from dotenv import load_dotenv
from telebot.types import InlineKeyboardMarkup as ikm
from telebot.types import InlineKeyboardButton as ikb
from floor_alert import get_current_floor_price, get_name
from Functions.file_handler import save_pickle, load_pickle


PICKLE_FILE = '../Data/v1_floorbot_ids_collection.pickle'

# Load environment variables
load_dotenv()
bot_token       = str(os.getenv('TELEGRAM_V1_FLOORBOT_TOKEN'))        # Replace with your own bot_token
private_chat_id = str(os.getenv('TELEGRAM_V1ET4NH_CHATID'))     # Replace with your own chat_id

# Start Bot
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')


def load_dict_user():
    dict_user = load_pickle(PICKLE_FILE)
    if 'Error' in dict_user:
        dict_user = {}
    return dict_user


def is_number_tryexcept(s):
    """ Returns True is string is a number. """
    try:
        s = s.replace(',', '.')
        float(s)
        return True
    except ValueError:
        return False


def get_update_message():
    send_message  = f"Update: *Bot fixed*!\n" \
                    f"- Automatic alerts should work now\n" \
                    f"- Floor Price Threshold can be set\n" \
                    f"- For each collection an alert bot can be configured:\n" \
                    f"1. Create a group\n" \
                    f"2. Find 'v1 Floor Bot' and add it to the group\n" \
                    f"3. Enjoy\n" \
                    f"Please restart by sending /start"
    send_message += f"\n\n-----\n" \
                    f"If you have any issues or feedback, feel free to [contact me](tg://user?id=383615621) :)\n" \
                    f"Check out my other [Telegram-Bots](https://linktr.ee/v1et4nh)"
    return send_message


@bot.message_handler(commands=['start', 'home'])
def send_welcome(message):
    dict_user = load_dict_user()
    chat_id   = str(message.chat.id)
    user      = str(message.from_user.username)
    print(time.strftime('%X %x %Z'))
    print(f"{user}: {message.text}")
    if chat_id not in dict_user:
        dict_user[chat_id] = {'username': user, 'collection': '', 'threshold': 0}
        send_message = f"{user} joined your Floor Bot"
        bot.send_message(-680483002, send_message)
        save_pickle(dict_user, PICKLE_FILE)
    bot.send_message(message.chat.id, floorbot_welcome_message, disable_web_page_preview=True)


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
    bot.send_message(message.chat.id, floorbot_help_message)


@bot.message_handler(commands=['floor'])
def floor(message):
    chat_id    = str(message.chat.id)
    dict_user  = load_pickle(PICKLE_FILE)
    collection = dict_user[chat_id]['collection']
    message    = get_current_floor_price(collection)
    bot.send_message(chat_id, message, disable_web_page_preview=True)


@bot.message_handler(commands=['collection'])
def collection(message):
    chat_id   = str(message.chat.id)
    dict_user = load_pickle(PICKLE_FILE)
    collection = dict_user[chat_id]['collection']
    if collection:
        url = 'https://opensea.io/collection/' + collection
        message = f"You are currently tracking [{collection}]({url})"
    else:
        message = f"You are not tracking any collection, yet.\n" \
                  f"Please define a collection first by sending me the opensea-url."
    bot.send_message(chat_id, message)


@bot.message_handler(commands=['stop'])
def stop_alert(message):
    chat_id = str(message.chat.id)
    dict_user = load_dict_user()
    user = str(message.from_user.username)
    if chat_id in dict_user:
        dict_user[chat_id] = {'username': user, 'collection': '', 'threshold': 0}
        save_pickle(dict_user, PICKLE_FILE)
    bot.send_message(message.chat.id, 'Alert stopped! Run alert again by sending /start')


##########     Admin     ##########
@bot.message_handler(commands=['getUserCount'])
def getuser(message):
    if message.chat.id == int(private_chat_id) or message.chat.id == 1899354791:
        dict_user = load_pickle(PICKLE_FILE)
        count = len(dict_user)
        bot.send_message(message.chat.id, "Number of User using this bot: " + str(count))
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


@bot.message_handler(commands=['update'])
def update(message):
    if message.chat.id == int(private_chat_id):
        dict_user     = load_pickle(PICKLE_FILE)
        send_message  = get_update_message()
        send_message += f"\n\nList of chatIDs:"
        for chat_id in dict_user:
            send_message += f"\n{dict_user[chat_id]['username']}"
        bot.send_message(message.chat.id, send_message, disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


@bot.message_handler(commands=['updateAll'])
def update_all(message):
    if message.chat.id == int(private_chat_id):
        dict_user = load_pickle(PICKLE_FILE)
        for chat_id in dict_user:
            bot.send_message(chat_id, get_update_message(), disable_web_page_preview=True)
        send_message = f"\n\nUpdates sent to:"
        for chat_id in dict_user:
            try:
                send_message += f"\n{dict_user[chat_id]['username']}"
            except:
                send_message += f"\n{chat_id}"
        bot.send_message(private_chat_id, send_message, disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


##########     User Interface     ###########
@bot.message_handler(func=lambda message: True)
def set_url(message):
    try:
        dict_user = load_dict_user()
        tmp_text  = message.text
        chat_id   = str(message.chat.id)
        print(time.strftime('%X %x %Z'))
        print(f"{chat_id}: {tmp_text}")
        if "opensea.io" in tmp_text:
            collection = tmp_text[tmp_text.rfind('/')+1:]
            name       = get_name(collection)
            dict_user[chat_id]['collection'] = collection
            save_pickle(dict_user, PICKLE_FILE)
            message_to_send  = f"Success!\n" \
                               f"Floor price of the collection\n" \
                               f">>>>> *{name}* <<<<<\n" \
                               f"will be tracked!\n\n" \
                               f"Please set your floor price threshold\n" \
                               f"(for any price change set it to 0): "
            bot.send_message(message.chat.id, message_to_send)
        elif is_number_tryexcept(tmp_text):
            tmp_text = tmp_text.replace(',', '.')
            floor_threshold = float(tmp_text)
            if 'collection' in dict_user[chat_id]:
                dict_user[chat_id]['threshold'] = floor_threshold
                save_pickle(dict_user, PICKLE_FILE)
                collection = dict_user[chat_id]['collection']
                name = get_name(collection)
                if floor_threshold == 0:
                    message_to_send = f"Success!\n" \
                                      f"Collection: *{name}*\n" \
                                      f"Alert-Method: Any Price Change"
                else:
                    message_to_send = f"Success!\n" \
                                      f"Collection: *{name}*\n" \
                                      f"Alert-Method: <*{floor_threshold} ETH*"
                bot.send_message(message.chat.id, message_to_send)
            else:
                message_to_send = f"Please define a collection first by sending me the opensea-url."
                bot.send_message(message.chat.id, message_to_send)
        else:
            bot.send_message(message.chat.id, f"Invalid input!\nPlease make sure it is an opensea-url or a number and try again: ")
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
