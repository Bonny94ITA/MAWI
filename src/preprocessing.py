from bs4 import BeautifulSoup
import re
import string
import requests
import wikipediaapi
from os.path import exists

from src.utils import get_polygon


def create_whitelist(): 
    """ Create the whitelist of words to capitalize in the text. 
    
    Args:
        headlines: list of headlines to analyze

    Returns:
        whitelist: list of words to capitalize
    """
    whitelist = ['strada', 'cimitero', 'teatro', 'mercato', 'parco', 'università', 'museo', 'cinema', 'aeroporto', 'chiesa', 'giardino', 'ospedale']

    return whitelist

def not_headline_chiarimento(css_class): 
    return css_class and css_class != "chiarimento"

def clean_html(soup: BeautifulSoup):
    """ Clean html from soup
    
    Args:
        soup: soup to clean
    
    Returns:
        soup cleaned
    """
    
    #Delete all the parts that are not meaningful

    # References in the text 

    references = soup.find_all('sup', class_='reference') 

    for ref in references:
        ref.decompose() 

    no_fonte = soup.find_all('sup', class_='noprint chiarimento-apice') 

    for ref in no_fonte:
        ref.decompose() 

    # Figcaption with text
    figcaptions = soup.find_all('figcaption')
    for figcaption in figcaptions: 
        figcaption.decompose() 

    figcaptions_div = soup.find_all('div', class_='thumbcaption')
    for figcaption in figcaptions_div:
        figcaption.decompose()

    # Headings
    headings = soup.find_all('h2', id=True)
    for heading in headings:
        heading.decompose() 

    # From Note to the end of the page
    note = soup.find('span', id='Note')

    if note:
        parent_tag = note.parent
        for sibling in parent_tag.find_next_siblings():
            sibling.decompose()

    headlines = []
    # Span HEADLINE!
    for span in soup.find_all('span', class_ = 'mw-headline'):
        headlines.append(span.string)

    white_list = create_whitelist()

    # delete other spans

    for span in soup.find_all('span', class_ = not_headline_chiarimento):
        span.decompose()
        

    # Table
    for table in soup.find_all('table'):
        table.decompose()

    # bullets not meaningful
    bullets_to_delete = soup.find_all(['ul', 'ol'], class_=True) 
    for bullet in bullets_to_delete:
        bullet.decompose()

    return soup, white_list

def add_punct_bullets(soup: BeautifulSoup): 
    """ Add punctuation to the bullets
    
    Args:
        soup: soup to clean
    
    Returns:
        soup cleaned
    """
    tag = soup.find_all(['ul', 'ol'], class_=False)

    not_punct = ['"',"'", '(', ')','[',']', ' ']
    for t in tag:
        sub_tag = t.find_all("li", class_=False) 
        if len(sub_tag) > 1:
            t.insert(0, " # ")
            for s in sub_tag[:-1]: 
                s.insert(0, " ^ ")
                if not s.text[-1] in string.punctuation or s.text[-1] in not_punct:
                    s.append(" ;")

            sub_tag[-1].insert(0, " ^ ") 
            if not sub_tag[-1].text[-1] in string.punctuation or sub_tag[-1].text[-1] in not_punct:
                sub_tag[-1].append(" .")
            
            sub_tag[-1].insert_after(" ", " # ")

    return soup

def substitute_whitelist(text: str, whitelist: list):
    """ Substitute the whitelist in the text. 
    
    Args:
        text: text to clean
        whitelist: whitelist of words to substitute
    
    Returns:
        text cleaned
    """
    
    for word in whitelist:
        text = re.sub(r'\b{}\b'.format(word), word.capitalize(), text)

    return text

def fetch_article(title: str, lang: str, path_save_links: str, path_save_text: str):
    session = requests.Session()
    url_api = "https://"+lang+".wikipedia.org/w/api.php"
    article_text = f""+path_save_text+title+".txt"
    article_links = f""+path_save_links+title+"_links.txt"
    
    if not exists(article_text): 

        # Get text
        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "prop": "text",
            "formatversion": "2"
        }

        response = session.get(url=url_api, params=params)
        data = response.json()
        content = data['parse']['text']
        soup = BeautifulSoup(content, features="lxml")

        soup, white_list = clean_html(soup)
        soup = add_punct_bullets(soup)
        cleaned_content = "\n".join([string for string in soup.text.split('\n') if string != '' and string != ' '])
        cleaned_content = substitute_whitelist(cleaned_content, white_list)
        cleaned_content = cleaned_content.replace("“", "\"").replace("”", "\"")

        with open(article_text, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

        # Get links
        wiki = wikipediaapi.Wikipedia(lang)
        page = wiki.page(title)
        keys = list(page.links.keys())

        with open(article_links, 'w', encoding='utf-8') as f: 
            f.writelines(keys)



def wiki_content(title: str, context = False):
    """ Search title page in wikipedia with MediaWiki API.

    Args: 
        title: str Wikipedia page title
        context: boolean if true is searched also the location of the context
    Returns:
        Wikipedia page content cleaned  
        Location of the context if context is True
    """

    file_content = f'response/wikiPageContent/{title}.txt'
    session = requests.Session()
    url_api = "https://it.wikipedia.org/w/api.php"
    
    if exists(file_content): 
        with open(file_content, "r", encoding='utf-8') as f: 
            cleaned_content = f.read()
    else: 

        params = {
            "action": "parse",
            "page": title,
            "format": "json",
            "prop": "text",
            "formatversion": "2"
        }

        response = session.get(url=url_api, params=params)
        data = response.json()
        content = data['parse']['text']
        soup = BeautifulSoup(content, features="lxml")

        soup, white_list = clean_html(soup)

        soup = add_punct_bullets(soup)

        cleaned_content = "\n".join([string for string in soup.text.split('\n') if string != '' and string != ' '])

        cleaned_content = substitute_whitelist(cleaned_content, white_list)
        
        cleaned_content = cleaned_content.replace("“", "\"").replace("”", "\"")

        with open(file_content, 'w', encoding='utf-8') as f:
            f.write(cleaned_content)

    if context: 
        params_coord = {
            "action": "query",
            "prop": "coordinates",
            "titles": title,
            "formatversion": "2",
            "format": "json"
        }

        response_coord = session.get(url=url_api, params=params_coord)
        data_coord = response_coord.json()

        print(data_coord)

        coordinates = data_coord['query']['pages'][0]['coordinates']
        location = {"name": title, 
                    "latitude": coordinates[0]['lat'], 
                    "longitude": coordinates[0]['lon'], 
                    "polygon": get_polygon(title)}
    
        return cleaned_content, location
    
    else: 
        return cleaned_content

