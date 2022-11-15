from utils.utils import get_entities_snippet, search_entities_geopy, wiki_content, get_nearby_pages, save_results
import spacy
import json


nlp = spacy.load("it_core_news_sm")


#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

cities = ["Torino"]

for city in cities:
    # Read wiki pages
    text, context = wiki_content(city, True)

    doc = nlp(text)

    cities1_path = f'assets/cities1.json'
    with open(cities1_path, 'r', encoding='utf-8') as f:
        cities_json = json.load(f)
    
    cities2_path = f'assets/cities2.json'
    with open(cities2_path, 'r', encoding='utf-8') as f:
        cities_json2 = json.load(f)
    
    cities = [city['name'] for city in cities_json]
    cities.extend([city['AccentCity'] for city in cities_json2])

    cities = list(set(cities))
    #counter, context, loc_context = get_context(doc, italian_cities, "name")

    print(context)

    # Get entities without duplicates
    searchable_entities, sentence_dict = get_entities_snippet(doc, cities) # da sentence_dict posso fare analisi

    print("number of entities: ", len(searchable_entities))

    # Search addresses with Google
    features = search_entities_geopy(searchable_entities, context, city)

    # nearby pages

    nearby_pages = get_nearby_pages(city)

    print(nearby_pages)
    """
    for page in nearby_pages:
        text = wiki_content(page)
        doc = nlp(text)

        searchable_entities = get_entities_snippet(doc, cities, searchable_entities)

        features = search_entities(searchable_entities, context, city, features)
    
    """
    save_results(features, context)


