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

def get_context(nlp_text, input_json: list, param_to_search: str):
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

def get_entities_snippet(nlp_text, cities: list, searchable_entities = dict()):
    """Get the entities from the nlp_text which are not cities and print snippet in which
        they appears.

    Args:
        nlp_text: spacy text
        cities: list with cities name to filter
    """

    sents = list(nlp_text.sents)
    sentence_dict = generate_sentences_dictionary(sents)
    for (index, sentence) in sentence_dict.items():
        entities = clean_entities(sentence)
        for ent in entities:
            if ent not in cities:
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
        if ent.label_ == "LOC":
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


def search_entities(searchable_entities: dict, context: dict, title_page: str, features = list()):
    """ Search entities with API geocode.maps
    
    Args:
        searchable_entities: list of entities to search
        loc_context: dict with information about context (city) 
        title_page: title of the page

    Returns:
        features: list with the results of the search (points and snippets)
    """

    response_file_path = f"response/spacy_pipeline/{title_page}.txt"
    delete_file(response_file_path)
    response_file_excel = f"response/spacy_pipeline/{title_page}.csv"
    delete_file(response_file_excel)

    name_context = context['name']
    for search_item in searchable_entities.keys():
        #text = urllib.parse.quote_plus(search_item + " " + name_context)
        text = urllib.parse.quote_plus(search_item)

        URLGEOJSON = 'https://geocode.maps.co/search?q={'+text+'}&format=geojson'
        print(URLGEOJSON)
        
        s = requests.Session()
        
        response= s.get(URLGEOJSON)
            
        try: 
            results = response.json()
        except json.decoder.JSONDecodeError: 
            print("Error in the response of the API")
            return

        if "features" in results: # there are locations
            results = results['features']

            if len(results) > 0:
                location = most_close_location(results, context)
                
                locationName = location['properties']['display_name'].strip()
                
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

                if category != "": 
                    if not ((category == "boundary" and type == "administrative") or 
                        (category == "highway" and (type == "motorway" or type == "motorway_junction")) or
                        category == "waterway" or (category == "amenity" and type == "bicycle_rental") or
                        type == "unclassified" or (category == "natural" and type == "water") or 
                        (category == "shop" and type != "gift")):

                        loc_point = Point((coordinates[0], coordinates[1]))
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

                        print_to_file(response_file_path, '-' * 50)

                        print_to_file(response_file_path, f"Research term: {search_item}")
                        print_to_file(response_file_path, URLGEOJSON)
                        print_to_file(response_file_path, f"Address: {locationName}")
                        print_to_file(response_file_path, f"GEOGSON: {loc_feature}")
        
                        print_to_file(response_file_path, '-' * 50)

        time.sleep(.600)
    
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
            #importance = result['properties']['importance']
            #if importance >= 0.4: 
            #    results_cleaned.append(result)
            #else: 
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
    poi_loc = (location['geometry']['coordinates'][1], location['geometry']['coordinates'][0])
    context_loc = (float(context['latitude']), float(context['longitude']))
    distance = hs.haversine(context_loc, poi_loc)

    for result in results:
        current_loc = (result['geometry']['coordinates'][1], result['geometry']['coordinates'][0])
        current_distance =  hs.haversine(context_loc, current_loc)
        #print("DISTANCE: ", current_distance)
        if distance > current_distance: 
            location = result
            distance = current_distance

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
    
    del Htag.contents[i-1:]

    cleaned_content = soup.get_text().replace('\n', ' ')

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