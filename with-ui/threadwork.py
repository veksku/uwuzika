import os
import discord #type: ignore
from discord.ext import commands, tasks #type: ignore
from dotenv import load_dotenv #type: ignore
import yt_dlp #type: ignore
from collections import deque
import asyncio
import validators #type: ignore
import random
import math
import time
import customtkinter #type: ignore
import queue
import sys
from threading import Thread, current_thread
import re
import io

shutdown = False
TOKEN = None
bot = None

class PaginationView(discord.ui.View):
    current_page = 1
    songs_per_page = 10
    
    async def send(self, ctx, current_song, start = 0, end = songs_per_page):
        self.current_song = current_song
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
        embed.add_field(name="", value=self.current_song, inline=False)
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

class StdoutLogger:
    def debug(self, msg):
        if msg.startswith("[debug]"):
            pass
        else:
            sys.stdout.write(f"{msg}\n")
    def info(self, msg):
        sys.stdout.write(f"[info] {msg}\n")
    def warning(self, msg):
        sys.stdout.write(f"[warn] {msg}\n")
    def error(self, msg):
        if "The uploader has not made this video available in your country" in str(msg):
            sys.stdout.write(f"[error] region_locked\n")
        elif "copyright claim" in str(msg):
            sys.stdout.write(f"[error] copyright\n")
        elif "This video may be inappropriate for some users." in str(msg):
            sys.stdout.write(f"[error] age_restricted\n")
        elif "Video unavailable. This video is not available" in str(msg):
            sys.stdout.write(f"[error] video_unavailable\n")
        else:
            sys.stdout.write(f"[error] {msg}\n")

def has_imagine_dragons(str):
    input = str.lower()

    if 'imagine dragons' in input:
        if random.uniform(0, 1) > 0.1:
            return True
        else:
            return False
    else:
        return False

async def search_ytdlp_async(query, ydl_opts):
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: _extract(query, ydl_opts))

def _extract(query, ydl_opts):
    attempts = 5
    for attempt in range(attempts):
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            # with StdoutYoutubeDL(ydl_opts) as ydl:
                return ydl.extract_info(query, download=False)
        except (yt_dlp.utils.DownloadError, yt_dlp.utils.ExtractorError, ValueError) as e:
            # print(f"greska {e}")
            if "The uploader has not made this video available in your country" in str(e):
                print(f"Video {query} is not available in your country.")
                return 'region_locked'
            if "copyright claim" in str(e):
                print(f"Video {query} got yoinked.")
                return 'copyright'
            if "This video may be inappropriate for some users." in str(e):
                print(f"Video {query} got yoinked.")
                return 'age_restricted'
            if "Video unavailable. This video is not available" in str(e):
                print(f"Video {query} is not available.")
                return 'video_unavailable'
            if 'Requested format is not available.' in str(e):
                print(f"Format extraction failed, attempt {attempt+1}, trying again...")
                time.sleep(3)
            else:
                print(f"GRESKA: {e}")
                raise
    print(f"Failed to process {query} after {attempts+1} attempts, either update yt-dlp or cry")
    return

async def is_retval_fine(results, channel, song):
    if results == None:
        return 0
    elif results == 'region_locked':
        asyncio.create_task(channel.send(f"Hejtuju Srbiju pa <{song}> nmz se pusti"))
        return 0
    elif results == 'copyright':
        asyncio.create_task(channel.send(f"Kopirajtovali <{song}> lmao"))
        return 0
    elif results == 'age_restricted':
        asyncio.create_task(channel.send(f"Pa <{song}> je sussy, age restricted video baka"))
        return 0
    elif results == 'video_unavailable':
        asyncio.create_task(channel.send(f"Video <{song}> je nedostupan brt", mention_author=False))
        return 0
    else:
        return 1
        
def fix_playlist_url(url):

    list_txt = '&list='
    playlist_txt = 'playlist?list='
    watch_txt = 'watch?v='

    offset = len(list_txt)
    i = url.find(list_txt)
    code_len = 34 # in case it has index, bruh
    link = url[i+offset:i+offset+code_len] # only playlist's code

    j = url.find(watch_txt) # get the base yt link, remove video's code

    retval = url[:j] + playlist_txt + link # playable playlist link

    return retval

