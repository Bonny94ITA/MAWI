from spacy.tokens import Doc
import csv
import os
import json
from wikidata.client import Client
from geojson import FeatureCollection, Feature
import requests

from src.location import detection_outliers

def find_indexes(doc: Doc, ch): 
    """ Find the index of the character ch in the doc.

    Args:
        doc: spacy doc where to search
        ch: character to search
    
    Returns:
        list of the indexes of the character ch
    """

    indexes = []
    end = 0
    for i, token in enumerate(doc):
        if token.text == ch:
            indexes.append(i)
        end = i
    indexes.append(end)
    return indexes

def print_to_file(file_path: str, text_to_append):
    with open(file_path, 'a', encoding='utf-8') as file:
        file.write(text_to_append + "\n")

def print_to_csv(file_path: str, object_to_append):
    properties = object_to_append['properties']
    data = [[properties['entity'], properties['name_location'], properties['category'], properties['type'], \
        properties['importance'], sent] for sent in properties['snippet']]
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file, dialect='excel')
        writer.writerows(data)

def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)

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

def get_polygon(name: str):
    """ Get the polygon of the location using wikidata API.

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

def get_entity_id(name: str):
    """ Get the entity id of the location using wikidata API.
    
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

def get_further_information(entities: list, city = "Torino"): 

    informations = dict()
    wikipedia.set_lang("it")
    for ent in entities: 
        try:
            page_ent = wikipedia.page(ent+" ("+city+")", redirect=True, preload=False)
            informations[ent] = page_ent.summary
        except wikipedia.DisambiguationError as e:
            title = e.options[0]
            page_ent = wikipedia.page(title, redirect=True, preload=False)
            informations[ent] = page_ent.summary
        except wikipedia.PageError as e:
            informations[ent] = None

    return informations