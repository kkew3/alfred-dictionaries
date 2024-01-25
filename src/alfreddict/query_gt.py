import sys
from urllib import parse
from pathlib import Path
import hashlib
import typing as ty

from alfreddict import utils


# Reference:
# https://gist.github.com/ayubmalik/149e2c7f28104f61cc1c862fe9834793?permalink_comment_id=4574200#gistcomment-4574200
def request_google_translate(
    query: str,
    tl: ty.Literal['en', 'zh-CN'],
    cachedir: Path,
    proxy: ty.Optional[str],
):
    params = {
        'q': query,
        'client': 'gtx',
        'sl': 'auto',
        'tl': tl,
        'dt': 't',
    }
    cache_name = hashlib.sha1(query.encode('utf-8')).hexdigest()[:12]
    return utils.request_web_json_cached(
        'https://translate.googleapis.com/translate_a/single', params,
        f'gg_{tl}_{cache_name}.json', cachedir, proxy)


def parse_json_response(resp):
    return ''.join(x[0] for x in resp[0])


def get_google_translate_url(
    query: str,
    tl: ty.Literal['en', 'zh-CN'],
) -> str:
    params = {
        'sl': 'auto',
        'tl': tl,
        'text': query,
        'op': 'translate',
    }
    url = 'https://translate.google.com'
    return '{}?{}'.format(url, parse.urlencode(params))


def generate_response_items(
    query: str,
    tl: ty.Literal['en', 'zh-CN'],
    translation: str,
):
    return [
        {
            'title': translation,
            'arg': get_google_translate_url(query, tl),
            'text': {
                'copy': translation,
                'largetype': translation,
            },
            'mods': {
                'cmd': {
                    'subtitle': 'Prounounce aloud using system voice',
                    'arg': query,
                },
            },
        },
    ]


@utils.response_written
def main():
    cachedir = utils.get_cachedir()
    cache_timeout = utils.get_cache_timeout()
    proxy = utils.get_proxy()
    tl = sys.argv[1]
    assert tl in ['en', 'zh-CN']
    if len(sys.argv) <= 2:
        return [], None
    query = sys.argv[2]

    if cache_timeout:
        utils.rm_obsolete_cache(cachedir, cache_timeout)

    resp = request_google_translate(query, tl, cachedir, proxy)
    translation = parse_json_response(resp)
    return generate_response_items(query, tl, translation), None


if __name__ == '__main__':
    main()
