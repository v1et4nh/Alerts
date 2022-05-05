import os
import requests
import discord
import time
import datetime
from time import sleep
from discord.ext import tasks
from dotenv import load_dotenv
from Functions.file_handler import load_pickle, save_pickle
from Functions.telegrambot import etherscan_api_key
from Functions.scraping_tools import getOSstats, get_name, get_coin, getOScollection

load_dotenv()
TOKEN   = os.getenv('DISCORD_TOKEN')
GUILD   = os.getenv('DISCORD_GUILD_STS_V1')
OS_API  = str(os.getenv('OPENSEA_API_KEY'))
PICKLE_FILE_FLOOR      = '../Data/discord_last_floor.pickle'
PICKLE_FILE_COLLECTION = '../Data/discord_collection.pickle'
PICKLE_FILE_COIN       = '../Data/discord_coin.pickle'
PICKLE_FILE_SNIPER     = '../Data/discord_sniper.pickle'
client = discord.Client()


def get_dict_collection():
    dict_collection = load_pickle(PICKLE_FILE_COLLECTION)
    try:
        if 'Error' in dict_collection:
            return {}
        return dict_collection
    except:
        return {}


def get_dict_coin():
    dict_coin = load_pickle(PICKLE_FILE_COIN)
    try:
        return dict_coin
    except:
        return {}


def get_dict_sniper():
    dict_sniper = load_pickle(PICKLE_FILE_SNIPER)
    try:
        if 'Error' in dict_sniper:
            return {}
        return dict_sniper
    except:
        return {}


def get_last_floor(collection):
    dict_floor = load_pickle(PICKLE_FILE_FLOOR)
    try:
        if collection not in dict_floor:
            dict_floor[collection] = 0
        return dict_floor
    except:
        dict_floor[collection] = 0
        return dict_floor


def get_gasfee():
    getgas = "https://api.etherscan.io/api?module=gastracker&action=gasoracle&apikey="
    data = requests.get(getgas + etherscan_api_key).json()

    low = data["result"]["SafeGasPrice"]
    avg = data["result"]["ProposeGasPrice"]
    fast = data["result"]["FastGasPrice"]

    gasinfo = f"""
    Low:        _{low} GWEI_
    Average:    _{avg} GWEI_
    High/Fast:  _{fast} GWEI_"""

    return gasinfo


def getETHprice():
    url_eur = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=eur%2Cbtc&include_market_cap=true&include_24hr_change=true"
    url_usd = "https://api.coingecko.com/api/v3/simple/price?ids=ethereum&vs_currencies=usd%2Cbtc&include_market_cap=true&include_24hr_change=true"
    data_eur = requests.get(url_eur).json()
    peur = round(data_eur["ethereum"]["eur"], 2)
    peur = format(peur, ",")
    peur_val = float(peur.replace(',', ''))
    data = requests.get(url_usd).json()
    pusd = round(data["ethereum"]["usd"], 2)
    pusd = format(pusd, ",")
    pusd_val = float(pusd.replace(',', ''))

    return peur_val, pusd_val


@tasks.loop(seconds=60)
async def floor():
    dict_collection = get_dict_collection()
    for collection in dict_collection:
        try:
            collection = dict_collection[collection]
            channel_id = collection['channel_id']
            slug       = collection['slug']
            stats      = getOSstats(slug)
            dict_floor = get_last_floor(collection['name'])
            last_floor = dict_floor[collection['name']]

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

                # Get channel
                channel = client.get_channel(int(channel_id))

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
                await channel.send(embed=embed)
                save_pickle(dict_floor, PICKLE_FILE_FLOOR)
        except:
            pass


@tasks.loop(seconds=60)
async def coin_tracking():
    dict_coin = get_dict_coin()
    for coin in dict_coin.keys():
        try:
            coin       = dict_coin[coin]
            channel_id = coin['channel_id']
            slug       = coin['slug']
            last_price = coin['price']
            name, currency, price = get_coin(slug)

            price = round(price, 2)
            if abs(last_price/price-1) > 0.04:
                icon = ''
                if last_price != 0:
                    change_ratio = round((float(price / last_price) - 1) * 100, 2)
                else:
                    change_ratio = 0
                change_ratio = str(change_ratio) + '%'
                if price >= last_price:
                    icon = ':rocket:'
                    change_ratio = '+' + str(change_ratio)
                elif price < last_price:
                    icon = ':small_red_triangle_down:'
                dict_coin[currency]['price'] = price
                # Get channel
                channel = client.get_channel(int(channel_id))
                embed = discord.Embed(
                    title=f"{icon} {price} EUR ({change_ratio}) - {name} Price",
                    color=discord.Color.blue()
                )
                embed.add_field(name=f"**{name}**", value=f"{price} EUR")
                await channel.send(embed=embed)
                save_pickle(dict_coin, PICKLE_FILE_COIN)
        except:
            pass


