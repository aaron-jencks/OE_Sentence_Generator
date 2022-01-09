from grammar.pos import Noun, Verb
from utils.grammar import WordOrder, Case, Plurality, Person, Tense, Mood

import random as rng


class Phrase:
    @staticmethod
    def generate_random():
        pass


class NounPhrase(Phrase):
    def __init__(self, n: Noun):
        self.noun = n

    def __repr__(self):
        return self.noun.get_declension()

    @staticmethod
    def generate_random():
        return NounPhrase(Noun.get_random_word())


class VerbPhrase(Phrase):
    def __init__(self, v: Verb):
        self.verb = v

    def __repr__(self):
        return self.verb.get_conjugation()

    @staticmethod
    def generate_random():
        return VerbPhrase(Verb.get_random_word())


class Clause:
    def __init__(self, subject: NounPhrase, verb: VerbPhrase, obj: NounPhrase):
        self.subject = subject
        self.verb = verb
        self.object = obj

    def __repr__(self):
        wo = WordOrder(rng.randint(0, 5))
        chunks = []
        for c in wo.name:
            if c == 'S':
                chunks.append(self.subject)
            elif c == 'V':
                chunks.append(self.verb)
            elif c == 'O':
                chunks.append(self.object)
        return ''.join(map(repr, chunks))

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
