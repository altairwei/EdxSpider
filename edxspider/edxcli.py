import click
import json
import http.cookiejar
import requests
import sys
import os
from edxspider.page_parser import parse_page
from edxspider.item_downloader import download_items
from requests import Response

@click.group()
def edxcli():
    pass


def fetch_html(url: str, cookie_file: str = None) -> Response:
    if cookie_file:
        cookies = http.cookiejar.MozillaCookieJar(cookie_file)
        cookies.load()
    else:
        cookies = None
    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status()
    return resp


@click.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.option('-C', '--output_folder', type=click.Path(exists=True))
@click.option('-t', '--tasks-file', type=click.File("w", encoding="utf-8"))
@click.option('--includes',
    help="String like '2:3,5:8,10:12' , intervals will be parsed by `range()`.")
@click.option('--excludes', help="Same as '--include' option.")
@click.argument('url')
def save(url, output_folder, cookie_file, tasks_file, includes, excludes):
    resp = fetch_html(url, cookie_file)
    #TODO: Lec_6 和 Lec_7 导出的 JSON 文件不完整
    tasks = parse_page(resp.text, tasks_file)
    download_items(tasks, output_folder, includes, excludes)

@click.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.option('--html-file', type=click.File("w", encoding="utf-8"))
@click.argument('url')
def fetch(url, html_file, cookie_file):
    resp = fetch_html(url, cookie_file)
    if html_file:
        html_file.write(resp.text)
    else:
        # Write byte to stdout instead of string
        os.write(1, resp.content)


@click.command()
@click.option('-t', '--tasks-file', type=click.File("w", encoding="utf-8"))
@click.argument('html_file', type=click.File("r", encoding="utf-8"))
def parse(html_file, tasks_file):
    if not tasks_file:
        tasks_file = sys.stdout
    parse_page(html_file.read(), tasks_file)


@click.command()
@click.option('--includes',
    help="String like '2:3,5:8,10:12' , intervals will be parsed by `range()`.")
@click.option('--excludes', help="Same as '--include' option.")
@click.option('-C', '--output_folder', type=click.Path(exists=True))
@click.argument('item_list_file', type=click.File("r"))
def download(item_list_file, output_folder, includes, excludes):
    download_items(json.load(item_list_file), output_folder, includes, excludes)


#TODO: add `wrap` command to wrap non-video page with a html template.
#   Content of page will be inserted into `<body>` element.

edxcli.add_command(save)
edxcli.add_command(fetch)
edxcli.add_command(parse)
edxcli.add_command(download)


if __name__ == '__main__':
    edxcli()