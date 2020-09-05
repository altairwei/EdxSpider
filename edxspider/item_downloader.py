import requests
import json
import os
import re
import http
from typing import List

import click
import pywebcopy
from collections import deque
from pathvalidate import sanitize_filename
from urllib.parse import urlparse
from requests.exceptions import Timeout, ConnectionError


def download_course(task_list: list, output_folder: str = None,
    includes: str = None, excludes: str = None, cookie_file: str = None):

    task_deque = deque(task_list)

    if cookie_file:
        cookies = http.cookiejar.MozillaCookieJar(cookie_file)
        cookies.load()
    else:
        cookies = None

    # Filter tasks
    '''
    if includes:
        includes = parse_selections(includes)
        task_deque = deque(filter(lambda item: int(item["index"]) in includes, task_deque))
    if excludes:
        excludes = parse_selections(excludes)
        task_deque = deque(filter(lambda item: int(item["index"]) not in excludes, task_deque))
    '''

    # Download items of task
    while task_deque:
        task = task_deque.popleft()
        click.echo(click.style("Start to download page: %s" % task["page_title"], fg="yellow"))
        # Create forlder to place videos
        dest_folder_parts = list(
            map(lambda folder: sanitize_filename(folder.strip()), task["path"].split(">")))
        if not output_folder:
            output_folder = os.getcwd()
        dest_folder = os.path.join(output_folder, *dest_folder_parts)
        os.makedirs(dest_folder, exist_ok=True)

        try:
            # Download videos and transcripts.
            wait_for_download_videos(task.get("videos", []), dest_folder)
            # Save whole pages
            '''
            if task.get("url", None):
                download_webpage_from_url(task["url"], dest_folder, cookies)
            '''
            if task.get("html", None):
                index_file_name = os.path.join(dest_folder, "index.html")
                with open(index_file_name, "w", encoding="UTF-8") as f:
                    f.write(task["html"])

            click.echo(click.style(
                "Download %s successfully" % task["page_title"], fg="green"))
        except (Timeout, ConnectionError, FileIncomplete) as e:
            print(e)
            click.echo(click.style(
                "Failed to download %s" % task["page_title"], fg="red"))
            task_deque.append(task)


def wait_for_download_videos(videos: List, dest_folder: str):
    video_deque = deque(videos)
    while video_deque:
        try:
            video_obj = video_deque.popleft()
            video_folder = os.path.join(dest_folder,
                sanitize_filename(video_obj.get("video_title", "")))
            os.makedirs(video_folder, exist_ok=True)
            if video_obj.get("video_link", None):
                v_url = video_obj["video_link"]
                v_filename = os.path.basename(urlparse(v_url).path)
                download_file(v_url, os.path.join(video_folder, v_filename))
            if video_obj.get("video_link", None) and video_obj.get("transcript_link", None):
                for s_url in video_obj["transcript_link"]:
                    # Get filename from server
                    remote_filename = get_uri_filename(s_url)
                    s_ext = os.path.splitext(remote_filename)[1]
                    s_name = os.path.splitext(os.path.basename(video_obj["video_link"]))[0]
                    s_filename = "{name}{ext}".format(
                        name = s_name,
                        ext = s_ext if s_ext else ".srt"
                    )
                    download_file(s_url, os.path.join(video_folder, s_filename))
        except (Timeout, ConnectionError, FileIncomplete) as e:
            print(e)
            click.echo(click.style(
                "Failed to download video: %s" % video_obj["video_title"], fg="red"))
            video_deque.append(video_obj)        


def download_webpage_from_url(url, dest_folder, cookies):
    if cookies:
        pywebcopy.SESSION.cookies = cookies
    args = {
        'url': url,
        'project_folder': dest_folder
    }
    pywebcopy.config["LOAD_JAVASCRIPT"] = False
    pywebcopy.save_webpage(**args)


def sizeof_fmt(num, suffix='B'):
    '''by Fred Cirera'''
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def download_file(url, filename):
    #TODO: 仍然没有解决下载视频可能不完整的BUG
    click.echo("From %s" % url)
    with requests.get(
        url, allow_redirects=True, stream=True, timeout=10
    ) as resp:
        resp.raise_for_status()
        total_length = int(resp.headers.get('content-length'))
        with open(filename, 'wb') as fh:
            with click.progressbar(
                length=total_length,
                label="Downloading %s (%s):" % (
                    os.path.basename(filename), sizeof_fmt(total_length))
            ) as bar:
                for data in resp.iter_content(chunk_size=4096):
                    if data:
                        fh.write(data)
                        bar.update(len(data))
        #TODO: check size of downloaded items
        if os.path.getsize(filename) != total_length:
            raise FileIncomplete


def parse_selections(selection):
    parts = list(map(lambda r: r.split(":"), selection.split(",")))
    twos = [list(range(int(part[0]), int(part[1]))) 
        for part in filter(lambda p: len(p) == 2, parts)]
    ones = [[int(part[0])]
        for part in filter(lambda p: len(p) == 1, parts)]
    return list(set([parts for parts in ones + twos for parts in parts]))


def get_uri_filename(url):
    with requests.get(url, allow_redirects=True, stream=True) as resp:
        cd_val = resp.headers.get('Content-Disposition', '')
        if cd_val:
            return re.findall("filename=\"(.+)\"", cd_val)[0]

class FileIncomplete(Exception):
    pass