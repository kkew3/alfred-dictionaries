import sys
from urllib import parse
from pathlib import Path
import datetime as dt
import typing as ty

import utils


# Reference:
# https://gist.github.com/ayubmalik/149e2c7f28104f61cc1c862fe9834793?permalink_comment_id=4574200#gistcomment-4574200
def request_google_translate(
    query: str,
    tl: ty.Literal['en', 'zh-CN'],
    cachedir: ty.Optional[Path],
    cache_timeout: ty.Optional[dt.timedelta],
    proxy: ty.Optional[str],
):
    params = {
        'q': query,
        'client': 'gtx',
        'sl': 'auto',
        'tl': tl,
        'dt': 't',
    }
    cache_name = utils.validate_filename(query)
    return utils.request_web_json_cached(
        'https://translate.googleapis.com/translate_a/single', params,
        'gg_{}_{}.json'.format(tl, cache_name), cachedir, cache_timeout, proxy)


def parse_json_response(resp):
    return resp[0][0][0]


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


def generate_response_items(query: str, tl: str, translation: str):
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
    try:
        query = sys.argv[2]
    except IndexError:
        return [], None
    resp = request_google_translate(query, tl, cachedir, cache_timeout, proxy)
    translation = parse_json_response(resp)
    return generate_response_items(query, tl, translation), None


if __name__ == '__main__':
    main()
