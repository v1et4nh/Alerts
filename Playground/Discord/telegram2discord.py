import os
import aiohttp
import nextcord
import textwrap
from dotenv import load_dotenv
from telethon import TelegramClient, events


load_dotenv()
API_ID       = int(os.getenv('TELETHON_API_ID'))
API_HASH     = str(os.getenv('TELETHON_API_HASH'))
CHAT_LIST    = list(map(int, str(os.getenv('TELETHON_CHAT_LIST')).split(', ')))
USER_LIST    = list(map(int, str(os.getenv('TELETHON_USER_LIST')).split(', ')))
CHANNEL_LINK = str(os.getenv('TELETHON_CHANNEL_LINK'))
WEBHOOK      = str(os.getenv('TELETHON_WEBHOOK'))


def start():
    with TelegramClient("DAN's Messages", API_ID, API_HASH) as client:
        @client.on(events.NewMessage(chats=CHAT_LIST))
        async def handler(event):
            print(f"Chat-ID: {event.chat_id}")
            print(f"User-ID: {event.message.sender.id}")
            if event.message.sender.id in USER_LIST or event.chat_id == -4796832607:  # Dan's Calls Channel
                message = f"{event.message.chat.title}: {event.message.message}"
                print(message)
                my_channel = await client.get_entity(CHANNEL_LINK)
                await client.send_message(entity=my_channel, message=message)
                await send_to_webhook(event.message.message, event.message.chat.title)
            else:
                print("Not DAN or myself")
                print(f"{event.message.sender.username}: {event.message.message}")

        client.run_until_disconnected()


async def send_to_webhook(message, username):
    async with aiohttp.ClientSession() as session:
        webhook = nextcord.Webhook.from_url(WEBHOOK, session=session)
        for line in textwrap.wrap(message, 2000, replace_whitespace=False):
            await webhook.send(content=line, username=username)

if __name__ == '__main__':
    start()
