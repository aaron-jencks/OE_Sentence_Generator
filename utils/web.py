import ssl


def use_unverified_ssl():
    ssl._create_default_https_context = ssl._create_unverified_context
