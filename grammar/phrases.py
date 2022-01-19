from grammar.pos import Noun, Verb, Adjective, Adverb, Preposition, Pronoun
from utils.grammar import WordOrder, Case, Plurality, Person, Tense, Mood
from grammar.restrictions import TransitivityRestriction, ParticipleRestriction, ModalityRestriction

import random as rng
from typing import List, Union


class Phrase:
    @staticmethod
    def generate_random():
        pass

    def meaning(self) -> str:
        pass


class AdjectivePhrase(Phrase):
    def __init__(self, a: Union[Adjective, Verb]):
        if isinstance(a, Verb):
            assert a.is_participle
        self.adjective = a

    def meaning(self) -> str:
        return rng.choice(self.adjective.meaning)

    @staticmethod
    def generate_random():
        word = Adjective.get_random_word()
        if rng.randint(0, 1) == 1:
            word = Verb.get_random_word([ParticipleRestriction(True)])
            word.is_participle = True
        return AdjectivePhrase(word)


class NounPhrase(Phrase):
    def __init__(self, n: Noun):
        self.noun = n

    def __repr__(self):
        return self.noun.get_declension()

    def meaning(self):
        return rng.choice(self.noun.meaning)

    @staticmethod
    def generate_random():
        return NounPhrase(Noun.get_random_word())


class VerbPhrase(Phrase):
    def __init__(self, main: Verb, modal: Verb = None, participle: Verb = None):
        self.main = main
        self.modal = modal
        self.participle = participle

    def __repr__(self):
        result = ''
        if self.modal is not None:
            result += self.modal.get_conjugation() + ' '
        result += self.main.get_conjugation()
        if self.participle is not None:
            result += ' ' + self.participle.get_conjugation()
        return result

    def meaning(self):
        result = ''
        if self.modal is not None:
            result += rng.choice(self.modal.meaning) + ' '
        result += rng.choice(self.main.meaning)
        if self.participle is not None:
            result += ' ' + rng.choice(self.participle.meaning)
        return result

    @staticmethod
    def generate_random():
        # VP: (Modal Main Participle*|Main Participle*|Main)
        # Modal always comes first, Main verb + participle is auxiliary
        version = rng.randint(1, 3)

        main = Verb.get_random_word()

        if version < 3:
            participle = Verb.get_random_word([ParticipleRestriction(True)])

            if version == 1:
                modal = Verb.get_random_word([ModalityRestriction(True)])
                phrase = VerbPhrase(main, modal, participle)
            else:
                phrase = VerbPhrase(main, participle=participle)
        else:
            phrase = VerbPhrase(main)

        return phrase


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
        return TransitiveVerbPhrase(Verb.get_random_word([TransitivityRestriction(True)]),
                                    direct_object, indirect_object)


class IntransitiveVerbPhrase(VerbPhrase):
    @staticmethod
    def generate_random():
        # VP: (Modal Main Participle*|Main Participle*|Main)
        # Modal always comes first, Main verb + participle is auxiliary
        version = rng.randint(1, 3)

        main = Verb.get_random_word()

        if version < 3:
            participle = Verb.get_random_word([ParticipleRestriction(True)])

            if version == 1:
                modal = Verb.get_random_word([ModalityRestriction(True)])
                phrase = IntransitiveVerbPhrase(main, modal, participle)
            else:
                phrase = IntransitiveVerbPhrase(main, participle=participle)
        else:
            phrase = IntransitiveVerbPhrase(main)

        return phrase


class PrepositionalPhrase(Phrase):
    def __init__(self, prep: Preposition, np: NounPhrase):
        self.prep = prep
        self.np = np

    def __repr__(self):
        return self.prep.root + ' ' + repr(self.np)

    def meaning(self) -> str:
        return rng.choice(self.prep.meaning) + ' ' + self.np.meaning()

    @staticmethod
    def generate_random():
        return PrepositionalPhrase(Preposition.get_random_word(), NounPhrase.generate_random())


class RelativeClause(Phrase):
    def __init__(self, pron: Pronoun, verb: VerbPhrase, noun: NounPhrase):
        self.pronoun = pron
        self.verb = verb
        self.noun = noun
        self.order = rng.randint(0, 1)

    def reset_word_order(self):
        self.order = rng.randint(0, 1)

    def get_word_order(self) -> List[Union[Pronoun, Phrase]]:
        chunks = [self.pronoun]
        if self.order == 1:
            chunks += [self.verb, self.noun]
        else:
            chunks += [self.noun, self.verb]
        return chunks

    def __repr__(self):
        chunks = self.get_word_order()
        return chunks[0].root + ' ' + ' '.join(map(repr, [c for c in chunks if isinstance(c, Phrase)]))

    @staticmethod
    def generate_random():
        # TODO VP needs to be conjugated whether the NP is the subject or if the Pronoun is the subject
        return RelativeClause(Pronoun.get_random_word(), VerbPhrase.generate_random(), NounPhrase.generate_random())


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

        verb = IntransitiveVerbPhrase.generate_random()
        if rng.randint(0, 1) == 1:
            verb = TransitiveVerbPhrase.generate_random()

        verb.main.plurality = sub.noun.plurality
        verb.main.mood = Mood.INDICATIVE
        verb.main.person = Person.THIRD
        verb.main.tense = Tense(rng.randint(0, 1))

        obj = NounPhrase.generate_random()
        obj.noun.case = Case.ACCUSATIVE
        obj.noun.plurality = Plurality(rng.randint(0, 1))

        return Clause(sub, verb, obj)
