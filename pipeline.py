from src.model import create_model, get_lang
from src.preprocessing import wiki_content, get_context
from src.entities import get_entities_snippet
from src.location import search_entities_geopy
from src.utils import get_nearby_pages, save_results, get_further_information, read_article

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

path_articles1_ita = f'input/articles1/ita/texts/'

titles_articles = [("Torino", "it")]

for (title, lang) in titles_articles:
    # Read wiki articles from file
    path_article = path_articles1_ita+title+".txt"
    text = read_article(path_article)
    #text, context = wiki_content(city, True)

    context = get_context(title, lang)

    nlp = create_model(lang)

    doc = nlp(text)

    print(context)

    geographic_scope = title # TODO: implementare algoritmo per individuarlo

    # Get entities without duplicates
    searchable_entities, sentence_dict = get_entities_snippet(doc)

    searchable_entities = get_further_information(searchable_entities, geographic_scope)

    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, context, geographic_scope)

    # Search nearby pages -> TODO: da aggiungere?

    save_results(features, context)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    name_context = context['name']
    file_path_entities_complete = f'results/extraction_entities_snippet/{name_context}_entities.txt'

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