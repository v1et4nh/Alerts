import os
import requests
import discord
import time
import yaml
import datetime
from time import sleep
from discord.ext import tasks, commands
from discord_ui import UI, SelectOption, SelectMenu
from dotenv import load_dotenv
from Functions.file_handler import load_pickle, save_pickle
from Functions.telegrambot import etherscan_api_key
from Functions.scraping_tools import getOSstats, get_name, get_coin, getOScollection, getETHprice

load_dotenv()
TOKEN   = os.getenv('DISCORD_TOKEN_V1_TEST')
GUILD   = os.getenv('DISCORD_GUILD_STS_V1')
OS_API  = str(os.getenv('OPENSEA_API_KEY'))
OS_API_1  = str(os.getenv('OPENSEA_API_KEY'))
OS_API_2  = str(os.getenv('OPENSEA_API_KEY_2'))
PICKLE_FILE_FLOOR      = '../Data/discord_last_floor_test.pickle'
PICKLE_FILE_COLLECTION = '../Data/discord_collection.pickle'
PICKLE_FILE_COIN       = '../Data/discord_coin.pickle'
PICKLE_FILE_SNIPER     = '../Data/discord_sniper.pickle'
PICKLE_FILE_DATA       = '../Data/discord_data.pickle'


from asyncio import TimeoutError

client = commands.Bot(" ")
ui = UI(client)


def get_dict_data():
    dict_blueprint = {
        'floor': {},
        'sales': {},
        'sniper': {}
    }
    dict_data = load_pickle(PICKLE_FILE_DATA)
    try:
        if 'Error' in dict_data:
            dict_data = dict_blueprint
    except:
        dict_data = dict_blueprint
    return dict_data


def get_last_floor(collection):
    dict_floor = load_pickle(PICKLE_FILE_FLOOR)
    try:
        if collection not in dict_floor:
            dict_floor[collection] = 0
    except:
        dict_floor[collection] = 0
    return dict_floor


def get_opensea_slug(message):
    args = message.content.strip().split(" ")
    name = 'unknown'
    result = "Error: I need the opensea-link or the slug of the collection"
    if len(args) == 1:
        user_input = args[0]
        if "opensea.io" in user_input:
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


