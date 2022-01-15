from controllers.sql import SQLController
from controllers.ui import debug, error
from utils.grammar import case_list, plurality_list, person_list, tense, mood, \
    long_syllable, separate_syllables, Gender, gender_list
from settings import old_english_word_json, modern_english_word_json
from utils.web import use_unverified_ssl

import json
from settings import data_path
from typing import List, Tuple, Dict, Union
import os.path as path
from tqdm import tqdm
import re


etymology_names = ['inh', 'der']
language_codes = ['ang', 'en']


def db_string(s: str) -> str:
    return '"{}"'.format(s.replace('"', "'"))


def convert_word_dictionary_noun(words: List[Dict[str, Union[List[str],
                                                             Dict[str, str],
                                                             str]]]) -> Dict[str, List[tuple]]:
    """
    :param words: List of dictionaries to be converted
    {
    'word': word,
    'definitions': List of definitions,
    'forms': List of dictionaries with case entries
    }
    :return: Returns a dictionary with each key corresponding to a table and it's value a list of data to insert
    """

    debug('Converting Noun dictionaries')
    roots = []
    declensions = []

    for w in tqdm(words):
        for d in w['definitions']:
            roots.append((db_string(w['word']), '"noun"', db_string(d),
                          w['word'].startswith('-') or w['word'].endswith('-')))  # Check for affix

        for decl in w['forms']:
            for c, d in decl.items():
                case, plurality = c.split(' ')
                declensions.append((db_string(d), w['word'],
                                    db_string(plurality.lower()), db_string(case.lower())))

    return {'old_english_words': roots, 'declensions': declensions}


def convert_word_dictionary_verb(words: List[Tuple[str, Dict[str, Union[List[str],
                                                                        List[Dict[str,
                                                                                  Union[str, Dict[str, str]]]],
                                                                        str]]]]) -> Dict[str, List[tuple]]:
    """
    :param words: List of dictionaries to be converted
    {
    'word': word,
    'definitions': List of definitions,
    'forms': A List of conjugation dictionaries
    Conjugation dictionaries: {
        'key':  The name indicating the conjugation form of this entry
        'form' The form of the root verb for this conjugation
    }
    }

    Possible keys for conjugation dictionaries:
    ('infinitive can', 0, 1),
    ('infinitive to', 0, 2),
    ('indicative first singular present', 2, 1),
    ('indicative first singular past', 2, 2),
    ('indicative second singular present', 3, 1),
    ('indicative second singular past', 3, 2),
    ('indicative third singular present', 4, 1),
    ('indicative third singular past', 4, 2),
    ('indicative plural present', 5, 1),
    ('indicative plural past', 5, 2),
    ('subjunctive singular present', 7, 1),
    ('subjunctive singular past', 7, 2),
    ('subjunctive plural present', 8, 1),
    ('subjunctive plural past', 8, 2),
    ('imperative singular', 9, 1),
    ('imperative plural', 10, 1),
    ('present participle', 12, 1),
    ('past participle', 12, 2)
    :return: Returns a dictionary with each key corresponding to a table and it's value a list of data to insert
    """

    debug('Converting Verb dictionaries')
    roots = []
    conjugations = []
    verbs = []

    for s, w in tqdm(words):
        for d in w['definitions']:
            roots.append((db_string(w['word']), '"verb"', db_string(d),
                          w['word'].startswith('-') or w['word'].endswith('-')))  # Check for affix

        verbs.append((w['word'], False, 0, s == 'transitive'))

        for conj in w['forms']:
            for c, d in conj.items():
                origin = w['word']
                word = db_string(d)
                person = '"none"'
                plurality = '"none"'
                emood = '"none"'
                etense = '"none"'
                is_participle = False
                is_infinitive = False

                tags = c.split(' ')
                if len(tags) == 2:
                    if tags[0] == 'imperative':
                        emood = db_string(tags[0].lower())
                        plurality = db_string(tags[1].lower())
                    elif tags[0] == 'infinitive':
                        is_infinitive = True
                        is_participle = tags[1] == 'can'
                    else:
                        is_participle = True
                        etense = db_string(tags[0].lower())
                elif len(tags) == 3:
                    emood = db_string(tags[0].lower())
                    plurality = db_string(tags[1].lower())
                    etense = db_string(tags[2].lower())
                elif len(tags) == 4:
                    emood = db_string(tags[0].lower())
                    person = db_string(tags[1].lower())
                    plurality = db_string(tags[2].lower())
                    etense = db_string(tags[3].lower())
                else:
                    debug('{} is not a valid tag name for a verb'.format(c))

                conjugations.append((word, origin, person, plurality, emood, etense, is_participle, is_infinitive))

    return {'old_english_words': roots, 'conjugations': conjugations, 'verbs': verbs}


