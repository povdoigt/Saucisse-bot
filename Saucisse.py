import os
from typing import Final
import discord
from dotenv import load_dotenv
from responses import get_response
from rythme_function import get_video, get_video_with_link, download_video, get_url_playlist
import asyncio
from tracks import Track

"""
déclaration des variables 
"""


queue = []
n = 0
vc = 0
voice_channel = ''
play_status = 'off'
pre = '!!'

async def reset():
    global queue,n,vc,voice_channel,play_status
    queue = []
    n = 0
    vc = 0
    voice_channel = ''
    play_status = 'off'


load_dotenv()
token = os.getenv('DISCORD_TOKEN')
code_path = os.getenv('CODE_PATH')
ffmpeg_path = os.getenv('FFMPEG_PATH')

# set up the bot
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)


# messages functionality
async def send_message(message, user_message):
    if not user_message:
        print('message was empty becaus intents were not enabled probably')
        return
    if is_private := (user_message[:3] == '///' or user_message == 'help'):
        if user_message[:3] == '///':
            user_message = user_message[3:]
    try:
        response = get_response(user_message)
        if response != '':
            await message.author.send(response) if is_private else await message.channel.send(response)

    except Exception as e:
        print(e)


async def skip(message):
    global n, queue, play_status, vc
    voice_channel = message.author.voice.channel
    await vc.disconnect()
    vc = await voice_channel.connect()
    await jouer_queue(vc)
    n = 0
    queue = []
    play_status = 'off'
    await vc.disconnect()


async def del_cur_song(message, index):
    global n, queue, play_status, vc
    voice_channel = message.author.voice.channel
    os.remove(queue[index-1].path)
    queue.pop(index-1)
    n -= 1
    await vc.disconnect()
    vc = await voice_channel.connect()
    await jouer_queue(vc)
    n = 0
    queue = []
    play_status = 'off'
    await vc.disconnect()


async def in_channel(message, command):
    global queue, n, vc, play_status
    if command == f"{pre}skip":
        await skip(message)
    elif queue != [] and play_status == 'off':
        play_status = 'on'
        voice_channel = message.author.voice.channel
        vc = await voice_channel.connect()
        await jouer_queue(vc)
        n = 0
        queue = []
        await vc.disconnect()
        play_status = 'off'
    elif command == f'{pre}n':
        await message.channel.send(n)
    elif command == f'{pre}quit':
        await quit_queue()
    elif command == f'{pre}clear':
        clear_queue()
    elif command == f'{pre}off':
        play_status = 'off'
    elif command == f'{pre}loop':
        play_status = 'loop'
        for i in range(n):
            download_video(queue[i].link)  # a verifier
    elif command == f'{pre}state':
        await message.channel.send(play_status)  
    elif command[:8] == f'{pre}remove':
        try:
            index = int(command[8:])
            name = str(queue[index-1].name)
            if index == n+1:
                await del_cur_song(message, index)
            elif index > n+1:
                os.remove(queue[index-1].path)
                queue.pop(index-1)
            if play_status == 'loop':
                if index < n+1:
                    os.remove(queue[index-1].path)
                    queue.pop(index-1)
                    n -= 1
            else:
                if index < n+1:
                    queue.pop(index-1)
                    n -= 1
            await message.channel.send(f'***{name}*** removed!!')
    
        except Exception as e:
            print(e)
    elif command[:7] == f'{pre}remtr':
        user = command [8:]
        m = n+1
        while m<len(queue):
            print('user track : ' + user)
            print('name: '+str(queue[m].name))
            print(str(queue[m].user) + ' : '+ user)
            if str(queue[m].user) == user:
                os.remove(queue[m].path)
                queue.pop(m)
            else:
                m+=1   


async def quit_queue():
    global n, queue, play_status
    await vc.disconnect()
    if play_status == 'loop':
        for i, j in enumerate(queue):
            os.remove(j.path)
    else:
        if n != len(queue):
            for i, j in enumerate(queue[n:]):  # a verifier
                os.remove(j.path)
    n = 0
    queue = []
    play_status = 'off'


def clear_queue():
    global queue, n
    queue = []
    n = 0


async def connect_to_a_channel(channel):
    global queue
    vc = await channel.connect()
    await jouer_queue(vc)
    queue = []
    n = 0
    await vc.disconnect()


