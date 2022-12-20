import csv 
import string

from spacy.tokens import Doc 
from spacy.tokens import Span

from src.sentences import first_upper, sent_contains_ent
from utils_2 import find_indexes

def get_entities_snippet(document: Doc, entities_to_search_prev = dict()):
    """ Get the entities from the nlp_text which are not cities and print snippet in which
        they appears.

    Args:
        document: spacy text
        entities_to_search_prev: dictionary with the entities to search of the previous text and do not search again
    
    Returns:
        entities_to_search: dictionary with the entities and the snippet in which they appear
        sentence_dict: dictionary with the index of the sentence in the text and the sentence itself
    """

    entities_to_search = dict()
    entities_to_search_pos = dict()
    ents = list(document.ents)
    sentence_dict = generate_sentences_dictionary(document)

    with open('Sentences.csv', 'w', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        for index, sent in sentence_dict.items():
            writer.writerow([index, sent.text.strip(" \n")])

    ents = clean_entities(ents)
    
    for ent in ents:    
        if ent.text not in entities_to_search_prev: 
            for (index, sentence) in sentence_dict.items():
                if sent_contains_ent(sentence, ent):
                    
                    sent = ""
                    for entities in sentence.ents: 
                        if entities.text == ent.text: 
                            sent = "*"
                            break

                    pos_ent = []
                    for subent in ent:
                        pos_ent.append(subent.pos_) 

                    sent = sent + first_upper(sentence.text.strip(" \n"))
                    if ent.text in entities_to_search and sent not in entities_to_search[ent.text] and "*"+sent not in entities_to_search[ent.text]:
                        entities_to_search[ent.text].append(sent)
                        entities_to_search_pos[ent.text].append(pos_ent)
                    elif ent not in entities_to_search:     
                        entities_to_search[ent.text] = [sent]
                        entities_to_search_pos[ent.text] = [pos_ent]                        

    entities_to_search = clean_entities_to_search(entities_to_search, entities_to_search_pos)

    return entities_to_search, sentence_dict

def ispunct(ch):
    return ch in string.punctuation

def clean_begin_entity(ent: Span):
    """ Clean the begin of the entity if contains article or adposition at the begining.

    Args:
        ent: entity to clean
    Returns:
        ent: entity cleaned
    """

    if len(ent) > 0 and ent[0].pos_ == "DET": 
        ent = ent[1:]
            
    if len(ent) > 0 and ent[0].pos_ == "ADP":
        ent = ent[1:]
    
    return ent

def clean_end_entity(ent: Span): 

    if len(ent) > 0: 
        if ent[-1].pos_ == "ADP": 
            ent = ent[:-1] 

        if ispunct(ent.text[-1]) and not ispunct(ent.text[0]) and ent.text.count(ent.text[-1]) == 1:
            ent = ent[:-1]

    return ent

def clean_bullet(ent: Span): 
    """ Clean the entity if is bulleted point. 

    Args:
        ent: entity to clean
    Returns:
        ent: entity cleaned
    """

    if len(ent) > 0 and ent.text.__contains__("#"): 
        begin = ent.start
        end = ent.end
        if ent[-1].text == "#": 
            end = end - 1 
        else: 
            begin = begin + 1 
        
        ent = ent.doc[begin: end]

    if len(ent) > 0 and ent.text.__contains__("^"):
        begin = ent.start
        end = ent.end
        if ent[-1].text == "^": 
            end = end - 1 
        else: 
            begin = begin + 1 
        
        ent = ent.doc[begin: end]

    return ent

def check_well_formed(ent: Span): 
    """ Check if the entity is well formed.

    Args:
        ent: entity to check
    Returns:
        ent if is well formed, new_ent otherwise
    """


    if len(ent) > 0: 
        if ent.text.count("\"") == 1:
            nbor = ent[-1].nbor()
            doc = ent.doc 
            
            while nbor.text != "\"":
                nbor = nbor.nbor()
            
            nbor = nbor.nbor()
            start_ent = ent.start
            end_ent = nbor.i

            span = doc[start_ent: end_ent]
            new_ent = span.char_span(0, len(span.text), label="LOC")
            return new_ent
    
    return ent

def clean_entities(entities: list):
    """ Clean the entities from the text with only entities useful.

    Args:
        entities: list of entities to clean
    Returns:
        entities_clean: list of the entities useful for the search
    """

    entities_clean = []
    for ent in entities:
        if ent.label_ == "LOC" or ent.label_ == "FAC": 
            ent = clean_begin_entity(ent)
            ent = clean_end_entity(ent)

            if len(ent) > 0 and ispunct(ent.text[-1]) and ispunct(ent.text[0]) and ent.text[0] == ent.text[-1]: 
                print("prima: ", ent)
                ent = ent[1:-1]
                print("corretta: ", ent)
                
            ent = clean_bullet(ent)
            ent = check_well_formed(ent)
            entities_clean.append(ent)

    return entities_clean

def clean_entities_to_search(entities_to_search: dict, entities_to_search_pos: dict):
    """ Clean the entities to search.

    Args:
        entities_to_search: dictionary with the entities to search
        entities_to_search_pos: dictionary with the entities to search and the pos of the words
    
    Returns:
        entities_to_search: dictionary with the entities to search cleaned
    """

    # unify entities written with the same words
    entities = list(entities_to_search.keys())
    entities_to_delete = []
    entities.sort(key= str.lower)

    for i in range(len(entities)):
        for j in range(i+1, len(entities)):
            if entities[i].lower() == entities[j].lower():
                if entities[i] > entities[j]:
                    entities_to_delete.append((entities[i], entities[j]))
                else: 
                    entities_to_delete.append((entities[j], entities[i]))

    for (entity_w, entity_r) in entities_to_delete:
        # merge snippet
        for snippet in entities_to_search[entity_w]:
            if snippet not in entities_to_search[entity_r] and "*"+snippet not in entities_to_search[entity_r]:
                entities_to_search[entity_r].append(snippet)
        del entities_to_search[entity_w]

    entities_to_delete = []
    # delete entities that are nouns or adjectives
    for entity in entities_to_search:
        if len(entities_to_search_pos[entity][0]) == 1: 
            is_noun = True
            for pos in entities_to_search_pos[entity]:
                if pos[0] != "NOUN" and pos[0] != "ADJ":
                    is_noun = False
            if is_noun: 
                entities_to_delete.append(entity)

    print("DA ELIMINARE: ", entities_to_delete)
    for entity in entities_to_delete:
        del entities_to_search[entity]
    
    return entities_to_search

def generate_sentences_dictionary(doc: Doc):
    """ Generate a dictionary with the snippet index and the snippet itself.
    
    Args:
        doc: document to generate the dictionary
    Returns:
        sentence_dict: dictionary with the index of the sentence and the index in the text
    """

    sentences_dict = {}
    sentences = correct_bulleted_split(doc)
    for index, sentence in enumerate(sentences): 
        if sentence.text != " " and sentence.text != "\n":
            sentences_dict[index] = sentence

    return sentences_dict

def correct_bulleted_split(doc: Doc): 
    """ Correct the bullet split in the sentences.

    Args:
        sentence_list: list of the sentences to correct
    
    Returns:
        sentence_list: list of the sentences corrected
    """

    sentences_correct = []
    begin = 0
    indexes = find_indexes(doc, "#")
    if len(indexes) > 0:
        for elem in indexes:
            section = doc[begin:elem].as_doc()
            if len(section) > 0: 
                indexes_bullet = find_indexes(section, "^")
                if len(indexes_bullet) > 1:
                    j = 0
                    for index_bullet in indexes_bullet:
                        sentence = section[j: index_bullet]
                        if len(sentence) > 0:
                            sentences_correct.append(sentence)
                        j = index_bullet + 1
                else: 
                    sentences_section = [sent for sent in section.sents if sent.text != " "]
                    sentences_correct.extend(sentences_section)
            
            begin = elem + 1

    return sentences_correct