##################
current_song = {}
queries = {}
voice_channel = {}
voice_client = {}

def create_bot():
    global bot
    intents = discord.Intents.default()
    intents.message_content = True

    bot = commands.Bot(command_prefix="!", intents=intents)
    prefix = '!'

    ydl_options_get_data = {
        "quiet": True,
        'skip_download': True,
        'playlist_items': '1-300',
        'extract_flat': True
    }

    ydl_options = {
        "format": "bestaudio[ext=m4a]/bestaudio/best",
        "logger": StdoutLogger(),
        "progress_with_newline": True,
        "verbose": True,
        "noplaylist": True,
    }

    ffmpeg_options = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn -c:a libopus -b:a 96k",
    }

    prefix = "!"

    @bot.event
    async def on_ready():
        print(f'{bot.user} muziku pusta.')

    @bot.event
    async def on_message(msg):
        
        GUILD_ID = msg.guild.id
        guild_id = str(GUILD_ID)
        
        voice_client[guild_id] = msg.guild.voice_client

        if not msg.content.startswith(prefix):
            return
        else:
            # provera da l je osopa u voicu gde je bot
            try:
                voice_channel[guild_id] = msg.author.voice.channel
                if voice_client[guild_id] is not None:
                    if voice_client[guild_id].channel != voice_channel[guild_id]:
                        await msg.reply("Vec sam ruku drugom kanalu obecala.", mention_author=False)
                        return
            except:
                await msg.reply("Pa udji u neki kanal keso!", mention_author=False)
                return

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
            if voice_client[guild_id] is None:
                return await msg.reply("Pa nisam u voicu keso.", mention_author=False)

            # Check if something is actually playing
            if not voice_client[guild_id].is_playing():
                return await msg.reply("Nista ne ide brt.", mention_author=False)
            
            # Pause the track
            voice_client[guild_id].pause()
            await msg.reply("STALO SVE!", mention_author=False)

        if (msg.content.split()[0].lower() == prefix + "play" or
            msg.content.split()[0].lower() == prefix + "p"):
        
            if voice_channel[guild_id] is None:
                await msg.reply("What the sigma?", mention_author=False)
                return
            
            if len(msg.content.split()) == 1:
                await msg.reply("Dje pesma?", mention_author=False)
                return

            if voice_client[guild_id] is None:
                voice_client[guild_id] = await voice_channel[guild_id].connect()
            # elif voice_channel != voice_client.channel:
            #     await msg.reply("Kidnapovali me na drugom voice kanalu! :(", mention_author=False)

            try:
                text = msg.content.split()[1]

                if queries.get(guild_id) is None:
                    queries[guild_id] = []
                if current_song.get(guild_id) is None:
                    current_song[guild_id] = None

                #if its url
                if validators.url(text) == True:
                    if "list=" in text:
                        info = None
                        to_edit = None
                        if "&list=RD" in text:
                            to_edit = await msg.channel.send("Miksovi su spori i nepouzdani - vrv nece bit iste pesme", mention_author=False)
                            info = _extract(text, ydl_options_get_data)
                        elif "&list=" in text:
                            fixed_url = fix_playlist_url(text)
                            info = _extract(fixed_url, ydl_options_get_data)
                        elif "playlist?list=" in text:
                            info = _extract(text, ydl_options_get_data)
                        else:
                            await msg.reply("New playlist link?", mention_author=False)
                            return
                        videos = info.get('entries', [])
                        for video in videos:
                            url, name = (video.get('url'), video.get('title', 'Bezimena'))
                            queries[guild_id].append((url, name, 1))
                        if to_edit is None:
                            await msg.reply(f"Dodata plejlista **{info.get('title')}**", mention_author=False)
                        else:
                            await to_edit.edit(content=f"Dodao **{info.get('title')}**")
                    else:
                        video = await search_ytdlp_async(text, ydl_options)
                        check = await is_retval_fine(video, msg.channel, video.get('url'))
                        url, name = (video.get('url'), video.get('title', 'Bezimena'))
                        
                        if not check:
                            return
                        
                        if has_imagine_dragons(name):
                            await msg.reply("BLASPHEMY", mention_author=True)
                            return

                        queries[guild_id].append((url, name, 0))
                        await msg.reply(f"Dodat video **{video.get('title')}**", mention_author=False)
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

                    if has_imagine_dragons(song_query):
                        await msg.reply("BLASPHEMY", mention_author=True)
                        return

                    data = await search_ytdlp_async("ytsearch1: " + song_query, ydl_options)

                    if len(data) == 0:
                        await msg.reply("Search prazan nzm.", mention_author=False)
                        return
                    
                    tracks = data.get("entries", [])
                    video = tracks[0]
                    url, name = (video.get('url'), video.get('title', 'Bezimena'))
                    check = await is_retval_fine(video, msg.channel, url)

                    if not check:
                        return
                    
                    queries[guild_id].append((url, name, 0))
                    await msg.reply(f"Dodat video **{video.get('title')}**", mention_author=False)

                if not (voice_client[guild_id].is_playing() or voice_client[guild_id].is_paused()):
                    await play_next_song(voice_client[guild_id], guild_id, msg.channel)
            except Exception as e:
                if not (str(e) == "Not connected to voice."):
                    print("exception trigerovan: " + str(e))
                    await msg.reply("Nesto oslo u kurac, vrv veljko kriv.", mention_author=False)
                return
                
        if (msg.content.split()[0].lower() == prefix + "np" or
            msg.content.split()[0].lower() == prefix + "nowplaying"):
            
            embed = discord.Embed(title="Treenutnaaa :revolving_hearts:")
            if current_song[guild_id] is None:
                embed.add_field(name="", value="Ne ide nista brt")
                return await msg.reply(embed=embed, mention_author=False)
            if voice_client[guild_id] and voice_client[guild_id].is_playing():
                embed.add_field(name="", value=current_song[guild_id][1])
                return await msg.reply(embed=embed, mention_author=False)
            elif voice_client[guild_id] and voice_client[guild_id].is_paused():
                embed.add_field(name="", value=f"Treba dide **{current_song[guild_id][1]}** al ju je neko stanlokovao.")
                return await msg.reply(embed=embed, mention_author=False)
            elif not voice_client[guild_id]:
                await msg.reply("Nisam u voicu keso.")

        if msg.content.split()[0].lower() == prefix + "skip":
            if voice_client[guild_id] and (voice_client[guild_id].is_playing() or voice_client[guild_id].is_paused()):
                # namerno reply pa skip jer je bilo nepredvidivo koja poruka ide prva
                await msg.reply("Preskocih pesmicu.", mention_author=False)
                voice_client[guild_id].stop()
            else:
                await msg.reply("E moj dijete, nema pesme za preskocit.", mention_author=False)

        if (msg.content.split()[0].lower() == prefix + "resume" or
            msg.content.split()[0].lower() == prefix + "continue"):
            # Check if the bot is in a voice channel
            if voice_client[guild_id] is None:
                return await msg.reply("Pa nisam u voicu keso.", mention_author=False)

            if not voice_client[guild_id].is_paused():
                return await msg.reply("Pa nisam pauziran brt.", mention_author=False)
            
            voice_client[guild_id].resume()
            await msg.reply("IDE GAS!", mention_author=False)

        if msg.content.split()[0].lower() == prefix + "leave":
            if not voice_client[guild_id] or not voice_client[guild_id].is_connected():
                return await msg.reply("Pa nisam u voicu keso.", mention_author=False)
            
            # Clear the guild's queue
            if guild_id in queries:
                queries[guild_id].clear()

            # If something is playing or paused, stop it
            if voice_client[guild_id].is_playing() or voice_client[guild_id].is_paused():
                voice_client[guild_id].stop()

            # (Optional) Disconnect from the channel
            await msg.reply(random_poruka_izlaska(), mention_author=False)
            await voice_client[guild_id].disconnect()

        if (msg.content.split()[0].lower() == prefix + "shuffle"):
            if len(queries[guild_id]) < 2:
                return await msg.reply("Premali je za shuffle, mislim na queue naravno...", mention_author=False)

            try:
                random.shuffle(queries[guild_id])
                return await msg.reply("Izmeso sam ga", mention_author=False) 
            except:
                return await msg.reply("Nesto nece", mention_author=False) 

        if (msg.content.split()[0].lower() == prefix + "queue" or 
            msg.content.split()[0].lower() == prefix + "q"):

            if current_song[guild_id] == None:
                embed = discord.Embed(title="Koje pjesme idu?")
                embed.add_field(name="Nema pjesme", value="")
                return await msg.reply(embed=embed, mention_author=False)

            if len(queries[guild_id]) == 0:
                embed = discord.Embed(title="Koje pjesme idu?")
                embed.add_field(name="Trenutna", value=current_song[guild_id][1], inline=False)
                embed.add_field(name="Ostatak kjua je prazan, anlaki", value="", inline=False)
                return await msg.reply(embed=embed, mention_author=False)

            data = queries[guild_id]
            pagination = PaginationView()
            pagination.data = data
            await pagination.send(ctx=msg, current_song=current_song[guild_id][1])

    async def play_next_song(voice_client, guild_id, channel):
        if queries[guild_id]:
            flag = 1
            while flag:
                song_data = queries[guild_id].pop(0)

                if song_data[2]:
                    info = await search_ytdlp_async(song_data[0], ydl_options)
                    check = await is_retval_fine(info, channel, song_data[0])
                    if check:
                        flag = 0
                        current_song[guild_id] = (info.get('url'), info.get('title'), 0)
                else:
                    flag = 0
                    current_song[guild_id] = song_data

            song = current_song[guild_id]

            source = discord.FFmpegOpusAudio(song[0], **ffmpeg_options, executable="bin\\ffmpeg\\ffmpeg.exe")

            def after_play(error):
                if error:
                    print(f"Pogreska kasam prob'o da pustim **{song[1]}**: {error}")
                asyncio.run_coroutine_threadsafe(play_next_song(voice_client, guild_id, channel), bot.loop)

            voice_client.play(source, after=after_play)
            asyncio.create_task(channel.send(f"Bengujem slusajuci: **{song[1]}**"))

        else:
            # await voice_client.disconnect()
            current_song[guild_id] = None
            queries[guild_id] = []
