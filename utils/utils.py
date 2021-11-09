from bs4 import BeautifulSoup
import requests
import urllib
import json


# JSON indent
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=3)
    print(text)


def read_text_file(path):
    text = ""
    with open(path) as f:
        lines = f.readlines()

    for line in lines:
        text += line
    return text


def count_occurrences(nlp_text, input_json, param_to_search):
    counter = {}
    for ent in nlp_text.ents:
        for elem in input_json:
            occurrence = elem[param_to_search]
            if occurrence == ent.text:
                if occurrence not in counter:
                    counter[occurrence] = 1
                else:
                    counter[occurrence] += 1
    return counter


def get_entities(nlp_text, counter):
    searchable_entities = []
    for ent in nlp_text.ents:
        if ent.text not in counter:
            searchable_entities.append(ent.text)
    return list(dict.fromkeys(searchable_entities))


def search_with_google(searchable_entities, context):
    for search_item in searchable_entities:
        text = urllib.parse.quote_plus(search_item + " " + context)
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

        print('-' * 50)
        print(URL)
        if address:
            address = address.get_text()
            address = address.strip()
            print("Elemento di ricerca: ", search_item)
            print("Indirizzo: ", address)

        print('-' * 50)
