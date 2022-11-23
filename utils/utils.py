from bs4 import BeautifulSoup
import requests
import urllib
import json
import os
from geojson import Feature, Point, FeatureCollection
import csv 
import haversine as hs
import time
from wikidata.client import Client
from shapely.geometry import Point, Polygon
from geopy.geocoders import Nominatim
from geopy import distance
import string

import pandas as pd 
import geopandas as gpd
import matplotlib.pyplot as plt
from geopy.extra.rate_limiter import RateLimiter


def get_context(nlp_text, input_json: list, param_to_search: str): # TODO: DELETE!
    """Get the context of the entities in the nlp_text.
    
    Args:
        nlp_text: spacy text
        input_json: json file with the entities to search
        param_to_search: parameter to search in the json file

    Returns:
        counter: dictionary with the entities (cities name) to search and their occurences
        context: string with the context of the text
        loc_context: coordinates of the context
    """

    counter = count_occurrences(nlp_text, input_json, param_to_search)
    print(counter)
    context = max(counter, key=counter.get)
    loc_context = find_loc_context(context, input_json, param_to_search) 
    return counter, context, loc_context

def find_loc_context(context: str, input_json: list, param_to_search: str): 
    """Find the object of the context.

    Args:
        context: context of the text
        input_json: json file with the entities to search

    Returns:
        loc_context: coordinates of the context
    """
    loc_context = {}
    for elem in input_json:
        if elem[param_to_search] == context:
            loc_context = elem
    return loc_context

def count_occurrences(nlp_text, input_json: list, param_to_search: str): # TODO: DELETE?
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

def sent_contains_ent(sentence, entity):
    """Check if the sentence contains the entity.

    Args:
        sentence: sentence to check
        entity: entity to check
    Returns:
        True if the sentence contains the entity, False otherwise
    """

    possible_begins = []

    j = 0
    while j < len(sentence): 
        if entity[0].text.lower() == sentence[j].text.lower(): 
            possible_begins.append(j)
        j += 1
    
    contains = False
    index = 0
    while not contains and index < len(possible_begins):
        contained_all = True
        i = 0
        j = possible_begins[index]
        while contained_all and i < len(entity) and j < len(sentence): 
            contained_all = (entity[i].text.lower() == sentence[j].text.lower())
            i += 1
            j += 1

        if i == len(entity) and contained_all:
            contains = True
        index += 1
    
    return contains


def get_entities_snippet(nlp_text, cities: list, entities_to_search_prev = dict()):
    """Get the entities from the nlp_text which are not cities and print snippet in which
        they appears.

    Args:
        nlp_text: spacy text
        cities: list with cities name to filter
        entities_to_search_prev: dictionary with the entities to search of the previous text and do not search again
    
    Returns:
        searchable_entities: dictionary with the entities and the snippet in which they appear
        sentence_dict: dictionary with  the index of the sentence in the text and the sentence itself
    """

    entities_to_search = dict()
    sents = list(nlp_text.sents)
    ents = list(nlp_text.ents)
    sentence_dict = generate_sentences_dictionary(sents)
    ents = clean_entities(ents, cities, sentence_dict)
    
    for ent in ents:    
        if ent.text not in entities_to_search_prev: 
            for (index, sentence) in sentence_dict.items():
                if sent_contains_ent(sentence, ent):
                    # Create snippet
                    before = sentence_dict.get(index-1, "")
                    if not isinstance(before, str):
                        before = before.text.strip()
                    after = sentence_dict.get(index+1, "")
                    if not isinstance(after, str):
                        after = after.text.strip()
                    
                    # forse si può usare ent.sent
                    sent = ""
                    for entities in sentence.ents: 
                        if entities.text == ent.text: 
                            sent = "*"
                            break
                    sent = sent + sentence.text.strip().capitalize()
                    if ent.text in entities_to_search and sent not in entities_to_search[ent.text] and "*"+sent not in entities_to_search[ent.text]:
                        entities_to_search[ent.text].append(sent)
                    elif ent not in entities_to_search:     
                        entities_to_search[ent.text] = [sent]

    entities_to_search = clean_entities_to_search(entities_to_search) #IN PROGRESS

    return entities_to_search, sentence_dict

