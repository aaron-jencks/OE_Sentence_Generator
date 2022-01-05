from soup_targets import soup_targets, wiktionary_root
from controllers.beautifulsoup import SoupVerbHeaderScraper
from controllers.ui import debug
from utils.web import use_unverified_ssl


def find_different_conjugation_tables():
    words = set()
    conj_table = set()
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
                words = words.union(w)
                debug('Found {} words so far'.format(len(words)))
        else:
            scraper = SoupVerbHeaderScraper(wiktionary_root + '/wiki/' + url, s, initial_table_set=conj_table)
            w = scraper.find_words()
            conj_table = scraper.table_set
            print('Found {} formats'.format(len(w)))
            words = words.union(w)
            debug('Found {} words so far'.format(len(words)))

    print('There are {} different conjugation table styles'.format(len(words)))
    print('\n\n'.join(words))


if __name__ == '__main__':
    use_unverified_ssl()
    find_different_conjugation_tables()
