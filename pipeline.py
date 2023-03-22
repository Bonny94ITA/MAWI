from src.model import create_model, get_lang
from src.preprocessing import wiki_content, get_context
from src.entities import get_entities_snippet
from src.location import search_entities_geopy
from src.utils import get_nearby_pages, save_results, get_further_information, read_article

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

path_articles1_ita = f'input/articles1/ita/texts/'

cities = ["Torino"]
# TODO: non parto più da una lista di città ma da una lista di pagine di Wikipedia già estratte 

# TODO: cambiare nomi alle cartelle: "response" -> "results", "spacy_pipeline" -> "extraction_entites_snippet", wikiPageContent -> sostituita da input

for city in cities:
    # Read wiki pages

    text = read_article(path_articles1_ita+city+".txt")
    #text, context = wiki_content(city, True)
    
    lang = get_lang(text) # adesso lo saprò prima senza questa fase

    context = get_context(city, lang)

    nlp = create_model(lang)

    doc = nlp(text)

    print(context)

    # Get entities without duplicates
    searchable_entities, sentence_dict = get_entities_snippet(doc)

    searchable_entities = get_further_information(searchable_entities, city)

    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, context, city)

    nearby_pages = get_nearby_pages(city)

    print(nearby_pages)
    
    for page in nearby_pages:
        print("Current page to analyze: ", page)
        text = wiki_content(page) # TO DO : sostituire con la funzione read_article????
        doc = nlp(text)

        searchable_entities, _ = get_entities_snippet(doc, searchable_entities)

        searchable_entities = get_further_information(searchable_entities, city)

        features, _ = search_entities_geopy(searchable_entities, context, city, features)

    save_results(features, context)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    name_context = context['name']
    file_path_entities_complete = f'results/spacy_pipeline/{name_context}_entities.txt'

    with open(file_path_entities_complete, 'w', encoding='utf-8') as f:
        for entity in entities_complete:
            f.write(entity + '\n')
