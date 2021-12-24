from controllers.sql import SQLController
from controllers.ui import debug, error
from utils.grammar import case_list, plurality_list, person_list, tense, mood, \
    long_syllable, separate_syllables, Gender, gender_list
from settings import old_english_word_json, modern_english_word_json

import json
from settings import data_path
from typing import List, Tuple, Dict
import os.path as path
from tqdm import tqdm
import re


etymology_names = ['inh', 'der']
language_codes = ['ang', 'en']


def initialize_database():
    cont = SQLController.get_instance()
    cont.reset_database()

    # debug('Reading English Words')
    # with open(modern_english_word_json, 'rb') as fp:
    #     lines = fp.read().decode('utf8').split('\n')
    #     tuples = []
    #     for li, line in enumerate(tqdm(lines[:-1])):
    #         j = json.loads(line)
    #         name = '"{}"'.format(j['word'].replace('"', "'"))
    #         pos = '"{}"'.format(j['pos'].replace('"', "'"))
    #         for sense in j['senses']:
    #             conj = True
    #             if 'form_of' not in sense:
    #                 conj = False
    #             definition = '"{}"'.format(
    #                 ('. '.join(sense['glosses']) if 'glosses' in sense else '').replace('"', "'"))
    #             tuples.append((name, pos, definition, li, conj))
    #     cont.insert_record('english_words', tuples)

    debug('Reading Old English Words')
    with open(old_english_word_json, 'rb') as fp:
        lines = fp.read().decode('utf8').split('\n')
        tuples = []
        declensions = []
        conjugations: List[Tuple[str, str, str, str, str, str, bool, bool]] = []
        noun_ipa: List[Tuple[str, str, int, bool]] = []
        noun_germ: List[Tuple[str, str, Gender]] = []
        for li, line in enumerate(tqdm(lines[:-1])):
            j = json.loads(line)

            pos = '"{}"'.format(j['pos'].replace('"', "'"))

            genders: List[Gender] = []
            if 'forms' not in j:
                # error('{} has no forms!'.format(j['word']))
                name = ['"{}"'.format(j['word'].replace('"', "'"))]
            else:
                name = ['"{}"'.format(w['form'].replace('"', "'")) for w in j['forms'] if 'canonical' in w['tags']]
                for w in j['forms']:
                    if 'canonical' in w['tags']:
                        if j['pos'] == 'noun':
                            for t in w['tags']:
                                if t in gender_list:
                                    genders.append(Gender[t.upper()])
                    else:
                        if j['pos'] == 'noun':
                            # Maybe a declension?
                            cases = find_declensions(w['tags'])
                            for c, p in cases:
                                for n in name:
                                    declensions.append((n, w['form'], c, p))

            for sense in j['senses']:
                conj = True
                if 'form_of' not in sense:
                    conj = False
                else:
                    # Detect Declensions
                    if j['pos'] == 'noun':
                        cases = find_declensions(sense['tags'])
                        for c, p in cases:
                            for f in sense['form_of']:
                                # debug('{} is the {} {} form of {}'.format(name, c, p, f['word']))
                                for n in name:
                                    declensions.append((n, f['word'], c, p))

                    # Detect Conjugations
                    elif j['pos'] == 'verb':
                        conjs = find_verb_conjugations(sense['tags'])
                        for per, pl, t, m, part, pre in conjs:
                            for f in sense['form_of']:
                                for n in name:
                                    conjugations.append((n, f['word'], per, pl, t, m, part, pre))

                if j['pos'] == 'noun':
                    # Find IPA for manual declension
                    if 'sounds' in j:
                        found = False
                        for s in j['sounds']:
                            if 'ipa' in s:
                                syllables = separate_syllables([s['ipa']])
                                for n in name:
                                    noun_ipa.append((n, str(s['ipa']),
                                                     len(syllables),
                                                     bool(re.fullmatch(long_syllable, syllables[-1]) is not None)))
                                found = True
                        if not found:
                            debug('No ipa translation found for {}'.format(j['word']))
                    else:
                        debug('No sounds found for {}'.format(j['word']))

                    # Detect proto-germanic
                    if 'etymology_templates' in j:
                        for temp in j['etymology_templates']:
                            if temp['name'] == 'inh':
                                # The word was inherited
                                args = temp['args']
                                if args['2'] == 'gem-pro':
                                    # And it was inherited from proto germanic
                                    proto = args['3']
                                    for n in name:
                                        for g in genders:
                                            noun_germ.append((n, proto, g))
                    else:
                        debug('{} is an OE innovation'.format(j['word']))

                definition = '"{}"'.format(
                    ('. '.join(sense['glosses']) if 'glosses' in sense else '').replace('"', "'"))
                for n in name:
                    tuples.append((n, pos, definition, li, conj))
        cont.insert_record('old_english_words', tuples)

        # Insert Linking Tables
        insert_declensions(declensions)
        insert_verb_conjugations(conjugations)
        insert_ipa(noun_ipa)
        insert_proto(noun_germ)


def find_declensions(sense: List[str]) -> List[Tuple[str, str]]:
    cases = []
    pluralities = []
    for tag in sense:
        if tag in case_list:
            cases.append(tag)

        if tag in plurality_list:
            pluralities.append(tag)

    tuples = []
    for c in cases:
        for p in pluralities:
            tuples.append((c, p))

    return tuples


