from spacy.tokens import Span

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
        if entity[0].text.lower() == sentence[j].text.lower(): 
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