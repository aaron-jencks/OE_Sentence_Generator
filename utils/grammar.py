from typing import List
import enum

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
