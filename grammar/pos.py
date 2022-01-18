from controllers.sql import SQLController
from utils.grammar import Case, Plurality, Mood, Tense, Person, Gender
from controllers.ui import debug
from grammar.restrictions import WordRestriction

from typing import List, Tuple, Union
import random as rng


class POS:
    def __init__(self, root: str, pos: str):
        self.root = root
        self.pos = pos

    @property
    def index(self) -> List[int]:
        cont = SQLController.get_instance()

        indices = cont.select_conditional('old_english_words', 'id',
                                          'name = "{}" and pos = "{}"'.format(self.root, self.pos))

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


class Declinable(POS):
    def __init__(self, root: str, pos: str, selection_statement: str, declension_table: str):
        super().__init__(root, pos)
        self.delcension_table = declension_table
        self.selection_statement = selection_statement
        self.case = Case.ROOT

    def create_conditional_statement(self) -> str:
        pass

    def parse_declension_results(self, declensions: List[tuple]) -> List[tuple]:
        pass

    def get_declension(self) -> str:
        cont = SQLController.get_instance()

        if self.case == Case.ROOT:
            return self.root
        else:
            declensions = cont.select_conditional(self.delcension_table, 'word',
                                                  self.create_conditional_statement())

            if len(declensions) > 1:
                debug('Multiple declensions for {} in {} '
                      'form found with indices {} and {}'.format(self.root,
                                                                 self.case.name.lower(),
                                                                 declensions[0][0],
                                                                 declensions[1][0]))
            elif len(declensions) == 0:
                debug('No word found for {} in the {}'.format(self.root,
                                                              self.case.name.lower()))
                return self.root

            dec_index = [d[0] for d in declensions]

            return dec_index[0]

    def get_possible_declensions(self) -> List[Tuple[Case, Plurality]]:
        cont = SQLController.get_instance()
        declensions = cont.select_conditional(self.delcension_table, self.selection_statement,
                                              'origin in ({})'.format(str(self.index)[1:-1]))
        return self.parse_declension_results(declensions)


class Noun(Declinable):
    def __init__(self, root: str):
        super().__init__(root, 'noun', 'plurality, noun_case', 'declensions')
        self.plurality = Plurality.NONE

    def __repr__(self) -> str:
        return '{} {} {}'.format(self.root, self.case.name.lower(), self.plurality.name.lower())

    def create_conditional_statement(self) -> str:
        return 'origin in ({}) and noun_case = "{}"{}'.format(
                                                      str(self.index)[1:-1],
                                                      self.case.name.lower(),
                                                      ' and plurality = "{}"'.format(
                                                        self.plurality.name.lower())
                                                      if self.plurality != Plurality.NONE else
                                                      '')

    def parse_declension_results(self, declensions: List[tuple]) -> List[tuple]:
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


class Pronoun(Declinable):
    def __init__(self, root: str):
        super().__init__(root, 'pronoun', 'plurality, noun_case, gender, person', 'pronouns')
        self.plurality = Plurality.NONE
        self.gender = Gender.NONE
        self.person = Person.NONE

    def __repr__(self) -> str:
        return '{} {} {}'.format(self.root, self.case.name.lower(), self.plurality.name.lower())

    def create_conditional_statement(self) -> str:
        condition = 'noun_case = "{}"'.format(self.case.name.lower())

        if self.plurality != Plurality.NONE:
            condition += ' and plurality = "{}"'.format(self.plurality.name.lower())
        if self.gender != Gender.NONE:
            condition += ' and gender = "{}"'.format(self.gender.name.lower())
        if self.person != Person.NONE:
            condition += ' and person = "{}"'.format(self.person.name.lower())

        return 'origin in ({}) and {}'.format(str(self.index)[1:-1], condition)

    def parse_declension_results(self, declensions: List[tuple]) -> List[tuple]:
        return [(Case.ROOT, Plurality.NONE, Gender.NONE, Person.NONE)] + \
               [(Case[c.upper()], Plurality[p.upper()], Gender[g.upper()], Person[per.upper()])
                for p, c, g, per in declensions]

    @staticmethod
    def get_random_word(restrictions: Union[List[WordRestriction], None] = None):
        cont = SQLController.get_instance()
        if restrictions is not None and len(restrictions) > 0:
            constraint_string = (' and '.join([r.get_sql_constraint() for r in restrictions])
                                 if restrictions is not None else '')
            possible_words = cont.select_conditional('pronouns', 'distinct origin', constraint_string)
            word = rng.choice(possible_words)[0]
            return Noun(cont.select_conditional('old_english_words', 'name', 'id = {}'.format(word))[0][0])
        else:
            possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "pronoun" and is_affix = 0')
        return Pronoun(rng.choice(possible_words)[0])


