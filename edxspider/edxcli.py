import click
import json
import http.cookiejar
import requests
import sys
import os
from edxspider.page_parser import parse_page
from edxspider.item_downloader import download_items

@click.group()
def edxcli():
    pass


@click.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.option('--html-file', type=click.File("w", encoding="utf-8"))
@click.argument('url')
def fetch(url, html_file, cookie_file):
    if cookie_file:
        cookies = http.cookiejar.MozillaCookieJar(cookie_file)
        cookies.load()
    else:
        cookies = None
    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status()
    if html_file:
        html_file.write(resp.text)
    else:
        os.write(1, resp.content)


@click.command()
@click.option('-t', '--tasks-file', type=click.File("w", encoding="utf-8"))
@click.argument('html_file', type=click.File("r", encoding="utf-8"))
def parse(html_file, tasks_file):
    if not tasks_file:
        tasks_file = sys.stdout
    parse_page(html_file, tasks_file)


def parse_selections(selection):
    parts = list(map(lambda r: r.split(":"), selection.split(",")))
    twos = [list(range(int(part[0]), int(part[1]))) 
        for part in filter(lambda p: len(p) == 2, parts)]
    ones = [[int(part[0])]
        for part in filter(lambda p: len(p) == 1, parts)]
    return list(set([parts for parts in ones + twos for parts in parts]))


@click.command()
@click.option('--includes',
    help="String like '2:3,5:8,10:12' , intervals will be parsed by `range()`.")
@click.option('--excludes', help="Same as '--include' option.")
@click.option('-C', '--output_folder', type=click.Path(exists=True))
@click.argument('item_list_file', type=click.File("r"))
def download(item_list_file, output_folder, includes, excludes):
    if includes:
        includes = parse_selections(includes)
    if excludes:
        excludes = parse_selections(excludes)
    download_items(json.load(item_list_file), output_folder, includes, excludes)


edxcli.add_command(fetch)
edxcli.add_command(parse)
edxcli.add_command(download)


if __name__ == '__main__':
    edxcli()