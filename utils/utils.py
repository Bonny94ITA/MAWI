from bs4 import BeautifulSoup
import requests
import json
import os
from geojson import Feature, Point, FeatureCollection
import csv 
from wikidata.client import Client
from shapely.geometry import Point, Polygon
from geopy.geocoders import Nominatim
from geopy import distance
import string
import spacy
import re

import pandas as pd 
from geopy.extra.rate_limiter import RateLimiter
from functools import partial
from spacy.tokens import Doc
from spacy.tokens import Span

def sent_contains_ent(sentence: Span, entity: Span):
    """ Check if the sentence contains the entity.

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

def first_upper(sentence: str):
    """ Make the first letter of the sentence uppercase.

    Args:
        sentence: sentence to modify

    Returns:
        sentence: sentence with the first letter uppercase
    """
    if sentence != "":
        sentence = sentence[0].upper() + sentence[1:]
    return sentence

def get_entities_snippet(document: Doc, entities_to_search_prev = dict()):
    """ Get the entities from the nlp_text which are not cities and print snippet in which
        they appears.

    Args:
        document: spacy text
        entities_to_search_prev: dictionary with the entities to search of the previous text and do not search again
    
    Returns:
        entities_to_search: dictionary with the entities and the snippet in which they appear
        sentence_dict: dictionary with the index of the sentence in the text and the sentence itself
    """

    entities_to_search = dict()
    entities_to_search_pos = dict()
    ents = list(document.ents)
    sentence_dict = generate_sentences_dictionary(document)

    with open('Sentences.csv', 'w', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for index, sent in sentence_dict.items():
            writer.writerow([index, sent.text.strip(" \n")])

    ents = clean_entities(ents)
    
    for ent in ents:    
        if ent.text not in entities_to_search_prev: 
            for (index, sentence) in sentence_dict.items():
                if sent_contains_ent(sentence, ent):
                    
                    sent = ""
                    for entities in sentence.ents: 
                        if entities.text == ent.text: 
                            sent = "*"
                            break

                    pos_ent = []
                    for subent in ent:
                        pos_ent.append(subent.pos_) 

                    sent = sent + first_upper(sentence.text.strip(" \n"))
                    if ent.text in entities_to_search and sent not in entities_to_search[ent.text] and "*"+sent not in entities_to_search[ent.text]:
                        entities_to_search[ent.text].append(sent)
                        entities_to_search_pos[ent.text].append(pos_ent)
                    elif ent not in entities_to_search:     
                        entities_to_search[ent.text] = [sent]
                        entities_to_search_pos[ent.text] = [pos_ent]                        

    entities_to_search = clean_entities_to_search(entities_to_search, entities_to_search_pos)

    return entities_to_search, sentence_dict

def clean_entities_to_search(entities_to_search: dict, entities_to_search_pos: dict):
    """ Clean the entities to search.

    Args:
        entities_to_search: dictionary with the entities to search
        entities_to_search_pos: dictionary with the entities to search and the pos of the words
    
    Returns:
        entities_to_search: dictionary with the entities to search cleaned
    """

    # unify entities written with the same words
    entities = list(entities_to_search.keys())
    entities_to_delete = []
    entities.sort(key= str.lower)

    for i in range(len(entities)):
        for j in range(i+1, len(entities)):
            if entities[i].lower() == entities[j].lower():
                if entities[i] > entities[j]:
                    entities_to_delete.append((entities[i], entities[j]))
                else: 
                    entities_to_delete.append((entities[j], entities[i]))

    for (entity_w, entity_r) in entities_to_delete:
        # merge snippet
        for snippet in entities_to_search[entity_w]:
            if snippet not in entities_to_search[entity_r] and "*"+snippet not in entities_to_search[entity_r]:
                entities_to_search[entity_r].append(snippet)
        # remove entity
        del entities_to_search[entity_w]

    entities_to_delete = []
    # delete entities that are nouns or adjectives
    for entity in entities_to_search:
        if len(entities_to_search_pos[entity][0]) == 1: 
            is_noun = True
            for pos in entities_to_search_pos[entity]:
                if pos[0] != "NOUN" and pos[0] != "ADJ":
                    is_noun = False
            if is_noun: 
                entities_to_delete.append(entity)

    print("DA ELIMINARE: ", entities_to_delete)
    for entity in entities_to_delete:
        del entities_to_search[entity]
    
    return entities_to_search

def clean_entities_to_search2(entities_to_search: dict): # TODO: delete??
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

def clean_entities(entities: list):
    """ Clean the entities from the text with only entities useful.

    Args:
        entities: list of entities to clean
    Returns:
        entities_clean: list of the entities useful for the search
    """

    entities_clean = []
    for ent in entities:
        if ent.label_ == "LOC" or ent.label_ == "FAC": 

            if len(ent) > 0 and ent[0].pos_ == "DET": 
                ent = ent[1:]
            
            if len(ent) > 0 and ent[0].pos_ == "ADP":
                ent = ent[1:]

            if len(ent) > 0 and ent[-1].pos_ == "ADP": 
                ent = ent[:-1] 

            if len(ent) > 0 and ispunct(ent.text[-1]): # delete punctuation at the end of the entity 
                if ispunct(ent.text[0]) and ent.text[0] == ent.text[-1]: 
                    print("prima: ", ent)
                    ent = ent[1:-1]
                    print("corretta: ", ent)
                else: 
                    if ent.text.count(ent.text[-1]) == 1:
                        ent = ent[:-1]
            
            if len(ent) > 0 and ent.text.__contains__("#"): 
                begin = ent.start
                end = ent.end
                if ent[-1].text == "#": 
                    end = end - 1 
                else: 
                    begin = begin + 1 
                
                ent = ent.doc[begin: end]
                #print("ENTITY CORRETTA: ", ent)

            if len(ent) > 0 and ent.text.__contains__("^"):
                begin = ent.start
                end = ent.end
                if ent[-1].text == "^": 
                    end = end - 1 
                else: 
                    begin = begin + 1 
                
                ent = ent.doc[begin: end]
                #print("ENTITY CORRETTA: ", ent)
                
            if len(ent) > 0: 
                if ent.text.count("\"") == 1:
                    nbor = ent[-1].nbor()
                    doc = ent.doc 
                    
                    while nbor.text != "\"":
                        nbor = nbor.nbor()
                    
                    nbor = nbor.nbor()
                    start_ent = ent.start
                    end_ent = nbor.i

                    span = doc[start_ent: end_ent]
                    new_ent = span.char_span(0, len(span.text), label="LOC")
                    #print("ENTITY COMPLETA: ", new_ent)
                    entities_clean.append(new_ent)
                else:     
                    entities_clean.append(ent)

    return entities_clean

def find(s, ch):
    """ Find all the indexes of the character ch in the string s.

    Args:
        s: string where to search
        ch: character to search
    
    Returns:
        list of the indexes of the character ch
    """
    return [i for i, ltr in enumerate(s) if ltr == ch]

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

def correct_bulleted_split(doc: Doc): 
    """ Correct the bullet split in the sentences.

    Args:
        sentence_list: list of the sentences to correct
    
    Returns:
        sentence_list: list of the sentences corrected
    """

    sentences_correct = []
    begin = 0
    indexes = find_indexes(doc, "#")
    if len(indexes) > 0:
        for elem in indexes:
            section = doc[begin:elem].as_doc()
            if len(section) > 0: 
                #print("\n \n SEZIONE: ", section.text)
                indexes_bullet = find_indexes(section, "^")
                if len(indexes_bullet) > 1:
                    j = 0
                    for index_bullet in indexes_bullet:
                        sentence = section[j: index_bullet]
                        #print("frase elenco puntato: ", sentence)
                        if len(sentence) > 0:
                            sentences_correct.append(sentence)
                        j = index_bullet + 1
                else: 
                    sentences_section = section.sents
                    sentences_correct.extend(sentences_section)
            
            begin = elem + 1

    return sentences_correct
    

def generate_sentences_dictionary(doc: Doc):
    """ Generate a dictionary with the snippet index and the snippet itself.
    
    Args:
        doc: document to generate the dictionary
    Returns:
        sentence_dict: dictionary with the index of the sentence and the index in the text
    """

    sentences_dict = {}
    sentences = correct_bulleted_split(doc)
    for index, sentence in enumerate(sentences): 
        sentences_dict[index] = sentence

    return sentences_dict

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

    return features

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

def create_whitelist(headlines: list): # TODO: AGGIUSTARE QUESTA LISTA!
    """ Create the whitelist of words to capitalize in the text. 
    
    Args:
        headlines: list of headlines to analyze

    Returns:
        whitelist: list of words to capitalize
    """

    nlp = spacy.load("it_core_news_sm")

    whitelist = []

    for headline in headlines:
        words = headline.split(" ")

        if len(words) == 1: 
            doc = nlp(words[0])
            lemma =  doc[0].lemma_
            if lemma == "musei": 
                lemma = "museo"
            elif lemma == "parchi": 
                lemma = "parco"
            elif lemma == "teatri": 
                lemma = "teatro"
            if lemma != "storia" and lemma != "territorio" and lemma != "gemellaggio" and lemma != "cucina":
                whitelist.append(lemma)

    whitelist.append("chiesa")
    whitelist.append("giardino")

    return whitelist

def not_headline_chiarimento(css_class): 
    return css_class and css_class != "chiarimento"

def clean_html(soup: BeautifulSoup):
    """ Clean html from soup
    
    Args:
        soup: soup to clean
    
    Returns:
        soup cleaned
    """
    
    #Delete all the parts that are not meaningful

    # References in the text 

    references = soup.find_all('sup', class_='reference') 

    for ref in references:
        ref.decompose() 

    no_fonte = soup.find_all('sup', class_='noprint chiarimento-apice') 

    for ref in no_fonte:
        ref.decompose() 

    # Figcaption with text
    figcaptions = soup.find_all('figcaption')
    for figcaption in figcaptions: 
        figcaption.decompose() 

    figcaptions_div = soup.find_all('div', class_='thumbcaption')
    for figcaption in figcaptions_div:
        figcaption.decompose()

    # Headings
    headings = soup.find_all('h2', id=True)
    for heading in headings:
        heading.decompose() 

    # From Note to the end of the page
    note = soup.find('span', id='Note')

    parent_tag = note.parent
    for sibling in parent_tag.find_next_siblings():
        sibling.decompose()

    headlines = []
    # Span HEADLINE!
    for span in soup.find_all('span', class_ = 'mw-headline'):
        headlines.append(span.string)

    white_list = create_whitelist(headlines)

    print("headlines: ", white_list)

    # delete other spans

    for span in soup.find_all('span', class_ = not_headline_chiarimento):
        span.decompose()
        

    # Table
    for table in soup.find_all('table'):
        table.decompose()

    # bullets not meaningful
    bullets_to_delete = soup.find_all(['ul', 'ol'], class_=True) 
    for bullet in bullets_to_delete:
        bullet.decompose()

    return soup, white_list

def add_punct_bullets(soup: BeautifulSoup): 
    """ Add punctuation to the bullets
    
    Args:
        soup: soup to clean
    
    Returns:
        soup cleaned
    """
    tag = soup.find_all(['ul', 'ol'], class_=False)

    not_punct = ['"',"'", '(', ')','[',']', ' ']
    for t in tag:
        sub_tag = t.find_all("li", class_=False) 
        if len(sub_tag) > 1:
            t.insert(0, " # ")
            for s in sub_tag[:-1]: 
                s.insert(0, " ^ ")
                if not s.text[-1] in string.punctuation or s.text[-1] in not_punct:
                    s.append(" ;")

            sub_tag[-1].insert(0, " ^ ") 
            if not sub_tag[-1].text[-1] in string.punctuation or sub_tag[-1].text[-1] in not_punct:
                sub_tag[-1].append(" .")
            
            sub_tag[-1].insert_after(" ", " # ")

    return soup

def substitute_whitelist(text: str, whitelist: list):
    """ Substitute the whitelist in the text. 
    
    Args:
        text: text to clean
        whitelist: whitelist of words to substitute
    
    Returns:
        text cleaned
    """
    
    for word in whitelist:
        text = re.sub(r'\b{}\b'.format(word), word.capitalize(), text)

    return text

def wiki_content(title: str, context = False):
    """ Search title page in wikipedia with MediaWiki API.

    Args: 
        title: str Wikipedia page title
        context: boolean if true is searched also the location of the context
    Returns:
        Wikipedia page content cleaned  
    """
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"

    params = {
        "action": "parse",
        "page": title,
        "format": "json",
        "prop": "text",
        "formatversion": "2"
    }

    response = session.get(url=url_api, params=params)
    data = response.json()
    content = data['parse']['text']
    soup = BeautifulSoup(content, features="lxml")
    
    with open(f'response/wikiPageContent/{title}_htmlnotcleaned.txt', 'w', encoding='utf-8') as f:
        f.write(soup.prettify())

    soup, white_list = clean_html(soup)

    soup = add_punct_bullets(soup)

    cleaned_content = re.sub(r'\n+', '\n', soup.text.strip('\n')) #soup.get_text(' ',strip=True)

    cleaned_content = substitute_whitelist(cleaned_content, white_list)
    
    cleaned_content = cleaned_content.replace("“", "\"").replace("”", "\"")

    with open(f'response/wikiPageContent/{title}_htmlcleaned.txt', 'w', encoding='utf-8') as f:
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