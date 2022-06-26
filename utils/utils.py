from bs4 import BeautifulSoup
import requests
import urllib
import json
import os
import time
from geojson import Feature, Point, FeatureCollection
import geojson

lab_to_discard = ["PER"]
italian_region = ["Piemonte", "Valle d'Aosta", "Liguria", "Lombardia", "Veneto", "Friuli-Venezia-Giulia", \
    "Trentino-Alto Adige", "Emilia Romagna", "Toscana", "Abruzzo", "Umbria", "Puglia", "Molise", "Campania", \
        "Lazio", "Basilicata", "Calabria", "Sardegna", "Sicilia"]

# JSON indent
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=3)
    print(text)


def read_text_file(path: str):
    """Read a text file from a path.

    Args: 
        path: path to the file
    Returns:
        text: text read from the file in string format
    """
    
    with open(path, encoding='utf-8') as f:
        lines = f.readlines()
    
    text = " ".join(str(line) for line in lines)

    return text


def count_occurrences(nlp_text, input_json: list, param_to_search: str):
    """Count occurences of the param to search of the input json in the
    nlp_text.

    Args:
        nlp_text: spacy text
        input_json: json file with the entities to search
        param_to_search: parameter to search in the json file
    
    Returns:
        counter: dictionary with the entities (cities name) to search and their occurences
    """
    counter = {}
    for ent in nlp_text.ents:
        for elem in input_json: 
            occurrence = elem[param_to_search] 
            if occurrence == ent.text: 
                if occurrence not in counter:
                    counter[ent.text] = 1
                else:
                    counter[ent.text] += 1
    return counter

def get_entities_snippet(nlp_text, counter: dict):
    """Get the entities from the nlp_text which are not cities and print snippet in which
        they appears.

    Args:
        nlp_text: spacy text
        counter: dictionary with the entities (cities name) to search and their occurences
    """

    searchable_entities = {}
    sents = list(nlp_text.sents)
    sentence_dict = generate_sentences_dictionary(sents)
    for ent in nlp_text.ents: 
        if ent.text not in counter and ent.label_ not in lab_to_discard and ent.text not in italian_region and ent.text != "Italia": 
            appears_in = search_dict(sentence_dict, ent)
            """for (index, sentence) in appears_in:
                print("Text: ", ent.text, "\n",
                    "Sentence index: ", index, "\n",
                    "Sentence: ", sentence, "\n")"""
            searchable_entities[ent.text] = [sent for sent in appears_in] #ent associate to the list of sentences in which it appears

    return searchable_entities

def search_dict(dict: dict, ent):
    """Search in a dictionary dict the entity ent. 
    Args:
        dict: dictionary where to search
        ent: entity to search

    Returns:
        list of the sentence index and sentence in which the entity appears
    """
    appears = []
    for index, sentence in dict.items():
        if ent.text in sentence.text:
            if index > 0:
                bef = dict.get(index-1, "")
                if not isinstance(bef, str):
                    bef = bef.text
                after = dict.get(index+1, "")
                if not isinstance(after, str):
                    after = after.text    
                appears.append(bef + " " + sentence.text + " " + after)
    
    return appears

def generate_sentences_dictionary(sentence_list: dict):
    """Generate a dictionary with the snipet index and the snippet itself.
    
    Args:
        sentence_list: list of sentences
    Returns:
        sentence_dict: dictionary with the index of the sentence and the index in the text
    """
    sentences_dict = {}
    for index, sentence in enumerate(sentence_list): #Can be useful if we like to have more snippet
        sentences_dict[index] = sentence

    return sentences_dict

def print_to_file(file_path, text_to_append):
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(text_to_append + "\n")


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def search_entities(searchable_entities: dict, context: str):
    """ Search entities with API geocode.maps
    
    Args:
        searchable_entities: list of entities to search
        context: context of the search (city, country, etc.)
    """

    response_file_path = f"response/spacy_pipeline/{context}.txt"
    response_geojson_file_path = f"response/spacy_pipeline/{context}_geojson.geojson"

    delete_file(response_file_path)

    list_features = []

    for search_item in searchable_entities.keys():
        text = urllib.parse.quote_plus(search_item+ " " + context)
       
        URLGEOJSON = 'https://geocode.maps.co/search?q={'+text+'}&format=geojson'
        print(URLGEOJSON)
        
        s = requests.Session()
        
        response= s.get(URLGEOJSON)
        result = response.json()

        result = result['features']

        print_to_file(response_file_path, '-' * 50)

        if len(result) > 0:
            location = result[0]
            locationName = location['properties']['display_name'].strip()
            if locationName.endswith("Italia") and locationName.__contains__(context): 
                coordinates = location['geometry']['coordinates']

                loc_point = Point((coordinates[0], coordinates[1]))
                loc_feature = Feature(geometry=loc_point, properties={"entity": search_item, 
                                    "name_location": addressAPI, "snippet": searchable_entities[search_item]})

                list_features.append(loc_feature)    

                print("DISPLAY NAME: ", locationName)
                print("RESULT GEOJSON: ", location)
                print("OBJECT GEOJSON: ", loc_feature)

                print_to_file(response_file_path, f"Research term: {search_item}")
                
                print_to_file(response_file_path, URLGEOJSON)
                print_to_file(response_file_path, f"Address: {locationName}")
                print_to_file(response_file_path, f"Address GEOJSON: {location}")
                print_to_file(response_file_path, f"GEOGSON: {loc_feature}")
            else: 
                addressAPI = ""    
        else: 
            addressAPI = ""
      
        print_to_file(response_file_path, '-' * 50)

        time.sleep(.600)
    
    geojson_object = FeatureCollection(list_features)
    print(len(geojson_object["features"]))
    with open(response_geojson_file_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_object, f, ensure_ascii=False, indent=4)
        print("The result has been saved as a file inside the response folder")



def wiki_content(titles):
    """Search title page in wikipedia with MediaWiki API.

    Args: 
        titles: Wikipedia page title
    Returns:
        Wikipedia page content cleaned 
    """
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": titles,
        "formatversion": "2"
    }

    response = session.get(url=url_api, params=params)
    data = response.json()
    content = data['query']['pages'][0]['extract']
    soup = BeautifulSoup(content, features="lxml")

    #Delete all the parts that are not meaningful
    Htag = soup.body
    i = 0
    find = False
    while i < len(Htag.contents) and not find:
        find = str(Htag.contents[i]) == '<h2><span id="Note">Note</span></h2>' 
        i += 1
    
    del Htag.contents[i-1:]

    cleaned_content = soup.get_text().replace('\n', ' ')

    with open(f'response/wikiPageContent/{titles}.txt', 'w', encoding='utf-8') as f:
        f.write(cleaned_content)
    
    return cleaned_content
