from utils.utils import get_entities_snippet, search_entities, search_entities, wiki_content, get_context
import spacy
import json


nlp = spacy.load("it_core_news_sm")

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

cities = ["Torino"]

for city in cities:
    # Read wiki pages
    text = wiki_content(city)
    doc = nlp(text)

    f = open('./assets/italian_cities_new.json')
    italian_cities = json.load(f)
    f.close()
    
    counter, context, loc_context = get_context(doc, italian_cities, "AccentCity")

    print(context)

    # Get entities without duplicates
    searchable_entities = get_entities_snippet(doc, counter)

    print("number of entities: ", len(searchable_entities))

    # Search addresses with Google
    search_entities(searchable_entities, loc_context, city)
