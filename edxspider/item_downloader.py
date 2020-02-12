import requests
import json
import os
import click
from pathvalidate import sanitize_filename
from urllib.parse import urlparse

def download_items(item_list, output_folder):
    items = []
    if type(item_list) is str:
        with open(item_list, "r", encoding="utf-8") as fh:
            items = json.load(fh)
    elif type(item_list) is list:
        items = item_list

    for item in items:
        dest_folder_parts = list(
            map(lambda folder: sanitize_filename(folder.strip()), item["title"].split(">")))
        dest_folder = os.path.join(output_folder, *dest_folder_parts)
        os.makedirs(dest_folder, exist_ok=True)
        if item.get("video_link", None):
            # Download video and transcript
            #TODO: Guss file suffix
            v_url = item["video_link"]
            s_url = item["transcript_link"]
            v_filename = os.path.basename(urlparse(v_url).path)
            s_filename = "%s.srt" % os.path.splitext(v_filename)[0]
            download_file(v_url, os.path.join(dest_folder, v_filename))
            download_file(s_url, os.path.join(dest_folder, s_filename))
        elif item.get("html_text", None):
            # Download exercises
            file_name = os.path.join(dest_folder, "index.html")
            with open(file_name, "w", encoding="utf-8") as fh:
                fh.write(item["html_text"])

def download_file(url, filename):
    resp = requests.get(url, allow_redirects=True, stream=True)
    resp.raise_for_status()
    with open(filename, 'wb') as fh:
        total_length = int(resp.headers.get('content-length'))
        with click.progressbar(
            length=total_length,
            label="Downloading %s:" % os.path.basename(filename)
        ) as bar:
            for data in resp.iter_content(chunk_size=4096):
                fh.write(data)
                bar.update(len(data))
        
        