def add_context_to_entities(entities_to_search: dict, sentence_dict: dict): # TODO DELETE?
    """Add the context to the entities to search.

    Args:
        entities_to_search: dictionary with the entities to search
        sentence_dict: dictionary with  the index of the sentence in the text and the sentence itself
    
    Returns:
        entities_to_search: dictionary with the entities to search and the context
    """

    for key in entities_to_search: # per ogni entità
        # cercare le frasi in cui compare 
        sentences = entities_to_search[key]
        for (index, sentence) in sentence_dict: 
            if key.text.lower() in sentence.text.lower() and sentence not in sentences: # non è sufficiente not in ma bisogna controllare per ogni stringa se contiene sentence
                before = sentence_dict.get(index-1, "")
                if not isinstance(before, str):
                    before = before.text.strip()
                after = sentence_dict.get(index+1, "")
                if not isinstance(after, str):
                    after = after.text.strip()
                
                sent_appear = before + " " + sentence.text.strip() + " " + after
                sentences.append(sent_appear)

        
    return entities_to_search

def clean_entities_to_search(entities_to_search: dict): 

    # unifico tutte le entitià uguali 
    entities = list(entities_to_search.keys())
    entities_to_delete = []
    entities.sort(key= str.lower)
    print("PRIMA: ", entities)

    for i in range(len(entities)):
        for j in range(i+1, len(entities)):
            if entities[i].lower() == entities[j].lower():
                if entities[i] > entities[j]:
                    entities_to_delete.append((entities[i], entities[j]))
                else: 
                    entities_to_delete.append((entities[j], entities[i]))

    print("DA ELIMINARE: ", entities_to_delete)
    for (entity_w, entity_r) in entities_to_delete:
        # prima unifico gli snippet
        for snippet in entities_to_search[entity_w]:
            if snippet not in entities_to_search[entity_r] and "*"+snippet not in entities_to_search[entity_r]:
                entities_to_search[entity_r].append(snippet)
        # poi rimuovo entity da entities_to_search
        del entities_to_search[entity_w]

    print("DOPO: ", entities)

    return entities_to_search

def clean_entities_to_search2(entities_to_search: dict):
    """Clean the entities to search from the dictionary.
    
    Args:
        entities_to_search: dictionary with the entities to search
    Returns:
        entities_to_search: cleaned dictionary with the entities to search
    """

    keys_to_delete = []

    for key in entities_to_search:
        if exists_dupe(key, entities_to_search):
            #print("Exist dupe!", key)
            keys_to_delete.append(key)
    
    for key in keys_to_delete:
        del entities_to_search[key]

    return entities_to_search


def exists_dupe(entity: str, entities: dict): 
    # TODO: l'idea sarebbe quella di vedere se per caso un'entità è stata individuata 
    # in più situazioni ma in forma leggermente diversa in modo da riunire la stessa definizione 
    # es. Regio - Teatro Regio  --> adesso ho un contesto vero e proprio, che relazione c'è tra i contesti??
    """Check if the entity is contained in another entity in the entities dictionary.

    Args:
        entity: entity to check
        entities: dictionary with the entities to search
    
    Returns:
        True if the entity already exists, False otherwise
    """

    is_dupe = False
    for key in entities:
        parts_key = key.split(" ")
        if entity != key and len(parts_key) > 1 and entity in parts_key:
            is_dupe = is_dupe or check_context(entity, key, entities)

    return is_dupe

def check_context(entity: str, key: str, entities: dict):
    """Check if the context of the two entities is the same.

    Args:
        entity: entity to check
        key: entity in the dictionary which can include entity 
        entities: dictionary with the entities to search
    
    Returns:
        True if the context is the same, False otherwise
    """

    context_entity = entities[entity]
    context_key = entities[key]

    check = True
    
    for sent_key in context_key:
        in_context_key = False
        for sent_entity in context_entity:
            in_context_key = in_context_key or (sent_entity == sent_key)
        
        check = check and in_context_key
    
    if check: 
        print("DUPE: Entity:", entity, "Key: " + key) 
        sentences_entity = entities[entity]
        sentences_key = entities[key]
        print("\t Sentences of: ", entity)
        for sent in sentences_entity: 
            if "*" in sent: 
                print(sent)
        
        print("\t Sentences of: ", key)
        for sent in sentences_key: 
            if "*" in sent: 
                print(sent)

    return check

def ispunct(ch):
    return ch in string.punctuation


