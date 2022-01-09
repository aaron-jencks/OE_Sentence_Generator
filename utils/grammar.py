from typing import List
import enum
import re

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
gender_list: List[str] = ['masculine', 'feminine', 'neuter']

syllable_separators = re.compile(r'[ˌ.,ˈ\']')
vowel_pattern = r'(([ɑouiIəeaɛæyø∅]|o̯|ɑ̯)(͜([ɑouiIəeaɛæyø∅]|o̯|ɑ̯))?[:ː]?)'
long_vowel_pattern = r'(([ɑouiIəeaɛæyø∅]|o̯|ɑ̯)((͜([ɑouiIəeaɛæyø∅]|o̯|ɑ̯))?)[:ː])'
consonant_pattern = r'(([mnŋpbtdkgfvθðszʃçxɣhljwrɫ]|n̥|l̥|r̥|w̥|d͡ʒ|t͡ʃ|t͡s)[ˠʰ]?)'
syllable_pattern = r'({v}|{c}{{1,3}}{v}|{v}{c}{{1,2}}|{c}{v}{c}{{1,4}})'.format(v=vowel_pattern, c=consonant_pattern)
long_syllable = r'({vl}|{c}{{1,3}}{vl}|{vl}{c}{{1,2}}|{c}{vl}{c}{{1,4}}|' \
                r'{c}{{2,3}}{v}|{v}{c}{{2}}|{c}{v}{c}{{2,4}})'.format(v=vowel_pattern,
                                                                      c=consonant_pattern,
                                                                      vl=long_vowel_pattern)


def separate_syllables(words: List[str]) -> List[str]:
    syllables = []
    for w in words:
        sy = re.split(syllable_separators, w[1:-1])
        for s in sy:
            if len(s) > 0:
                syllables.append(s)
    return syllables


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
    NONE = 3


class Tense(enum.Enum):
    PAST = 0
    PRESENT = 1
    NONE = 2


class Mood(enum.Enum):
    INDICATIVE = 0
    IMPERATIVE = 1
    SUBJUNCTIVE = 2
    PARTICIPLE = 3
    INFINITIVE = 4
    ROOT = 6
    NONE = 5


class Gender(enum.Enum):
    MASCULINE = 0
    FEMININE = 1
    NEUTER = 2
    NONE = 3


class WordOrder(enum.Enum):
    SVO = 0
    SOV = 1
    OSV = 2
    VSO = 3
    VOS = 4
    OVS = 5
