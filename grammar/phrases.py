from grammar.pos import Noun, Verb
from utils.grammar import WordOrder, Case, Plurality, Person, Tense, Mood

import random as rng
from typing import List, Union


class Phrase:
    @staticmethod
    def generate_random():
        pass

    def meaning(self) -> str:
        pass


class NounPhrase(Phrase):
    def __init__(self, n: Noun):
        self.noun = n

    def __repr__(self):
        return self.noun.get_declension()

    def meaning(self):
        return rng.choice(self.noun.meaning)[0]

    @staticmethod
    def generate_random():
        return NounPhrase(Noun.get_random_word())


class VerbPhrase(Phrase):
    def __init__(self, v: Verb):
        self.verb = v

    def __repr__(self):
        return self.verb.get_conjugation()

    def meaning(self):
        return rng.choice(self.verb.meaning)[0]

    @staticmethod
    def generate_random():
        return VerbPhrase(Verb.get_random_word())


class TransitiveVerbPhrase(VerbPhrase):
    def __init__(self, v: Verb, direct_object: NounPhrase, indirect_object: Union[NounPhrase, None] = None):
        super().__init__(v)
        self.do = direct_object
        self.io = indirect_object

    def __repr__(self):
        chunks = [super().__repr__()]
        if self.io is not None:
            chunks.append(repr(self.io))
        chunks.append(repr(self.do))
        return ' '.join(chunks)

    @staticmethod
    def generate_random():
        direct_object = NounPhrase.generate_random()
        indirect_object = None
        if rng.randint(0, 1) == 1:
            indirect_object = NounPhrase.generate_random()
        return TransitiveVerbPhrase(Verb.get_random_word(), direct_object, indirect_object)


class IntransitiveVerbPhrase(VerbPhrase):
    @staticmethod
    def generate_random():
        return IntransitiveVerbPhrase(Verb.get_random_word())


class Clause:
    def __init__(self, subject: NounPhrase, verb: VerbPhrase, obj: NounPhrase):
        self.subject = subject
        self.verb = verb
        self.object = obj
        self.word_order = WordOrder(rng.randint(0, 5))

    def reset_word_order(self):
        self.word_order = WordOrder(rng.randint(0, 5))

    def get_word_order(self) -> List[Phrase]:
        wo = self.word_order
        chunks = []
        for c in wo.name:
            if c == 'S':
                chunks.append(self.subject)
            elif c == 'V':
                chunks.append(self.verb)
            elif c == 'O':
                chunks.append(self.object)
        return chunks

    def __repr__(self):
        chunks = self.get_word_order()
        return ' '.join(map(repr, chunks))

    def translation(self) -> str:
        return ', '.join([p.meaning() for p in self.get_word_order()]) + '({})'.format(self.word_order)

    @staticmethod
    def generate_random():
        sub = NounPhrase.generate_random()
        sub.noun.case = Case.NOMINATIVE
        sub.noun.plurality = Plurality(rng.randint(0, 1))

        # TODO Assumes all verbs are transitive

        verb = VerbPhrase.generate_random()
        verb.verb.plurality = sub.noun.plurality
        verb.verb.mood = Mood.INDICATIVE
        verb.verb.person = Person.THIRD
        verb.verb.tense = Tense(rng.randint(0, 1))

        obj = NounPhrase.generate_random()
        obj.noun.case = Case.ACCUSATIVE
        obj.noun.plurality = Plurality(rng.randint(0, 1))

        return Clause(sub, verb, obj)