def find_verb_conjugations(sense: List[str]) -> List[Tuple[str, str, str, str, bool, bool]]:
    persons = []
    pluralities = []
    tenses = []
    moods = []
    participle = False
    preterite = False

    for tag in sense:
        if tag in plurality_list:
            pluralities.append(tag)
        elif tag in person_list:
            persons.append(tag)
        elif tag in tense:
            tenses.append(tag)
        elif tag in mood:
            moods.append(tag)
        elif tag == 'participle':
            participle = True
        elif tag == 'preterite':
            preterite = True

    tuples = []
    for a in persons:
        for b in pluralities:
            for c in tenses:
                for d in moods:
                    tuples.append((a, b, c, d, participle, preterite))

    return tuples


def insert_declensions(declensions: List[Tuple[str, str, str, str]]):
    cont = SQLController.get_instance()

    debug('Inserting Noun Declension Table')
    words = list(set(['"{}"'.format(d[1].replace('"', "'")) for d in declensions] + [d[0] for d in declensions]))
    where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
    indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

    debug('Generating foreign key dictionary')
    pos_dict = {}
    index_dict = {}
    for index, name, pos in indices:
        if name not in index_dict:
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'noun' and pos_dict[name] != 'noun':
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'noun':
            debug('Possible ambiguous declension of {} as a {} and {}'.format(name, pos, pos_dict[name]))

    debug('linking...')
    tuples = []
    for o, w, c, p in declensions:
        if w in index_dict:
            orig = o[1:-1]
            if orig in index_dict:
                tuples.append((index_dict[w], index_dict[orig], '"{}"'.format(p), '"{}"'.format(c)))
            else:
                debug('{} was not found to be a root word'.format(o))
        else:
            debug('{} was not found to be a root word'.format(w))

    cont.insert_record('declensions', tuples)


def insert_ipa(declensions: List[Tuple[str, str, int, bool]]):
    cont = SQLController.get_instance()

    debug('Inserting Noun IPA Table')
    words = list(set([d[0] for d in declensions]))
    where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
    indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

    debug('Generating foreign key dictionary')
    pos_dict = {}
    index_dict = {}
    for index, name, pos in indices:
        if name not in index_dict:
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'noun' and pos_dict[name] != 'noun':
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'noun':
            debug('Possible ambiguous pos of {} as a {} and {}'.format(name, pos, pos_dict[name]))

    debug('linking...')
    tuples = []
    for w, t, c, p in declensions:
        w = w[1:-1]
        if w in index_dict:
            tuples.append(('"{}"'.format(index_dict[w]), '"{}"'.format(t.replace('"', "'")), c, 1 if p else 0))
        else:
            debug('{} was not found to be a root word'.format(w))

    cont.insert_record('ipa', tuples)


def insert_proto(declensions: List[Tuple[str, str, Gender]]):
    cont = SQLController.get_instance()

    debug('Inserting Noun Proto Germanic Table')
    words = list(set([d[0] for d in declensions]))
    where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
    indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

    debug('Generating foreign key dictionary')
    pos_dict = {}
    index_dict = {}
    for index, name, pos in indices:
        if name not in index_dict:
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'noun' and pos_dict[name] != 'noun':
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'noun':
            debug('Possible ambiguous pos of {} as a {} and {}'.format(name, pos, pos_dict[name]))

    debug('linking...')
    tuples = []
    for w, t, g in declensions:
        w = w[1:-1]
        if w in index_dict:
            tuples.append(('"{}"'.format(index_dict[w]),
                           '"{}"'.format(t.replace('"', "'")),
                           '"{}"'.format(g.name.lower())))
        else:
            debug('{} was not found to be a root word'.format(w))

    cont.insert_record('nouns', tuples)


def insert_verb_conjugations(conjugations: List[Tuple[str, str, str, str, str, str, bool, bool]]):
    cont = SQLController.get_instance()

    debug('Inserting Verb Conjugation Table')
    words = list(set(['"{}"'.format(d[1].replace('"', "'")) for d in conjugations] + [d[0] for d in conjugations]))
    where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
    indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

    debug('Generating foreign key dictionary')
    pos_dict = {}
    index_dict = {}
    for index, name, pos in indices:
        if name not in index_dict:
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'verb' and pos_dict[name] != 'verb':
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'verb':
            debug('Possible ambiguous conjugation of {} as a {} and {}'.format(name, pos, pos_dict[name]))

    debug('linking...')
    tuples = []
    for o, w, per, pl, t, m, pt, pr in conjugations:
        if w in index_dict:
            orig = o[1:-1]
            if orig in index_dict:
                tuples.append((index_dict[w], index_dict[orig],
                               '"{}"'.format(per), '"{}"'.format(pl), '"{}"'.format(t), '"{}"'.format(m),
                               1 if pt else 0, 1 if pr else 0))
            else:
                debug('{} was not found to be a root verb'.format(o))
        else:
            debug('{} was not found to be a root verb'.format(w))

    cont.insert_record('conjugations', tuples)


if __name__ == '__main__':
    initialize_database()
