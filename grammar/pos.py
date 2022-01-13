from controllers.sql import SQLController
from utils.grammar import Case, Plurality, Mood, Tense, Person
from controllers.ui import debug
from grammar.restrictions import WordRestriction

from typing import List, Tuple, Union
import random as rng


class Noun:
    def __init__(self, root: str):
        self.root = root
        self.case: Case = Case.ROOT
        self.plurality: Plurality = Plurality.NONE

    def __repr__(self) -> str:
        return '{} {} {}'.format(self.root, self.case.name.lower(), self.plurality.name.lower())

    @property
    def index(self) -> List[int]:
        cont = SQLController.get_instance()

        indices = cont.select_conditional('old_english_words', 'id',
                                          'name = "{}" and pos = "noun"'.format(self.root))

        if len(indices) > 1:
            debug('Multiple indices found for root {} with indices {} and {}'.format(self.root,
                                                                                     indices[0][0],
                                                                                     indices[1][0])
                  )
        elif len(indices) == 0:
            debug('No index found for {}'.format(self.root))
            return [-1]

        return [index[0] for index in indices]

    @property
    def meaning(self) -> List[str]:
        cont = SQLController.get_instance()
        definitions = cont.select_conditional('old_english_words', 'definition',
                                              'id in ({})'.format(str(self.index)[1:-1]))
        return definitions

    def get_declension(self) -> str:
        cont = SQLController.get_instance()

        if self.case == Case.ROOT:
            return self.root
        else:
            declensions = cont.select_conditional('declensions', 'word',
                                                  'origin in ({}) and noun_case = "{}"{}'.format(
                                                      str(self.index)[1:-1],
                                                      self.case.name.lower(),
                                                      ' and plurality = "{}"'.format(
                                                        self.plurality.name.lower())
                                                      if self.plurality != Plurality.NONE else
                                                      ''))

            if len(declensions) > 1:
                debug('Multiple declensions for {} in {} {} '
                      'form found with indices {} and {}'.format(self.root,
                                                                 self.case.name.lower(),
                                                                 self.plurality.name.lower(),
                                                                 declensions[0][0],
                                                                 declensions[1][0]))
            elif len(declensions) == 0:
                debug('No word found for {} in the {} {}'.format(self.root,
                                                                 self.case.name.lower(), self.plurality.name.lower()))
                return self.root

            dec_index = [d[0] for d in declensions]

            return dec_index[0]

    def get_possible_declensions(self) -> List[Tuple[Case, Plurality]]:
        cont = SQLController.get_instance()
        declensions = cont.select_conditional('declensions', 'plurality, noun_case', 'origin in ({})'.format(
            str(self.index)[1:-1]))
        return [(Case.ROOT, Plurality.NONE)] + [(Case[c.upper()], Plurality[p.upper()]) for p, c in declensions]

    @staticmethod
    def get_random_word(restrictions: Union[List[WordRestriction], None] = None):
        cont = SQLController.get_instance()
        if restrictions is not None and len(restrictions) > 0:
            constraint_string = (' and '.join([r.get_sql_constraint() for r in restrictions])
                                 if restrictions is not None else '')
            possible_words = cont.select_conditional('declensions', 'distinct origin', constraint_string)
            word = rng.choice(possible_words)[0]
            return Noun(cont.select_conditional('old_english_words', 'name', 'id = {}'.format(word))[0][0])
        else:
            possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "noun" and is_affix = 0')
        return Noun(rng.choice(possible_words)[0])


