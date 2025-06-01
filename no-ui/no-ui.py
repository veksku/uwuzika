import os
import discord #type: ignore
from discord.ext import commands #type: ignore
from dotenv import load_dotenv #type: ignore
import yt_dlp #type: ignore
from collections import deque
import asyncio
import validators #type: ignore
import random
import math
from pytube import Playlist
from pytube import YouTube
from json import loads

class PaginationView(discord.ui.View):
    current_page = 1
    songs_per_page = 10
    
    async def send(self, ctx, start = 0, end = songs_per_page):
        self.message = await ctx.reply(view=self, mention_author=False)
        await self.update_message(self.data, start, end)
    
    async def update_message(self, data, start, end):
        self.update_buttons()
        data_scoop = []
        for i in range(start, end):
            if i == len(data):
                break
            data_scoop.append(data[i])
        await self.message.edit(embed=self.create_embed(data_scoop, start), view=self)
    
    def create_embed(self, data, start):
        embed = discord.Embed(title="Koje pjesme idu?")
        embed.add_field(name="Trenutna", value="", inline=False)
        embed.add_field(name="", value=current_song, inline=False)
        embed.add_field(name="", value="", inline=False)
        embed.add_field(name="DALJE IDE DALJE IDE", value="", inline=False)
        for item in data:
            start += 1
            embed.add_field(name="", value=f"{str(start)}. {item[1]}", inline=False)
        return embed

    def update_buttons(self):
        if self.current_page == 1:
            self.first_page_button.disabled = True
            self.prev_button.disabled = True
            self.first_page_button.style = discord.ButtonStyle.gray
            self.prev_button.style = discord.ButtonStyle.gray
        else:
            self.first_page_button.disabled = False
            self.prev_button.disabled = False
            self.first_page_button.style = discord.ButtonStyle.green
            self.prev_button.style = discord.ButtonStyle.primary
        
        if self.current_page == math.ceil(len(self.data) / self.songs_per_page):
            self.last_page_button.disabled = True
            self.next_button.disabled = True
            self.last_page_button.style = discord.ButtonStyle.gray
            self.next_button.style = discord.ButtonStyle.gray
        else:
            self.last_page_button.disabled = False
            self.next_button.disabled = False
            self.last_page_button.style = discord.ButtonStyle.green
            self.next_button.style = discord.ButtonStyle.primary

    @discord.ui.button(label="|<", style=discord.ButtonStyle.gray)
    async def first_page_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = 1
        until_item = self.current_page * self.songs_per_page
        from_item = until_item - self.songs_per_page
        await self.update_message(self.data, 0, until_item)
    
    @discord.ui.button(label="<", style=discord.ButtonStyle.gray)
    async def prev_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page -= 1
        until_item = self.current_page * self.songs_per_page
        from_item = until_item - self.songs_per_page
        await self.update_message(self.data, from_item, until_item)

    @discord.ui.button(label=">", style=discord.ButtonStyle.gray)
    async def next_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page += 1
        until_item = self.current_page * self.songs_per_page
        from_item = until_item - self.songs_per_page
        await self.update_message(self.data, from_item, until_item)

    @discord.ui.button(label=">|", style=discord.ButtonStyle.gray)
    async def last_page_button(self, interaction:discord.Interaction, button: discord.ui.Button):
        await interaction.response.defer()
        self.current_page = math.ceil(len(self.data) / self.songs_per_page)
        until_item = self.current_page * self.songs_per_page
        from_item = until_item - self.songs_per_page
        await self.update_message(self.data, from_item, until_item)

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        return ydl.extract_info(query, download=False)
    
def get_urls_from_playlist(playlist):
    urls = []
    playlist_urls = Playlist(playlist)

    for url in playlist_urls:
        urls.append(url)

    return urls

# im a hackerman, and youtube links are stupid
def hack_url_from_playlist(playlist):
    playlist_txt = 'playlist?list='
    offset = len(playlist_txt)
    i = playlist.find(playlist_txt)
    link = playlist[i+offset:]
                            #ts works lol \/
    retval = playlist[:i] + "watch?v=a&list=" + link
    print(retval)

    return retval