async def ajouter_queue(ctx, user_message):
    try:
        voice_channel = ctx.author.voice.channel
        if voice_channel != None:
            if user_message[:6] == f'{pre}play':
                user_message = user_message[7:]
                for i, j in enumerate(user_message):
                    if j == ' ':
                        user_message = user_message[:i] + '+' + user_message[i+1:]
                path, link = get_video(user_message)
                queue.append(Track(path[37:-4], path, link,ctx.author))
                await ctx.channel.send(f' **{queue[-1].name}** ajouté a la queufe!!')
                voice_channel = ctx.author.voice.channel
                return voice_channel
            elif user_message[:6] == f'{pre}link':
                user_message = user_message[7:]
                path = get_video_with_link(user_message)
                queue.append(Track(path[37:-4], path, user_message,ctx.author))
                await ctx.channel.send(f' **{queue[-1].name}** ajouté a la queufe!!')
                voice_channel = ctx.author.voice.channel
                return voice_channel
            elif user_message[:6] == f'{pre}plst':
                link = user_message[7:]
                urls = get_url_playlist(link)
                for i,j in enumerate(urls):
                    path = get_video_with_link(j)
                    queue.append(Track(path[37:-4], path,j,ctx.author))
                    await ctx.channel.send(f' **{queue[-1].name}** ajouté a la queufe!!')
                voice_channel = ctx.author.voice.channel
                return voice_channel
        else:
            await ctx.channel.send('c\'est non')
            return False
    except Exception as e:
        await ctx.channel.send('c\'est non')
        return False
        
        
async def play_salom(message, user_message):
    global play_status
    if user_message[:7] == f'{pre}salom':
        if play_status == 'on':
            quit_queue()
        play_status = 'on'
        voice_channel = message.author.voice.channel
        vc = await voice_channel.connect()
        audio = get_video_with_link(
            'https://www.youtube.com/watch?v=4Fge4EPiKA0')
        vc.play(discord.FFmpegPCMAudio(
            executable='C:/Users/Malo/Desktop/ffmpeg-n7.0-latest-win64-lgpl-7.0/bin/ffmpeg.exe', source=audio))
        while vc.is_playing():
            await asyncio.sleep(1)
        os.remove(audio)
        await vc.disconnect()
        play_status = 'off'


async def jouer_queue(vc):
    global n
    if len(queue) <= n and play_status == 'on':
        return
    elif len(queue) <= n and play_status == 'loop':
        n = 0
    if len(queue) > n:
        vc.play(discord.FFmpegPCMAudio(
            executable='C:/Users/Malo/Desktop/ffmpeg-n7.0-latest-win64-lgpl-7.0/bin/ffmpeg.exe', source=queue[n].path))
    while vc.is_playing():
        await asyncio.sleep(1)
    if play_status != 'loop':
        if len(queue) > n:
            os.remove(queue[n].path)
    if play_status != 'off':
        n += 1
        await jouer_queue(vc)



async def print_queue(message, user_message):
    if user_message == f'{pre}queue':
        if queue == []:
            str = '# **Queue vide**'
        else:
            str = '# **queue : **\n'
            for i, j in enumerate(queue):
                if i == n:
                    str += f"""* ***{i+1} ---> {j.user} : {j.name}***\n"""
                else:
                    str += f"""* {i+1} ---> {j.user} : {j.name}\n"""
        await message.channel.send(str)

# reactiuon functionality


async def send_reacion(message, user_message):
    if 'saucisse' in user_message:
        await message.channel.send('<:saucisse:1184936192496648326>')

# step 3 handeling the startup for our bot


@client.event
async def on_ready():
    print(f'{client.user} has connected to Discord')

# step 4 handeling incoming messages


@client.event
async def on_message(message):
    global voice_channel
    if message.author == client.user:
        return
    username = str(message.author)
    user_message = message.content
    channel = str(message.channel)

    print(f'[{channel}] {username} : {user_message}')

    await send_message(message, user_message)
    await send_reacion(message, user_message)
    if channel != 'Direct Message with Unknown User':
        voice_channel = await ajouter_queue(message, user_message)
        if voice_channel != False:
            await in_channel(message, user_message)
            await print_queue(message, user_message)
            await play_salom(message, user_message)
    if user_message == f'{pre}reset':
        await reset()


# step 5 main entry point
def main():
    client.run(token)


if __name__ == '__main__':
    main()
