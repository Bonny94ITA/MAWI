from utils.utils import count_occurrences, get_entities_snippet2, search_entities, search_entities, wiki_content, read_text_file
import spacy
import json


nlp = spacy.load("it_core_news_sm")

cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

for city in cities:
    # Read wiki pages
    text = wiki_content(city)
    doc = nlp(text)

    # Opening JSON file
    f = open('./assets/italian_cities.json')
    italian_cities = json.load(f)
    f.close()
    
    # Count occurrences
    counter = count_occurrences(doc, italian_cities, "name")  
    
    # Max occurrence
    context = max(counter, key=counter.get) 
    print(context)

    # Get entities without duplicates
    searchable_entities = get_entities_snippet2(doc, counter)

    print("number of entities: ", len(searchable_entities))

    # Search addresses with Google
    search_entities(searchable_entities, context, city)
