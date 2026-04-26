import urllib.request
import re
from pytubefix import YouTube
import os
from dotenv import load_dotenv


load_dotenv()
code_path = os.getenv('CODE_PATH')


def get_url(search_query):
    url = "https://www.youtube.com/results?search_query=" + search_query

    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')

    video_ids = re.findall(r'watch\?v=(\S{11})', html)

    video_urls = ["https://www.youtube.com/watch?v=" +
                  video_id for video_id in video_ids]

    return video_urls[0]

def get_url_all(url):
    response = urllib.request.urlopen(url)
    html = response.read().decode('utf-8')

    video_ids = re.findall(r'watch\?v=(\S{11})', html)

    video_urls = ["https://www.youtube.com/watch?v=" +
                  video_id for video_id in video_ids]

    return video_urls


def get_url_playlist(url):
    a_supp = []
    urls = get_url_all(url)
    for i,j in enumerate (urls):
        for k in range(i+1,len(urls)):
            if j == urls[k]:
                a_supp.append(k)
    list2 = set(a_supp)
    lsit3 = list(list2)
    lsit3.sort()
    lsit3.reverse()

    for i,j in enumerate(lsit3):
        urls.pop(j)

    return urls


def download_video(url):
    yt = YouTube(str(url))

    video = yt.streams.filter(only_audio=True).first()

    out_file = video.download(
        output_path='C:/saucisse')
    
    print(yt.title + " has been successfully downloaded.")
    obj = yt
    return out_file,obj


def get_video(search):
    url = get_url(search)
    title,obj = download_video(url)
    return title, url, obj


def get_video_with_link(link):
    print(link)
    title,obj = download_video(link)
    return title,obj

def transtime(T):
    a = T//3600
    T -= a*3600
    b = T//60
    T -= b*60
    if a>0:
        return f"{a}h {b}min {T}s"
    elif b>0:
        return f"{b}min {T}s"
    else:
        return f"{T}s"