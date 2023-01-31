from spacy.tokens import Span, Doc
from src.utils import find_indexes

def sent_contains_ent(sentence: Span, entity: Span):
    """ Check if the sentence contains the entity.

    Args:
        sentence: sentence to check
        entity: entity to check
    Returns:
        True if the sentence contains the entity, False otherwise
    """
    possible_begins = []

    j = 0
    while j < len(sentence): 
        #print('Entity', entity)
        try:
            text_entity = entity[0].text.lower()
        except:
            print("Entity: ", entity)
        #print('Sentence', sentence)
        text_sentence = sentence[j].text.lower()
        if text_entity == text_sentence: 
            possible_begins.append(j)
        j += 1
    
    contains = False
    index = 0
    while not contains and index < len(possible_begins):
        contained_all = True
        i = 0
        j = possible_begins[index]
        while contained_all and i < len(entity) and j < len(sentence): 
            contained_all = (entity[i].text.lower() == sentence[j].text.lower())
            i += 1
            j += 1

        if i == len(entity) and contained_all:
            contains = True
        index += 1
    
    return contains

def first_upper(sentence: str):
    """ Make the first letter of the sentence uppercase.

    Args:
        sentence: sentence to modify

    Returns:
        sentence: sentence with the first letter uppercase
    """
    if sentence != "":
        sentence = sentence[0].upper() + sentence[1:]
    return sentence

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