@client.listen("on_message")
async def on_message(message: discord.Message):
    if message.content == "!start":
        msg = await message.channel.send("Select a tool:", components=[SelectMenu(options=[
            SelectOption("Breakeven Calculator", label="Breakeven", description="Show the break-even point to sell"),
            SelectOption("Coin Tracker", label="Coin", description="Track the price of a coin"),
            SelectOption("Floor Tracker", label="Floor", description="Track the floor of a collection"),
            SelectOption("Gas Tracker", label="Gas", description="Set an alert for gas fee"),
            SelectOption("Royalty", label="Royalty", description="Get the royalty and OS fee of a collection"),
            SelectOption("Sales Bot", label="Sales", description="Get sales alert for a collection"),
            SelectOption("Sniper Bot", label="Sniper", description="Set a sniper for a collection"),
            SelectOption("Wallet Tracker", label="Wallet", description="Track a wallet for buy/sell activities")
        ], max_values=1)])
        try:
            sel = await msg.wait_for("select", client, by=message.author, timeout=120)
            await sel.respond(f"You selected {sel.selected_values[0]}")
            selected = sel.selected_options[0].content
            if selected == "Breakeven":
                pass
            elif selected == "Coin":
                pass
            elif selected == "Floor":
                msg  = await message.channel.send("Which collection floor do you want to track?\n"
                                                  "Please send me the opensea-link or the slug of the collection :)")
                resp = await client.wait_for("message", timeout=120)
                slug, name, status = get_opensea_slug(resp)
                dict_data = get_dict_data()
                if 'Error' not in status:
                    msg = await message.channel.send("Only get an alert if floor falls below a threshold.\n"
                                                     "Set your threshold (e.g. 0.2 or 0 if you want to get an alert for every floor change):")
                    resp = await client.wait_for("message", timeout=120)
                    args = resp.content.strip().split(" ")
                    if len(args) == 1:
                        user_input = args[0]
                        if str(user_input).isnumeric:
                            threshold = float(user_input)

                            if name not in dict_data['floor']:
                                dict_data['floor'][name] = {
                                    'name':       name,
                                    'slug':       slug,
                                    'channel_id': {str(message.channel.id): threshold},
                                    'last_floor': 0
                                }
                            else:
                                dict_data['floor'][name]['channel_id'][str(message.channel.id)] = threshold
                            save_pickle(dict_data, PICKLE_FILE_DATA)
                            message_to_send = f"Success!\n" \
                                              f"Floor price of the collection\n" \
                                              f">>>>> *{name}* <<<<<\n" \
                                              f"will be tracked!\n" \
                                              f"Threshold is set to {threshold}\n\n"
                            await message.channel.send(message_to_send)
                        else:
                            await message.channel.send("Error: Threshold is not a number")
                    else:
                        await message.channel.send("Error: Threshold is not a number")
                else:
                    await message.channel.send(status)
            elif selected == "Gas":
                pass
            elif selected == "Royalty":
                msg = await message.channel.send("For which collection do you want to get the royalties?\n"
                                                 "Please send me the opensea-link or the slug of the collection :)")
                resp = await client.wait_for("message", timeout=120)
                slug, name, status = get_opensea_slug(resp)
                if "Error" not in status:
                    stats = getOScollection(slug)
                    royalty = stats['collection']['dev_seller_fee_basis_points']
                    royalty = 0.01 * float(royalty)
                    await message.channel.send(f"**Royalty of the collection >> {name} <<:**\n"
                                               f"{royalty} %")
                else:
                    await message.channel.send(status)
            elif selected == "Sales":
                pass
            elif selected == "Sniper":
                msg = await message.channel.send("For which collection do you want to set up a sniper?\n"
                                                 "Please send me the opensea-link or the slug of the collection :)")
                resp = await client.wait_for("message", timeout=120)
                slug, name, status = get_opensea_slug(resp)
                dict_data = get_dict_data()
                if "Error" not in status:
                    msg = await message.channel.send("Get only listings under a threshold.\n"
                                                     "Set your threshold (eg. 0.2 or 0 if you dont want to set a threshold at all):")
                    resp = await client.wait_for("message", timeout=120)
                    args = resp.content.strip().split(" ")
                    if len(args) == 1:
                        user_input = args[0]
                        if str(user_input).isnumeric:
                            threshold = float(user_input)

                            if name not in dict_data['sniper']:
                                dict_data['sniper'][name] = {
                                    'name':         name,
                                    'slug':         slug,
                                    'channel_id':   {str(message.channel.id): threshold},
                                    'last_listing': 0
                                }
                            else:
                                dict_data['sniper'][name]['channel_id'][str(message.channel.id)] = threshold
                            save_pickle(dict_data, PICKLE_FILE_DATA)
                            message_to_send = f"Success!\n" \
                                              f"Sniper is set for the collection\n" \
                                              f">>>>> *{name}* <<<<<\n" \
                                              f"with a threshold of {threshold}\n\n"
                            await message.channel.send(message_to_send)
                        else:
                            await message.channel.send('Error: Threshold is not a number')
                    else:
                        await message.channel.send('Error: Threshold is not a number')
                else:
                    await message.channel.send(status)
            elif selected == "Wallet":
                pass
        except TimeoutError:
            await msg.delete()
    elif message.content == "!stop":
        dict_data  = get_dict_data()
        channel_id = str(message.channel.id)
        print('DEBUG')
        list_options = []
        for tool in dict_data:
            if dict_data[tool]:
                for collection in dict_data[tool]:
                    if channel_id in dict_data[tool][collection]['channel_id']:
                        list_options.append([tool, collection])
        selectOptions = []
        for i, options in enumerate(list_options):
            tool, collection = options
            selectOptions.append(eval(f"SelectOption('{tool}{i}', label='{tool}: {collection}')"))
        msg = await message.channel.send("What do you want to stop?", components=[SelectMenu(options=selectOptions, max_values=1)])
        try:
            sel = await msg.wait_for("select", client, by=message.author, timeout=120)
            tool, collection = sel.selected_options[0].content.split(': ')
            del dict_data[tool][collection]['channel_id'][channel_id]
            if not dict_data[tool][collection]['channel_id']:
                del dict_data[tool][collection]

            # Save new dict
            save_pickle(dict_data, PICKLE_FILE_DATA)
            message_to_send = f"Success!\n" \
                              f"{tool}: {collection} is deleted from this channel!\n\n"
            await sel.respond(message_to_send)
        except TimeoutError:
            await msg.delete()


