from utils.utils import count_occurrences, get_entities_snippet, search_entities, search_entities, wiki_content, read_text_file
import spacy
import json


nlp = spacy.load("it_core_news_sm")
cities = ["Liberty a Torino", "Barocco a Milano"]

for city in cities:
    # Read wiki pages
    text = wiki_content(city)
    #text = read_text_file('assets/Extract_torino.txt')
    doc = nlp(text)

    sentence_list = list(doc.sents) 

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
    searchable_entities = get_entities_snippet(doc, counter)

    print("number of entities: ", len(searchable_entities))

    # Search addresses with Google
    search_entities(searchable_entities, context)