def clean_entities(entities: list, cities: list, sentence_dict: dict): 
    """Clean the entities from the text.

    Args:
        entities: list of entities to clean
    Returns:
        entities: list of the entities useful for the search
    """
    entities_clean = []
    for ent in entities:
        if ent.label_ == "LOC" and ent.text not in cities:
            if ispunct(ent.text[-1]): # delete punctuation at the end of the entity 
                if ent.text[-1] != '"': # TODO: nel preprocessing aggiungere uno spazio prima della punteggiatura delle virgolette???
                    ent = ent[:-1]

            #if ent[-1].pos_ == "ADP": 
            #    ent = ent[:-1] 

            entities_clean.append(ent)
    
    """
    entities_to_delete = []
    entities_clean.sort(key= lambda x: x.text.lower())
    print("PRIMA: ", entities_clean)

    #entities_to_print = [entity.text for entity in entities_clean]
    #entities_to_print.sort(key= str.lower)
    #print("PRIMA: ", entities_to_print)

    for i in range(len(entities_clean)):
        for j in range(i+1, len(entities_clean)):
            if entities[i].text.lower() == entities[j].text.lower():
                if entities[i].text > entities[j].text:
                    entities_to_delete.append(entities[i])
                else: 
                    entities_to_delete.append(entities[j])

    print("DA ELIMINARE: ", entities_to_delete)
    for entity in entities_to_delete:
        entities_clean.remove(entity)

    print("DOPO: ", entities_clean)
    """
    return entities_clean

def clean_entities2(sentence, cities: list): 
    """Clean the entities from the nlp_text.

    Args:
        nlp_text: spacy text
    Returns:
        entities: list of the entities useful for the search
    """
    entities = []
    for ent in sentence.ents:
        if ent.label_ == "LOC" and ent.text not in cities:
            if ispunct(ent.text[-1]): # delete punctuation at the end of the entity
                ent = ent[:-1]

            if ent[-1].pos_ == "ADP": # delete the last word if it is an adposition oppure conviene includere nell'entità anche la parola dopo?
                ent = ent[:-1]

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
    data = [[properties['entity'], properties['name_location'], properties['category'], properties['type'], properties['importance'], sent] for sent in properties['snippet']]
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='excel')
        writer.writerows(data)

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

def to_geojson(df: pd.DataFrame):
    """Convert a dataframe to geojson.

    Args:
        df: dataframe to convert
    Returns:
        geojson: geojson file
    """
    features = []
    for _, row in df.iterrows():
        loc_point = row['coordinates']
        loc_feature = Feature(
            geometry=loc_point,
            properties={
                "entity": row['entity'],
                "name_location": row['name_location'],
                "class": row['class'],
                "type": row['type'],
                "snippet": row['snippet']
            }
        )
        features.append(loc_feature)
    
    return features

def search_entities_geopy(searchable_entities: dict, context: dict, title_page: str, features = list()): 
    locator = Nominatim(user_agent="PoI_geocoding")
    geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
    name_context = context['name']
    locations = []
    for ent in searchable_entities.keys():
        locations.extend([[ent, ent + " " + name_context, searchable_entities[ent]]])

    df = pd.DataFrame(locations, columns=['entity', 'to_search', 'snippet'])
    df.head()
    df['address'] = df['to_search'].apply(geocode)

    df = df[pd.notnull(df['address'])]
    df['coordinates'] = df['address'].apply(lambda loc: Point((loc.longitude, loc.latitude)) if loc else None)
    
    df['name_location'] = df['address'].apply(lambda loc: loc.address if loc else None)

    df[['class', 'type']] = df['address'].apply(lambda loc: pd.Series([loc.raw['class'], loc.raw['type']]) if loc else None)

    print(df)
    geojson_entities = to_geojson(df)

    features.extend(geojson_entities)
    # save entities

    response_file_path = f"response/spacy_pipeline/{title_page}.txt"

    delete_file(response_file_path)

    entities_final = df['entity'].to_list()

    entities_final.sort(key=str.lower)

    for entity in entities_final:
        print_to_file(response_file_path, entity)

    return features

