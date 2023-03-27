import pandas as pd
from functools import partial

from geojson import Feature, Point, FeatureCollection

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy import distance
from geopy.point import Point as GeoPoint

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

def search_entities_geopy(searchable_entities: dict, geographic_scope: dict, title_page: str, lang: str, locator: Nominatim, features: list = list()): 
    """ Search the entities in the searchable_entities dictionary with GeoPy library
        and return the corrispondent features geojson.

    Args:
        searchable_entities: dictionary with the entities to search
        geographic_scope: dictionary with the context of the text in which the entities are searched
        title_page: title of the page
        lang: language of the page
        locator: geopy locator
        features: list of features geojson
    
    Returns:
        features: list of features geojson
    """

    geocode = RateLimiter(locator.geocode, min_delay_seconds=1)
    name_geographic_scope = geographic_scope['name']
    bbox = geographic_scope['bbox']
    country_code = geographic_scope['country_code']
    state = geographic_scope['state']
    locations = []

    # Modify the searchable entities to search with the context
    for ent in searchable_entities.keys():
        to_search = {"street": ent, "state": state, "city": name_geographic_scope}
        #if not ent.__contains__(name_geographic_scope): 
        #    to_search = {"street": ent + " " + name_geographic_scope}
        locations.extend([[ent, to_search, searchable_entities[ent]]])

    df = pd.DataFrame(locations, columns=['entity', 'to_search', 'snippet'])
    df.head()
    df['address'] = df['to_search'].apply(partial(geocode, language=lang, viewbox=bbox, country_codes=[country_code], bounded=True, exactly_one=False))
    df = df[pd.notnull(df['address'])]

    df['address'] = df['address'].apply(lambda list_loc: most_close_location(list_loc, geographic_scope))
    df['coordinates'] = df['address'].apply(lambda loc: Point((loc.longitude, loc.latitude)) if loc else None)
    df['name_location'] = df['address'].apply(lambda loc: loc.address if loc else None)
    df[['class', 'type']] = df['address'].apply(lambda loc: pd.Series([loc.raw['class'], loc.raw['type']]) if loc else None)

    df['to_search'] = df['to_search'].apply(lambda to_search: to_search['street'])

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

def most_close_location(results: list, geographic_scope: dict):
    """ Return the most close location from the list of results
    
    Args:
        results: list of results
        geographic_scope: dict that represents the geographic scope
    
    Returns:
        location: the most close location
    """
    location = results[0]
    poi_loc = (location.latitude, location.longitude)
    loc_geographic_scope = (float(geographic_scope['latitude']), float(geographic_scope['longitude']))
    
    distance_min = distance.distance(loc_geographic_scope, poi_loc).km

    for result in results:
        current_loc = (result.latitude, result.longitude)
        current_distance = distance.distance(loc_geographic_scope, current_loc).km
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


def get_geographic_scope(article: Doc, lang: str, geocoder: Nominatim): 
    """ Return the geographic scope of the article.

    Geographic scope is defined as the most common GPE entity in the article.
    
    Args:
        article: article to analyze
    
    Returns:
        geographic scope (dict): the geographic scope of the article, with the name, the coordinates and the state geometry
    """
    
    most_common_gpe = get_most_common_gpe(article)
    to_search = {"city": most_common_gpe}
    location = geocoder.geocode(to_search, language=lang, addressdetails=True, exactly_one=True)

    state_name = location.raw['address']['state']
    to_search = {"state": state_name}
    state_location = geocoder.geocode(to_search, language=lang, exactly_one=True)
    bounding_box = state_location.raw['boundingbox']

    bbox = [GeoPoint(float(bounding_box[1]), float(bounding_box[2])), GeoPoint(float(bounding_box[0]), float(bounding_box[3]))]

    country_code = location.raw['address']['country_code']


    geographic_scope = {
        "name": most_common_gpe,
        "latitude": location.latitude,
        "longitude": location.longitude,
        "bbox": bbox, 
        "country_code": country_code,
        "state": state_name
    }


    return geographic_scope
    


def get_most_common_gpe(article: Doc):
    ents = article.ents
    ents_gpe = [ent.text for ent in ents if ent.label_ == "GPE"]
    count = Counter(ents_gpe)
    most_common_gpe = count.most_common(1)[0][0]

    return most_common_gpe