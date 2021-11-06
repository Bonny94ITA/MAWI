import json

filtered_cities = []

with open('../assets/cities.json', encoding='utf8') as f:
    data = json.load(f)

    for element in data:
        if element['country_code'] == 'IT':
            filtered_cities.append(element)

with open('../assets/italian_cities.json', 'w') as f:
    json.dump(filtered_cities, f)
