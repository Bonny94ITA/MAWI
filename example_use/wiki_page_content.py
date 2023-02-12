import json
import requests as req
import sys
from bs4 import BeautifulSoup
import time
import string 

arguments = sys.argv[1:]

if len(arguments) == 0:
    titles = "Museo diffuso della Resistenza, della deportazione, della guerra, dei diritti e della libertà"
else:
    titles, *tail = sys.argv[1:]

session = req.Session()
url_api = "https://it.wikipedia.org/w/api.php"

# Versione 1
#params = {
#    "action": "query",
#    "prop": "revisions",
#    "titles": titles,
#    "rvprop": "content",
#    "rvslots": "main",
#    "formatversion": "2",
#    "format": "json"
# }

#response = session.get(url=url_api, params=params)
#data = response.json()


#content = data['query']['pages'][0]['revisions'][0]['slots']['main']['content']
#soup = BeautifulSoup(content, features="lxml")    

#print("body:", soup.body.text)
# jprint(data)

#content_body = soup.body.text

# Versione 2
#time.sleep(100)

#session = req.Session()

params = {
    "action": "parse",
    "page": titles,
    "formatversion": "2",
    "prop": "text",
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

references = soup.find_all('sup', class_='reference') 

for ref in references:
    ref.decompose() # tolto i riferimenti

no_fonte = soup.find_all('sup', class_='noprint chiarimento-apice') 

for ref in no_fonte:
    ref.decompose() # tolto i riferimenti

# togliere tutto ciò che è nelle figcaption
figcaptions = soup.find_all('figcaption')
for figcaption in figcaptions: 
    figcaption.decompose() # tolto le descrizioni sotto le immagini

figcaptions_div = soup.find_all('div', class_='thumbcaption')
for figcaption in figcaptions_div:
    figcaption.decompose() # tolto le descrizioni sotto le immagini nei div

headings = soup.find_all('h2', id=True)
for heading in headings:
    heading.decompose() # tolto le intestazioni

note = soup.find('span', id='Note')

# prima vado al titolo padre 
parent_tag = note.parent
# elimino i fratelli 
for sibling in parent_tag.find_next_siblings():
    #print(sibling)
    sibling.decompose()

# svuoto tutti gli span

for span in soup.find_all('span', title=False):
    span.decompose()

for table in soup.find_all('table'):
    table.decompose()

bullets_to_delete = soup.find_all(['ul', 'ol'], class_=True) # da aggiungere 
for bullet in bullets_to_delete:
    bullet.decompose()

# add punct in bullets 
tag = soup.find_all(['ul', 'ol'], class_=False)

not_punct = ['"',"'", '(', ')','[',']', ' ']
for t in tag:
    sub_tag = t.find_all("li", class_=False) 
    if len(sub_tag) > 1:
        for s in sub_tag[:-1]: 
            if not s.text[-1] in string.punctuation or s.text[-1] in not_punct:
                s.append(" ;")

        if not sub_tag[-1].text[-1] in string.punctuation or sub_tag[-1].text[-1] in not_punct:
            sub_tag[-1].append(" .")


with open(f'response/wikiPageContent/{titles}_soup.txt', 'w', encoding='utf-8') as f:
    f.write(soup.prettify())

with open(f'response/wikiPageContent/{titles}_text.txt', 'w', encoding='utf-8') as f:
    f.write(soup.get_text(' ', strip=True))


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

params_vic = {
    "action": "query",
    "list": "geosearch",
    "gsradius": 3000,
    "gspage": titles, #"gscoord": str(lat) + "|" + str(lon),
    "gsprop": "type", # su cui poi posso filtrare landmark!!
    "formatversion": "2",
    "format": "json"
}

"""
DATA VICINANZA: {'batchcomplete': True, 'query': {'geosearch': [{'pageid': 3305528, 'ns': 0, 'title': 'Circondario di Torino', 'lat': 45.066667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm2nd'}, {'pageid': 9284, 'ns': 0, 'title': 'Provincia di Torino', 'lat': 45.066667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm2nd'}, {'pageid': 4921152, 'ns': 0, 'title': 'Città metropolitana di Torino', 'lat': 45.06666666666667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm2nd'}, {'pageid': 267198, 'ns': 0, 'title': 'Piemonte', 'lat': 45.06666666666667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm1st'}, {'pageid': 2588349, 'ns': 0, 'title': 'Torino', 'lat': 45.066667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm3rd'}, {'pageid': 1843770, 'ns': 0, 'title': 'Palazzo Birago di Borgaro', 'lat': 45.066637, 'lon': 7.697183, 'dist': 221.3, 'primary': True, 'type': 'landmark'}, {'pageid': 901246, 'ns': 0, 'title': 'Casa Scaccabarozzi', 'lat': 45.067826, 'lon': 7.696926, 'dist': 273.7, 'primary': True, 'type': 'landmark'}, {'pageid': 2886809, 'ns': 0, 'title': 'Chiesa di Santa Giulia (Torino)', 'lat': 
45.06964, 'lon': 7.69945, 'dist': 333.4, 'primary': True, 'type': 'landmark'}, {'pageid': 393797, 'ns': 0, 'title': 'Taverna del Santopalato', 'lat': 45.065767, 'lon': 7.695875, 'dist': 339.1, 'primary': True, 'type': 'landmark'}, {'pageid': 3313841, 'ns': 0, 'title': 'Ponte Vittorio Emanuele I', 'lat': 45.0635, 'lon': 7.6984, 'dist': 373.9, 'primary': True, 'type': 'landmark'}]}}


DATA VICINANZA: {'batchcomplete': True, 'query': {'geosearch': [{'pageid': 3305528, 'ns': 0, 'title': 'Circondario di Torino', 'lat': 45.066667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm2nd'}, {'pageid': 9284, 'ns': 0, 'title': 'Provincia di Torino', 'lat': 45.066667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm2nd'}, {'pageid': 4921152, 'ns': 0, 'title': 'Città metropolitana di Torino', 'lat': 45.06666666666667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm2nd'}, {'pageid': 267198, 'ns': 0, 'title': 'Piemonte', 'lat': 45.06666666666667, 'lon': 7.7, 'dist': 0, 'primary': True, 'type': 'adm1st'}, {'pageid': 1843770, 'ns': 0, 'title': 'Palazzo Birago di Borgaro', 'lat': 45.066637, 'lon': 7.697183, 'dist': 221.3, 'primary': True, 'type': 'landmark'}, {'pageid': 901246, 'ns': 0, 'title': 'Casa Scaccabarozzi', 'lat': 45.067826, 'lon': 7.696926, 'dist': 273.7, 'primary': True, 'type': 'landmark'}, {'pageid': 2886809, 'ns': 0, 'title': 'Chiesa di Santa Giulia (Torino)', 'lat': 45.06964, 'lon': 7.69945, 'dist': 333.4, 'primary': True, 'type': 'landmark'}, {'pageid': 393797, 'ns': 0, 'title': 'Taverna 
del Santopalato', 'lat': 45.065767, 'lon': 7.695875, 'dist': 339.1, 'primary': True, 'type': 'landmark'}, {'pageid': 3313841, 'ns': 0, 'title': 'Ponte Vittorio Emanuele I', 'lat': 45.0635, 'lon': 7.6984, 'dist': 373.9, 'primary': True, 'type': 'landmark'}, {'pageid': 1324880, 'ns': 0, 'title': 'Piazza Vittorio Veneto (Torino)', 'lat': 45.064806, 'lon': 7.695417, 'dist': 415.2, 'primary': True, 'type': 'landmark'}]}}
"""

response_vic= session.get(url=url_api, params=params_vic)

data_vic = response_vic.json()

landmarks = [loc for loc in data_vic['query']['geosearch'] if loc['type'] == 'landmark']

print("DATA VICINANZA:", data_vic)

print("LANDMARKS: ", landmarks)
