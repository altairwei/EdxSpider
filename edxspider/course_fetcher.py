import http
import os
import sys
from typing import List, Dict
from urllib.parse import urlencode, urlparse
from copy import deepcopy

import click
import requests
from requests import Response


def get_request(url, cookie_file: str = None):
    if cookie_file:
        cookies = http.cookiejar.MozillaCookieJar(cookie_file)
        cookies.load()
    else:
        cookies = None
    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status()
    return resp


def fetch_course(course_id: str, cookie_file: str = None):
    # course_id such as MITx+18.6501x+2T2020
    url = "https://courses.edx.org/api/courseware/course/course-v1:" + course_id
    return get_request(url, cookie_file)


def fetch_course_blocks(course_id: str, username: str, cookie_file: str = None):
    url = "https://courses.edx.org/api/courses/v2/blocks/?"
    params = {
        "course_id": "course-v1:" + course_id,
        "username": username,
        "depth": 3,
        "requested_fields": "children,show_gated_sections,graded"
    }
    url += urlencode(params)
    return get_request(url, cookie_file)


def fetch_course_sequences(course_id, element_id, cookie_file: str = None):
    url = ("https://courses.edx.org/api/courseware/sequence/"
           "block-v1:{course_id}+type@sequential+block@{element_id}").format(
               course_id=course_id, element_id=element_id)
    return get_request(url, cookie_file)


def parse_url(url):
    u = urlparse(url)
    p = u.path.split("/")
    course_id = p[2].replace("course-v1:", "")
    index = 4 if p[3] == "jump_to" else 3
    element_id = p[index].split("@")[-1]
    return (course_id, element_id)


def fetch_html(url: str, cookie_file: str = None) -> str:
    resp = get_request(url, cookie_file)
    return resp.text


def handle_html_task(task: Dict, cookie_file: str = None) -> Dict:
    print("Fetching %s" % task["id"], file=sys.stderr)
    new_task = deepcopy(task)
    url = "https://courses.edx.org/xblock/%s?" % new_task["id"]
    params = {
        "show_title": 0,
        "show_bookmark_button": 0
    }
    url += urlencode(params)
    new_task["url"] = url
    new_task["html"] = fetch_html(url, cookie_file)
    return new_task