def search_entities(searchable_entities: dict, context: dict, title_page: str, features = list()): # TODO: DELETE?
    """ Search entities with API geocode.maps
    
    Args:
        searchable_entities: list of entities to search
        loc_context: dict with information about context (city) 
        title_page: title of the page

    Returns:
        features: list with the results of the search (points and snippets)
    """

    geolocator = Nominatim(user_agent="PoI_geocoding")

    
    response_file_path = f"response/spacy_pipeline/{title_page}.txt"
    delete_file(response_file_path)
    response_file_excel = f"response/spacy_pipeline/{title_page}.csv"
    delete_file(response_file_excel)

    name_context = context['name']
    entities = []
    for search_item in searchable_entities.keys():
        #text = urllib.parse.quote_plus(search_item + " " + name_context)
        #text = urllib.parse.quote_plus(search_item)

        #URLGEOJSON = 'https://geocode.maps.co/search?q={'+text+'}&format=geojson'
        #print(URLGEOJSON)
        
        #s = requests.Session()
        
        #response= s.get(URLGEOJSON)
            
        #try: 
        #    results = response.json()
        #except json.decoder.JSONDecodeError: 
        #    print("Error in the response of the API")
        #    return

        results = geolocator.geocode(search_item, exactly_one = False)

        if results is not None:
            results = [res.raw for res in results]

            for result in results:
                result['lat'] = float(result['lat'])
                result['lon'] = float(result['lon'])

            if len(results) > 0:
                location = most_close_location(results, context)
                
                locationName = location['display_name'].strip()

                category = ""
                type = ""
                importance = ""
                if 'class' in location:
                    category = location['class']
                if 'type' in location:
                    type = location['type']
                if 'importance' in location:    
                    importance = location['importance']

                if category != "":
                    loc_point = Point((location['lon'], location['lat']))
                    loc_feature = Feature(geometry=loc_point, properties={
                                    "entity": search_item, 
                                    "name_location": locationName,
                                    "category": category,
                                    "type": type,
                                    "importance": importance,
                                    "snippet": searchable_entities[search_item]})
                    
                    print_to_csv(response_file_excel, loc_feature)
                    
                    features.append(loc_feature)    

                    print("DISPLAY NAME: ", locationName)

                    entities.append(search_item)

        time.sleep(.600)
    
    entities.sort()
    for entity in entities:
        print_to_file(response_file_path, entity)

    print(context)
    return features

def detection_outliers(results: list, context: dict):
    """ Detection of outliers in results.
    
    Args:
        results: list of data to analyze
        centroid: centroid of the results
    Returns:
        list of results without outliers
        list of outliers
    """

    results_cleaned, outliers = compute_distances(results, context)

    return results_cleaned, outliers

def compute_distances(results: list, context: dict):
    """ Compute the distance between the centroid and the results.
    
    Args:
        results: list of data to analyze
        centroid: centroid of the results
    Returns:
        list of results cleaned
        list of outliers
    """

    city_polygon = context['polygon']['geometry']['coordinates'][0]
    results_cleaned = []
    results_outliers = []
    for result in results:
        coordinates = result['geometry']['coordinates']
        point = Point(coordinates[0], coordinates[1])
        if point_in_polygon(point, city_polygon):
            results_cleaned.append(result)
        else:  
            results_outliers.append(result)

    return results_cleaned, results_outliers

def point_in_polygon(point: Point, polygon: list):
    """ Check if a point is inside a polygon.
    
    Args:
        point: point to check
        polygon: polygon to check
    
    Returns:
        True if the point is inside the polygon, False otherwise
    """
    coords_poly = [(coord[0], coord[1]) for coord in polygon] 
    poly = Polygon(coords_poly)

    within = point.within(poly) 

    return within
    
def metric_haversine(a, b):
    return hs.haversine(a, b)
    
def most_close_location(results: list, context: dict):
    """ Return the most close location from the list of results
    
    Args:
        results: list of results
        context: tuple of coordinates (lat, lon)
    
    Returns:
        location: the most close location
    """
    location = results[0]
    poi_loc = (location['lat'], location['lon'])
    context_loc = (float(context['latitude']), float(context['longitude']))
    
    distance_min = distance.distance(context_loc, poi_loc).km

    for result in results:
        current_loc = (result['lat'], result['lon'])
        current_distance = distance.distance(context_loc, current_loc).km
        if distance_min > current_distance: 
            location = result
            distance_min = current_distance

    return location


def save_results(features: list, context: dict): 
    """ Save results of the search
    
    Args: 
        features: list of feature to save
        context: dict with information of context

    """

    name_context = context['name']

    geojson = FeatureCollection(features)

    results_path = f"response/spacy_pipeline/{name_context}.geojson"
    results_cleaned_path = f"response/spacy_pipeline/{name_context}_cleaned.geojson"
    results_outliers_path = f"response/spacy_pipeline/{name_context}_outliers.geojson"

    delete_file(results_path)
    delete_file(results_cleaned_path)
    delete_file(results_outliers_path)

    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
        print("The result complete has been saved as a file inside the response folder")

    features_cleaned, outliers = detection_outliers(features, context)

    features_cleaned.append(context['polygon'])
    outliers.append(context['polygon'])

    geojson_cleaned = FeatureCollection(features_cleaned)
    geojson_outliers = FeatureCollection(outliers)
    
    with open(results_cleaned_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_cleaned, f, ensure_ascii=False, indent=4)
        print("The result cleaned has been saved as a file inside the response folder")

    with open(results_outliers_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_outliers, f, ensure_ascii=False, indent=4)
        print("The result outliers has been saved as a file inside the response folder")


