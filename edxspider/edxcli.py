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


@click.command()
@click.argument('item_list')
@click.argument('output_folder')
def download(item_list, output_folder):
    download_items(item_list, output_folder)


edxcli.add_command(fetch)
edxcli.add_command(parse)
edxcli.add_command(download)


if __name__ == '__main__':
    edxcli()