import json
import requests as req


# indenta JSON
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=3)
    print(text)


session = req.Session()
url_api = "https://en.wikipedia.org/w/api.php"
titles = "Turin"

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

jprint(data)
content = data['query']['pages'][0]['revisions'][0]['slots']['main']['content']

# Versione 2
params = {
    "action": "parse",
    "prop": "text",
    "page": titles,
    "formatversion": "2",
    "format": "json"
}

response = session.get(url=url_api, params=params)
data = response.json()

# jprint(data)