class Verb(POS):
    def __init__(self, root: str):
        super().__init__(root, 'verb')
        self.plurality: Plurality = Plurality.NONE
        self.mood: Mood = Mood.ROOT
        self.person: Person = Person.NONE
        self.tense: Tense = Tense.NONE
        self.is_infinitive: bool = False
        self.is_participle: bool = False
        self.verb_type: str = ''

    @property
    def is_modal(self) -> bool:
        return self.verb_type == 'auxiliary'

    @property
    def is_transitive(self) -> bool:
        return self.verb_type == 'transitive'

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


class Adverb(POS):
    def __init__(self, a: str):
        super().__init__(a, 'adverb')

    @staticmethod
    def get_random_word():
        cont = SQLController.get_instance()
        possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "adverb" and is_affix = 0')
        return Adverb(rng.choice(possible_words)[0])


class Adjective(Declinable):
    def __init__(self, root: str):
        super().__init__(root, 'adjective', 'strength, gender, plurality, noun_case', 'adjectives')
        self.plurality: Plurality = Plurality.NONE
        self.gender: Gender = Gender.NONE
        self.strength = False

    def __repr__(self) -> str:
        return '{}'.format(self.root)

    def create_conditional_statement(self) -> str:
        condition = 'strength = {} and noun_case = "{}"'.format(1 if self.strength else 0, self.case.name.lower())

        if self.plurality != Plurality.NONE:
            condition += ' and plurality = "{}"'.format(self.plurality.name.lower())
        if self.gender != Gender.NONE:
            condition += ' and gender = "{}"'.format(self.gender.name.lower())

        return 'origin in ({}) and {}'.format(str(self.index)[1:-1], condition)

    def parse_declension_results(self, declensions: List[tuple]) -> List[tuple]:
        return [(False, Gender.NONE, Case.ROOT, Plurality.NONE)] + \
               [(s == 1, Gender[g.upper()], Case[c.upper()], Plurality[p.upper()]) for s, g, p, c in declensions]

    @staticmethod
    def get_random_word(restrictions: Union[List[WordRestriction], None] = None):
        cont = SQLController.get_instance()
        if restrictions is not None and len(restrictions) > 0:
            constraint_string = (' and '.join([r.get_sql_constraint() for r in restrictions])
                                 if restrictions is not None else '')
            possible_words = cont.select_conditional('adjectives', 'distinct origin', constraint_string)
            word = rng.choice(possible_words)[0]
            return Noun(cont.select_conditional('old_english_words', 'name', 'id = {}'.format(word))[0][0])
        else:
            possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "adjective" and is_affix = 0')

        return Adjective(rng.choice(possible_words)[0])


class Determiner(Declinable):
    def __init__(self, root: str):
        super().__init__(root, 'determiner', 'strength, gender, plurality, noun_case', 'adjectives')
        self.plurality: Plurality = Plurality.NONE
        self.gender: Gender = Gender.NONE
        self.strength = False

    def __repr__(self) -> str:
        return '{}'.format(self.root)

    def create_conditional_statement(self) -> str:
        condition = 'strength = {} and noun_case = "{}"'.format(1 if self.strength else 0, self.case.name.lower())

        if self.plurality != Plurality.NONE:
            condition += ' and plurality = "{}"'.format(self.plurality.name.lower())
        if self.gender != Gender.NONE:
            condition += ' and gender = "{}"'.format(self.gender.name.lower())

        return 'origin in ({}) and {}'.format(str(self.index)[1:-1], condition)

    def parse_declension_results(self, declensions: List[tuple]) -> List[tuple]:
        return [(False, Gender.NONE, Case.ROOT, Plurality.NONE)] + \
               [(s == 1, Gender[g.upper()], Case[c.upper()], Plurality[p.upper()]) for s, g, p, c in declensions]

    @staticmethod
    def get_random_word(restrictions: Union[List[WordRestriction], None] = None):
        cont = SQLController.get_instance()
        if restrictions is not None and len(restrictions) > 0:
            constraint_string = (' and '.join([r.get_sql_constraint() for r in restrictions])
                                 if restrictions is not None else '')
            possible_words = cont.select_conditional('adjectives', 'distinct origin', constraint_string)
            word = rng.choice(possible_words)[0]
            return Noun(cont.select_conditional('old_english_words', 'name', 'id = {}'.format(word))[0][0])
        else:
            possible_words = cont.select_conditional('old_english_words', 'name', 'pos = "determiner" and is_affix = 0')

        return Adjective(rng.choice(possible_words)[0])
