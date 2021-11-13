import requests
from bs4 import BeautifulSoup


def get_soup(url):
    res = requests.get(url)
    if res.status_code != 200 or 'client has been blocked' in res.text:
        res = requests.get(url, headers={"User-Agent": "Mozilla/5.0"})
        if res.status_code != 200:
            return 'RequestsError'
    soup = BeautifulSoup(res.text, "html.parser")
    return soup
