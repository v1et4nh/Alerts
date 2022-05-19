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
from asyncio import TimeoutError
from Functions.file_handler import load_pickle, save_pickle
from Functions.scraping_tools import getOSstats, get_name, get_coin, getOScollection, getETHprice

load_dotenv()
TOKEN   = os.getenv('DISCORD_TOKEN_V1_TEST')
GUILD   = os.getenv('DISCORD_GUILD_STS_V1')
OS_API  = str(os.getenv('OPENSEA_API_KEY'))
OS_API_1  = str(os.getenv('OPENSEA_API_KEY'))
OS_API_2  = str(os.getenv('OPENSEA_API_KEY_2'))
PICKLE_FILE_DATA = '../Data/discord_data.pickle'
TIMEOUT = 60

client = commands.Bot(" ")
ui = UI(client)


def check_wait_for(message):
    return message.author


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
            sel = await msg.wait_for("select", client, by=message.author, timeout=TIMEOUT)
            await sel.respond(f"You selected {sel.selected_values[0]}")
            selected = sel.selected_options[0].content
            if selected == "Breakeven":
                pass
            elif selected == "Coin":
                msg = await message.channel.send("What coin do you want to track?\n"
                                                 "Please find the coin on https://nomics.com and send me the url to the coin:")
                resp = await client.wait_for("message", timeout=TIMEOUT)
                url  = resp.content
                slug = url.split('/')[-1].split('-')[0].upper()
                name, currency, price = '', 0, 0
                try:
                    name, currency, price = get_coin(slug)
                    bool_success = True
                except:
                    bool_success = False
                if not bool_success:
                    await message.channel.send("Something went wrong. Please try again!")
                else:
                    if name is None:
                        await message.channel.send("Error: Unknown currency!")
                    else:
                        msg = await message.channel.send("Set the change rate:")
                        resp = await client.wait_for("message", timeout=TIMEOUT)
                        if '%' in resp.content:
                            change_rate = float(resp.content.replace('%', '').strip()) / 100
                            change_type = 'relative'
                            change_text = f"{change_rate*100}% (relative)"
                        else:
                            change_rate = float(resp.content.strip())
                            change_type = 'absolute'
                            change_text = f"{change_rate} (absolute)"
                        dict_data = get_dict_data()
                        if currency not in dict_data['coin']:
                            dict_data['coin'][currency] = {
                                'url':      url,
                                'name':     name,
                                'currency': currency,
                                'slug':     slug,
                                'last_price': 0.0,
                                'channel_id': {str(message.channel.id): [change_type, change_rate]},
                            }
                        else:
                            dict_data['coin'][currency]['channel_id'][str(message.channel.id)] = [change_type, change_rate]
                        save_pickle(dict_data, PICKLE_FILE_DATA)
                        message_to_send = f"Success!\n" \
                                          f"Tracker is set up for the coin\n" \
                                          f">>>>> *{name}* <<<<<\n" \
                                          f"with a change rate of {change_text}!\n"
                        await message.channel.send(message_to_send)

            elif selected == "Floor":
                msg  = await message.channel.send("Which collection floor do you want to track?\n"
                                                  "Please send me the opensea-link or the slug of the collection :)")
                resp = await client.wait_for("message", timeout=TIMEOUT)
                slug, name, status = get_opensea_slug(resp)
                dict_data = get_dict_data()
                if 'Error' not in status:
                    msg = await message.channel.send("Only get an alert if floor falls below a threshold.\n"
                                                     "Set your threshold (e.g. 0.2 or 0 if you want to get an alert for every floor change):")
                    resp = await client.wait_for("message", timeout=TIMEOUT)
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
                resp = await client.wait_for("message", timeout=TIMEOUT)
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
                resp = await client.wait_for("message", timeout=TIMEOUT)
                slug, name, status = get_opensea_slug(resp)
                dict_data = get_dict_data()
                if "Error" not in status:
                    msg = await message.channel.send("Get only listings under a threshold.\n"
                                                     "Set your threshold (eg. 0.2 or 0 if you dont want to set a threshold at all):")
                    resp = await client.wait_for("message", timeout=TIMEOUT)
                    args = resp.content.strip().split(" ")
                    if len(args) == 1:
                        user_input = args[0]
                        if str(user_input).isnumeric:
                            threshold = float(user_input)

                            # Traits
                            os_data = getOScollection(slug)
                            os_data = os_data['collection']
                            traits  = os_data['traits']
                            selectTraits = []
                            for trait in traits:
                                selectTraits.append(eval(f"SelectOption('{trait}', label='{trait}')"))

                            dict_trait_filter = {}
                            msg = await message.channel.send("Do you want to add a trait-filter?", components=[SelectMenu(options=[
                                SelectOption("Yes", label="Yes", description="Add Trait Filter"),
                                SelectOption("No", label="No", description="No Trait Filter")
                            ], max_values=1)])
                            sel = await msg.wait_for("select", client, by=message.author, timeout=TIMEOUT)
                            add_filter = sel.selected_options[0].content
                            await sel.respond(f"You selected '{add_filter}'")
                            while add_filter == 'Yes':
                                try:
                                    msg_trait = await message.channel.send("Select the trait:", components=[SelectMenu(options=selectTraits, max_values=1)])
                                    sel = await msg_trait.wait_for("select", client, by=message.author, timeout=TIMEOUT)
                                    sel_trait = sel.selected_options[0].content
                                    if sel_trait not in dict_trait_filter:
                                        dict_trait_filter[sel_trait] = []
                                    await sel.respond(f"You selected {sel_trait}")
                                    selectSubTraits = []
                                    for trait in traits[sel_trait]:
                                        selectSubTraits.append(eval(f"SelectOption('{trait}', label='{trait}')"))
                                    msg_trait = await message.channel.send(f"Select the {sel_trait}-trait (multiple selection possible):", components=[SelectMenu(options=selectSubTraits, max_values=len(selectSubTraits))])
                                    sel = await msg_trait.wait_for("select", client, by=message.author, timeout=TIMEOUT)
                                    for subtrait in sel.selected_options:
                                        if subtrait.content not in dict_trait_filter[sel_trait]:
                                            dict_trait_filter[sel_trait].append(subtrait.content)
                                    await sel.respond(f"Your filter selected so far: {dict_trait_filter}")
                                    msg = await message.channel.send("Do you want to add a trait-filter?", components=[SelectMenu(options=[
                                        SelectOption("Yes", label="Yes", description="Add Trait Filter"),
                                        # SelectOption("Edit", label="Edit", description="Edit Trait Filter"),
                                        SelectOption("No", label="No", description="No Trait Filter")
                                    ], max_values=1)])
                                    sel = await msg.wait_for("select", client, by=message.author, timeout=TIMEOUT)
                                    add_filter = sel.selected_options[0].content
                                    await sel.respond(f"You selected '{add_filter}'")
                                except TimeoutError:
                                    await msg.delete()

                            if name not in dict_data['sniper']:
                                dict_data['sniper'][name] = {
                                    'name':         name,
                                    'slug':         slug,
                                    'channel_id':   {str(message.channel.id): threshold},
                                    'last_listing': 0,
                                    'trait_filter': dict_trait_filter
                                }
                            else:
                                dict_data['sniper'][name]['channel_id'][str(message.channel.id)] = threshold
                            save_pickle(dict_data, PICKLE_FILE_DATA)
                            message_to_send = f"Success!\n" \
                                              f"Sniper is set for the collection\n" \
                                              f">>>>> *{name}* <<<<<\n" \
                                              f"with a threshold of {threshold} with following trait filter:\n" \
                                              f"{dict_trait_filter}\n"
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
            sel = await msg.wait_for("select", client, by=message.author, timeout=TIMEOUT)
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
            # dict_floor      = get_last_floor(collection['name'])
            last_floor      = collection['last_floor']
            # last_floor      = dict_floor[collection['name']]

            # Get floor price
            try:
                floor_price = float(stats['floor_price'])
            except:
                floor_price = 0
            collection['last_floor'] = floor_price
            dict_data['floor'][collection['name']] = collection

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
                save_pickle(dict_data, PICKLE_FILE_DATA)
        except:
            pass


