from utils.grammar import Case, Plurality, Gender

from typing import List, Union
import random as rng


class DeclensionException(Exception):
    def __init__(self, msg: str):
        super().__init__(msg)


class InvalidGenderException(DeclensionException):
    def __init__(self, given: Gender, required: Union[Gender, List[Gender]]):
        super().__init__('Invalid gender of {} for target of {}'.format(given, required))


class StemType:
    def __init__(self, suffix: Union[str, List[str]]):
        self.suffix = suffix

    def get_suffix(self, c: Case, p: Plurality, g: Gender) -> str:
        return ''

    def decline(self, root: str, c: Case, p: Plurality, g: Gender) -> str:
        return root + self.get_suffix(c, p, g)


class AStem(StemType):
    def __init__(self):
        super().__init__(['az', 'ą'])

    def get_suffix(self, c: Case, p: Plurality, g: Gender) -> str:
        if p == Plurality.SINGULAR or p == Plurality.NONE:
            if c == Case.NOMINATIVE or c == Case.ACCUSATIVE:
                return ''
            elif c == Case.GENITIVE:
                return 'es'
            elif c == Case.DATIVE:
                return 'e'
        else:
            if c == Case.GENITIVE:
                return 'a'
            elif c == Case.DATIVE:
                return 'um'

        if g == Gender.MASCULINE:
            return 'as'
        elif g == Gender.NEUTER:
            if g.weight:
                return ''
            else:
                return 'u'
        else:
            raise InvalidGenderException(g, [Gender.MASCULINE, Gender.NEUTER])


class OStem(StemType):
    def __init__(self):
        super().__init__('ō')

    def get_suffix(self, c: Case, p: Plurality, g: Gender) -> str:
        if g != Gender.NEUTER:
            raise InvalidGenderException(g, Gender.Neuter)

        if p == Plurality.SINGULAR or p == Plurality.NONE:
            if c == Case.NOMINATIVE:
                if g == Gender.Neuter:
                    # TODO Fix this based on the syllable weight
                    return '' if g.weight else 'u'
            else:
                return 'e'
        else:
            if c == Case.DATIVE:
                return 'um'
            elif c == Case.ACCUSATIVE:
                if rng.randint(0, 1) == 1:
                    return 'a'
                else:
                    return 'e'
            else:
                return 'a'


class NStem(StemType):
    def __init__(self):
        super().__init__('')

    def get_suffix(self, c: Case, p: Plurality, g: Gender) -> str:
        if p == Plurality.PLURAL and c == Case.DATIVE:
            return 'um'
        elif (p == Plurality.SINGULAR or p == Plurality.NONE) and c != Case.NOMINATIVE:
            return 'an'
        elif p == Plurality.PLURAL and (c == Case.NOMINATIVE or c == Case.ACCUSATIVE):
            return 'an'
        elif p == Plurality.PLURAL and c == Case.GENITIVE:
            return 'ena'
        elif g == Gender.MASCULINE:
            return 'a'
        else:
            return 'e'


class IStem(StemType):
    def __init__(self):
        super().__init__('iz')

    def get_suffix(self, c: Case, p: Plurality, g: Gender) -> str:
        if p == Plurality.PLURAL:
            if c == c.DATIVE:
                return 'um'
            elif c == c.ACCUSATIVE:
                return 'a' if rng.randint(0, 1) else 'e'
            else:
                return 'a'
        elif c == Case.NOMINATIVE:
            return ''
        elif c == Case.ACCUSATIVE:
            return '' if rng.randint(0, 1) else 'e'
        else:
            return 'e'


class UStem(StemType):
    def __init__(self):
        super().__init__('')

    def get_suffix(self, c: Case, p: Plurality, g: Gender) -> str:
        if g == Gender.Neuter:
            raise InvalidGenderException(g, [Gender.MASCULINE, Gender.FEMININE])
