from soup_targets import soup_targets, wiktionary_root
from controllers.beautifulsoup import SoupVerbHeaderScraper
from controllers.ui import debug


def find_different_conjugation_tables():
    words = set()
    debug('Searching for verbs')
    for s, url in soup_targets['verbs'].items():
        debug('Searching for {}'.format(s))
        if isinstance(url, dict):
            for g, gurl in url.items():
                debug('Checking for {}'.format(g))
                scraper = SoupVerbHeaderScraper(wiktionary_root + '/wiki/' + gurl, s)
                w = scraper.find_words()
                print('Found {} formats'.format(len(w)))
                words = words.union(w)
        else:
            scraper = SoupVerbHeaderScraper(wiktionary_root + '/wiki/' + url, s)
            w = scraper.find_words()
            print('Found {} formats'.format(len(w)))
            words = words.union(w)
        debug('Found {} words so far'.format(len(words)))

    print('There are {} different conjugation table styles'.format(len(words)))
    print('\n'.join(words))


if __name__ == '__main__':
    find_different_conjugation_tables()
