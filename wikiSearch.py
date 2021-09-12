import json
import requests as req
import sys

arguments = sys.argv[1:]

if len(arguments) == 0:
    searchpage = "Turin"
else:
    searchpage, *tail = sys.argv[1:]


# indenta JSON
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=3)
    print(text)


session = req.Session()
url_api = "https://en.wikipedia.org/w/api.php"

params = {
    "action": "query",
    "format": "json",
    "list": "search",
    "srsearch": searchpage,
}

response = session.get(url=url_api, params=params)
data = response.json()

if data['query']['search'][0]['title'] == searchpage:
    print("Your search page '" + searchpage + "' exists on English Wikipedia")

with open(f'response/wikiSearch/{searchpage}.json', 'w') as f:
    json.dump(data, f)
    print("The result has been saved as a file inside the response folder")


# jprint(data)

# for elem in data['query']['search']:
#     print(elem['snippet'] + '\n')
