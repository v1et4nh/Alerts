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
from Functions.telegrambot import bot_v1_testbot_token, bot_v1_floorbot_token


PICKLE_FILE = '../Data/v1_floorbot_ids_collection.pickle'
# PICKLE_FILE = '../Data/v1_testbot_ids_project.pickle'

# Load environment variables
load_dotenv()
bot_token       = bot_v1_floorbot_token
private_chat_id = str(os.getenv('TELEGRAM_V1ET4NH_CHATID'))

# Start Bot
bot = telebot.TeleBot(bot_token, parse_mode='Markdown')


def load_dict_user():
    dict_user = load_pickle(PICKLE_FILE)
    if 'Error' in dict_user:
        dict_user = {}
    return dict_user


def is_number_tryexcept(s):
    """ Returns True if string is a number. """
    try:
        s = s.replace(',', '.').replace('>', '').replace('<', '').strip()
        float(s)
        return True
    except ValueError:
        return False


def get_update_message():
    send_message  = f">>> Update: *New Feature: Alert-Type*! <<<\n\n" \
                    f"*ENG*: Now you can define three types of alerts. Examples:\n" \
                    f"'<0.5': get alerted if floor *falls below* threshold (here: 0.5)\n" \
                    f"'>0.5': get alerted if floor *exceeds* threshold\n" \
                    f"'0':      get alerted for *any* price change\n---\n" \
                    f"*GER*: Man kann jetzt den Alarm-Typ einstellen. Beispiele:\n" \
                    f"'<0.5': Alarm, wenn Floor unter Grenzwert fällt (hier: 0.5)\n" \
                    f"'>0.5': Alarm, wenn Floor Grenzwert überschreitet\n" \
                    f"'0':      Alarm bei jeglicher Preis-Änderung"
    send_message += f"\n\n-----\n" \
                    f"Issues or Feedback? -> [contact me](tg://user?id=383615621) :)\n" \
                    f"Want to see more? -> [Visit my website](https://linktr.ee/v1et4nh)\n" \
                    f"Love the bot? -> /donate <3"
    return send_message


@bot.message_handler(commands=['start', 'home'])
def send_welcome(message):
    dict_user = load_dict_user()
    chat_id   = str(message.chat.id)
    user      = str(message.from_user.username)
    print(time.strftime('%X %x %Z'))
    print(f"{user}: {message.text}")
    if chat_id not in dict_user:
        user = user.replace('_', '').replace('-', '')
        dict_user[chat_id] = {'username': user, 'collection': '', 'threshold': 0, 'alert_type': '<'}
        send_message = f"{user} joined your Floor Bot"
        bot.send_message('-680483002', send_message)
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
    if collection:
        send_message = get_current_floor_price(collection)
        bot.send_message(chat_id, send_message, disable_web_page_preview=True)
    else:
        send_message = f"You are not tracking any collection, yet.\n" \
                       f"Please define a collection first by sending me the opensea-url."
        bot.send_message(chat_id, send_message)


@bot.message_handler(commands=['collection'])
def collection(message):
    chat_id   = str(message.chat.id)
    dict_user = load_pickle(PICKLE_FILE)
    collection = dict_user[chat_id]['collection']
    if collection:
        url = 'https://opensea.io/collection/' + collection
        send_message = f"You are currently tracking [{collection}]({url})"
    else:
        send_message = f"You are not tracking any collection, yet.\n" \
                       f"Please define a collection first by sending me the opensea-url."
    bot.send_message(chat_id, send_message)


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


@bot.message_handler(commands=['clean_empty_dict'])
def clean_dict(message):
    if message.chat.id == int(private_chat_id) or message.chat.id == 1899354791:
        dict_user = load_dict_user()
        len_dict_before = len(dict_user)
        empty_chat_ids = [chat_id for chat_id in dict_user if not dict_user[chat_id]['collection']]
        for chat_id in empty_chat_ids:
            dict_user.pop(chat_id)
        len_dict_after = len(dict_user)
        save_pickle(dict_user, PICKLE_FILE)
        bot.send_message(message.chat.id, f'User Dictionary reduced from {len_dict_before} to {len_dict_after}')
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


@bot.message_handler(commands=['update'])
def update(message):
    if message.chat.id == int(private_chat_id):
        dict_user     = load_pickle(PICKLE_FILE)
        send_message  = get_update_message()
        send_message += f"\n\nList of chatIDs:"
        for chat_id in dict_user:
            try:
                send_message += f"\n{dict_user[chat_id]['username']}"
            except:
                send_message += f"\n{chat_id}"
        bot.send_message(message.chat.id, send_message, disable_web_page_preview=True)
    else:
        bot.send_message(message.chat.id, "Error! You are not authorized to do that!")


@bot.message_handler(commands=['updateAll'])
def update_all(message):
    if message.chat.id == int(private_chat_id):
        dict_user = load_pickle(PICKLE_FILE)
        list_user_sent = []
        for chat_id in dict_user:
            try:
                bot.send_message(chat_id, get_update_message(), disable_web_page_preview=True)
                list_user_sent.append(chat_id)
            except:
                pass
        send_message = f"\n\nUpdates sent to:"
        for chat_id in list_user_sent:
            try:
                send_message += f"\n{dict_user[chat_id]['username']}"
            except:
                send_message += f"\n{chat_id}"
        send_message += f"\nCount: {len(list_user_sent)}/{len(dict_user)}"
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
                               f"Please set your floor price threshold and alert type\n" \
                               f"E.g. '<0.5' or '>0.5' (for any price change set it to 0): "
            bot.send_message(message.chat.id, message_to_send)
        elif is_number_tryexcept(tmp_text):
            tmp_text = tmp_text.replace(',', '.')
            alert_type = '<'
            if tmp_text[0] == '>' or tmp_text[0] == '<':
                alert_type = tmp_text[0]
                tmp_text = tmp_text.replace('>', '').replace('<', '')
                tmp_text = tmp_text.strip()
            floor_threshold = float(tmp_text)
            if dict_user[chat_id]['collection']:
                dict_user[chat_id]['threshold'] = floor_threshold
                dict_user[chat_id]['alert_type'] = alert_type
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
                                      f"Alert-Method: *{alert_type}{floor_threshold} ETH*"
                bot.send_message(message.chat.id, message_to_send)
            else:
                message_to_send = f"Please define a collection first by sending me the opensea-url."
                bot.send_message(message.chat.id, message_to_send)
        else:
            bot.send_message(message.chat.id, f"Invalid input!\nPlease make sure it is an opensea-url or a number and try again: ")
    except:
        bot.send_message(message.chat.id, 'Something went wrong :(\n Please try again or use /help to see all available commands.')


# Start Bot
print('Bot Listener started..')
while True:
    try:
        print('Bot started..')
        bot.polling(none_stop=True)
    except:
        sleep(2)
        print('Bot restart..')
