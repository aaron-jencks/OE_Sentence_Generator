from utils.grammar import Case, Plurality


class WordRestriction:
    def get_sql_constraint(self) -> str:
        pass


class CaseRestriction(WordRestriction):
    def __init__(self, c: Case):
        self._c = c

    def get_sql_constraint(self) -> str:
        return 'declension = "{}"'.format(self._c.name.lower())


class PluralityRestriction(WordRestriction):
    def __init__(self, c: Plurality):
        self._c = c

    def get_sql_constraint(self) -> str:
        return 'declension = "{}"'.format(self._c.name.lower())
