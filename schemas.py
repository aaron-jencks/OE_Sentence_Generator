english_schemas = '''english_words (
id integer primary key,
name text not null,
pos text not null,
definition text not null,
wiktionary_entry integer not null,
is_conjugation bool not null
);
'''

old_english_schemas = '''old_english_words (
id integer primary key,
name text not null,
pos text not null,
definition text not null,
wiktionary_entry integer not null,
is_conjugation bool not null
);
'''

translations_schemas = '''translations (
id integer primary key,
ne integer not null,
oe integer not null,
foreign key (ne) references english_words(id),
foreign key (oe) references old_english_words(id)
);
'''

conjugations_schemas = '''conjugations (
id integer primary key,
word integer not null,
origin integer not null,
person text,
plurality text,
mood text,
tense text,
participle bool not null,
preterite bool not null,
foreign key (word) references old_english_words(id),
foreign key (origin) references old_english_words(id)
);
'''

declensions_schemas = '''declensions (
id integer primary key,
word integer not null,
origin integer not null,
plurality text,
declension text not null,
foreign key (word) references old_english_words(id),
foreign key (origin) references old_english_words(id)
);
'''

nouns_schemas = '''nouns (
id integer primary key,
word integer not null,
proto_germanic text,
gender text,
foreign key (word) references old_english_words(id)
);
'''

ipa_schemas = '''ipa (
id integer primary key,
word integer not null,
ipa_text text not null,
syllable_count integer not null,
heavy bool not null,
foreign key (word) references old_english_words(id)
);'''


schemas = [
    english_schemas,
    old_english_schemas,
    translations_schemas,
    conjugations_schemas,
    declensions_schemas,
    nouns_schemas,
    ipa_schemas
]

triggers = [
]

views = [
]

record_typing = {
    'english_words': '(name, pos, definition, wiktionary_entry, is_conjugation)',
    'old_english_words': '(name, pos, definition, wiktionary_entry, is_conjugation)',
    'translations': '(ne, oe)',
    'conjugations': '(word, origin, person, plurality, mood, tense, participle, preterite)',
    'declensions': '(word, origin, plurality, declension)',
    'nouns': '(word, proto_germanic, gender)',
    'ipa': '(word, ipa_text, syllable_count, heavy)'
}
