import os
import requests
import discord
import time
from time import sleep
from discord.ext import tasks
from dotenv import load_dotenv
from Functions.file_handler import load_pickle, save_pickle
from Functions.telegrambot import etherscan_api_key
from Crypto_Alert.mint_alert import getETHprice, getEtherScanData, getMintedAmount, getCurrentMintPrice

load_dotenv()
TOKEN   = os.getenv('DISCORD_TOKEN')
GUILD   = os.getenv('DISCORD_GUILD')
CHANNEL = os.getenv('DISCORD_CHANNEL')
PICKLE_FILE = '../Data/rebelz_discord_last_counter.pickle'

client = discord.Client()


def get_last_message():
    dict_last_messages = load_pickle(PICKLE_FILE)
    try:
        return dict_last_messages['counter']
    except:
        return 10000


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


@tasks.loop(seconds=1)
async def test():
    dict_data    = getEtherScanData()
    last_counter = get_last_message()
    mint_counter = getMintedAmount(dict_data)
    print(time.strftime('%X %x %Z'))
    print(last_counter, mint_counter)
    if mint_counter - last_counter > 0:
        amount_left = 10000 - mint_counter
        price = getCurrentMintPrice(dict_data)
        eur, usd, _ = getETHprice()
        eur_price = int(eur * price)
        usd_price = int(usd * price)
        gasinfo = get_gasfee()
        channel = client.get_channel(int(CHANNEL))
        embed = discord.Embed(
            title="Rebelz Mint ALERT",
            url="https://realdrewdata.medium.com/",
            description="New rebel just minted",
            color=discord.Color.blue())
        embed.set_author(name="v1et4nh", url="https://twitter.com/v1et_le",
                         icon_url="https://pbs.twimg.com/profile_images/1462827760175529991/Uy0ScCuC_400x400.jpg")
        embed.set_thumbnail(url="https://pbs.twimg.com/profile_images/1449467742961156100/xeYtwpLD_400x400.jpg")
        embed.add_field(name="**Rebelz amount minted**", value=str(mint_counter), inline=False)
        embed.add_field(name="**Rebelz left**", value=str(amount_left), inline=False)
        embed.add_field(name="**Current Mint Price**",
                        value=str(price) + ' ETH (' + str(eur_price) + ' € | ' + str(usd_price) + ' US$)', inline=False)
        embed.add_field(name="**Current Gas Fee**", value=gasinfo, inline=False)
        await channel.send(embed=embed)
        dict_counter = {'counter': mint_counter}
        save_pickle(dict_counter, PICKLE_FILE)


@client.event
async def on_ready():
    for guild in client.guilds:
        if guild.name == GUILD:
            break

    print(f'{client.user} has connected to the following guild:')
    print(f'{guild.name}(id: {guild.id})')
    test.start()


while True:
    try:
        print('Bot started..')
        client.run(TOKEN)
    except:
        sleep(5)
        print('Bot restart..')
