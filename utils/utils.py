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
    text = ""
    with open(path) as f:
        lines = f.readlines()

    for line in lines:
        text += line
    return text


def count_occurrences(nlp_text, input_json, param_to_search):
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
    searchable_entities = []
    sentence_dict = generate_sentences_dictionary(list(nlp_text.sents))
    for ent in nlp_text.ents:
        if ent.text not in counter:

            print("Text: ", ent.text,
                  ent.start_char,
                  ent.end_char, "\n",
                  "Sentence index: ", sentence_dict[ent.start_char], "\n",
                  "Sentence: ", list(nlp_text.sents)[sentence_dict[ent.start_char]])

            searchable_entities.append(ent.text)

    return list(dict.fromkeys(searchable_entities))


def generate_sentences_dictionary(sentence_list):
    sentences_dict = {}
    first_char = 0
    for idx, sentence in enumerate(sentence_list):
        # print("Sentence: ", sentence)
        last_char = first_char + len(sentence) - 1
        # print("idx: ", len(sentence))

        while first_char <= last_char:
            sentences_dict[first_char] = idx
            first_char += 1

    return sentences_dict


def print_to_file(file_path, text_to_append):
    with open(file_path, "a") as file:
        file.write(text_to_append + "\n")


def delete_file(file_path):
    if os.path.exists(file_path):
        os.remove(file_path)


def search_with_google(searchable_entities, context):
    response_file_path = f"response/spacy_pipeline/{context}.txt"

    delete_file(response_file_path)

    for search_item in searchable_entities:
        text = urllib.parse.quote_plus(search_item + " " + context)
        URL = 'https://google.it/search?q=' + text + "&hl=it"

        # print(URL)

        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36',
        }

        s = requests.Session()
        page = s.get(URL, headers=headers)
        soup = BeautifulSoup(page.content, 'html5lib')
        print(soup)
        address = soup.find(class_='LrzXr')

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

    with open(f'response/wikiPageContent/{titles}.txt', 'w') as f:
        json.dump(cleaned_content, f, ensure_ascii=False)

    return cleaned_content
