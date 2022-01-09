import os.path as path

main_home = '.'
date_time_format = '%Y-%m-%d.%H-%M-%S'
time_format = '%H-%M-%S'
date_format = '%Y-%m-%d'
database_path = path.join(main_home, 'words.db')
model_path = path.join(main_home, 'models')
data_path = path.join(main_home, 'data')
html_cache_path = path.join(data_path, 'html')
old_english_word_json = path.join(data_path, 'kaikki.org-dictionary-OldEnglish.json')
modern_english_word_json = path.join(data_path, 'kaikki.org-dictionary-English.json')

# Web Settings
cache_html = True
offline_mode = False
