import pandas as pd
from functools import partial

from geojson import Feature, Point, FeatureCollection

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy import distance

from spacy.tokens import Doc

from collections import Counter

from src.utils import delete_file, print_to_file

def to_geojson(df: pd.DataFrame):
    """ Convert a dataframe to geojson.

    Args:
        df: dataframe to convert
    Returns:
        features: list of features geojson
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

def merge_entities(features: list, entities_final: list):
    """ Merge the entities with the entities already found.

    Args:
        features: list of features geojson
        entities_final: list of entities already found
    Returns:
        entities_final: list of entities already found merged
    """
    for feature in features:
        entity = feature['properties']['entity']
        if entity not in entities_final:
            entities_final.append(entity)
    
    return entities_final

def search_entities_geopy(searchable_entities: dict, context: dict, title_page: str, features: list = list(), lang: str = "it"): 
    """ Search the entities in the searchable_entities dictionary with GeoPy library
        and return the corrispondent features geojson.

    Args:
        searchable_entities: dictionary with the entities to search
        context: dictionary with the context of the text in which the entities are searched
        title_page: title of the page
        features: list of features geojson
    
    Returns:
        features: list of features geojson
    """
    locator = Nominatim(user_agent="PoI_geocoding")
    geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
    name_context = context['name']
    locations = []

    # Modify the searchable entities to search with the context
    for ent in searchable_entities.keys():
        to_search = ent
        if not ent.__contains__(name_context): 
            to_search = to_search + " " + name_context
        locations.extend([[ent, to_search, searchable_entities[ent]]])

    df = pd.DataFrame(locations, columns=['entity', 'to_search', 'snippet'])
    df.head()
    df['address'] = df['to_search'].apply(partial(geocode, language=lang, exactly_one=False))
    df = df[pd.notnull(df['address'])]

    df['address'] = df['address'].apply(lambda list_loc: most_close_location(list_loc, context))
    df['coordinates'] = df['address'].apply(lambda loc: Point((loc.longitude, loc.latitude)) if loc else None)
    df['name_location'] = df['address'].apply(lambda loc: loc.address if loc else None)
    df[['class', 'type']] = df['address'].apply(lambda loc: pd.Series([loc.raw['class'], loc.raw['type']]) if loc else None)

    print(df)
    df.to_csv("results/dataframe.csv")
    
    geojson_entities = to_geojson(df)

    # Save entities

    results_file_path = f"results/extraction_entities_snippet/{title_page}.txt"
    delete_file(results_file_path)
    entities_final = df['entity'].to_list()
    entities_final = merge_entities(features, entities_final)
    entities_final.sort(key=str.lower)

    for entity in entities_final:
        print_to_file(results_file_path, entity)

    features.extend(geojson_entities)

    return features, entities_final

def most_close_location(results: list, context: dict):
    """ Return the most close location from the list of results
    
    Args:
        results: list of results
        context: tuple of coordinates (lat, lon)
    
    Returns:
        location: the most close location
    """
    location = results[0]
    poi_loc = (location.latitude, location.longitude)
    context_loc = (float(context['latitude']), float(context['longitude']))
    
    distance_min = distance.distance(context_loc, poi_loc).km

    for result in results:
        current_loc = (result.latitude, result.longitude)
        current_distance = distance.distance(context_loc, current_loc).km
        if distance_min > current_distance: 
            location = result
            distance_min = current_distance

    return location

def get_location_names(list: list[tuple[str, str, str]]): 

    locator = Nominatim(user_agent="Extension_geocoding")
    geocode = RateLimiter(locator.geocode, min_delay_seconds=1)

    locations = []
    for name, summary, _ in list:
        to_search = name + " Torino"
        locations.extend([[name, to_search, summary]])

    df = pd.DataFrame(locations, columns=['entity', 'to_search', 'snippet'])
    df.head()
    df['address'] = df['to_search'].apply(partial(geocode, language='it', exactly_one=True))

    df = df[pd.notnull(df['address'])]

    df['coordinates'] = df['address'].apply(lambda loc: Point((loc.longitude, loc.latitude)) if loc else None)

    df['name_location'] = df['address'].apply(lambda loc: loc.address if loc else None)

    df[['class', 'type']] = df['address'].apply(lambda loc: pd.Series([loc.raw['class'], loc.raw['type']]) if loc else None)

    print(df)

    geojson = FeatureCollection(to_geojson(df))

    return geojson


def get_geographic_scope(article: Doc): 
    """ Return the geographic scope of the article.

    Geographic scope is defined as the most common GPE entity in the article.
    
    Args:
        article: article to analyze
    
    Returns:
        geographic scope: the geographic scope of the article
    """
    
    ents = article.ents
    ents_gpe = [ent.text for ent in ents if ent.label_ == "GPE"]
    count = Counter(ents_gpe)
    geographic_scope = count.most_common(1)[0][0]

    return geographic_scope

    