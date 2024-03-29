import math
from pathlib import Path
import sys
import collections
import hashlib
import typing as ty

from alfreddict import utils


def request_urban_dictionary(
    word: str,
    cachedir: ty.Optional[Path],
    proxy: ty.Optional[str],
) -> dict:
    cache_name = hashlib.sha1(word.encode('utf-8')).hexdigest()[:12]
    return utils.request_web_json_cached(
        'https://api.urbandictionary.com/v0/define', {'term': word},
        f'ub_{cache_name}.json.gz', cachedir, proxy)


WordEntry = collections.namedtuple(
    'WordEntry', ['word', 'upvote', 'downvote', 'definition', 'permalink'])


def parse_json_response(resp):
    return [
        WordEntry(res['word'], res['thumbs_up'], res['thumbs_down'],
                  res['definition'].replace('[', '').replace(']', ''),
                  res['permalink']) for res in resp['list']
    ]


def wilson_score_lb(entry: WordEntry) -> float:
    n = entry.upvote + entry.downvote
    if n == 0:
        return 0.0
    p = entry.upvote / n
    z = 1.96  # confidence=95%, or alpha=0.05
    return (p + math.pow(z, 2) / (2 * n) - z * math.sqrt(
        (p * (1 - p) + math.pow(z, 2) /
         (4 * n)) / n)) / (1 + math.pow(z, 2) / n)


def generate_response_items(entries: ty.List[WordEntry]):
    resp = []
    thumbs_up_char = chr(9650)
    thumbs_down_char = chr(9660)
    for entry in entries:
        resp.append({
            'title': (f'{entry.word} | '
                      f'{thumbs_up_char} {entry.upvote}  '
                      f'{thumbs_down_char} {entry.downvote}'),
            'subtitle':
            entry.definition,
            'arg':
            entry.permalink,
            'text': {
                'copy': entry.word,
                'largetype': entry.definition,
            },
            'mods': {
                'cmd': {
                    'subtitle': 'Prounounce aloud using system voice',
                    'arg': entry.word,
                },
            },
        })
    return resp


@utils.response_written
def main():
    cachedir = utils.get_cachedir()
    cache_timeout = utils.get_cache_timeout()
    proxy = utils.get_proxy()
    try:
        query = sys.argv[1]
    except IndexError:
        return [], None

    if cache_timeout:
        utils.rm_obsolete_cache(cachedir, cache_timeout)

    resp = request_urban_dictionary(query, cachedir, proxy)
    entries = parse_json_response(resp)
    entries.sort(key=wilson_score_lb, reverse=True)
    return generate_response_items(entries), None


if __name__ == '__main__':
    main()
