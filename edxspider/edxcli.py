import click
from edxspider.page_fetcher import fetch_page
from edxspider.page_parser import parse_page
from edxspider.item_downloader import download_items

@click.group()
def edxcli():
    pass


@click.command()
@click.option('-c', '--cookie-file', help="A filename that stores cookies.")
@click.argument('url')
@click.argument('output')
def fetch(url, output, cookie_file):
    fetch_page(url, output, cookie_file)


@click.command()
@click.argument('index_file')
@click.argument('item_list_file')
def parse(index_file, item_list_file):
    parse_page(index_file, item_list_file)


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
@click.argument('item_list')
@click.argument('output_folder')
def download(item_list, output_folder, includes, excludes):
    if includes:
        includes = parse_selections(includes)
    if excludes:
        excludes = parse_selections(excludes)
    download_items(item_list, output_folder, includes, excludes)


edxcli.add_command(fetch)
edxcli.add_command(parse)
edxcli.add_command(download)


if __name__ == '__main__':
    edxcli()