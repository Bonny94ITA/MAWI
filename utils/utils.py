from bs4 import BeautifulSoup
import requests
import urllib
import json
import os
import time


# JSON indent
def jprint(obj):
    text = json.dumps(obj, sort_keys=True, indent=3)
    print(text)


def read_text_file(path):
    """Read a text file from a path.

    Args: 
        path: path to the file
    Returns:
        text: text read from the file in string format
    """
    
    with open(path) as f:
        lines = f.readlines()
    
    text = " ".join(str(line) for line in lines)

    return text


def count_occurrences(nlp_text, input_json, param_to_search):
    """Count occurences of the param to search of the input json in the
    nlp_text.

    Args:
        nlp_text: spacy text
        input_json: json file with the entities to search
        param_to_search: parameter to search in the json file
    
    Returns:
        counter: dictionary with the entities (cities name) to search and their occurences
    """
    counter = {}
    for ent in nlp_text.ents:
        for elem in input_json: 
            occurrence = elem[param_to_search] 
            if occurrence == ent.text: 
                if occurrence not in counter:
                    counter[occurrence] = 1
                else:
                    counter[occurrence] += 1
    return counter


def get_entities(nlp_text, counter):
    """ Get the entities from the nlp_text which are not cities.

    Args:
        nlp_text: spacy text
        counter: dictionary with the entities (cities name) to search and their occurences
    """
    searchable_entities = []
    sentence_dict = generate_sentences_dictionary(list(nlp_text.sents))
    for ent in nlp_text.ents:
        if ent.text not in counter: #se l'entità non è nel counter quindi non è una città
            #print("Text: ", ent.text,
                 # ent.start_char,
                  #ent.end_char, "\n",
                  #"Sentence index: ", sentence_dict[ent.start_char], "\n",
                  #"Sentence: ", list(nlp_text.sents)[sentence_dict[ent.start_char]])

            searchable_entities.append(ent.text)
    print(list(dict.fromkeys(searchable_entities)))
    return list(dict.fromkeys(searchable_entities))


def generate_sentences_dictionary(sentence_list):
    """ Generate a dictionary with the sentence index and the start char index.
    
    Args:
        sentence_list: list of sentences
    Returns:
        sentence_dict: dictionary with the index of the sentence and the index in the text
    """
    sentences_dict = {}
    first_char = 0
    for idx, sentence in enumerate(sentence_list):
        last_char = first_char + len(sentence) - 1
        
        while first_char <= last_char:
            sentences_dict[first_char] = idx
            first_char += 1

    return sentences_dict


def print_to_file(file_path, text_to_append):
    with open(file_path, "a", encoding="utf-8") as file:
        file.write(text_to_append + "\n")


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def search_with_google(searchable_entities, context):
    """ Search entities in Google.
    
    Args:
        searchable_entities: list of entities to search
        context: context of the search (city, country, etc.)
    """

    response_file_path = f"response/spacy_pipeline/{context}.txt"

    delete_file(response_file_path)

    for search_item in searchable_entities:
        text = urllib.parse.quote_plus(search_item + " " + context)
        URL = 'https://google.it/search?q=' + text + "&hl=it"

        print(URL)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        }

        s = requests.Session()
        page = s.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, 'html5lib')
        # print(soup)
        address = soup.find(class_='LrzXr')
        print("Address: ", address)

        activity = soup.find(class_='zloOqf', string="€")
        print("Activity: ", activity)

        print_to_file(response_file_path, '-' * 50)
        print_to_file(response_file_path, URL)
        if address:
            address = address.get_text()
            address = address.strip()
            print_to_file(
                response_file_path,
                f"Research term: {search_item}")
            print_to_file(response_file_path, f"Address: {address}")

        print_to_file(response_file_path, '-' * 50)

        time.sleep(.600)


def wiki_content(titles):
    """Search title page in wikipedia with MediaWiki API.

    Args: 
        titles: Wikipedia page title
    Returns:
        Wikipedia page content cleaned 
    """
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"

    params = {
        "action": "query",
        "format": "json",
        "prop": "extracts",
        "titles": titles,
        "formatversion": "2"
    }

    response = session.get(url=url_api, params=params)
    data = response.json()
    content = data['query']['pages'][0]['extract']
    soup = BeautifulSoup(content, features="lxml")
    cleaned_content = soup.get_text().replace('\n', '')

    with open(f'response/wikiPageContent/{titles}.txt', 'w', encoding='utf-8') as f:
        json.dump(cleaned_content, f, ensure_ascii=False)

    return cleaned_content