def convert_word_dictionary_adverb(words: List[Tuple[str, Dict[str, Union[List[str],
                                                                        List[Dict[str,
                                                                                  Union[str, Dict[str, str]]]],
                                                                        str]]]]) -> Dict[str, List[tuple]]:
    """
    :param words: List of dictionaries to be converted
    {
    'word': word,
    'definitions': List of definitions,
    'forms': A List of conjugation dictionaries
    }
    :return: Returns a dictionary with each key corresponding to a table and it's value a list of data to insert
    """

    debug('Converting Adverb dictionaries')
    roots = []
    adverbs = {}

    for s, w in tqdm(words):
        for d in w['definitions']:
            roots.append((db_string(w['word']), '"adverb"', db_string(d),
                          w['word'].startswith('-') or w['word'].endswith('-')))  # Check for affix

        if w['word'] not in adverbs:
            adverbs[w['word']] = {'comparative': False, 'superlative': False}

        if s == 'comparative':
            adverbs[w['word']]['comparative'] = True
        elif s == 'superlative':
            adverbs[w['word']]['superlative'] = True

    adverb_entries = []
    for w in adverbs.keys():
        adverb_entries.append((w, adverbs[w]['comparative'], adverbs[w]['superlative']))

    return {'old_english_words': roots, 'adverbs': adverb_entries}


def convert_word_dictionary_adjectives_generic(words: List[Dict[str, Union[List[str], List[Dict[str,
                                                                                                Union[str,
                                                                                                      Dict[str, str]]]],
                                                                           str]]], pos: str) -> Dict[str, List[tuple]]:
    """
    :param words: List of dictionaries to be converted
    {
    'word': word,
    'definitions': List of definitions,
    'forms': A List of conjugation dictionaries
    Conjugation Dictionaries {
        'plurality': plural or singular  # if this exists then there will be no plurality in the rest of the cases
        Each case has a gender suffix separated by a space
        'nominative'
        'accusative'
        'genitive'
        'dative'
        'instrumental'

        Example:
        'singular nominative masculine'
        or
        'nominative masculine'  if plurality is defined
    }
    }
    :param pos: the POS of this list of words
    :return: Returns a dictionary with each key corresponding to a table and it's value a list of data to insert
    """

    debug('Converting {} dictionaries'.format(pos))
    roots = []
    adjectives = []

    for w in tqdm(words):
        for d in w['definitions']:
            roots.append((db_string(w['word']), '"{}"'.format(pos), db_string(d),
                          w['word'].startswith('-') or w['word'].endswith('-')))  # Check for affix

        for form in w['forms']:
            strength = form['strength']
            if 'plurality' in form:
                # singular form
                plurality = form['plurality']
                for c, f in form.items():
                    if c != 'plurality' and c != 'strength':
                        case, gender = c.split(' ')
                        adjectives.append((w['word'], db_string(f),
                                           strength == 'strong',
                                           db_string(gender), db_string(case), db_string(plurality)))
            else:
                for c, f in form.items():
                    if c != 'strength':
                        plurality, case, gender = c.split(' ')
                        adjectives.append((w['word'], db_string(f),
                                           strength == 'strong',
                                           db_string(gender), db_string(case), db_string(plurality)))

    return {'old_english_words': roots, 'adjectives': adjectives}


