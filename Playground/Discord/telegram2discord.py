import os
from dotenv import load_dotenv
from telethon import TelegramClient, events


load_dotenv()
API_ID       = int(os.getenv('TELETHON_API_ID'))
API_HASH     = str(os.getenv('TELETHON_API_HASH'))
CHAT_LIST    = list(map(int, str(os.getenv('TELETHON_CHAT_LIST')).split(', ')))
USER_LIST    = list(map(int, str(os.getenv('TELETHON_USER_LIST')).split(', ')))
CHANNEL_LINK = str(os.getenv('TELETHON_CHANNEL_LINK'))


with TelegramClient("DAN's Messages", API_ID, API_HASH) as client:
    @client.on(events.NewMessage(chats=CHAT_LIST))
    async def handler(event):
        if event.message.sender.id in USER_LIST:
            message = f"{event.message.sender.username}: {event.message.message}"
            print(message)
            my_channel = await client.get_entity(CHANNEL_LINK)
            await client.send_message(entity=my_channel, message=message)
        else:
            print("Not DAN or myself")
            print(f"{event.message.sender.username}: {event.message.message}")

    client.run_until_disconnected()
