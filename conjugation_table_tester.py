from soup_targets import soup_targets, wiktionary_root
from controllers.beautifulsoup import SoupVerbHeaderScraper
from controllers.ui import debug
from utils.web import use_unverified_ssl

from typing import Dict


def display_word_dict(wd: Dict[str, str]) -> str:
    result = ''
    for w, t in wd.items():
        result += w + '\n' + t + '\n\n'
    return result


def find_different_conjugation_tables():
    conj_table = set()
    word_dict = {}
    words = set()

    debug('Searching for verbs')
    for s, url in soup_targets['verbs'].items():
        debug('Searching for {}'.format(s))
        if isinstance(url, dict):
            for g, gurl in url.items():
                debug('Checking for {}'.format(g))
                scraper = SoupVerbHeaderScraper(wiktionary_root + '/wiki/' + gurl, s, initial_table_set=conj_table)
                w = scraper.find_words()
                conj_table = scraper.table_set
                print('Found {} formats'.format(len(w)))
                for wt, ct in w:
                    if ct not in words:
                        word_dict[ct] = wt
                        words.add(ct)
                debug('Found {} words so far'.format(len(words)))
        else:
            scraper = SoupVerbHeaderScraper(wiktionary_root + '/wiki/' + url, s, initial_table_set=conj_table)
            w = scraper.find_words()
            conj_table = scraper.table_set
            print('Found {} formats'.format(len(w)))
            for wt, ct in w:
                if ct not in words:
                    word_dict[ct] = wt
                    words.add(ct)
            debug('Found {} words so far'.format(len(words)))

    print('There are {} different conjugation table styles'.format(len(words)))
    wds = display_word_dict(word_dict)
    print(wds)

    with open('./table_types.txt', 'w+') as fp:
        fp.write(wds)


if __name__ == '__main__':
    use_unverified_ssl()
    find_different_conjugation_tables()