@tasks.loop(seconds=30)
async def floor():
    dict_data = get_dict_data()
    dict_collection = dict_data['floor']
    for collection in dict_collection:
        try:
            collection      = dict_collection[collection]
            dict_channel_id = collection['channel_id']
            slug            = collection['slug']
            stats           = getOSstats(slug)
            dict_floor      = get_last_floor(collection['name'])
            last_floor      = dict_floor[collection['name']]

            # Get floor price
            try:
                floor_price = float(stats['floor_price'])
            except:
                floor_price = 0
            dict_floor[collection['name']] = floor_price

            # Trigger
            if abs(floor_price-last_floor) > 0:
                icon = ''
                if last_floor != 0:
                    change_ratio = round((float(floor_price / last_floor) - 1) * 100, 2)
                else:
                    change_ratio = 0
                change_ratio = str(change_ratio) + '%'
                if floor_price > last_floor:
                    icon = ':rocket:'
                    change_ratio = '+' + str(change_ratio)
                elif floor_price < last_floor:
                    icon = ':small_red_triangle_down:'

                # Get FIAT price
                eur, usd, = getETHprice()
                eur_price = int(eur * floor_price)
                usd_price = int(usd * floor_price)

                try:
                    ratio = round(stats['count'] / stats['num_owners'], 2)
                except:
                    ratio = 0

                url = 'https://opensea.io/collection/' + slug

                embed = discord.Embed(
                    title=f"{icon} Ξ{floor_price} ({change_ratio}) - {collection['name']} Floor",
                    url=url,
                    color=discord.Color.blue()
                )
                embed.add_field(name=f"**{collection['name']} Floor**", value=f"Ξ{floor_price} ({eur_price}€ | {usd_price}$)", inline=False)
                embed.add_field(name="NFTs", value=str(int(stats['count'])), inline=True)
                embed.add_field(name="Holders", value=str(stats['num_owners']), inline=True)
                embed.add_field(name="NFT-to-Holders-Ratio", value=str(ratio), inline=False)
                embed.add_field(name="Volume traded", value=str(round(stats['total_volume'], 2)), inline=False)

                # Get channel
                for channel_id in dict_channel_id:
                    channel = client.get_channel(int(channel_id))
                    # Only send, if floor is below threshold
                    threshold = dict_channel_id[channel_id]
                    if threshold == 0 or floor_price <= threshold:
                        await channel.send(embed=embed)

                # Save collection
                save_pickle(dict_floor, PICKLE_FILE_FLOOR)
        except:
            pass


