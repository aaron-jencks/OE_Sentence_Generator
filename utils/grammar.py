from typing import List, Tuple
import enum
import random as rng

from controllers.sql import SQLController
from controllers.ui import debug

# AdjP: (Adj|Participle V)
# NP: (AdjP NP|Det AdjP NP|Det NP|N|Gerund/Participle V|NP Conj NP|NP PrepP|NP Relative Clause)  Determiner always comes firt
# VP: (Modal Main Participle*|Main Participle*|Main) Modal always comes first, Main verb + participle is auxiliary
# PrepP: (Prep NP) Preposition always comes first
# Relative Clause: (Pronoun (NP VP|VP NP)) Relative Pronoun always comes first
# Clause: (NP VP NP AdvP|VP NP NP AdvP|NP NP VP AdvP) AdvP location if free
# AdvP: (Adv AdjP|AdjP Adv|Adv VP|VP Adv|Adv)


case_list: List[str] = ['oblique', 'genitive', 'dative', 'accusative', 'nominative', 'instrumental']
plurality_list: List[str] = ['singular', 'plural']

person_list: List[str] = ['first-person', 'second-person', 'third-person']
tense: List[str] = ['past', 'present']
mood: List[str] = ['indicative', 'imperative', 'subjunctive']

strength: List[str] = ['strong', 'weak']
gender: List[str] = ['masculine', 'feminine', 'neuter']


class Case(enum.Enum):
    OBLIQUE = 0
    GENITIVE = 1
    DATIVE = 2
    ACCUSATIVE = 3
    NOMINATIVE = 4
    INSTRUMENTAL = 5
    ROOT = 6


class Plurality(enum.Enum):
    SINGULAR = 0
    PLURAL = 1
    NONE = 2


class Person(enum.Enum):
    FIRST = 0
    SECOND = 1
    THIRD = 2


class Tense(enum.Enum):
    PAST = 0
    PRESENT = 1


class Mood(enum.Enum):
    INDICATIVE = 0
    IMPERATIVE = 1
    SUBJUNCTIVE = 2


class Strength(enum.Enum):
    WEAK = 0
    STRONG = 1


class Gender(enum.Enum):
    MASCULINE = 0
    FEMININE = 1
    NEUTER = 2


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

    def get_declension(self) -> str:
        cont = SQLController.get_instance()

        if self.case == Case.ROOT:
            return self.root
        else:
            declensions = cont.select_conditional('conjugations', 'word',
                                                  'origin in ({}) and declension = "{}"{}'.format(
                                                      self.case.name.lower(),
                                                      str(self.index)[1:-1],
                                                      ' and "{}"'.format(
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

            return cont.select_conditional('old_english_words', 'name', 'id in ({})'.format(str(dec_index)[1:-1]))[0][0]

    def get_possible_declensions(self) -> List[Tuple[Case, Plurality]]:
        cont = SQLController.get_instance()
        declensions = cont.select_conditional('declensions', 'plurality, declension', 'origin in ({})'.format(
            str(self.index)[1:-1]))
        return [(Case.ROOT, Plurality.NONE)] + [(Case[c.upper()], Plurality[p.upper()]) for p, c in declensions]

    @staticmethod
    def get_random_word():
        cont = SQLController.get_instance()
        possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "noun"')
        return Noun(rng.choice(possible_words)[0])


