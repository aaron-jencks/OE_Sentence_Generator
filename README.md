# OE Sentence Generator
And Old English Sentence Generator. This project makes use of wiktionary dumps to generate a database that can then be
used to generate random Old English sentences. 

# Database Layout
The database consists of several tables
- **English Words**: Contains the english words used for translation.
- **Old English Words**: Contains all of the old english words including different forms, the `is_conjugation` field is used to determine if the word is a root or not.
- **Declensions**: Contains information about the different declensions for root nouns
- **Conjugations**: Contains information about the different conjugations for root verbs.
- **Noun Information**: Contains information such as the proto germanic ancestor (if any) and the gender
- **IPA and syllable information**: Contains the IPA translation of nouns and indicates the syllable count and syllable heaviness.

For more information about  the tables specifically you can look in the [schemas.py](./schemas.py) file.

## Table Uses
These tables serve the purpose of providing ease of conjugation of all of the words, the [dbinit.py](./dbinit.py) file
is used to generate the database.

# POS

Even though the software automatically generates sentences, if you'd like it is also possible to generate single Parts of Speech. Currently only Nouns and Verbs are supported.

## Nouns

The `Noun` class implements all of the methods needed to generate and decline a noun. You can either specify the root word manually,
or have one randomly selected from the database.

```python
from grammar.pos import Noun
n = Noun.get_random_word()  # Generates a new random noun
```

You can also specify restrictions, such as the available cases, gender, and plurality
(Currently only Case and Plurality are implemented)

```python
from grammar.pos import Noun
from grammar.restrictions import CaseRestriction, PluralityRestriction
from utils.grammar import Case, Plurality

# Generates a noun that has a nominative plural declension available
n = Noun.get_random_word([CaseRestriction(Case.NOMINATIVE), 
                          PluralityRestriction(Plurality.PLURAL)])
```

## Verbs

The `Verb` class implements all of the methods needed to generate and conjugate a verb. You can either specify the root word manually,
or have one randomly selected from the database.

```python
from grammar.pos import Verb
v = Verb.get_random_word()  # Generates a new random verb
```

You can also specify restrictions, though, currently only Plurality and Transitivity are supported

```python
from grammar.pos import Verb
from grammar.restrictions import PluralityRestriction
from utils.grammar import Plurality

# Generates a verb that has a plural conjugation available
v = Verb.get_random_word([PluralityRestriction(Plurality.PLURAL)])
```
