import http.cookiejar
import requests


def fetch_page(url, output = None, cookie_file = None):
    if cookie_file:
        cookies = http.cookiejar.MozillaCookieJar(cookie_file)
        cookies.load()
    else:
        cookies = None
    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status()
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(resp.text)
    else:
        return resp.text