def check_url(url: str):
    video = YouTube(url)
    ret_val = get_description_and_name(video)
    if (ret_val[0] == "Auto-generated by YouTube."):
        name = ret_val[1]
        return name
    else:
        return url

def get_description_and_name(video: YouTube):
    i: int = video.watch_html.find('"shortDescription":"')
    desc: str = '"'
    i += 20  # excluding the `"shortDescription":"`
    while True:
        letter = video.watch_html[i]
        desc += letter  # letter can be added in any case
        i += 1
        if letter == '\\':
            desc += video.watch_html[i]
            i += 1
        elif letter == '"':
            break
    text = loads(desc)

    return [text.splitlines()[-1], text.splitlines()[2]] #3rd row is "author · song"

current_song = None

def run_bot():
    load_dotenv()
    TOKEN = os.getenv('DISCORD_TOKEN')

    # GUILD_ID = 947999713641250857 #moj kanal
    GUILD_ID = 163016060545531905 #LOW
    SONG_QUEUES = {}

    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    prefix = '!'

    ydl_options = {
        "format": "bestaudio[abr<=96]/bestaudio",
        "noplaylist": True,
        "youtube_include_dash_manifest": False,
        "youtube_include_hls_manifest": False,
    }

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k",
    }

    prefix = "!"
    
    voice_channel = None

    @bot.event
    async def on_ready():
        test_guild = discord.Object(id=GUILD_ID)
        await bot.tree.sync(guild=test_guild)

        print(f'{bot.user} muziku pusta.')

    @bot.event
    async def on_message(msg):
        
        # de je onaj sto pise poruku
        voice_client = msg.guild.voice_client

        #ignorisi sve sto nema prefix
        if not msg.content.startswith(prefix):
            return
        else:
            # provera da l je osopa u voicu gde je bot
            try:
                voice_channel = msg.author.voice.channel
                if voice_client is not None:
                    if voice_client.channel != voice_channel:
                        await msg.reply("Vec sam ruku drugom kanalu obecala.", mention_author=False)
                        return
            except:
                await msg.reply("Pa udji u neki kanal keso!", mention_author=False)
                return

        guild_id = str(GUILD_ID) #hardkodovano, mora se proveri posle

        # RIP acim, id = 207929494009413632
        if msg.author.id == 207929494009413632:
            if random.uniform(0, 1) < 0.05:
                await msg.reply(random_poruka_acimu(), mention_author=False)

        if ("nigga" in msg.content):
            if random.uniform(0, 1) < 0.2:
                await msg.reply("https://tenor.com/view/lamar-franklin-lamar-roasts-franklin-gif-20079680", mention_author=False)

        if (msg.content.split()[0].lower() == prefix + "pause" or
            msg.content.split()[0].lower() == prefix + "stop"):
            # Check if the bot is in a voice channel
            if voice_client is None:
                return await msg.reply("Pa nisam u voicu keso.", mention_author=False)

            # Check if something is actually playing
            if not voice_client.is_playing():
                return await msg.reply("Nista ne ide brt.", mention_author=False)
            
            # Pause the track
            voice_client.pause()
            await msg.reply("STALO SVE!", mention_author=False)

        if (msg.content.split()[0].lower() == prefix + "play" or
            msg.content.split()[0].lower() == prefix + "p"):
        
            if voice_channel is None:
                await msg.reply("What the sigma?", mention_author=False)
                return
            
            if len(msg.content.split()) == 1:
                await msg.reply("Dje pesma?", mention_author=False)
                return

            if voice_client is None:
                voice_client = await voice_channel.connect()
            # elif voice_channel != voice_client.channel:
            #     await msg.reply("Kidnapovali me na drugom voice kanalu! :(", mention_author=False)

            try:
                text = msg.content.split()[1]
                queries = []
                is_url = False
                ytsearch1 = "ytsearch1:"
                #if its url
                if validators.url(text) == True:
                    is_url = True
                    if "playlist?list=" in text:
                        fixed_playlist_url = hack_url_from_playlist(text)
                        urls = get_urls_from_playlist(fixed_playlist_url)
                        for url in urls:
                            queries.append(url)
                    elif "&list=" in text:
                        urls = get_urls_from_playlist(text)
                        for url in urls:
                            queries.append(url)
                    else:
                        queries.append(text)
                #if its words
                else:
                    song_query = ''
                    i = 0
                    for words in msg.content.split():
                        if i == 0:
                            pass
                        else:
                            song_query += words
                            song_query += ' '
                        i += 1
                    queries.append(song_query)
                
                for query in queries:
                    # mrzimo &pp=
                    if(is_url):
                        print("Query pre: " + query)
                        if "&pp=" in query:
                            i = query.find("&")
                            query = query[:i]
                        query = check_url(query)
                        print("Query posle: " + query)
                    search_term = ytsearch1 + query
                    results = await search_ytdlp_async(search_term, ydl_options)
                    tracks = results.get("entries", [])
                    
                    # this check is prob not needed anymore
                    if len(tracks) == 0:
                        await msg.reply("MENI NECE, probaj da nije link.", mention_author=False)
                        return

                    first_track = tracks[0]
                    audio_url = first_track["url"]
                    title = first_track.get("title", "Bezimena")

                    if SONG_QUEUES.get(guild_id) is None:
                        SONG_QUEUES[guild_id] = deque()

                    SONG_QUEUES[guild_id].append((audio_url, title))

                    if voice_client.is_playing() or voice_client.is_paused():
                        await msg.reply(f"Dodadoh: **{title}**", mention_author=False)
                    else:
                        await play_next_song(voice_client, guild_id, msg.channel)
            except Exception as e:
                print("exception trigerovan: " + str(e))
                if not (str(e) == "Not connected to voice."):
                    await msg.reply("Nesto oslo u kurac, vrv veljko kriv.", mention_author=False)
                return

        if (msg.content.split()[0].lower() == prefix + "np" or
            msg.content.split()[0].lower() == prefix + "nowplaying"):
            global current_song
            embed = discord.Embed(title="Treenutnaaa :revolving_hearts:")
            if current_song is None:
                embed.add_field(name="", value="Ne ide nista brt")
                return await msg.reply(embed=embed, mention_author=False)
            if voice_client and voice_client.is_playing():
                embed.add_field(name="", value=current_song)
                return await msg.reply(embed=embed, mention_author=False)
            elif voice_client and voice_client.is_paused():
                embed.add_field(name="", value=f"Treba dide **{current_song}** al ju je neko stanlokovao.")
                return await msg.reply(embed=embed, mention_author=False)
            elif not voice_client:
                await msg.reply("Nisam u voicu keso.")

        if msg.content.split()[0].lower() == prefix + "skip":
            if voice_client and (voice_client.is_playing() or voice_client.is_paused()):
                # namerno reply pa skip jer je bilo nepredvidivo koja poruka ide prva
                await msg.reply("Preskocih pesmicu.", mention_author=False)
                voice_client.stop()
            else:
                await msg.reply("E moj dijete, nema pesme za preskocit.", mention_author=False)

        if (msg.content.split()[0].lower() == prefix + "resume" or
            msg.content.split()[0].lower() == prefix + "continue"):
            # Check if the bot is in a voice channel
            if voice_client is None:
                return await msg.reply("Pa nisam u voicu keso.", mention_author=False)

            if not voice_client.is_paused():
                return await msg.reply("Pa nisam pauziran brt.", mention_author=False)
            
            voice_client.resume()
            await msg.reply("IDE GAS!", mention_author=False)

        if msg.content.split()[0].lower() == prefix + "leave":
            if not voice_client or not voice_client.is_connected():
                return await msg.reply("Pa nisam u voicu keso.", mention_author=False)
            
            # Clear the guild's queue
            if guild_id in SONG_QUEUES:
                SONG_QUEUES[guild_id].clear()

            # If something is playing or paused, stop it
            if voice_client.is_playing() or voice_client.is_paused():
                voice_client.stop()

            # (Optional) Disconnect from the channel
            await msg.reply(random_poruka_izlaska(), mention_author=False)
            await voice_client.disconnect()
        
        
        if (msg.content.split()[0].lower() == prefix + "queue" or 
            msg.content.split()[0].lower() == prefix + "q"):
            
            if current_song == None:
                embed = discord.Embed(title="Koje pjesme idu?")
                embed.add_field(name="Nema pjesme", value="")
                return await msg.reply(embed=embed, mention_author=False)

            if len(SONG_QUEUES[guild_id]) == 0:
                embed = discord.Embed(title="Koje pjesme idu?")
                embed.add_field(name="Trenutna", value=current_song, inline=False)
                embed.add_field(name="Ostatak kjua je prazan, anlaki", value="", inline=False)
                return await msg.reply(embed=embed, mention_author=False)

            data = SONG_QUEUES[guild_id]
            pagination = PaginationView()
            pagination.data = data
            await pagination.send(msg)

    async def play_next_song(voice_client, guild_id, channel):
        global current_song
        if SONG_QUEUES[guild_id]:
            current_song = SONG_QUEUES[guild_id][0][1]
            audio_url, title = SONG_QUEUES[guild_id].popleft()

            source = discord.FFmpegOpusAudio(audio_url, **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

            def after_play(error):
                if error:
                    print(f"Pogreska kasam prob'o da pustim {title}: {error}")
                asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

            voice_client.play(source, after=after_play)
            asyncio.create_task(channel.send(f"Bengujem slusajuci: **{title}**"))
        else:
            # await voice_client.disconnect()
            current_song = None
            SONG_QUEUES[guild_id] = deque()    

    bot.run(TOKEN)

def random_poruka_acimu():
    opcije = [
        "DE SI POSO ACIME?? AHAHHA",
        """No problem! Here's the information about the Mercedes CLR GTR:

The Mercedes CLR GTR is a remarkable racing car celebrated for its outstanding performance and sleek design. Powder by a potent 6.0-liter V12 engine, it delivers over 600 horsepower.🔧

Acceleration from 0 to 100km/h takes approximately 3.7 seconds, with a remarkable top speed surpassing 320km/h. 🥇

Incorporation advanced aerodynamic features and cutting-edge stability technologies, the ClR GTR ensures exceptional stability and control, particularly during high-speed maneuvers. 💨

Originally priced around $1.5 million, the Mercedes CLR GTR is considered one of the most exclusive and prestigious racing cars ever produced. 💰

It's limited production run of just five units adds to its rarity, making it highly sought after by racing enthusiasts and collectors worldwide. 🌎""",
        "Dje normalna muzika??",
        "AHHHAHAHAHAHAHAHAHAHA",
        "Radije bih Somija koji repuje.",
        "Ko mac kopa, pa reci hop.",
        "Ti si BAS ONO sto ljudi ne vole kod sina jedinaca!",
        "Jedna pesma = jedno penkalo.",
        "Uf nesto me boli pazuh..",
        "Ja MNOGO volim da pustam muziku. Muziku, a ne TO.",
        "Idu dva mrava i odose.."
    ]
    return random.choice(opcije)

def random_poruka_izlaska():
    opcije = [
        "Uzeli ste mi 10 poena, dovidjenja!",
        "Mozda ste me usmrtili, ali ja cu se vratiti jaci no ikad!",
        "UmOrAahn sAhm, ujUutrRu raAdim..",
        "Odlazim, otiso sam, nema me.",
        "Cao cao je l otiso cao",
        "Znate li kako drzati naivnu osobu u neizvesnosti?"
    ]
    return random.choice(opcije)

if __name__ == "__main__":
    run_bot()