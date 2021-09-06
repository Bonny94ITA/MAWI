import json
import requests as req


# indenta JSON
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=3)
    print(text)


session = req.Session()
url_api = "https://en.wikipedia.org/w/api.php"
searchpage = "Turin"

params = {
    "action": "query",
    "format": "json",
    "list": "search",
    "srsearch": searchpage
}

response = session.get(url=url_api, params=params)
data = response.json()

if data['query']['search'][0]['title'] == searchpage:
    print("Your search page '" + searchpage + "' exists on English Wikipedia")

jprint(data)

for elem in data['query']['search']:
    print(elem['snippet'] + '\n')

