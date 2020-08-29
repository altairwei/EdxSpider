import html
import json
from copy import deepcopy
from typing import TextIO, List, Dict
from bs4 import BeautifulSoup, PageElement
from urllib.parse import urlparse, urlunparse

def parse_page(index_doc: str, item_list_file: TextIO = None) -> list:
    all_content = list(map(
        grab_video_subtitle, extract_inner_documents(index_doc)))
    # Write item list
    if item_list_file:
        json.dump(all_content, item_list_file)

    return all_content


def extract_inner_documents(index_html: str) -> List[Dict]:
    """This is the beginning of the whole parsing process."""
    all_tasks = []
    document = BeautifulSoup(index_html, 'lxml')
    seq_list_ol = document.find(id = "sequence-list")
    all_seq_content_li = seq_list_ol.find_all("li")
    for seq_content_li in all_seq_content_li:
        # Construct a 'content' object to gather information
        task = dict()
        data_index = seq_content_li.button["data-index"]
        data_path = seq_content_li.button["data-path"]
        task["title"] = data_path
        task["index"] = data_index
        # Parse inner html then find out video and transcript links
        seq_content = document.find(id = "seq_contents_%s" % data_index)
        task["inner_html"] = seq_content.get_text()
        all_tasks.append(task)
    return all_tasks

def grab_video_subtitle(task: Dict) -> Dict:
    # document.querySelectorAll(".xmodule_VideoBlock") 代表着一个模块。
    new_task = deepcopy(task)
    inner_html = new_task["inner_html"]
    inner_document = BeautifulSoup(inner_html, 'html.parser')
    # Extract videos
    video_blocks = inner_document.find_all(class_ = ".xmodule_VideoBlock")
    if video_blocks:
        new_task["videos"] = list(map(parse_video_block, video_blocks))
    # Extract exercise content
    if not video_blocks:
        inner_html_esc = html.unescape(inner_html)
        inner_document = BeautifulSoup(inner_html_esc, 'html.parser')
        problem_el = inner_document.find(class_ = "problem")
        if problem_el:
            new_task["html_text"] = str(problem_el.div)
    return new_task

def parse_video_block(video_block: PageElement) -> Dict:
    video_object = {}
    video_title_el = video_block.find("h3")
    video_object["video_title"] = str(video_title_el.string) if video_title_el else None
    video_link_el = video_block.find(class_ = "btn-link video-sources video-download-button")
    video_object["video_link"] = video_link_el["href"] if video_link_el else None
    transcript_link_el = video_block.select(".wrapper-download-transcripts a")
    video_object["transcript_link"] = set()
    for srt_link in transcript_link_el:
        srt_url = srt_link["href"]
        u = urlparse(srt_url)
        if not u.scheme:
            u = u._replace(scheme='https')
        if not u.netloc:
            u = u._replace(netloc='courses.edx.org')
        srt_url = urlunparse(u)
        video_object["transcript_link"].add(srt_url)
    video_object["transcript_link"] = list(video_object["transcript_link"])
    return video_object