import json
import requests as req
import sys
from bs4 import BeautifulSoup


arguments = sys.argv[1:]

if len(arguments) == 0:
    titles = "Torino"
else:
    titles, *tail = sys.argv[1:]

session = req.Session()
url_api = "https://it.wikipedia.org/w/api.php"

# Versione 1
# params = {
#     "action": "query",
#     "prop": "revisions",
#     "titles": titles,
#     "rvprop": "content",
#     "rvslots": "main",
#     "formatversion": "2",
#     "format": "json"
# }
#
# response = session.get(url=url_api, params=params)
# data = response.json()

# jprint(data)


# Versione 2

params = {
    "action": "parse",
    "prop": "text",
    "page": titles,
    "formatversion": "2",
    "format": "json"
}

"""
params = {
    "action": "query",
    "prop": "extracts",
    "titles": titles,
    "formatversion": "2",
    "format": "json"
}
"""


response = session.get(url=url_api, params=params)
data = response.json()
# jprint(data)

#content = data['query']['pages'][0]['revisions'][0]['slots']['main']['content']

with open(f'response/wikiPageContent/{titles}.json', 'w', encoding='utf-8') as f:
    json.dump(data, f) 

# estrarre il testo dalla pagina

content = data['parse']['text']#[0]['extract']
soup = BeautifulSoup(content, features="lxml")    

cleaned_content = soup.get_text().replace('\n', ' ')

#print(cleaned_content)

print("BODY: ", soup.find_all('p'))

with open(f'response/wikiPageContent/{titles}_soup.txt', 'w', encoding='utf-8') as f:
    f.write(cleaned_content)

# tentativo per avere le coordinate geografiche di una pagina wiki

params_coord = {
    "action": "query",
    "prop": "coordinates",
    "titles": titles,
    "formatversion": "2",
    "format": "json"
}

response_coord = session.get(url=url_api, params=params_coord)

data_coord = response_coord.json()

print(data_coord)

page = data_coord['query']['pages'][0]

print(page)

#key = list(page.keys())[0]

coord = page['coordinates']

print(coord)

lat = coord[0]['lat']
lon = coord[0]['lon']
loc = (lat, lon)

#session = req.Session()
#url = "https://it.wikipedia.org/wiki/Speciale:NelleVicinanze#/coord/45.0733841,7.6212119"

#r = req.get(url=url)



#data = response.json()

#content = data['query']['pages'][0]['revisions'][0]['slots']['main']['content']

#soup = BeautifulSoup(r.content, 'html.parser')
#print("CONTENT:", soup)
