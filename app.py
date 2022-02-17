from ast import excepthandler
from distutils import command
import nextcord
from nextcord import FFmpegPCMAudio, PCMVolumeTransformer
from nextcord.ext import commands
import logging
from youtube_dl import YoutubeDL
from tenor_boombox import Tenor_Boombox
import colorama
from colorama import Fore, Style
from firebase_boombox import Firebase_Boombox
from keep_alive import keep_alive
from lyrics_extractor import SongLyrics
import asyncio
import requests
import urllib
import os
import sys
import re
import json
import random
from pprint import pprint

# SET DEFAULT BOT SETTINGS
BOT_NAME="boombox_v3"   # used for DB, do not absolutely change or you will lose access to prefixes previously changed by servers using this bot
DESCRIPTION = "A Test Bot utilizing Nextcord.py"
NOT_IDEAL_COMMAND_PREFIX = ('@', '#')
COMMAND_PREFIX = "!"    # Default command prefix

# SET LOGGING
logger = logging.getLogger('nextcord')
logger.setLevel(logging.DEBUG)
handler = logging.FileHandler(filename=f'{BOT_NAME}.log', encoding='utf-8', mode='w')    # dump logs to boombox_v3.log
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)
handler = logging.StreamHandler(sys.stdout)   # display logs in the console as well
handler.setFormatter(logging.Formatter('%(asctime)s:%(levelname)s:%(name)s: %(message)s'))
logger.addHandler(handler)

# SET FFMPEG OPTIONS
FFMPEG_OPTIONS = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5','options': '-vn'}

# INITIALIZE TENOR CLASS OBJECT
search_tenor = Tenor_Boombox()

# SET NEXTCORD STUFF
intents = nextcord.Intents.default()
intents.members = True
bot = commands.Bot(command_prefix=COMMAND_PREFIX, description=DESCRIPTION, intents=intents)

# INITIALIZE FIREBASE DB!
data = {}
fb_db = Firebase_Boombox(logger, colorama, BOT_NAME)


def check_db():
    global data
    fb_db_status = fb_db.check_db()
    logger.info(f"{Fore.YELLOW}Do we have db for {BOT_NAME}? : {str(fb_db_status)}")
    
    if fb_db_status == False:
        logger.info(f"{Fore.GREEN}Creating DB...")
        fb_db.create_db()
        
    data = fb_db.check_db()

    if data:
        logger.info(f"{Fore.GREEN}DB is initialized!{Style.RESET_ALL}")
    else:
        logger.error(f"{Fore.RED}DB cannot be initialized, please debug{Style.RESET_ALL}")
        quit()


def sync_db(guild_id):
    logger.info(data)
    for guild in data:
        guild_data = data[guild_id]

        allowed_setting_in_firebase_db = ['command_prefix', 'guild_name']
        illegal_settings_in_data = []
        for setting in guild_data:
            if setting not in allowed_setting_in_firebase_db:
                illegal_settings_in_data.append(setting)

    data_to_be_sync = data
    for illegal_setting in illegal_settings_in_data:
        data_to_be_sync[guild_id].pop(illegal_setting)

    fb_db.sync_database(data_to_be_sync)


def ld():
    with open('data.json', 'r') as openfile:
        data = json.load(openfile)



def sd():
    with open("data.json", "w") as outfile:
        json.dump(data, outfile)


def is_yt_link(text):
    if re.match(pattern='http(?:s?):\/\/(?:www\.)?youtu(?:be\.com\/(?:watch\?v=|embed\/)|\.be\/)(?P<video_id>[\w\-\_]*)(&(amp;)?‌​[\w\?‌​=]*)?', string=text):
        return True
    else:
        return False


def get_song_lyrics(title):
    extract_lyrics = SongLyrics(os.environ['BOOMBOX_PROGRAMMABLE_SEARCH_ENGINE_KEY'], os.environ['BOOMBOX_PROGRAMMABLE_SEARCH_ENGINE_ID'])
    song_data = extract_lyrics.get_lyrics(title)
    return song_data


def song_lyrics_embed(title, lyrics):
    '''Creates an Discord Embed that shows the lyrics of the currently playing song.'''
    embed=nextcord.Embed(title=title, description=lyrics, color=0x05ff09)
    return embed


