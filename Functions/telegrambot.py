import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
bot_token              = str(os.getenv('TELEGRAM_BOT_TOKEN'))           # Replace with your own bot_token
bot_v1_gasfeebot_token = str(os.getenv('TELEGRAM_V1_GASFEEBOT_TOKEN'))  # Replace with your own bot_token
bot_v1_floorbot_token  = str(os.getenv('TELEGRAM_V1_FLOORBOT_TOKEN'))   # Replace with your own bot_token
bot_chatID_group       = str(os.getenv('TELEGRAM_BOT_CHATID_GROUP'))    # Replace with your own bot_chatID
bot_chatID_private     = str(os.getenv('TELEGRAM_BOT_CHATID_PRIVATE'))  # Replace with your own bot_chatID
etherscan_api_key      = str(os.getenv('ETHERSCAN_API_KEY'))            # Replace with your own apy key


def telegram_bot_sendtext(bot_message, bot_token=bot_token, bot_chatID=bot_chatID_group, disable_web_page_preview=False, parse_mode='Markdown'):
    """
    :param bot_message: str, Message to be sent
    :param bot_token: str, Token of your bot defined @botFather, default: from environment variable
    :param bot_chatID: str, ID of the chat you want to send the message to (could be an individual chat or channel),
    default from environment variable
    :return: response status, eg. <Response [200]>
    """
    send_text = f"https://api.telegram.org/bot{bot_token}" \
                f"/sendMessage?chat_id={bot_chatID}" \
                f"&disable_web_page_preview={disable_web_page_preview}" \
                f"&parse_mode={parse_mode}" \
                f"&text={bot_message}"
    # send_text  = 'https://api.telegram.org/bot' + bot_token
    # send_text += '/sendMessage?chat_id=' + bot_chatID
    # if disable_web_page_preview:
    #     send_text += '&disable_web_page_preview=true'
    # send_text += '&parse_mode=Html&text=' + bot_message
    response = requests.get(send_text)
    print(response)
    return response.json()


def telegram_bot_sendphoto_file(str_picpath, bot_token=bot_token, bot_chatID=bot_chatID_group):
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


def telegram_bot_sendphoto_url(url_pic, bot_token=bot_token, bot_chatID=bot_chatID_group):
    """
    :param str_picpath: str, path to the image
    :param bot_token: str, Token of your bot defined @botFather, default: from environment variable
    :param bot_chatID: str, ID of the chat you want to send the message to (could be an individual chat or channel),
    default: from environment variable
    :return:
    """
    send_photo = 'https://api.telegram.org/bot' + bot_token + '/sendPhoto?chat_id=' + bot_chatID + '&photo=' + url_pic
    img_stat = requests.get(send_photo)
    return img_stat


if __name__ == '__main__':
    url = 'https://lh3.googleusercontent.com/vy0zF0QPZuGGLqcwC3C1vk5fdlhFHatUS-v6JKcrnlMv8EeX071MVTebFcCj1g1XHZ_iLW0wMZWkO540Yp9OsDMIXhAbUj-eNfShAA=s250'
    telegram_bot_sendphoto_url(url, bot_chatID=bot_chatID_private)
