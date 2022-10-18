from utils.utils import get_entities_snippet, search_entities, search_entities, wiki_content, get_context
import spacy
import json


nlp = spacy.load("it_core_news_sm")

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

cities = ["Torino"]

for city in cities:
    # Read wiki pages
    text, location = wiki_content(city, True)
    doc = nlp(text)

    f = open('./assets/italian_cities_new.json')
    cities_json = json.load(f)
    f.close()
    
    cities = [city['AccentCity'] for city in cities_json]

    print(cities[:10])
    #counter, context, loc_context = get_context(doc, italian_cities, "name")

    print(location)

    # Get entities without duplicates
    searchable_entities = get_entities_snippet(doc, cities)

    print("number of entities: ", len(searchable_entities))

    # Search addresses with Google
    search_entities(searchable_entities, location, city)