@tasks.loop(seconds=60)
async def sniper():
    dict_data   = get_dict_data()
    dict_sniper = dict_data['sniper']
    print(yaml.dump(dict_data, sort_keys=False, default_flow_style=False))
    for collection_name in dict_sniper:
        try:
            collection      = dict_sniper[collection_name]
            dict_channel_id = collection['channel_id']
            slug            = collection['slug']
            last_time       = collection['last_listing']
            # os_data         = getOScollection(slug)
            # os_data         = os_data['collection']
            # contract   = os_data['primary_asset_contracts'][0]['address']
            # traits     = os_data['traits']
            url = f"https://api.opensea.io/api/v1/events?" \
                  f"collection_slug={slug}" \
                  f"&event_type=created" \
                  f"&occurred_after={int(last_time)}"
            headers = {
                "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36",
                "referrer": "https://api.opensea.io/api/v1",
                "Accept": "application/json",
                "X-API-KEY": OS_API
            }

            response = requests.request("GET", url, headers=headers)
            print(f"{collection_name} - resp code: {response.status_code}")
            if response.status_code != 200:
                if OS_API == OS_API_1:
                    OS_API = OS_API_2
                else:
                    OS_API = OS_API_1
            data = response.json()
            for asset in reversed(data['asset_events']):
                # Get timestamp
                last_time = collection['last_listing']
                str_timestamp = asset['listing_time']
                if '.' in str_timestamp:
                    str_timestamp = datetime.datetime.strptime(str_timestamp, "%Y-%m-%dT%H:%M:%S.%f")
                else:
                    str_timestamp = datetime.datetime.strptime(str_timestamp, "%Y-%m-%dT%H:%M:%S")
                str_timestamp += datetime.timedelta(hours=2)
                current_timestamp = time.mktime(str_timestamp.timetuple()) + (str_timestamp.microsecond / 1000000.0)

                # Check if timestamp is later than last timestamp
                if current_timestamp > last_time:
                    # Payment token
                    payment_token = asset['payment_token']['symbol']
                    if payment_token != 'WETH':
                        eur, usd, = getETHprice()
                        # Floor Price
                        stats = getOSstats(slug)
                        try:
                            floor_price = float(stats['floor_price'])
                        except:
                            floor_price = 0
                        eur_floor = int(eur * floor_price)
                        usd_floor = int(usd * floor_price)

                        # Price
                        price = int(asset['starting_price'])
                        price = price / 1000000000000000000
                        eur_price = int(eur * price)
                        usd_price = int(usd * price)

                        # Other Data
                        if asset['asset']:
                            asset_index = 'asset'
                        else:
                            # Skip bundles
                            # asset_index = 'asset_bundle'
                            continue
                        os_url = asset[asset_index]['permalink']
                        img    = asset[asset_index]['image_url']
                        name   = asset[asset_index]['name']

                        # Collection Info
                        coll_img  = asset[asset_index]['collection']['image_url']
                        coll_name = asset[asset_index]['collection']['name']
                        coll_url  = f"https://opensea.io/collection/{slug}"

                        # Traits
                        token_id = asset[asset_index]['token_id']
                        url = f"https://api.opensea.io/api/v1/assets?" \
                              f"token_ids={token_id}" \
                              f"&collection_slug={slug}"

                        resp = requests.request("GET", url, headers=headers)
                        data = resp.json()
                        dict_traits = data['assets'][0]['traits']
                        new_dict = {}
                        for trait in dict_traits:
                            new_dict[trait['trait_type']] = {'name': trait['trait_type'], 'value': trait['value']}
                        dict_traits = new_dict

                        # Send discord message
                        embed = discord.Embed(
                            title=f"Ξ{price} - {name}",
                            url=os_url,
                            color=discord.Color.blue()
                        )
                        embed.set_author(name=f"{coll_name}", url=coll_url, icon_url=coll_img)
                        embed.set_thumbnail(url=img)
                        embed.add_field(name=f"**Price**", value=f"Ξ{price} ({eur_price}€ | {usd_price}$)", inline=True)
                        embed.add_field(name=f"**Floor**", value=f"Ξ{floor_price} ({eur_floor}€ | {usd_floor}$)", inline=True)
                        embed.add_field(name=f"**listing time**", value=f"{str_timestamp} (<t:{int(current_timestamp)}:R>)", inline=False)
                        embed.add_field(name="**____________________**", value='**Properties**', inline=False)
                        for trait in dict_traits:
                            tmp_dict = dict_traits[trait]
                            embed.add_field(name=f"**{tmp_dict['name']}**", value=f"{tmp_dict['value']}", inline=True)
                        embed.timestamp = datetime.datetime.now() - datetime.timedelta(hours=2)
                        embed.set_footer(text="v1_Bot", icon_url="https://pbs.twimg.com/profile_images/1493400962198822914/wOjOlROX_400x400.jpg")

                        # Get channel
                        for channel_id in dict_channel_id:
                            channel   = client.get_channel(int(channel_id))
                            # Only send, if listing is under threshold
                            threshold = dict_channel_id[channel_id]
                            if threshold == 0 or price <= threshold:
                                await channel.send(embed=embed)

                        # Store last_time
                        collection['last_listing'] = current_timestamp
                        dict_sniper[collection_name] = collection
                        save_pickle(dict_sniper, PICKLE_FILE_SNIPER)
        except:
            pass


@client.event
async def on_ready():
    for guild in client.guilds:
        print(f'{client.user} has connected to the following guild:')
        print(f'{guild.name}(id: {guild.id})')

    floor.start()
    # coin_tracking.start()
    sniper.start()


while True:
    try:
        print('Bot started..')
        client.run(TOKEN)
    except:
        sleep(5)
        print('Bot restart..')
