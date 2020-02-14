import requests
import json
import os
import click
from pathvalidate import sanitize_filename
from urllib.parse import urlparse

def download_items(item_list, output_folder, includes = None, excludes = None):
    items = item_list
    if includes:
        items = filter(lambda item: int(item["index"]) in includes, items)
    if excludes:
        items = filter(lambda item: int(item["index"]) not in excludes, items)
    for item in items:
        dest_folder_parts = list(
            map(lambda folder: sanitize_filename(folder.strip()), item["title"].split(">")))
        dest_folder = os.path.join(output_folder, *dest_folder_parts)
        os.makedirs(dest_folder, exist_ok=True)
        if item.get("video_link", None):
            v_url = item["video_link"]
            v_filename = os.path.basename(urlparse(v_url).path)
            download_file(v_url, os.path.join(dest_folder, v_filename))
        if item.get("video_link", None) and item.get("transcript_link", None):
            s_url = item["transcript_link"]
            s_filename = "%s.srt" % os.path.splitext(
                os.path.basename(item["video_link"]))[0]
            download_file(s_url, os.path.join(dest_folder, s_filename))
        if item.get("html_text", None):
            # Download exercises
            file_name = os.path.join(dest_folder, "index.html")
            with open(file_name, "w", encoding="utf-8") as fh:
                fh.write(item["html_text"])

def sizeof_fmt(num, suffix='B'):
    '''by Fred Cirera'''
    for unit in ['','Ki','Mi','Gi','Ti','Pi','Ei','Zi']:
        if abs(num) < 1024.0:
            return "%3.1f%s%s" % (num, unit, suffix)
        num /= 1024.0
    return "%.1f%s%s" % (num, 'Yi', suffix)

def download_file(url, filename):
    #TODO: raise error when lost connection
    click.echo("From %s" % url)
    with requests.get(url, allow_redirects=True, stream=True) as resp:
        resp.raise_for_status()
        with open(filename, 'wb') as fh:
            total_length = int(resp.headers.get('content-length'))
            with click.progressbar(
                length=total_length,
                label="Downloading %s (%s):" % (
                    os.path.basename(filename), sizeof_fmt(total_length))
            ) as bar:
                for data in resp.iter_content(chunk_size=4096):
                    if data:
                        fh.write(data)
                        bar.update(len(data))