def convert_word_dictionary_adjectives(words: List[Dict[str, Union[List[str], List[Dict[str, Union[str,
                                                                                                   Dict[str, str]]]],
                                                                   str]]]) -> Dict[str, List[tuple]]:
    return convert_word_dictionary_adjectives_generic(words, 'adjective')


def convert_word_dictionary_determiners(words: List[Dict[str, Union[List[str], List[Dict[str, Union[str,
                                                                                                    Dict[str, str]]]],
                                                                    str]]]) -> Dict[str, List[tuple]]:
    return convert_word_dictionary_adjectives_generic(words, 'determiner')


def convert_word_dictionary_pronoun(words: List[Dict[str, Union[List[str],
                                                             Dict[str, str],
                                                             str]]]) -> Dict[str, List[tuple]]:
    """
    :param words: List of dictionaries to be converted
    {
    'word': word,
    'definitions': List of definitions,
    'forms': List of dictionaries with case entries
    }
    :return: Returns a dictionary with each key corresponding to a table and it's value a list of data to insert
    """

    debug('Converting Noun dictionaries')
    roots = []
    declensions = []

    for w in tqdm(words):
        for d in w['definitions']:
            roots.append((db_string(w['word']), '"pronoun"', db_string(d),
                          w['word'].startswith('-') or w['word'].endswith('-')))  # Check for affix

        for decl in w['forms']:
            for c, d in decl.items():
                chunks = c.split(' ')
                gender = 'none'
                person = 'none'
                plurality = 'none'
                if len(chunks) == 3:
                    case, plurality, mystery = chunks
                    if mystery in gender_list:
                        gender = mystery
                    else:
                        person = mystery
                else:
                    case, mystery = chunks
                    if mystery in gender_list:
                        gender = mystery
                    else:
                        plurality = mystery

                declensions.append((db_string(d), w['word'],
                                    db_string(plurality.lower()), db_string(case.lower()),
                                    db_string(gender.lower()), db_string(person.lower())))

    return {'old_english_words': roots, 'pronouns': declensions}


conversion_dict = {
    'nouns': convert_word_dictionary_noun,
    'verbs': convert_word_dictionary_verb,
    'adverbs': convert_word_dictionary_adverb,
    'adjectives': convert_word_dictionary_adjectives,
    'determiners': convert_word_dictionary_determiners,
    'pronouns': convert_word_dictionary_pronoun
}


