import requests
from bs4 import BeautifulSoup
import urllib

text = 'Borgo Medievale Torino'
text = urllib.parse.quote_plus(text)

URL = 'https://google.com/search?q=' + text

print(URL)

headers = {
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
}

s = requests.Session()
page = s.get(URL, headers=headers)
soup = BeautifulSoup(page.content, 'html5lib')
# print(soup)
address = soup.find(class_='LrzXr').get_text()
address = address.strip()
print(address)
