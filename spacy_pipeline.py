from utils.utils import get_entities_snippet, search_entities, wiki_content, get_nearby_pages, save_results
import spacy
import json


nlp = spacy.load("it_core_news_sm")

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

cities = ["Torino"]

for city in cities:
    # Read wiki pages
    text, context = wiki_content(city, True)
    doc = nlp(text)

    f = open('./assets/italian_cities_new.json')
    cities_json = json.load(f)
    f.close()

    f2 = open('./assets/italian_cities.json')
    cities_json2 = json.load(f2)
    f2.close()
    
    cities = [city['AccentCity'] for city in cities_json]
    cities.extend([city['name'] for city in cities_json2])

    print(cities[:10])
    #counter, context, loc_context = get_context(doc, italian_cities, "name")

    print(context)

    # Get entities without duplicates
    searchable_entities = get_entities_snippet(doc, cities)

    print("number of entities: ", len(searchable_entities))

    # Search addresses with Google
    features = search_entities(searchable_entities, context, city)

    # nearby pages

    nearby_pages = get_nearby_pages(city)

    print(nearby_pages)

    for page in nearby_pages:
        text = wiki_content(page)
        doc = nlp(text)

        searchable_entities = get_entities_snippet(doc, cities, searchable_entities)

        features = search_entities(searchable_entities, context, city, features)

    save_results(features, context)


