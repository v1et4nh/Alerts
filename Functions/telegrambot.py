import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
bot_token          = str(os.getenv('TELEGRAM_BOT_TOKEN'))           # Replace with your own bot_token
bot_chatID_group   = str(os.getenv('TELEGRAM_BOT_CHATID_GROUP'))          # Replace with your own bot_chatID
bot_chatID_private = str(os.getenv('TELEGRAM_BOT_CHATID_PRIVATE'))  # Replace with your own bot_chatID


def telegram_bot_sendtext(bot_message, bot_token=bot_token, bot_chatID=bot_chatID_group):
    """
    :param bot_message: str, Message to be sent
    :param bot_token: str, Token of your bot defined @botFather, default: from environment variable
    :param bot_chatID: str, ID of the chat you want to send the message to (could be an individual chat or channel),
    default from environment variable
    :return: response status, eg. <Response [200]>
    """
    send_text  = 'https://api.telegram.org/bot' + bot_token + '/sendMessage?chat_id=' + bot_chatID + '&parse_mode=Markdown&text=' + bot_message
    response = requests.get(send_text)
    print(response)
    return response.json()


def telegram_bot_sendphoto(str_picpath, bot_token=bot_token, bot_chatID=bot_chatID_group):
    """
    :param str_picpath: str, path to the image
    :param bot_token: str, Token of your bot defined @botFather, default: from environment variable
    :param bot_chatID: str, ID of the chat you want to send the message to (could be an individual chat or channel),
    default: from environment variable
    :return:
    """
    send_photo = 'https://api.telegram.org/bot' + bot_token + '/sendPhoto?chat_id=' + bot_chatID
    files = {'photo': open(str_picpath, 'rb')}
    img_stat = requests.post(send_photo, files=files)
    return img_stat


if __name__ == '__main__':
    telegram_bot_sendtext('Test')
