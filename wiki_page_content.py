import json
import requests as req
import sys

arguments = sys.argv[1:]

if len(arguments) == 0:
    titles = "Turin"
else:
    titles, *tail = sys.argv[1:]

session = req.Session()
url_api = "https://en.wikipedia.org/w/api.php"

# Versione 1
params = {
    "action": "query",
    "prop": "revisions",
    "titles": titles,
    "rvprop": "content",
    "rvslots": "main",
    "formatversion": "2",
    "format": "json"
}

response = session.get(url=url_api, params=params)
data = response.json()

# jprint(data)
content = data['query']['pages'][0]['revisions'][0]['slots']['main']['content']

with open(f'response/wikiPageContent/{titles}.json', 'w') as f:
    json.dump(data, f)

# Versione 2
# params = {
#     "action": "parse",
#     "prop": "text",
#     "page": titles,
#     "formatversion": "2",
#     "format": "json"
# }

# response = session.get(url=url_api, params=params)
# data = response.json()

# jprint(data)