def playing_now_embed(title, webpage_url, thumbnail_url):
    '''Creates an Discord Embed that shows the currently playing song.'''
    embed=nextcord.Embed(title="Playing Now", color=0x05ff09)
    embed.set_thumbnail(url=thumbnail_url)
    embed.add_field(name=title, value=webpage_url, inline=False)
    return embed


def get_playing_now(guild_id):
    song = data[guild_id]['currently_playing']
    title = song['title']
    webpage_url = song['webpage_url']
    thumbnail_url = song['thumbnail_url']
    
    logger.info(title, webpage_url, thumbnail_url)
    return title, webpage_url, thumbnail_url


def added_to_queue_embed(title, webpage_url, thumbnail_url):
    '''Creates an Discord Embed that shows the song has been added to queue.'''
    embed=nextcord.Embed(title="Added to queue", color=0x05ff09)
    embed.set_thumbnail(url=thumbnail_url)
    embed.add_field(name=title, value=webpage_url, inline=False)
    return embed


def play_song(guild_id, bot_voice_client_obj):
    logger.info(bot_voice_client_obj)
    # logger.info(data[guild_id]['songs'])
    logger.info(f"{len(data[guild_id]['songs'])} song(s) left including current one")

    # logger.info(data[guild_id]['songs'])
    if len(data[guild_id]['songs']) > 0:
        channel = data[guild_id]['songs'][0]['channel']     # the channel where the user has requested the song

        song = data[guild_id]['songs']
        title = data[guild_id]['songs'][0]['title']                     # title of the video
        webpage_url = data[guild_id]['songs'][0]['webpage_url']         # normal youtube url
        source = data[guild_id]['songs'][0]['source']                   # playable by FFMPEG youtube url
        thumbnail_url = data[guild_id]['songs'][0]['thumbnail_url']     # thumbnail url

        bot.loop.create_task(channel.send(embed=playing_now_embed(title, webpage_url, thumbnail_url)))      # send the Now Playing embed to the channel of the user that requested it
        bot_voice_client_obj.play(FFmpegPCMAudio(source, **FFMPEG_OPTIONS), after=lambda e: play_song(guild_id, bot_voice_client_obj))  # stream the music!
        
        data[guild_id]['currently_playing'] = {
            'title': title,
            'webpage_url': webpage_url,
            'thumbnail_url': thumbnail_url
        }

        if len(data[guild_id]['songs']) != 0:
            data[guild_id]['songs'].pop(0)  # remove the song from the queue

    else:
        channel = data[guild_id]['last_channel_requested_music']
        bot.loop.create_task(channel.send(embed=nextcord.Embed(title="Queue", description="No more songs in the queue.")))
        

def verify_yt_link(link):
    logger.info(f"verifies if this link works:\n{link}")


    try:
        urllib.request.urlopen(link).getcode()
    except:
        logger.info("Link did not worked :/")
        return False
    else:
        logger.info("Link worked!")
        return True


def fetch_gif_from_tenor(search_query, limit):
    gif_data = search_tenor.fetch_gif_data(search_query, limit)
    return gif_data


async def change_activity(loop=True):
    taylor_swift_albums = [
    'Taylor Swift',
    'Speak Now',
    '1989',
    'reputation',
    'Lover',
    'Folklore',
    'Evermore',
    "Fearless (Taylor's Version)",
    "Red (Taylor's Version)",
    ]

    amount_of_servers = f'{format(len(bot.guilds))} servers'

    activities_choices = [
        nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{COMMAND_PREFIX}help"),
        nextcord.Activity(type=nextcord.ActivityType.listening, name=f"{random.choice(taylor_swift_albums)}"),
        nextcord.Streaming(platform="Youtube", name="Polaroid Love", url="https://www.youtube.com/watch?v=vRdZVDWs3BI"),
        nextcord.Streaming(platform="Youtube", name="Sa Susunod Na Habang Buhay", url="https://www.youtube.com/watch?v=yB2J6kXxJIY"),
        nextcord.Streaming(platform="Youtube", name="Maybe The Night", url="https://www.youtube.com/watch?v=hJhVURhdLEg"),
        nextcord.Streaming(platform="Youtube", name="Araw - Araw", url="https://www.youtube.com/watch?v=XVhEm62Uqog"),
        nextcord.Streaming(platform="Youtube", name="Earl: Maybe The Night", url="https://www.youtube.com/watch?v=ND0mP8ftmQE"),
        nextcord.Streaming(platform="Youtube", name="Leaves feat. Young K", url="https://www.youtube.com/watch?v=5oxxi0d7AQI"),
        nextcord.Activity(type=nextcord.ActivityType.listening, name=amount_of_servers)
    ]

    if loop:
        while True:
            await bot.change_presence(activity=random.choice(activities_choices))
            await asyncio.sleep(300)
    else:
        await bot.change_presence(activity=random.choice(activities_choices))


