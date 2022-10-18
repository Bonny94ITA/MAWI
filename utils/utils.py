from bs4 import BeautifulSoup
import requests
import urllib
import json
import os
from geojson import Feature, Point, FeatureCollection
import csv 
import haversine as hs
import numpy as np
from kneed import KneeLocator
import matplotlib.pyplot as plt

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

def get_entities_snippet(nlp_text, cities: list):
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
            #if ent not in counter:
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


def search_entities(searchable_entities: dict, loc_context: dict, title_page: str):
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
    
    context = loc_context['name']
    for search_item in searchable_entities.keys():
        #text = urllib.parse.quote_plus(search_item + " " + context)
        text = urllib.parse.quote_plus(search_item)

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
                location = most_close_location(result, loc_context) # ma se si usasse anche la similarità????
                
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

                        list_features.append(loc_feature)    

                        print("DISPLAY NAME: ", locationName)
                        #print("RESULT GEOJSON: ", location)
                        #print("OBJECT GEOJSON: ", loc_feature)

                        print_to_file(response_file_path, '-' * 50)

                        print_to_file(response_file_path, f"Research term: {search_item}")
                        print_to_file(response_file_path, URLGEOJSON)
                        print_to_file(response_file_path, f"Address: {locationName}")
                        print_to_file(response_file_path, f"GEOGSON: {loc_feature}")
        
                        print_to_file(response_file_path, '-' * 50)

        #time.sleep(.600)
    
    geojson_object = FeatureCollection(list_features)
    #print(len(geojson_object["features"]))
    with open(response_geojson_file_path, 'w', encoding='utf-8') as f:
        json.dump(geojson_object, f, ensure_ascii=False, indent=4)
        print("The result has been saved as a file inside the response folder")

    data_cleaned, outliers = detection_outliers(list_features, loc_context)

    geojson_object_cleaned = FeatureCollection(data_cleaned)
    response_cleaned = f"response/spacy_pipeline/{title_page}_cleaned.geojson"
    geojson_object_outliers = FeatureCollection(outliers)
    response_outliers = f"response/spacy_pipeline/{title_page}_outliers.geojson"

    with open(response_cleaned, 'w', encoding='utf-8') as f:
        json.dump(geojson_object_cleaned, f, ensure_ascii=False, indent=4)
        print("The result has been saved as a file inside the response folder")

    with open(response_outliers, 'w', encoding='utf-8') as f:
        json.dump(geojson_object_outliers, f, ensure_ascii=False, indent=4)
        print("The result has been saved as a file inside the response folder")

    print(loc_context)


def detection_outliers(results: list, context: dict):
    """ Detection of outliers in results.
    
    Args:
        results: list of data to analyze
        centroid: centroid of the results
    Returns:
        list of outliers
    """

    centroid = (float(context['latitude']), float(context['longitude']))
    
    data_analyzed, distance = analyze_data(results, centroid)


    data_cleaned = [item[0] for item in data_analyzed if item[1] < distance]

    outliers = [item[0] for item in data_analyzed if item[0] not in data_cleaned]

    return data_cleaned, outliers

def analyze_data(results: list, centroid: tuple):
    """ Analyze the data to find the distance from the centroid that suits the cluster
    
    Args:
        results: list of data to analyze
        centroid: centroid of the results
    
    Returns:
        distance from the centroid
    """
    
    data_analyzed = [] # preprocessing dei dati per la clusterizzazione

    for result in results:
        data_analyzed.append((result, hs.haversine(centroid, (result['geometry']['coordinates'][1], result['geometry']['coordinates'][0]))))

    data_analyzed.sort(key=lambda x: x[1])    

    distances_mesaured = [item[1] for item in data_analyzed] 

    max_distance = max(distances_mesaured)

    distances = np.arange(1, max_distance + 2, 2)
    n_points = np.zeros(len(distances))

    for i in range(len(distances)): 
        n_points[i] = len([item for item in data_analyzed if item[1] < distances[i]])

    # visualizzazione dei dati
    kl = KneeLocator(distances, n_points, S=1, curve="concave", direction="increasing", interp_method="polynomial")
    #kl.plot_knee()
    
    knee = kl.knee

    plt.xlabel('distance from centroid')
    plt.ylabel('number of points ')
    plt.plot(distances, n_points, 'bx-')
    plt.vlines(knee, plt.ylim()[0], plt.ylim()[1], linestyles='dashed')

    plt.show()

    print("KNEEE: ", knee)
    return data_analyzed, knee
    
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


def wiki_content(title, loc = False):
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

    if loc: 
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
                    "longitude": coordinates[0]['lon']}
    
        return cleaned_content, location
    
    else: 
        return cleaned_content


def get_nearby_pages(page: str):
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"
    params_vic = {
        "action": "query",
        "list": "geosearch",
        "gsradius": 3000,
        "gspage": page,
        "gsprop": "type", # su cui poi posso filtrare landmark!!
        "formatversion": "2",
        "format": "json"
    }

    response_vic= session.get(url=url_api, params=params_vic)

    data_vic = response_vic.json()

    landmarks = [loc for loc in data_vic['query']['geosearch'] if loc['type'] == 'landmark']

    return landmarks