import urllib
from bs4 import BeautifulSoup
import requests
import spacy
import json
from spacy.lang.it.examples import sentences
from spacy.pipeline.ner import DEFAULT_NER_MODEL
from spacy import displacy

nlp = spacy.load("it_core_news_sm")
# config = {
#     "moves": None,
#     "update_with_oracle_cut_size": 100,
#     "model": DEFAULT_NER_MODEL,
#     "incorrect_spans_key": "incorrect_spans",
# }
# nlp.add_pipe("ner", config=config)

print("Initial sentence: ", sentences[0])
doc = nlp(sentences[0])
print("Tagged sentence: ", doc.text)

text = ""
with open('./assets/definition.txt') as f:
    lines = f.readlines()

for line in lines:
    text += line

doc = nlp(text)
# doc = nlp("In zona San Donato, oltre alla vistosissima Casa Fenoglio, in via Piffetti vi sono due esempi databili 1908, opera di Giovanni Gribodo e poco distante vi sono altri esemplari di edifici liberty in via Durandi e via Cibrario e ancora in via Piffetti, al civico 35; mentre di Giovan Battista Benazzo sono Casa Tasca (1903), che ostenta decori floreali, motivi geometrici circolari e ricche decorazioni in ferro battuto per ringhiere e finestre.")

# for token in doc:
# print(token.text, token.pos_, token.dep_)

# Opening JSON file
f = open('./assets/italian_cities.json')


counter = {}
searchable_entities = []

italian_cities = json.load(f)
for ent in doc.ents:
    for city in italian_cities:
        city_name = city["name"]
        if city_name == ent.text:

            if city_name not in counter:
                counter[city_name] = 1
            else:
                counter[city_name] += 1

            # print(ent.text, ent.start_char, ent.end_char,
            #       ent.label_, spacy.explain(ent.label_))

    if ent.text not in counter:
        searchable_entities.append(ent.text)


print(counter)
print(searchable_entities)


for search_item in searchable_entities:
    # print(search_item)

    text = urllib.parse.quote_plus(search_item + " Torino")

    URL = 'https://google.it/search?q=' + text + "&hl=it"

    # print(URL)

    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7s) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Safari/605.1.15',
    }

    s = requests.Session()
    page = s.get(URL, headers=headers)
    soup = BeautifulSoup(page.content, 'html5lib')
    # print(soup)
    address = soup.find(class_='LrzXr')

    if address:
        address = address.get_text()
        address = address.strip()
        print(search_item)
        print(URL)
        print(address)

    print('-' * 50)
