import json
import requests as req
import sys

arguments = sys.argv[1:]

if len(arguments) == 0:
    searchpage = "Torino"
else:
    searchpage, *tail = sys.argv[1:]

session = req.Session()
url_api = "https://en.wikipedia.org/w/api.php"

params = {
    "action": "query",
    "srlimit": "max",
    "format": "json",
    "list": "search",
    "srsearch": "piazza carlo alberto",
}

response = session.get(url=url_api, params=params)
data = response.json()

if data['query']['search'][0]['title'] == searchpage:
    print("Your search page '" + searchpage + "' exists on English Wikipedia")

with open(f'response/wikiSearch/{searchpage}.json', 'w') as f:
    json.dump(data, f, indent=4)
    print("The result has been saved as a file inside the response folder")

# jprint(data)

# for elem in data['query']['search']:
#     print(elem['snippet'] + '\n')