class Verb:
    def __init__(self, root: str):
        self.root = root
        self.plurality: Plurality = Plurality.NONE
        self.mood: Mood = Mood.ROOT
        self.person: Person = Person.NONE
        self.tense: Tense = Tense.NONE
        self.is_infinitive: bool = False
        self.is_participle: bool = False

    def __repr__(self) -> str:
        if self.is_participle:
            return '{} {} Participle'.format(self.root, self.tense)
        elif self.is_infinitive:
            return '{} {} Infinitive'.format(self.root, 'can' if self.is_participle else 'to')
        elif self.mood == Mood.IMPERATIVE:
            return '{} Imperative {}'.format(self.root, self.plurality)
        elif self.mood == Mood.SUBJUNCTIVE:
            return '{} Subjunctive {} {}'.format(self.root, self.plurality, self.tense)
        else:
            return '{} {} {} {} {}'.format(self.root, self.mood, self.person, self.plurality, self.tense)

    @property
    def index(self) -> List[int]:
        cont = SQLController.get_instance()

        indices = cont.select_conditional('old_english_words', 'id',
                                          'name = "{}" and pos = "verb"'.format(self.root))

        if len(indices) > 1:
            debug('Multiple indices found for root {} with indices {} and {}'.format(self.root,
                                                                                     indices[0][0],
                                                                                     indices[1][0])
                  )
        elif len(indices) == 0:
            debug('No index found for {}'.format(self.root))
            return [-1]

        return [index[0] for index in indices]

    @property
    def meaning(self) -> List[str]:
        cont = SQLController.get_instance()
        definitions = cont.select_conditional('old_english_words', 'definition',
                                              'id in ({})'.format(str(self.index)[1:-1]))
        return definitions

    def get_conjugation(self) -> str:
        cont = SQLController.get_instance()

        if self.mood == Mood.ROOT:
            return self.root
        else:
            condition = 'mood = "{}" and participle = {} and is_infinitive = {}'.format(self.mood.name.lower(),
                                                                                        1 if self.is_participle else 0,
                                                                                        1 if self.is_infinitive else 0)
            if self.plurality != Plurality.NONE:
                condition += ' and plurality = "{}"'.format(self.plurality.name.lower())
            if self.person != Person.NONE:
                condition += ' and person = "{}"'.format(self.person.name.lower())
            if self.tense != Tense.NONE:
                condition += ' and tense = "{}"'.format(self.tense.name.lower())

            conjugations = cont.select_conditional('conjugations', 'word',
                                                   'origin in ({}) and '.format(str(self.index)[1:-1]) + condition)

            if len(conjugations) > 1:
                debug('Multiple conjugations for {} in {} {} '
                      'form found with indices {} and {}'.format(self.root,
                                                                 self.mood.name.lower(),
                                                                 self.plurality.name.lower(),
                                                                 conjugations[0][0],
                                                                 conjugations[1][0]))
            elif len(conjugations) == 0:
                debug('No word found for {} in the {} {}'.format(self.root,
                                                                 self.mood.name.lower(), self.plurality.name.lower()))
                return self.root

            dec_index = [d[0] for d in conjugations]

            return dec_index[0]

    def get_possible_conjugations(self) -> List[Tuple[Plurality, Tense, Mood, Person, bool, bool]]:
        cont = SQLController.get_instance()
        conjugations = cont.select_conditional('conjugations',
                                               'plurality, tense, mood, person, participle, is_infinitive',
                                               'origin in ({})'.format(str(self.index)[1:-1]))
        return [(Plurality.NONE, Tense.NONE, Mood.NONE, Person.NONE, False, False)] + \
               [(Plurality[p.upper().strip()], Tense[t.upper()], Mood[m.upper()],
                 Person[per.upper()], par, inf)
                for p, t, m, per, par, inf in conjugations]

    @staticmethod
    def get_random_word(restrictions: Union[List[WordRestriction], None] = None):
        cont = SQLController.get_instance()
        if restrictions is not None and len(restrictions) > 0:
            constraint_string = (' and '.join([r.get_sql_constraint() for r in restrictions])
                                 if restrictions is not None else '')
            possible_words = cont.select_conditional('conjugations join verbs on verbs.word = conjugations.origin',
                                                     'distinct origin', constraint_string)
            word = rng.choice(possible_words)[0]
            return Verb(cont.select_conditional('old_english_words', 'name', 'id = {}'.format(word))[0][0])
        else:
            possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "verb" and is_affix = 0')
        return Verb(rng.choice(possible_words)[0])


class Adverb:
    def __init__(self, a: str):
        self.root = a

    @property
    def index(self) -> List[int]:
        cont = SQLController.get_instance()

        indices = cont.select_conditional('old_english_words', 'id',
                                          'name = "{}" and pos = "noun"'.format(self.root))

        if len(indices) > 1:
            debug('Multiple indices found for root {} with indices {} and {}'.format(self.root,
                                                                                     indices[0][0],
                                                                                     indices[1][0])
                  )
        elif len(indices) == 0:
            debug('No index found for {}'.format(self.root))
            return [-1]

        return [index[0] for index in indices]

    @property
    def meaning(self) -> List[str]:
        cont = SQLController.get_instance()
        definitions = cont.select_conditional('old_english_words', 'definition',
                                              'id in ({})'.format(str(self.index)[1:-1]))
        return definitions

    @staticmethod
    def get_random_word():
        cont = SQLController.get_instance()
        possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "adverb" and is_affix = 0')
        return Adverb(rng.choice(possible_words)[0])
