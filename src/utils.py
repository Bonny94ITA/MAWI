import csv
import os
import json
import requests
import wikipedia

from shapely.geometry import Point, Polygon
from geojson import FeatureCollection, Feature, Point
from wikidata.client import Client
from spacy.tokens import Doc

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

def save_results(features: list, path_results: str, title_page: str): 
    """ Save results of the search
    
    Args: 
        features: list of feature to save
        title_page: title of the page

    """

    geojson = FeatureCollection(features)

    results_path = path_results+"/"+title_page+".geojson" 
    results_cleaned_path = path_results+"/"+title_page+"_cleaned.geojson"
    results_outliers_path = path_results+"/"+title_page+"_outliers.geojson"

    delete_file(results_path)
    delete_file(results_cleaned_path)
    delete_file(results_outliers_path)

    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
        print("The result complete has been saved as a file inside the response folder")

def get_entity_id(name: str, lang: str = "it"):
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
        "language": lang,
        "format": "json"
    }

    response = session.get(url=url_api, params=params)
    data = response.json()
    entity_id = data['search'][0]['id']

    return entity_id

def get_nearby_pages(page: str, lang: str = "it"):
    """ Return pages near the page in argument.

    Args: 
        page (str): string with the page

    Returns: 
        list of pages near the page in argument
    """
    session = requests.Session()
    url_api = "https://"+lang+".wikipedia.org/w/api.php"
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

def get_further_information(entities: dict, name_geographic_scope: str, lang: str): 
    """ Get the summary of the entities using wikipedia API.

    Args:
        entities: dictionary with the entities
        name_geographic_scope: name of the geographic scope of the article
        lang: language of the wikipedia article
    
    Returns:
        entities: dictionary with the summary of the entities
    """

    wikipedia.set_lang(lang)
    for ent in entities: 
        to_search = ent
        title = None
        if not ent.__contains__(name_geographic_scope):
            to_search = ent+" ("+name_geographic_scope+")"
        try:
            page_ent = wikipedia.page(to_search)
            entities[ent].append(page_ent.summary)
        except wikipedia.DisambiguationError as e:
            try:
                title = e.options[0]
                page_ent = wikipedia.page(title)
                entities[ent].append(page_ent.summary)
            except wikipedia.DisambiguationError as e2:
                title = e2.options[0]
                print("DisambiguationError")
                print("Ricerca iniziale: ", to_search)
                print("Titolo: ", title)
        except wikipedia.PageError as e:
            print("PageError")
            print("Ricerca iniziale: ", to_search)
            print("Titolo: ", title)
            pass

    return entities


def detection_outliers(results: list, context: dict):
    """ Detection of outliers in results.
    
    Args:
        results: list of data to analyze
        context: context of the results
    Returns:
        results_cleaned: list of results without outliers
        outlier: list of outliers
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

def get_list_names(path: str):
    """
    Get the list of names from a file.
    
    Args:
        path: path of the file
    
    Returns:
        names: list of names
    """
    names = []
    with open(path, 'r', encoding='utf-8') as file:
        names = file.readlines()
        names = [name.replace("\n", "") for name in names]

    return names

def get_summary_names(names: list[str]):
    """
    Get the summary of the names using wikipedia API.

    Args:
        names: list of names
    
    Returns:
        summaries: list of tuples with the name and the summary
    """
    wikipedia.set_lang("it")

    summaries = []
    for name in names: 
        print(name)
        summary = ""
        try: 
            summary = wikipedia.summary(name)
            
            print(summary + "\n\n")
        except wikipedia.DisambiguationError as e:
            print("DisambiguationError")
            print(e.options)
            print("\n\n")
            pass
        except wikipedia.PageError as e:
            print("PageError")
            print(e)
            print("\n\n")
            pass
        finally:
            summaries.append((name, summary))

    return summaries

def get_genders_names(names: list[tuple[str, str]]):
    """
    Get gender of the names using wikidata API.

    Args:
        names: list of tuples with the name and the summary
    
    Returns:
        genders: list of tuples with name, summary and gender
    """

    client = Client()
    genders = []
    for name, summary in names:
        print(name)
        gender = "Undefined"
        try:
            entity_id = get_entity_id(name)

            try:
                print(entity_id)
                entity = client.get(entity_id, load=True)

                gender_prop = client.get('P21')
                
                gender_val = entity[gender_prop]

                print(str(gender_val))

                if str(gender_val) == "<wikidata.entity.Entity Q6581072>":
                    print("Personaggio femminile!\n\n")
                    gender = "female"

            except:
                pass

        except IndexError: # entity_id not found
            pass

        finally:
            genders.append((name, summary, gender))
    
    return genders

def save_results_extension(path: str, geojson: FeatureCollection): 

    """
    Save the results in a file.
    
    Args:
        path: path of the file
        geojson: geojson to save
    
    Returns:
        None
    """

    with open(path, 'w', encoding='utf-8') as f:
        json.dump(geojson, f, ensure_ascii=False, indent=4)
        print("The result complete has been saved as a file inside the response folder")

def read_article(path: str): 
    """
    Read the article from a file.

    Args:
        path: path of the file
    
    Returns:
        article: string with the article
    """
    file = open(path, "r", encoding='utf-8') 
    article = file.read() 
    file.close() 

    return article

def read_titles(path: str, lang: str): 
    titles_articles = []

    with open(path, 'r', encoding='utf-8') as f:
        f.readline()
        line = f.readline().strip()

        if lang == "it":
            while line != "#EN":
                titles_articles.append(line)
                line = f.readline().strip()
        else:
            while line != "#EN":
                line = f.readline().strip()
            line = f.readline().strip()
            while line:
                titles_articles.append(line)
                line = f.readline().strip()

    return titles_articles
