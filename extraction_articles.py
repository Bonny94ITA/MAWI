from src.preprocessing import fetch_article


import wikipediaapi
# mi conviene mettere da parte tutti i link che ha la pagina con altre pagine

path_articles1_names = f'input/articles1/articles1_names.txt'

titles_articles_ita = []
titles_articles_eng = []

with open(path_articles1_names, 'r', encoding='utf-8') as f:
    f.readline()
    line = f.readline().strip()
    while line != "#ENG":
        titles_articles_ita.append(line)
        line = f.readline().strip()
    
    line = f.readline().strip()
    while line:
        titles_articles_eng.append(line)
        line = f.readline().strip()

# Fetch articles from Wikipedia

for title in titles_articles_ita:
    print("Current page to analyze: ", title)
    fetch_article(title, "it", "input/articles1/ita/links/", "input/articles1/ita/texts/")

