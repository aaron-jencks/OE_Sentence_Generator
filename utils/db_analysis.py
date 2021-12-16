import json
from controllers.sql import SQLController
from typing import List
from controllers.ui import debug
from settings import old_english_word_json


def load_words_and_objects(selection_criteria: str) -> List[object]:
    cont = SQLController.get_instance()

    debug('Loading wiktionary lines')
    with open(old_english_word_json, mode='rb') as fp:
        wiktionary_lines = fp.read().decode('utf8').splitlines(keepends=False)

    debug('Extracting database selection')
    selection = cont.select_conditional('old_english_words', 'name, wiktionary_entry', selection_criteria)

    debug('Loading json objects')
    objects = [json.loads(wiktionary_lines[line]) for _, line in selection]

    debug('Words Loaded Successfully')
    return objects
