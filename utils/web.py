import ssl


illegal_filename_characters = '#%&${}\\<>*?/ !\'":@+`|='


def prepare_filename(url: str) -> str:
    current = url[8:]
    for i in illegal_filename_characters:
        current = current.replace(i, '')
    return current + '.html'


def use_unverified_ssl():
    ssl._create_default_https_context = ssl._create_unverified_context
