import os
import requests
import discord
from time import sleep
from discord.ext import tasks
from dotenv import load_dotenv
from Functions.file_handler import load_pickle, save_pickle
from Functions.telegrambot import etherscan_api_key
from Functions.scraping_tools import getOSstats, get_name, get_coin

load_dotenv()
TOKEN   = os.getenv('DISCORD_TOKEN')
GUILD   = os.getenv('DISCORD_GUILD_STS_V1')
PICKLE_FILE_FLOOR      = '../Data/discord_last_floor.pickle'
PICKLE_FILE_COLLECTION = '../Data/discord_collection.pickle'
PICKLE_FILE_COIN       = '../Data/discord_coin.pickle'
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
            print(last_price)
            if abs(last_price/price-1) > 0.04:
                icon = ''
                if last_price != 0:
                    change_ratio = round((float(price / last_price) - 1) * 100, 2)
                else:
                    change_ratio = 0
                change_ratio = str(change_ratio) + '%'
                print(change_ratio)
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


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(f'{client.user} has connected to the following guild:')
    print(f'{guild.name}(id: {guild.id})')
    floor.start()
    coin_tracking.start()


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
            pass

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


while True:
    try:
        print('Bot started..')
        client.run(TOKEN)
    except:
        sleep(5)
        print('Bot restart..')
