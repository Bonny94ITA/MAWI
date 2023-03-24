from src.model import create_model, create_geocoder
from src.preprocessing import get_context
from src.entities import get_entities_snippet
from src.location import search_entities_geopy, get_geographic_scope
from src.utils import save_results, get_further_information, read_article

from datetime import datetime

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

path_articles1_it = f'input/articles1/it/texts/'
path_articles1_en = f'input/articles1/en/texts/'

titles_articles = [("Torino", "it")]

model_it = create_model("it")
model_en = create_model("en")

geocoder = create_geocoder()

for (title, lang) in titles_articles:
    # Read wiki articles from file
    path_article = path_articles1_it+title+".txt"
    startTime = datetime.now()
    text = read_article(path_article)
    print("Read article takes: ", str(datetime.now() - startTime))

    if lang == "it":
        nlp = model_it
    else:
        nlp = model_en

    doc = nlp(text)

    geographic_scope = get_geographic_scope(doc, lang, geocoder) # TODO: controllare che funzioni anche per gli articoli di tipo 2

    # Get entities without duplicates

    startTime = datetime.now()
    searchable_entities, sentence_dict = get_entities_snippet(doc)
    print("Get_entities_snippet method takes: ", str(datetime.now() - startTime))

    startTime = datetime.now()
    searchable_entities = get_further_information(searchable_entities, geographic_scope['name'], lang)
    print("Get_further_information method takes: ", str(datetime.now() - startTime))


    startTime = datetime.now()
    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, geographic_scope, title, lang, geocoder)
    print("search_entities_geopy method takes: ", str(datetime.now() - startTime)) # TODO: cercare di diminuire i tempi

    # Search nearby pages -> TODO: da aggiungere?

    save_results(features, title)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    file_path_entities_complete = f'results/extraction_entities_snippet/{title}_entities.txt'

    with open(file_path_entities_complete, 'w', encoding='utf-8') as f:
        for entity in entities_complete:
            f.write(entity + '\n')

"""
    
    nearby_pages = get_nearby_pages(city)


    print(nearby_pages)
    
    for page in nearby_pages:
        print("Current page to analyze: ", page)
        text = wiki_content(page) # TO DO : sostituire con la funzione read_article????
        doc = nlp(text)

        searchable_entities, _ = get_entities_snippet(doc, searchable_entities)

        searchable_entities = get_further_information(searchable_entities, city)

        features, _ = search_entities_geopy(searchable_entities, context, city, features)
"""