from controllers.sql import SQLController
from utils.grammar import Case, Plurality
from controllers.ui import debug

from typing import List
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