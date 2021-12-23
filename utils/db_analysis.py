import json
from controllers.sql import SQLController
from typing import List, Dict
from controllers.ui import debug, error
from settings import old_english_word_json


def load_words_and_objects(selection_criteria: str) -> List[dict]:
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


def extract_tags(json_objects: List[dict]) -> List[List[str]]:
    tags = []
    for obj in json_objects:
        for sense in obj['senses']:
            if 'tags' in sense:
                tags.append(sense['tags'])
            else:
                error('{} has no tags list'.format(obj['word']))
    return tags


def extract_ipa(json_objects: List[dict]) -> List[str]:
    ipa = []
    for w in json_objects:
        if 'sounds' in w:
            found = False
            for s in w['sounds']:
                if 'ipa' in s:
                    ipa.append(s['ipa'])
                    found = True
            if not found:
                debug('No ipa translation found for {}'.format(w['word']))
        else:
            debug('No sounds found for {}'.format(w['word']))
    return ipa


def load_ipa(selection_criteria: str) -> List[str]:
    words = load_words_and_objects(selection_criteria)
    return extract_ipa(words)
