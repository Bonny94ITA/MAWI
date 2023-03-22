from src.utils import get_list_names, get_summary_names, get_genders_names, save_results_extension
from src.location import get_location_names


file_names = f"results/extension/Torino_names.txt"
file_result = f'results/extension/Torino_names.json'

names = get_list_names(file_names)

summaries = get_summary_names(names)

genders = get_genders_names(summaries)

locations_names = get_location_names(genders)



save_results_extension(file_result, locations_names)



