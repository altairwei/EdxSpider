import http.cookiejar
import requests


def fetch_page(url, output = None, cookie_file = None):
    cookies = http.cookiejar.MozillaCookieJar(cookie_file)
    cookies.load()
    resp = requests.get(url, cookies=cookies)
    resp.raise_for_status()
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(resp.text)
    else:
        return resp.text