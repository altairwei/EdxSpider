import json
import sys
import os
import http

import click
import requests
from requests import Response

from edxspider.page_parser import (parse_page, grab_video_subtitle)
from edxspider.item_downloader import download_course
from edxspider.course_fetcher import (
    fetch_course, fetch_course_blocks,
    fetch_html, fetch_course_sequences,
    parse_url, handle_html_task)


@click.group()
def edxcli():
    pass


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
    html_text = fetch_html(url, cookie_file)
    #TODO: Lec_6 和 Lec_7 导出的 JSON 文件不完整
    tasks = parse_page(html_text, tasks_file)
    download_course(tasks, output_folder, includes, excludes)


@click.group(invoke_without_command=True)
@click.pass_context
def fetch(ctx):
    pass


@fetch.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.option('-ci', '--course-id', help="Course id.")
@click.option('-ei', '--element-id', help="Lecture id.")
@click.option('-u', '--url', help="Url of lecture page.")
def task(course_id, element_id, url, cookie_file):
    if course_id and element_id:
        pass
    elif url:
        course_id, element_id = parse_url(url)
    else:
        raise Exception("Unknown course_id and element_id.")
    resp = fetch_course_sequences(course_id, element_id, cookie_file)
    resp_json = resp.json()
    tasks = resp_json["items"]
    proc_tasks = list(map(
        lambda task: handle_html_task(task, cookie_file), tasks))
    os.write(1, json.dumps(proc_tasks, indent=2).encode("UTF-8"))


@fetch.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.argument('course_id')
def info(course_id, cookie_file):
    resp = fetch_course(course_id, cookie_file)
    os.write(1, resp.content)


@fetch.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.argument('course_id')
@click.argument('username')
def blocks(course_id, username, cookie_file):
    resp = fetch_course_blocks(course_id, username, cookie_file)
    os.write(1, resp.content)


@fetch.command()
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.argument('course_id')
@click.argument('element_id')
def seqs(course_id, element_id, cookie_file):
    resp = fetch_course_sequences(course_id, element_id, cookie_file)
    os.write(1, resp.content)


@click.group()
def parse():
    pass


@parse.command("task")
@click.option("--html/--no-html", default=True)
@click.argument('tasks_file', type=click.File("rb"))
def parse_task(tasks_file, html):
    tasks = json.load(tasks_file)
    proc_tasks = list(map(grab_video_subtitle, tasks))
    if not html:
        for task in proc_tasks:
            del task['html']
    os.write(1, json.dumps(proc_tasks, indent=2).encode("UTF-8"))


@click.command()
@click.option('--includes',
    help="String like '2:3,5:8,10:12' , intervals will be parsed by `range()`.")
@click.option('--excludes', help="Same as '--include' option.")
@click.option('-C', '--output_folder', type=click.Path(exists=True))
@click.option('-c', '--cookie-file', type=click.Path(exists=True),
    help="A filename that stores cookies.")
@click.argument('item_list_file', type=click.File("rb"))
def download(item_list_file, output_folder, includes, excludes, cookie_file):
    download_course(json.load(item_list_file), output_folder, includes, excludes, cookie_file)


#TODO: add `wrap` command to wrap non-video page with a html template.
#   Content of page will be inserted into `<body>` element.

edxcli.add_command(save)
edxcli.add_command(fetch)
edxcli.add_command(parse)
edxcli.add_command(download)


if __name__ == '__main__':
    edxcli()