def initialize_database_scraper():
    from soup_targets import soup_targets, wiktionary_root
    from controllers.sql import SQLController
    from controllers.beautifulsoup import SoupStemScraper, SoupVerbClassScraper, \
        SoupAdverbScraper, SoupAdjectiveScraper, SoupDeterminerScraper, SoupPronounScraper

    cont = SQLController.get_instance()
    cont.reset_database()
    cont.setup_tables()

    noun_declension_tables = set()
    verb_conjugation_tables = set()
    roots = []
    declensions = []
    conjugations = []
    verbs = []
    adverbs = []
    adjectives = []
    pronouns = []
    for t, u in soup_targets.items():
        words = []
        debug('Searching for {}'.format(t))
        for s, url in u.items():
            debug('Searching for {}'.format(s))
            if isinstance(url, dict):
                for g, gurl in url.items():
                    debug('Checking for {}'.format(g))
                    scraper = None
                    if t == 'nouns':
                        scraper = SoupStemScraper(wiktionary_root + '/wiki/' + gurl, s,
                                                  initial_table_set=noun_declension_tables)
                        words += scraper.find_words()
                        noun_declension_tables = scraper.table_set
                    elif t == 'verbs':
                        scraper = SoupVerbClassScraper(wiktionary_root + '/wiki/' + gurl,
                                                       initial_table_set=verb_conjugation_tables)
                        words += [(s, w) for w in scraper.find_words()]
                        verb_conjugation_tables = scraper.table_set
                    elif t == 'adverbs':
                        scraper = SoupAdverbScraper(wiktionary_root + '/wiki/' + gurl, s)
                        words += [(s, w) for w in scraper.find_words()]
                    elif t == 'adjectives':
                        scraper = SoupAdjectiveScraper(wiktionary_root + '/wiki/' + gurl, s)
                        words += scraper.find_words()
                    elif t == 'determiners':
                        scraper = SoupDeterminerScraper(wiktionary_root + '/wiki/' + gurl, s)
                        words += scraper.find_words()
                    elif t == 'pronouns':
                        scraper = SoupPronounScraper(wiktionary_root + '/wiki/' + gurl, s)
                        words += scraper.find_words()
            else:
                scraper = None
                if t == 'nouns':
                    scraper = SoupStemScraper(wiktionary_root + '/wiki/' + url, s,
                                              initial_table_set=noun_declension_tables)
                    words += scraper.find_words()
                    noun_declension_tables = scraper.table_set
                elif t == 'verbs':
                    scraper = SoupVerbClassScraper(wiktionary_root + '/wiki/' + url,
                                                   initial_table_set=verb_conjugation_tables)
                    words += [(s, w) for w in scraper.find_words()]
                    verb_conjugation_tables = scraper.table_set
                elif t == 'adverbs':
                    scraper = SoupAdverbScraper(wiktionary_root + '/wiki/' + url, s)  # There are no tables for adverbs
                    words += [(s, w) for w in scraper.find_words()]
                elif t == 'adjectives':
                    scraper = SoupAdjectiveScraper(wiktionary_root + '/wiki/' + url, s)
                    words += scraper.find_words()
                elif t == 'determiners':
                    scraper = SoupDeterminerScraper(wiktionary_root + '/wiki/' + url, s)
                    words += scraper.find_words()
                elif t == 'pronouns':
                    scraper = SoupPronounScraper(wiktionary_root + '/wiki/' + url, s)
                    words += scraper.find_words()
            debug('Found {} words so far'.format(len(words)))

        tuple_dict = conversion_dict[t](words)
        if 'old_english_words' in tuple_dict:
            roots += tuple_dict['old_english_words']
        if 'declensions' in tuple_dict:
            declensions += tuple_dict['declensions']
        if 'conjugations' in tuple_dict:
            conjugations += tuple_dict['conjugations']
        if 'verbs' in tuple_dict:
            verbs += tuple_dict['verbs']
        if 'adverbs' in tuple_dict:
            adverbs += tuple_dict['adverbs']
        if 'adjectives' in tuple_dict:
            adjectives += tuple_dict['adjectives']
        if 'pronouns' in tuple_dict:
            pronouns += tuple_dict['pronouns']

    cont.insert_record('old_english_words', roots)
    insert_declensions(declensions)
    insert_verb_conjugations(conjugations)
    insert_verb_transitivities(verbs)
    insert_adverbs(adverbs)
    insert_adjectives(adjectives)
    insert_pronoun(pronouns)


def initialize_database_dump():
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
    if len(declensions) > 0:
        # words = list(set(['"{}"'.format(d[1].replace('"', "'")) for d in declensions] + [d[0] for d in declensions]))
        words = list(set(['"{}"'.format(d[1].replace('"', "'")) for d in declensions]))  # for scraper style
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
        # for o, w, c, p in declensions:
        for w, o, p, c in declensions:  # for scraper style
            # if w in index_dict:
            #     # orig = o[1:-1]
            #     orig = o  # for scraper style
            #     if orig in index_dict:
            #         tuples.append((w, index_dict[orig], db_string(p), db_string(c)))
            #     else:
            #         debug('{} was not found to be a root word'.format(o))
            # else:
            #     debug('{} was not found to be a root word'.format(w))

            # For scraper style
            orig = o  # for scraper style
            if orig in index_dict:
                tuples.append((w, index_dict[orig], p, c))
            else:
                debug('{} was not found to be a root word'.format(o))

        cont.insert_record('declensions', tuples)