def wiki_content(title, context = False):
    """Search title page in wikipedia with MediaWiki API.

    Args: 
        title: str Wikipedia page title
        context: boolean if true is searched also the location of the context
    Returns:
        Wikipedia page content cleaned  
    """
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": title,
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
    
    tag = soup.find_all('span', id=True) # find all the titles of paragraphs in the text

    for t in tag:
        t.decompose()

    del Htag.contents[i-1:]

    # add punct in bullets 
    tag = soup.find_all('ul', class_=False)

    not_punct = ['"',"'", '(', ')','[',']', ' ']
    for t in tag:
        sub_tag = t.find_all("li")
        if len(sub_tag) > 1:
            for s in sub_tag[:-1]: 
                if not s.text[-1] in string.punctuation or s.text[-1] in not_punct:
                    s.append(" ;")

        if not sub_tag[-1].text[-1] in string.punctuation or sub_tag[-1].text[-1] in not_punct:
            sub_tag[-1].append(" .")
    
    cleaned_content = soup.get_text(' ', strip=True)

    with open(f'response/wikiPageContent/{title}_notcleaned.txt', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    with open(f'response/wikiPageContent/{title}.txt', 'w', encoding='utf-8') as f:
        f.write(cleaned_content)

    if context: 
        params_coord = {
            "action": "query",
            "prop": "coordinates",
            "titles": title,
            "formatversion": "2",
            "format": "json"
        }

        response_coord = session.get(url=url_api, params=params_coord)
        data_coord = response_coord.json()

        print(data_coord)

        coordinates = data_coord['query']['pages'][0]['coordinates']
        location = {"name": title, 
                    "latitude": coordinates[0]['lat'], 
                    "longitude": coordinates[0]['lon'], 
                    "polygon": get_polygon(title)}
    
        return cleaned_content, location
    
    else: 
        return cleaned_content


def get_polygon(name):
    """
    Get the polygon of the location using wikidata API.

    Args:
        name: name of the location
    
    Returns:
        polygon: polygon of the location
    """

    entity_id= get_entity_id(name)

    client = Client()

    client.request
    entity = client.get(entity_id, load=True)

    easternpoint_prop = client.get('P1334')
    easternpoint = entity[easternpoint_prop]
    e_coord = [easternpoint.longitude, easternpoint.latitude]

    northernpoint_prop = client.get('P1332')
    northernpoint = entity[northernpoint_prop]
    n_coord = [northernpoint.longitude, northernpoint.latitude]

    southernpoint_prop = client.get('P1333')
    southernpoint = entity[southernpoint_prop] 
    s_coord = [southernpoint.longitude, southernpoint.latitude]

    westernpoint_prop = client.get('P1335')
    westernpoint = entity[westernpoint_prop]
    w_coord = [westernpoint.longitude, westernpoint.latitude]

    city = {
        "type": "Polygon", 
        "coordinates": [
                [e_coord, n_coord, w_coord, s_coord, e_coord]
        ]
    }

    feature = Feature(geometry=city, properties={"name": "turin"})

    return feature


def get_entity_id(name):
    """
    Get the entity id of the location using wikidata API.
    
    Args:
        name: name of the location
    
    Returns:
        entity_id: entity id of the location
    """
    session = requests.Session()
    url_api = "https://wikidata.org/w/api.php"
    params = {
        "action": "wbsearchentities",
        "search": name,
        "language": "it",
        "format": "json"
    }

    response = session.get(url=url_api, params=params)
    data = response.json()
    entity_id = data['search'][0]['id']

    return entity_id


def get_nearby_pages(page: str):
    """ Return pages near the page in argument.

    Args: 
        page (str): string with the page

    Returns: 
        list of pages near the page in argument
    """
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"
    params = {
        "action": "query",
        "list": "geosearch",
        "gsradius": 3000,
        "gspage": page,
        "gsprop": "type", 
        "formatversion": "2",
        "format": "json"
    }

    response = session.get(url=url_api, params=params)

    nearby_pages = response.json()

    landmarks = [pages['title'] for pages in nearby_pages['query']['geosearch'] if pages['type'] == 'landmark']

    return landmarks