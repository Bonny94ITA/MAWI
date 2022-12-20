import pandas as pd
from functools import partial

from geojson import Feature, Point, FeatureCollection, Polygon

from geopy.extra.rate_limiter import RateLimiter
from geopy.geocoders import Nominatim
from geopy import distance

from src.utils_2 import delete_file, print_to_file


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

def search_entities_geopy(searchable_entities: dict, context: dict, title_page: str, features = list()): 
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
    for ent in searchable_entities.keys():
        to_search = ent
        if not ent.__contains__(name_context): 
            to_search = to_search + " " + name_context
        locations.extend([[ent, to_search, searchable_entities[ent]]])

    df = pd.DataFrame(locations, columns=['entity', 'to_search', 'snippet'])
    df.head()
    df['address'] = df['to_search'].apply(partial(geocode, language='it', exactly_one=False))

    df = df[pd.notnull(df['address'])]

    df['address'] = df['address'].apply(lambda list_loc: most_close_location(list_loc, context))

    df['coordinates'] = df['address'].apply(lambda loc: Point((loc.longitude, loc.latitude)) if loc else None)
    
    df['name_location'] = df['address'].apply(lambda loc: loc.address if loc else None)

    df[['class', 'type']] = df['address'].apply(lambda loc: pd.Series([loc.raw['class'], loc.raw['type']]) if loc else None)

    print(df)
    df.to_csv("response/dataframe.csv")
    
    geojson_entities = to_geojson(df)

    features.extend(geojson_entities)
    # save entities

    response_file_path = f"response/spacy_pipeline/{title_page}.txt"

    delete_file(response_file_path)

    entities_final = df['entity'].to_list()

    entities_final.sort(key=str.lower)

    for entity in entities_final:
        print_to_file(response_file_path, entity)

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