@bot.event
async def on_ready():
    Fore.GREEN
    logger.info(f"My name is {bot.user}")
    logger.info(f"and my ID is {bot.user.id}")
    logger.info(f"I'm logged in and ready!")
    Style.RESET_ALL

    bot.loop.create_task(change_activity(loop=True))


@bot.event
async def on_message(message):
    channel = message.channel
    guild_id = str(message.guild.id)
    guild_name = message.guild.name

    try:
        data[guild_id]
        logger.info("success loading data from data")
    except KeyError:
        logger.info("guild not existing yet, creating default settings...")
        data[guild_id] = {
            'guild_name': guild_name,
            'command_prefix': COMMAND_PREFIX,
            'songs': [],
            'last_channel_requested_music': ''
        }
        sync_db(guild_id)

    try:
        command_prefix = data[guild_id]['command_prefix']
    except KeyError:
        command_prefix = COMMAND_PREFIX
    # we set dollar sign as the default command prefix if the guild hasn't set their own in the bot.

    message.content = message.content.strip()

    if not message.author.bot:
        logger.info(message)
        logger.info(f"{message.author.name}#{message.author.discriminator}: {message.content}")
        

    if message.content.startswith(f"{command_prefix}Hi"):       # returns "Hi"
        await channel.send("Hello!")


    elif message.content.startswith(f"{command_prefix}Hello"):      # returns "Hello"
        await channel.send("Hi!")

        
    elif message.content == f"{command_prefix}help" or message.content == f"{command_prefix}h":
        commands_help = f'''
**__Boomboxv3 Guide:__**
`{command_prefix}h` or `{command_prefix}help` : sends this help message!


**Music Commands:**
`{command_prefix}join` : joins the bot to the voice channel
`{command_prefix}play <youtube link or search query>` : plays a youtube link or video name
`{command_prefix}pause` : pauses the current playing song
`{command_prefix}resume` : resumes the paused song
`{command_prefix}skip` or `{command_prefix}next` : skips to the next song
`{command_prefix}playing-now` : shows the currently playing song
`{command_prefix}queue` : displays the queued songs
`{command_prefix}move <Channel ID or Name>` : moves the bot to another voice channel, if parameter is empty it will move to the user's current voice channel
`{command_prefix}disconnect` or `{command_prefix}dc` : disconnects the bot from the voice channel

**Other Commands:**
`{command_prefix}prefix` : shows the currently set prefix
`{command_prefix}prefix-change` : changes the prefix
`{command_prefix}Hi` : says "Hello"
`{command_prefix}Hello` : says "Hi"
`{command_prefix}simon-says` or `{command_prefix}repeat after me` : says back what the user will say

**Debug Commands:**
`{command_prefix}guild-info` : returns the server id & name'''

        await channel.send(commands_help)


    elif message.content == f"{command_prefix}guild-info":     # returns the server id & name
        response = f"Guild / Server ID: {guild_id}\nName: {guild_name}"
        logger.info(response)
        await channel.send(response)


    elif message.content == f"{command_prefix}prefix":     # returns the current prefix
        response = command_prefix
        logger.info(response)
        await channel.send(f"`{response}`")


    elif message.content == f"{command_prefix}prefix-change":      # changes the current prefix


        def check_prefix(message):
            if len(message.content) > 1:
                return (True, "Exceeded character limit, must be only 1!")
            elif message.content in NOT_IDEAL_COMMAND_PREFIX:
                return (False, f"Prefix can't be `{message.content}`\nProhibited Discord character...")
            else:
                return (True, message.content)


        await channel.send("What should be the new prefix? Type below:")
        new_prefix = await bot.wait_for('message')

        result = check_prefix(new_prefix)
        if result[0] == False:
            await channel.send(result[1])
        else:
            data[guild_id]['command_prefix'] = result[1]
            sync_db(guild_id)
            
            await channel.send(f"`{result[1]}` has been set as command prefix for this server.")


    elif message.content == f"{command_prefix}repeat after me" or message.content == f"{command_prefix}simon-says":    # repeats the what the user has said
        def check_if_not_self(message):
            if message.author.bot:
                pass
            elif message.author:
                return message.content

        user_who_triggered = message.author

        await channel.send("Send your message and I will repeat it!")
        
        got_text = False
        while got_text == False:
            response = await bot.wait_for('message', check=check_if_not_self)
            if response.author == user_who_triggered:
                got_text = True
        
        await channel.send(response.content)


    elif message.content.startswith(f"{command_prefix}gif"):
        search_query = message.content[5:]
        logger.info(f"gif search query: {search_query}")
        limit = 20
        gif_data = fetch_gif_from_tenor(f"Cute "+search_query, limit)
        image_link = gif_data['results'][random.randint(0, limit-1)]['media'][0]['gif']['url']
        await channel.send(image_link)
        logger.info(f"{command_prefix}gif - triggered")


    elif message.content == f"{command_prefix}presence-change-random":
        await change_activity()


    elif message.content == f"{command_prefix}presence-change":
        def check_if_not_self(message):
            if not message.author.bot:
                return message.content

        user_who_triggered = message.author

        await channel.send("What should be the new activity of the bot?")
        
        got_text = False
        while got_text == False:
            response = await bot.wait_for('message', check=check_if_not_self)
            if response.author == user_who_triggered:
                got_text = True

        activity = nextcord.CustomActivity(name=response.content)
        await bot.change_presence(status=nextcord.Status.online, activity=activity)
        await channel.send(f"{BOT_NAME.title()} has been changed to {response.content}")


    elif message.content == f"{command_prefix}join":
        user_voice_state = message.author.voice
        logger.info(f"user_voice_state:\n{user_voice_state}")

        if not message.author.voice:    # the user is not connected to any voice channel
            await channel.send(f"You are not connected to a voice channel")
            return

        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
            # logger.info(bot_voice_client_obj)
            # logger.info(f"type of bot_voice_client_obj: {bot_voice_client_obj}")
        except KeyError:    # if it fails, that means the bot is not connected, so we will connect the bot
            data[guild_id]['voice_client_object'] = await user_voice_state.channel.connect()            # save the voice client object to guild's database
            bot_voice_client_obj = data[guild_id]['voice_client_object']                                # get hold of the guild's current voice client object
            await message.guild.change_voice_state(channel=user_voice_state.channel, self_deaf=True)    #mute the bot to reduce data usage
            logger.info(f"bot_voice_state: {bot_voice_client_obj}")
            await channel.send(f"Joined {user_voice_state.channel.mention}")
            return

        if message.author.voice.channel.id != bot_voice_client_obj.channel.id:   # if the user's voice channel and bot's doesn't match

            if bot_voice_client_obj.is_playing():   # do not move if there is something playing
                await channel.send(f"Bot is playing something in {bot_voice_client_obj.channel.mention}\nStop all the currently playing songs or move the bot.")
            else:   # move if nothing is playing
                await channel.send(f"Moving to {message.author.voice.channel.mention}")
                await bot_voice_client_obj.move_to(message.author.voice.channel)

        else:
            await channel.send(f"Bot is already connected!")


    elif message.content == f"{command_prefix}pause":
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if message.author.voice.channel.id == bot_voice_client_obj.channel.id:

            if bot_voice_client_obj.is_playing():
                bot_voice_client_obj.pause()
                await channel.send("Paused ⏸")
            elif bot_voice_client_obj.is_paused():
                await channel.send("Already paused ⏸")
            else:
                await channel.send("Nothing is playing")

        else:
            await channel.send(f"Join {bot_voice_client_obj.channel.mention} and then you can {message.content[1:]} the music")


    elif message.content == f"{command_prefix}stop":
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if message.author.voice.channel.id == bot_voice_client_obj.channel.id:

            if bot_voice_client_obj.is_playing() or bot_voice_client_obj.is_paused():
                bot_voice_client_obj.stop()
                bot_voice_client_obj.pause()
                await channel.send("Music stopped ⏹️")
                # TODO Remember to put code here to remove the currently playing music from the queue
            else:
                await channel.send("Nothing is playing")

        else:
            await channel.send(f"Join {bot_voice_client_obj.channel.mention} and then you can {message.content[1:]} the music")


    elif message.content == f"{command_prefix}next" or message.content == f"{command_prefix}skip":
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if message.author.voice.channel.id == bot_voice_client_obj.channel.id:
            
            if bot_voice_client_obj.is_playing() or bot_voice_client_obj.is_paused():
                bot_voice_client_obj.stop()
                await channel.send(f"Skipped ⏭️")
                # TODO Remember to put code here to remove the currently playing music from the queue
            else:
                await channel.send("Nothing is playing")
        
        else:
            await channel.send(f"Join {bot_voice_client_obj.channel.mention} and then you can {message.content[1:]} the music")


    elif message.content == f"{command_prefix}resume":
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return
        
        if message.author.voice.channel.id == bot_voice_client_obj.channel.id:

            if bot_voice_client_obj.is_paused():
                bot_voice_client_obj.resume()
                await channel.send("Resumed ▶️")
            elif bot_voice_client_obj.is_playing():
                await channel.send("Already playing")
            else:
                await channel.send("Nothing is playing")

        else:
            await channel.send(f"Join {bot_voice_client_obj.channel.mention} and then you can {message.content[1:]} the music")


    elif message.content == f"{command_prefix}disconnect" or message.content == f"{command_prefix}dc":  # disconnects the bot from the call
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if message.author.voice.channel.id == bot_voice_client_obj.channel.id:
            await channel.send(f"Disconnecting from {bot_voice_client_obj.channel.mention}")    #notify the user
            await bot_voice_client_obj.disconnect()     # disconnect from the voice channel
            del data[guild_id]['voice_client_object']   # delete the voice client object
        else:
            await channel.send(f"Join {bot_voice_client_obj.channel.mention} and then you can {message.content[1:]} {BOT_NAME.title()}")

    
    elif message.content == f"{command_prefix}playing-now":
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if bot_voice_client_obj.is_playing():
            song = get_playing_now(guild_id)
            await channel.send(embed=playing_now_embed(song[0], song[1], song[2])) 
        else:
            await channel.send("Nothing is playing")

    
    elif message.content.startswith(f"{command_prefix}move"):
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        voice_channel_id_or_name = message.content[5:].strip()

        if len(message.content) < 6:
            if message.author.voice:
                await bot_voice_client_obj.move_to(message.author.voice.channel)
                await channel.send(f"Moved to {message.author.voice.channel.mention}")
                await bot_voice_client_obj.guild.change_voice_state(self_deaf=True)
                
            else:
                await channel.send("You are connected to a voice channel.")
            return
        
        try:
            voice_channel_id_or_name = int(voice_channel_id_or_name)
        except ValueError:
            voice_channel_id_or_name = str(voice_channel_id_or_name)

        if type(voice_channel_id_or_name) == int:
            channel_obj = message.guild.get_channel(voice_channel_id_or_name)     #attempt to get the channel object
            if channel_obj == None:
                await channel.send("Invalid Channel ID")
                return
        elif type(voice_channel_id_or_name) == str:
            channel_obj = nextcord.utils.get(message.guild.voice_channels, name=voice_channel_id_or_name)       #attempt to get the channel object
            if channel_obj == None:
                await channel.send("Invalid Channel Name")
                return
        
        logger.info(channel_obj)
        logger.info(f"User {message.author.name} has told us to move to {channel_obj.name}")
        
        await bot_voice_client_obj.move_to(channel_obj)
        await channel.send(f"Moved to {channel_obj.mention}")
        await bot_voice_client_obj.guild.change_voice_state(self_deaf=True)


    elif message.content.startswith(f"{command_prefix}play"):   # plays the given youtube link or the query that the user has provided
        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if message.content == f'{command_prefix}play':
            if len(data[guild_id]['songs']) == 0:
                await channel.send("Queue is empty")
            elif bot_voice_client_obj.is_playing():
                await channel.send("Already playing")
            else:
                await channel.send("Nothing is playing")
        # ?play
        elif len(message.content) > 5:
            possible_yt_link = message.content[5:].strip()
            logger.info(possible_yt_link)

            with YoutubeDL({'format': 'bestaudio', 'noplaylist':'True', 'logger': logger}) as ydl:
                    try: requests.get(possible_yt_link)
                    except: info = ydl.extract_info(f"ytsearch:{possible_yt_link}", download=False)['entries'][0]
                    else: info = ydl.extract_info(possible_yt_link, download=False)

            video, source = (info, info['formats'][0]['url'])
            # plogger.info(info)

            if not verify_yt_link(source):
                await channel.send("I apologize, this song cannot be added to queue.\nPlease try again another link or keyword...")
                return

            try:
                data[guild_id]['songs']     # check if the songs list is initialized
            except KeyError:
                data[guild_id]['songs'] = []    # make the list if it doesn't exist

            data[guild_id]['songs'].append({
                'title': info['title'],
                'webpage_url': info['webpage_url'],
                'source': info['formats'][0]['url'],
                'thumbnail_url': info['thumbnails'][0]['url'],
                'channel': message.channel,
            },)

            data[guild_id]['last_channel_requested_music'] = message.channel

            if not bot_voice_client_obj.is_playing():
                play_song(guild_id, bot_voice_client_obj)
            else:
                await channel.send(embed=added_to_queue_embed(info['title'], info['webpage_url'], info['thumbnails'][0]['url']))


    elif message.content.startswith(f"{command_prefix}queue"):
        songs_queued = len(data[guild_id]['songs'])
        logger.info(songs_queued)
        

        if len(data[guild_id]['songs']) == 0:
            embed=nextcord.Embed(title="Queue", description="Empty")
            await channel.send(embed=embed)

        if len(data[guild_id]['songs']) > 0:
            if len(data[guild_id]['songs']) == 1:
                queue_description = "1 song left"
            else:
                queue_description = f"{len(data[guild_id]['songs'])} songs left"
                
            embed=nextcord.Embed(title="Queue", description=queue_description)

            count = 1
            for song in data[guild_id]['songs'][:3]:
                embed.add_field(name=f"{count} - {song['title']}", value=song['webpage_url'], inline=False)

                count += 1

            if songs_queued > 4:    # display more songs in queue if the songs amount is more than 4
                embed.add_field(name="Upcoming:", value=f"{songs_queued - 3} more songs in queue", inline=False)
            elif songs_queued - 3 == 1:     # display 1 more song left if the songs are greater than 3 (4..5..6..etc...) or equal to 3
                embed.add_field(name="Upcoming:", value="1 more song in queue", inline=False)

            await channel.send(embed=embed)

    elif message.content.startswith(f"{command_prefix}lyrics"):
        if len(message.content) > 7:
            song_name = message.content[7:].strip()
            song_data = get_song_lyrics(song_name)
            await channel.send(embed=song_lyrics_embed(title=song_data['title'], lyrics=song_data['lyrics']))
            return

        try:
            bot_voice_client_obj = data[guild_id]['voice_client_object']    # try to get hold of the guild's current voice client object.
        except KeyError:
            await channel.send(f"Bot is not connected...")  # if it fails, that means the bot is not connected.
            return

        if bot_voice_client_obj.is_playing():
            title, webpage_url, thumbnail_url = get_playing_now(guild_id)
            song_data = get_song_lyrics(title)
            await channel.send(embed=song_lyrics_embed(title, song_data['lyrics']))
        else:
            await channel.send("Nothing is playing")
            

check_db()
keep_alive()
bot.run(os.environ['BOOMBOX_V3_TOKEN'])


