import requests
import json
import os
import re

import click
from collections import deque
from pathvalidate import sanitize_filename
from urllib.parse import urlparse
from requests.exceptions import Timeout, ConnectionError

def download_items(item_list: list, output_folder: str = None, includes: str = None, excludes: str = None):
    items = deque(item_list)

    # Filter tasks
    if includes:
        includes = parse_selections(includes)
        items = deque(filter(lambda item: int(item["index"]) in includes, items))
    if excludes:
        excludes = parse_selections(excludes)
        items = deque(filter(lambda item: int(item["index"]) not in excludes, items))

    # Download items of task
    while items:
        item = items.popleft()
        dest_folder_parts = list(
            map(lambda folder: sanitize_filename(folder.strip()), item["title"].split(">")))
        if not output_folder:
            output_folder = os.getcwd()
        dest_folder = os.path.join(output_folder, *dest_folder_parts)
        os.makedirs(dest_folder, exist_ok=True)
        try:
            if item.get("video_link", None):
                v_url = item["video_link"]
                v_filename = os.path.basename(urlparse(v_url).path)
                download_file(v_url, os.path.join(dest_folder, v_filename))
            if item.get("video_link", None) and item.get("transcript_link", None):
                for s_url in item["transcript_link"]:
                    # Get filename from server
                    remote_filename = get_uri_filename(s_url)
                    s_ext = os.path.splitext(remote_filename)[1]
                    s_name = os.path.splitext(os.path.basename(item["video_link"]))[0]
                    s_filename = "{name}{ext}".format(
                        name = s_name,
                        ext = s_ext if s_ext else ".srt"
                    )
                    download_file(s_url, os.path.join(dest_folder, s_filename))
            if item.get("html_text", None):
                # Download exercises
                file_name = os.path.join(dest_folder, "index.html")
                with open(file_name, "w", encoding="utf-8") as fh:
                    fh.write(item["html_text"])
            click.echo(click.style(
                "Download item[%s] successfully" % item["index"], fg="green"))
        except (Timeout, ConnectionError, FileIncomplete) as e:
            print(e)
            click.echo(click.style(
                "Failed to download item[%s]" % item["index"], fg="red"))
            items.append(item)

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