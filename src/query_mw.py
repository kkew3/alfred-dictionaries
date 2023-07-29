import sys
import collections
from pathlib import Path
from urllib import parse
import datetime as dt
import itertools
import typing as ty

import utils


def request_mw_dictionary(
    api_key: str,
    word: str,
    cachedir: ty.Optional[Path],
    cache_timeout: ty.Optional[dt.timedelta],
    proxy: ty.Optional[str],
) -> list:
    cache_name = utils.validate_filename(word)
    return utils.request_web_json_cached(
        'https://dictionaryapi.com/api/v3/references/collegiate/json/'
        + parse.quote(word), {'key': api_key},
        'mw_{}.json.gz'.format(cache_name), cachedir, cache_timeout, proxy)


def request_mw_audio(
    url: str,
    cachedir: ty.Optional[Path],
    cache_timeout: ty.Optional[dt.timedelta],
    proxy: ty.Optional[str],
) -> ty.Optional[Path]:
    cache_name = 'mw_{}'.format(Path(parse.urlparse(url).path).name)
    return utils.request_web_data_blob_cached(url, {}, cache_name, cachedir,
                                              cache_timeout, proxy)


def parse_audio_url(name: str) -> str:
    """
    Parse audio basename as URL according to
    https://dictionaryapi.com/products/json#sec-2.prs .

    :param name: the audio basename
    :return: the audio URL
    """
    url = 'https://media.merriam-webster.com/audio/prons/en/us/mp3/{}/{}.mp3'
    if name.startswith('bix'):
        subdir = 'bix'
    elif name.startswith('gg'):
        subdir = 'gg'
    elif name[0].isdigit():
        subdir = 'number'
    elif name[0] in '_':  # may not be complete
        subdir = 'number'
    else:
        subdir = name[0]
    return url.format(subdir, name)


WordEntry = collections.namedtuple(
    'WordEntry', ['id_', 'word', 'fl', 'prs_url', 'shortdef', 'dict_url'])


def parse_json_resp_item(resp_item) -> WordEntry:
    id_ = resp_item['meta']['id']
    hw = resp_item['hwi']['hw']
    fl = resp_item['fl']
    dict_url = ('https://www.merriam-webster.com/dictionary/'
                + parse.quote(hw))
    try:
        prs_url = parse_audio_url(resp_item['hwi']['prs'][0]['sound']['audio'])
    except (KeyError, IndexError):
        prs_url = None
    shortdef = itertools.starmap('{}. {}; '.format,
                                 enumerate(resp_item['shortdef'], 1))
    shortdef = ''.join(shortdef)
    return WordEntry(id_, hw, fl, prs_url, shortdef, dict_url)


def generate_response_items(entries: ty.List[WordEntry]):
    resp = []
    speaker_char = chr(128264)
    for entry in entries:
        if entry.prs_url:
            title = '{} ({}) {}'.format(entry.word, entry.fl, speaker_char)
        else:
            title = '{} ({})'.format(entry.word, entry.fl)
        if entry.prs_url:
            mods_dict = {
                'cmd': {
                    'subtitle': 'Prounounce aloud',
                    'arg': str(entry.prs_url),
                },
            }
        else:
            mods_dict = {
                'cmd': {
                    'subtitle': entry.shortdef,
                    'arg': ''
                },
            }
        resp.append({
            'uid': entry.id_,
            'title': title,
            'subtitle': entry.shortdef,
            'arg': entry.dict_url,
            'mods': mods_dict,
            'text': {
                'copy': entry.word,
                'largetype': entry.shortdef,
            },
        })
    return resp


class MWAPIKeyNotProvided(Exception):
    def __init__(self):
        super().__init__('M-W dictionary is not accessible since API key '
                         'is not provided')


@utils.response_written
def main():
    cachedir = utils.get_cachedir()
    cache_timeout = utils.get_cache_timeout()
    api_key = utils.get_mw_api_key()
    proxy = utils.get_proxy()
    try:
        query = sys.argv[1]
    except IndexError:
        return [], None

    if not api_key:
        raise MWAPIKeyNotProvided
    resp = request_mw_dictionary(api_key, query, cachedir, cache_timeout,
                                 proxy)
    local_entries = []
    for entry in map(parse_json_resp_item, resp):
        if entry.prs_url:
            prs_local_path = request_mw_audio(entry.prs_url, cachedir,
                                              cache_timeout, proxy)
        else:
            prs_local_path = None
        local_entries.append(
            WordEntry(entry.id_, entry.word, entry.fl, prs_local_path,
                      entry.shortdef, entry.dict_url))
    return generate_response_items(local_entries), None


if __name__ == '__main__':
    main()
