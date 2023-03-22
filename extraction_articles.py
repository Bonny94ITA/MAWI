from src.preprocessing import fetch_article

path_articles1_names = f'input/articles1/articles1_names.txt'

titles_articles_it = []
titles_articles_en = []

with open(path_articles1_names, 'r', encoding='utf-8') as f:
    f.readline()
    line = f.readline().strip()
    while line != "#EN":
        titles_articles_it.append(line)
        line = f.readline().strip()
    
    line = f.readline().strip()
    while line:
        titles_articles_en.append(line)
        line = f.readline().strip()

# Fetch articles from Wikipedia

for title in titles_articles_it:
    print("Current page to analyze: ", title)
    fetch_article(title, "it", "input/articles1/it/links/", "input/articles1/it/texts/")

for title in titles_articles_en:
    print("Current page to analyze: ", title)
    fetch_article(title, "en", "input/articles1/en/links/", "input/articles1/en/texts/")

