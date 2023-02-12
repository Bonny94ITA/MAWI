from src.model import create_model
from src.preprocessing import wiki_content
from src.entities import get_entities_snippet
from src.location import search_entities_geopy
from src.utils import get_nearby_pages, save_results, get_further_information2, get_further_information

#cities = ["Torino", "Roma", "Bologna", "Milano", "Liberty a Torino", "Barocco a Milano"]

cities = ["Torino"]
nlp = create_model()

for city in cities:
    # Read wiki pages
    text, context = wiki_content(city, True)

    doc = nlp(text)

    print(context)

    # Get entities without duplicates
    searchable_entities, sentence_dict = get_entities_snippet(doc)

    searchable_entities = get_further_information(searchable_entities, city)

    # Search addresses with Google
    features, entities_final = search_entities_geopy(searchable_entities, context, city)

    # nearby pages

    nearby_pages = get_nearby_pages(city)

    print(nearby_pages)
    
    for page in nearby_pages:
        print("Current page to analyze: ", page)
        text = wiki_content(page)
        doc = nlp(text)

        searchable_entities, _ = get_entities_snippet(doc, searchable_entities)

        searchable_entities = get_further_information(searchable_entities, city)

        features, _ = search_entities_geopy(searchable_entities, context, city, features)
    
    # TODO: fare in modo che i risultati ottenuti dall'analisi di altre pagine vengano in qualche modo inclusi 
    # nei risultati precedenti

    save_results(features, context)

    print("number of entities: ", len(searchable_entities))

    entities_complete = list(searchable_entities.keys())
    entities_complete.sort(key= str.lower)
    name_context = context['name']
    file_path_entities_complete = f'response/spacy_pipeline/{name_context}_entities.txt'

    with open(file_path_entities_complete, 'w', encoding='utf-8') as f:
        for entity in entities_complete:
            f.write(entity + '\n')


    ## Further analysis

    #snippet_ent = get_further_information2(entities_final)

    #file_path_snippet_ent = f'response/spacy_pipeline/Snippet_entities.txt'

    #with open(file_path_snippet_ent, 'w', encoding='utf-8') as f:
    #    for key, snippet in snippet_ent.items():
    #        f.write(key +'\n')
    #        if snippet is None: 
    #            f.write('No snippet available' + '\n')
    #        else: 
    #            f.write(snippet + '\n')

