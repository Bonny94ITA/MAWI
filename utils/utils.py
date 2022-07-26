from bs4 import BeautifulSoup
import requests
import urllib
import json
import os
import time
from geojson import Feature, Point, FeatureCollection
import csv 

lab_to_discard = ["PER", "ORG", "MISC"]
italian_region = ["Piemonte", "Valle d'Aosta", "Liguria", "Lombardia", "Veneto", "Friuli-Venezia-Giulia", \
    "Trentino-Alto Adige", "Emilia-Romagna", "Toscana", "Abruzzo", "Umbria", "Puglia", "Molise", "Campania", \
        "Lazio", "Basilicata", "Calabria", "Sardegna", "Sicilia"]

continents = ['Europa', 'Asia', 'Africa', 'America', 'Oceania', 'Antartica']
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
    entities = clean_entities(nlp_text)
    for ent in entities: 
        if ent not in counter: 
            appears_in = search_dict(sentence_dict, ent)
            """for (index, sentence) in appears_in:
                print("Text: ", ent.text, "\n",
                    "Sentence index: ", index, "\n",
                    "Sentence: ", sentence, "\n")"""
            searchable_entities[ent] = [sent for sent in appears_in] #ent associate to the list of sentences in which it appears

    return searchable_entities

def get_entities_snippet2(nlp_text, counter: dict):
    """Get the entities from the nlp_text which are not cities and print snippet in which
        they appears.

    Args:
        nlp_text: spacy text
        counter: dictionary with the entities (cities name) to search and their occurences
    """

    searchable_entities = {}
    sents = list(nlp_text.sents)
    sentence_dict = generate_sentences_dictionary(sents)
    for (index, sentence) in sentence_dict.items():
        entities = clean_entities(sentence)
        for ent in entities:
            if ent not in counter:
                before = sentence_dict.get(index-1, "")
                if not isinstance(before, str):
                    before = before.text
                after = sentence_dict.get(index+1, "")
                if not isinstance(after, str):
                    after = after.text
                
                sent = before + " " + sentence.text + " " + after
                if ent in searchable_entities and sent not in searchable_entities[ent]:
                    searchable_entities[ent].append(sent)
                else:     
                    searchable_entities[ent] = [sent]

    return searchable_entities


def clean_entities(nlp_text): 
    """Clean the entities from the nlp_text.

    Args:
        nlp_text: spacy text
    Returns:
        list_entities: list of the entities useful for the search
    """
    entities = []
    for ent in nlp_text.ents:
        if ent.label_ not in lab_to_discard and ent.text not in italian_region and ent.text != "Italia" and ent.text not in continents: 
            entities.append(ent.text)
    return entities


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
        if ent in sentence:
            if index > 0:
                bef = dict.get(index-1, "")
                after = dict.get(index+1, "") 
                appears.append(bef + " " + sentence + " " + after)
    
    return appears

def generate_sentences_dictionary(sentence_list: list):
    """Generate a dictionary with the snipet index and the snippet itself.
    
    Args:
        sentence_list: list of sentences
    Returns:
        sentence_dict: dictionary with the index of the sentence and the index in the text
    """
    sentences_dict = {}
    for index, sentence in enumerate(sentence_list): 
        sentences_dict[index] = sentence

    return sentences_dict

def print_to_file(file_path: str, text_to_append):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(text_to_append + "\n")

def print_to_csv(file_path: str, object_to_append):
    properties = object_to_append['properties']
    #text_to_append = [properties['entity'], properties['name_location'], properties['snippet']]
    data = [[properties['entity'], properties['name_location'], properties['category'], properties['type'], properties['importance'], sent] for sent in properties['snippet']]
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='excel')
        writer.writerows(data)

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def search_entities(searchable_entities: dict, context: str, title_page: str):
    """ Search entities with API geocode.maps
    
    Args:
        searchable_entities: list of entities to search
        context: context of the search (city, country, etc.)
    """

    response_file_path = f"response/spacy_pipeline/{title_page}.txt"
    response_geojson_file_path = f"response/spacy_pipeline/{title_page}_geojson.geojson"
    response_file_excel = f"response/spacy_pipeline/{title_page}.csv"

    delete_file(response_file_path)
    delete_file(response_geojson_file_path)
    delete_file(response_file_excel)

    list_features = []

    for search_item in searchable_entities.keys():
        text = urllib.parse.quote_plus(search_item + " " + context)
       
        URLGEOJSON = 'https://geocode.maps.co/search?q={'+text+'}&format=geojson'
        print(URLGEOJSON)
        
        s = requests.Session()
        
        response= s.get(URLGEOJSON)
        try: 
            result = response.json()
        except json.decoder.JSONDecodeError as jsonError: 
            print("Error in the response of the API")
            return

        if "features" in result: 
            result = result['features']

            if len(result) > 0:
                location = result[0]
                locationName = location['properties']['display_name'].strip()
                locationNameList = locationName.split(", ")
                city = ""

                if locationNameList[-2].isdigit(): 
                    city = locationNameList[-4] 
                else: 
                    city = locationNameList[-3] 
                    
                if locationName.endswith("Italia") and city.__contains__(context): 
                    coordinates = location['geometry']['coordinates']
                    category = ""
                    type = ""
                    importance = ""
                    if 'category' in location['properties']:
                        category = location['properties']['category']
                    if 'type' in location['properties']:
                        type = location['properties']['type']
                    if 'importance' in location['properties']:    
                        importance = location['properties']['importance']

                    loc_point = Point((coordinates[0], coordinates[1]))
                    loc_feature = Feature(geometry=loc_point, properties={
                                    "entity": search_item, 
                                    "name_location": locationName,
                                    "category": category,
                                    "type": type,
                                    "importance": importance,
                                    "snippet": searchable_entities[search_item]})
                    
                    print_to_csv(response_file_excel, loc_feature)

                    list_features.append(loc_feature)    

                    print("DISPLAY NAME: ", locationName)
                    print("RESULT GEOJSON: ", location)
                    print("OBJECT GEOJSON: ", loc_feature)

                    print_to_file(response_file_path, '-' * 50)

                    print_to_file(response_file_path, f"Research term: {search_item}")
                    print_to_file(response_file_path, URLGEOJSON)
                    print_to_file(response_file_path, f"Address: {locationName}")
                    print_to_file(response_file_path, f"GEOGSON: {loc_feature}")
      
                    print_to_file(response_file_path, '-' * 50)

        #time.sleep(.600)
    
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