@tasks.loop(seconds=60)
async def sniper():
    dict_data   = get_dict_data()
    dict_sniper = dict_data['sniper']
    print(time.strftime('%X %x %Z'))
    print(yaml.dump(dict_data, sort_keys=False, default_flow_style=False))
    for collection_name in dict_sniper:
        try:
            collection      = dict_sniper[collection_name]
            dict_channel_id = collection['channel_id']
            slug            = collection['slug']
            last_time       = collection['last_listing']
            dict_filter     = collection['trait_filter']
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
                continue
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
                        # Filter Traits
                        bool_skip = False
                        for trait in dict_filter:
                            if trait not in dict_traits:
                                bool_skip = True
                                break
                            if dict_traits[trait]['value'] not in dict_traits[trait]:
                                bool_skip = True
                                break
                        if bool_skip:
                            continue

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
                        dict_data['sniper'][collection_name] = collection
                        save_pickle(dict_data, PICKLE_FILE_DATA)
        except:
            pass


@tasks.loop(seconds=60)
async def coin():
    dict_data = get_dict_data()
    dict_coin = dict_data['coin']
    for coin in dict_coin:
        try:
            coin = dict_coin[coin]
            dict_channel_id = coin['channel_id']
            slug = coin['slug']
            last_price = coin['last_price']
            coin_url = coin['url']
            # coin_name = coin['name'],
            # coin_currency = coin['currency']

            name, currency, price = get_coin(slug)
            for channel_id in dict_channel_id:
                channel = client.get_channel(int(channel_id))
                change_type, change_rate = dict_channel_id[channel_id]
                if change_type == 'absolute':
                    if abs(last_price - price) < change_rate:
                        continue
                elif change_type == 'relative':
                    if abs(last_price / price - 1) < change_rate:
                        continue
                icon = ''
                if last_price != 0:
                    change_ratio = round((float(price/last_price)-1)*100, 2)
                else:
                    change_ratio = 0
                change_ratio = str(change_ratio) + '%'
                if price >= last_price:
                    icon = ':rocket:'
                    change_ratio = '+' + str(change_ratio)
                elif price < last_price:
                    icon = ':small_red_triangle_down:'
                embed = discord.Embed(
                    title=f"{icon} {price} EUR ({change_ratio}) - {name} Price",
                    url=coin_url,
                    color=discord.Color.blue()
                )
                embed.add_field(name=f"**{name}**", value=f"{price} EUR")
                await channel.send(embed=embed)
            coin['last_price'] = price
            dict_data['coin'][currency] = coin
            save_pickle(dict_data, PICKLE_FILE_DATA)
        except:
            pass


@client.event
async def on_ready():
    for guild in client.guilds:
        print(f'{client.user} has connected to the following guild:')
        print(f'{guild.name}(id: {guild.id})')

    floor.start()
    coin.start()
    sniper.start()


while True:
    try:
        print('Bot started..')
        client.run(TOKEN)
    except:
        sleep(5)
        print('Bot restart..')