##################

def run_bot():
    print("Inicijalizujem bota..")
    async def start():
        await bot.start(TOKEN)
    
    asyncio.run(start())

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

if sys.stdout is None:
    sys.stdout = io.StringIO()
if sys.stderr is None:
    sys.stderr = io.StringIO()

ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')

class Gui:
    def __init__(self, queue_list):
        
        sys.stderr.write = self.redirector
        sys.stdout.write = self.redirector

        self.queue_list = queue_list
        
        self.root = customtkinter.CTk()
        self.root.geometry("700x450")
        self.root.title("uwuzika")
        self.root.resizable(False, True)
        
        self.root.protocol('WM_DELETE_WINDOW', self.stop_bot_and_exit)

        self.start_button = customtkinter.CTkButton(self.root, text="Startuj bota", command=self.start_bot)
        self.start_button.pack(padx=20, pady=3)

        self.textbox = customtkinter.CTkTextbox(self.root)
        self.textbox.pack(padx=20, pady=3, fill='both', expand='y')

        self.textbox.configure(state='disabled')

        self.copy_button = customtkinter.CTkButton(self.root, text="Copy", command=self.copy_all,
                                                   width=50, height=20)
        self.copy_button.pack(padx=5, pady=3)

        self.root.after(100, self.read_queue)

    def redirector(self, str):
        self.textbox.configure(state='normal')
        self.textbox.insert(customtkinter.END, ansi_escape.sub('', str))
        self.textbox.see(customtkinter.END)
        self.textbox.configure(state='disabled')

    def copy_all(self):
        text = self.textbox.get("1.0", "end")
        self.root.clipboard_clear()
        self.root.clipboard_append(text)

    def start_bot(self):
        load_dotenv()
        global TOKEN
        TOKEN = os.getenv('DISCORD_TOKEN')
        create_bot()
        if TOKEN is None:
            print("Dje token?")
        else:
            t1 = Thread(target=run_bot, daemon=True)
            self.start_button.configure(state='disabled')
            t1.start()

    def stop_bot_and_exit(self):
        global bot
        if bot is None or bot.is_closed():
            self.root.destroy()
        else:
            future = asyncio.run_coroutine_threadsafe(bot.close(), bot.loop)
            future.add_done_callback(lambda f: self.root.destroy())
            
    def read_queue(self):
        pass

def start():
    queue_list = queue.Queue()
    gui = Gui(queue_list)
    gui.root.mainloop()

if __name__ == "__main__":
    start()