@tasks.loop(seconds=60)
async def sniper():
    dict_sniper = get_dict_sniper()
    print(f"{dict_sniper}")
    for collection_name in dict_sniper:
        try:
            collection = dict_sniper[collection_name]
            channel_id = collection['channel_id']
            slug       = collection['slug']
            os_data    = getOScollection(slug)
            os_data    = os_data['collection']
            # contract   = os_data['primary_asset_contracts'][0]['address']
            # traits     = os_data['traits']
            url = f"https://api.opensea.io/api/v1/events?" \
                  f"collection_slug={slug}" \
                  f"&event_type=created"
            headers = {
                "Accept": "application/json",
                "X-API-KEY": OS_API
            }

            response = requests.request("GET", url, headers=headers)
            print(f"resp code: {response.status_code}")
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
                            asset_index = 'asset_bundle'
                            # Skip bundles
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
                        headers = {
                            "Accept": "application/json",
                            "X-API-KEY": OS_API
                        }
                        resp = requests.request("GET", url, headers=headers)
                        data = resp.json()
                        dict_traits = data['assets'][0]['traits']
                        new_dict = {}
                        for trait in dict_traits:
                            new_dict[trait['trait_type']] = {'name': trait['trait_type'], 'value': trait['value']}
                        dict_traits = new_dict

                        # Send discord message
                        channel = client.get_channel(int(channel_id))
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
        if guild.name == GUILD:
            break

    print(f'{client.user} has connected to the following guild:')
    print(f'{guild.name}(id: {guild.id})')
    floor.start()
    coin_tracking.start()
    sniper.start()


@client.event
async def on_message(message):
    if message.author.bot:
        return

    if message.content.startswith("!add"):
        args = message.content.split(" ")
        if len(args) == 2:
            dict_collection = get_dict_collection()
            user_input = args[1]
            if "opensea.io" in user_input:
                slug = user_input[user_input.rfind('/')+1:]
            else:
                slug = user_input
            name = get_name(slug)
            if name is None:
                await message.channel.send("Wrong collection slug")
            else:
                dict_collection[name] = {
                    'name': name,
                    'channel_id': message.channel.id,
                    'slug': slug,
                    'last_floor': 0
                }
                save_pickle(dict_collection, PICKLE_FILE_COLLECTION)
                message_to_send = f"Success!\n" \
                                  f"Floor price of the collection\n" \
                                  f">>>>> *{name}* <<<<<\n" \
                                  f"will be tracked!\n\n"
                await message.channel.send(message_to_send)
        else:
            await message.channel.send("I need the slug or the OS-link of the collection")
    elif message.content.startswith("!stop"):
        dict_collection = get_dict_collection()
        try:
            for collection in dict_collection:
                name = collection
                collection = dict_collection[collection]
                if collection['channel_id'] == message.channel.id:
                    del dict_collection[name]
                    save_pickle(dict_collection, PICKLE_FILE_COLLECTION)
                    message_to_send = f"Success!\n" \
                                      f"Floor price will no longer be tracked for the collection\n" \
                                      f">>>>> *{name}* <<<<<\n\n"
                    await message.channel.send(message_to_send)
                    break
        except:
            message.channel.send("Something went wrong - Please Try Again")

    ### Coin Tracker ###
    elif message.content.startswith("!track"):
        args = message.content.split(" ")
        if len(args) == 2:
            dict_coin = get_dict_coin()
            user_input = args[1]
            name, currency, price = get_coin(user_input)
            if name is None:
                await message.channel.send("Unknown currency")
            else:
                dict_coin[currency] = {
                    'channel_id': message.channel.id,
                    'name': name,
                    'currency': currency,
                    'slug': user_input,
                    'price': 0.01
                }
                save_pickle(dict_coin, PICKLE_FILE_COIN)
                message_to_send = f"Success!\n" \
                                  f"Price of the coin\n" \
                                  f">>>>> *{name}* <<<<<\n" \
                                  f"will be tracked!\n\n"
                await message.channel.send(message_to_send)
        else:
            await message.channel.send("I need the currency of the coin listed on nomics.com")
    elif message.content.startswith("!untrack"):
        args = message.content.split(" ")
        if len(args) == 2:
            dict_coin = get_dict_coin()
            user_input = args[1]
            try:
                del dict_coin[user_input]
                save_pickle(dict_coin, PICKLE_FILE_COIN)
                message_to_send = f"Success!\n" \
                                  f"Price will be no longer tracked for the coin\n" \
                                  f">>>>> *{user_input}* <<<<<\n\n"
                await message.channel.send(message_to_send)
            except:
                await message.channel.send("Something went wrong - Unknown coin")
        else:
            await message.channel.send("I need the symbol of the coin!")

    ### Sniper Tool ###
    elif message.content.startswith("!sniper"):
        args = message.content.split(" ")
        if len(args) == 2:
            dict_sniper = get_dict_sniper()
            user_input  = args[1]
            if "opensea.io" in user_input:
                slug = user_input[user_input.rfind('/')+1:]
            else:
                slug = user_input
            name = get_name(slug)
            if name is None:
                await message.channel.send('Wrong collection slug')
            else:
                dict_sniper[name] = {
                    'name': name,
                    'channel_id': message.channel.id,
                    'slug': slug,
                    'last_listing': 0
                }
                save_pickle(dict_sniper, PICKLE_FILE_SNIPER)
                message_to_send = f"Success!\n" \
                                  f"Sniper is set for the collection\n" \
                                  f">>>>> *{name}* <<<<<\n\n"
                await message.channel.send(message_to_send)
        else:
            await message.channel.send("I need the slug or the OS-link of the collection")
    elif message.content.startswith("!deactivate sniper"):
        dict_sniper = get_dict_sniper()
        try:
            for collection in dict_sniper:
                name = collection
                collection = dict_sniper[collection]
                if collection['channel_id'] == message.channel.id:
                    del dict_sniper[name]
                    save_pickle(dict_sniper, PICKLE_FILE_SNIPER)
                    message_to_send = f"Success!\n" \
                                      f"Sniper is stopped for the collection\n" \
                                      f">>>>> *{name}* <<<<<\n\n"
                    await message.channel.send(message_to_send)
                    break
        except:
            message.channel.send("Something went wrong, try again!")


while True:
    try:
        print('Bot started..')
        client.run(TOKEN)
    except:
        sleep(5)
        print('Bot restart..')
