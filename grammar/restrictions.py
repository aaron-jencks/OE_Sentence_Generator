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


class TransitivityRestriction(WordRestriction):
    def __init__(self, t: bool):
        self._t = t

    def get_sql_constraint(self) -> str:
        return 'verb_type = "{}"'.format('transitive' if self._t else 'intransitive')


class ModalityRestriction(WordRestriction):
    def __init__(self, t: bool):
        self._t = t

    def get_sql_constraint(self) -> str:
        return 'verb_type {} "auxiliary"'.format('=' if self._t else '!=')


class ParticipleRestriction(WordRestriction):
    def __init__(self, t: bool):
        self._t = t

    def get_sql_constraint(self) -> str:
        return 'participle = {}'.format(1 if self._t else 0)