def insert_pronoun(declensions: List[Tuple[str, str, str, str, str, str]]):
    cont = SQLController.get_instance()

    debug('Inserting Noun Declension Table')
    if len(declensions) > 0:
        words = list(set([db_string(d[1]) for d in declensions]))  # for scraper style
        where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
        indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

        debug('Generating foreign key dictionary')
        pos_dict = {}
        index_dict = {}
        for index, name, pos in indices:
            if name not in index_dict:
                index_dict[name] = index
                pos_dict[name] = pos
            elif pos == 'pronoun' and pos_dict[name] != 'pronoun':
                index_dict[name] = index
                pos_dict[name] = pos
            elif pos == 'pronoun':
                debug('Possible ambiguous declension of {} as a {} and {}'.format(name, pos, pos_dict[name]))

        debug('linking...')
        tuples = []
        for w, o, p, c, g, per in declensions:  # for scraper style
            # For scraper style
            orig = o  # for scraper style
            if orig in index_dict:
                tuples.append((w, index_dict[orig], p, c, per, g))
            else:
                debug('{} was not found to be a root word'.format(o))

        cont.insert_record('pronouns', tuples)


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
    words = list(set([db_string(d[1]) for d in conjugations]))
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
    for w, o, per, pl, t, m, pt, pr in conjugations:
        if o in index_dict:
            tuples.append((w, index_dict[o],
                           per, pl, t, m,
                           1 if pt else 0, 1 if pr else 0))
        else:
            debug('{} was not found to be a root verb'.format(o))

    cont.insert_record('conjugations', tuples)


def insert_verb_transitivities(conjugations: List[Tuple[str, bool, int, bool]]):
    cont = SQLController.get_instance()

    debug('Inserting Verb Conjugation Table')
    words = list(set([db_string(d[0]) for d in conjugations]))
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
    for w, stren, cl, trans in conjugations:
        if w in index_dict:
            tuples.append((index_dict[w], 1 if stren else 0, cl, 1 if trans else 0))
        else:
            debug('{} was not found to be a root verb'.format(w))

    cont.insert_record('verbs', tuples)


def insert_adverbs(adverbs: List[Tuple[str, bool, bool]]):
    cont = SQLController.get_instance()

    debug('Inserting Adverb Table')
    words = list(set([db_string(d[0]) for d in adverbs]))
    where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
    indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

    debug('Generating foreign key dictionary')
    pos_dict = {}
    index_dict = {}
    for index, name, pos in indices:
        if name not in index_dict:
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'adverb' and pos_dict[name] != 'adverb':
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'adverb':
            debug('Possible ambiguous conjugation of {} as a {} and {}'.format(name, pos, pos_dict[name]))

    debug('linking...')
    tuples = []
    for w, comp, sup in adverbs:
        if w in index_dict:
            tuples.append((index_dict[w], 1 if comp else 0, 1 if sup else 0))
        else:
            debug('{} was not found to be a root adverb'.format(w))

    cont.insert_record('adverbs', tuples)


def insert_adjectives(adverbs: List[Tuple[str, str, bool, str, str, str]]):
    cont = SQLController.get_instance()

    debug('Inserting Adjective Declension Table')
    words = list(set([db_string(d[0]) for d in adverbs]))
    where_clause = 'name in ({})'.format(','.join(words)) if len(words) > 1 else 'name = {}'.format(words[0])
    indices = cont.select_conditional('old_english_words', 'id, name, pos', where_clause)

    debug('Generating foreign key dictionary')
    pos_dict = {}
    index_dict = {}
    for index, name, pos in indices:
        if name not in index_dict:
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'adjective' and pos_dict[name] != 'adjective':
            index_dict[name] = index
            pos_dict[name] = pos
        elif pos == 'adjective':
            debug('Possible ambiguous conjugation of {} as a {} and {}'.format(name, pos, pos_dict[name]))

    debug('linking...')
    tuples = []
    for w, o, stren, gen, case, plur in adverbs:
        if w in index_dict:
            tuples.append((index_dict[w], o, 1 if stren else 0, gen, case, plur))
        else:
            debug('{} was not found to be a root adverb'.format(w))

    cont.insert_record('adjectives', tuples)


if __name__ == '__main__':
    use_unverified_ssl()
    initialize_database_scraper()
