import os
import logging
import discord
from time import sleep
from dotenv import load_dotenv

from Functions.file_handler import load_pickle, save_pickle
from Functions.scraping_tools import getOSstats, get_name, get_coin, getOScollection, getETHprice


load_dotenv()
TOKEN     = os.getenv('DISCORD_TOKEN_V1_TEST')
GUILD     = os.getenv('DISCORD_GUILD_STS_V1')
OS_API    = str(os.getenv('OPENSEA_API_KEY'))
OS_API_1  = str(os.getenv('OPENSEA_API_KEY'))
OS_API_2  = str(os.getenv('OPENSEA_API_KEY_2'))
PICKLE_FILE_DATA = '../Data/discord_bot_full_test_data.pickle'
TIMEOUT   = 60


def get_dict_data():
    dict_blueprint = {
        'coin':   {},
        'floor':  {},
        'gas':    {},
        'sales':  {},
        'sniper': {},
        'wallet': {}
    }
    dict_data = load_pickle(PICKLE_FILE_DATA)
    try:
        if 'Error' in dict_data:
            dict_data = dict_blueprint
    except:
        dict_data = dict_blueprint
    return dict_data


def get_collection(message):
    args   = message.content.strip().split(" ")
    name   = 'unknown'
    result = "Error: I need the opensea-link or the slug of the collection"
    if len(args) == 1:
        user_input = args[0]
        if "opensea.io" in user_input or "blur.io" in user_input:
            slug = user_input[user_input.rfind('/') + 1:]
        else:
            slug = user_input
        name = get_name(slug)
        if name is not None and "Error" not in name:
            result = slug
    if "Error" not in result:
        message_to_send = f"You've selected: {result}"
    else:
        message_to_send = f"{result}"

    return result, name, message_to_send


class ToolDropdown(discord.ui.Select):
    def __init__(self):
        self.user = None
        # Set the options
        options = [
            discord.SelectOption(label="Floor Tracker",
                                 value="Floor",
                                 description="Track the floor price of a collection"),
            discord.SelectOption(label="Listing Alert",
                                 value="Listing",
                                 description="Get new listings of a collection")
        ]

        super().__init__(placeholder='Select a tool...', min_values=1, max_values=1, options=options)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message()


class ToolDropdownView(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.add_item(ToolDropdown())
        self.value = None

    async def interaction_check(self, interaction: discord.Interaction, /) -> bool:
        self.stop()
        self.value = self.children[0].values[0]
        return True


class MyClient(discord.Client):

    async def on_ready(self):
        print("Logged on as ", self.user)

    async def on_message(self, message):
        # don't respond to ourselves
        if message.author == self.user:
            return

        if message.content == '!start':
            bot_user = self.user
            channel  = message.channel
            view = ToolDropdownView()
            await message.channel.send(view=view)
            await view.wait()
            if view.value == 'Floor':
                await message.channel.send(f"Which collection do you want to track?\n"
                                           f"Please send me the slug or Blur/OS-url to the collection:")

                def check(m):
                    return m.content != '' and m.channel == channel and m.author != bot_user

                resp = await client.wait_for("message", timeout=TIMEOUT, check=check)
                slug, name, status = get_collection(resp)
                await message.channel.send(status)
                dict_data = get_dict_data()
                if 'Error' not in status:
                    await message.channel.send(f"\n-----\n"
                                               f"Get alerted if floor falls below a threshold.\n"
                                               f"Set your threshold (0 for any floor price changes): ")
                    resp = await client.wait_for("message", timeout=TIMEOUT, check=check)
                    args = resp.content.strip().split(" ")
                    if len(args) == 1:
                        user_input = args[0]
                        if str(user_input).isnumeric:
                            threshold = float(user_input)

                            if slug not in dict_data['floor']:
                                dict_data['floor'][slug] = {
                                    'name':       name,
                                    'slug':       slug,
                                    'channel_id': {str(message.channel.id): threshold},
                                    'user_id':    {str(message.author): threshold},
                                    'last_floor': 0
                                }
                            else:
                                dict_data['floor'][slug]['channel_id'][str(message.channel.id)] = threshold
                                dict_data['floor'][slug]['user_id'][str(message.author)] = threshold
                            save_pickle(dict_data, PICKLE_FILE_DATA)
                            message_to_send = f"Success!\n" \
                                              f"Floor price of the collection\n" \
                                              f">>>>> *{name}* <<<<<\n" \
                                              f"will be tracked!\n" \
                                              f"Threshold is set to {threshold}\n\n"
                            await message.channel.send(message_to_send)
                        else:
                            await message.channel.send("Error: Threshold is not a number. Please try again!")
                    else:
                        await message.channel.send("Error: Threshold is not a number. Please try again!")
                else:
                    await message.channel.send(status)


# Starting Point #

logging_handler = logging.FileHandler(filename='discord.log', encoding='utf-8', mode='w')

while True:
    try:
        print('Bot started..')
        intents = discord.Intents.default()
        intents.message_content = True
        client = MyClient(intents=intents)
        client.run(TOKEN, log_handler=logging_handler)
    except Exception as e:
        sleep(5)
        print(e)
        print('Bot restart..')
