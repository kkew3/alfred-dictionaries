import sys
import collections
from pathlib import Path
from urllib import parse
import itertools
import hashlib
import typing as ty

from alfreddict import utils


def request_mw_dictionary(
    api_key: str,
    word: str,
    cachedir: ty.Optional[Path],
    proxy: ty.Optional[str],
) -> ty.List[ty.Any]:
    cache_name = hashlib.sha1(word.encode('utf-8')).hexdigest()[:12]
    return utils.request_web_json_cached(
        'https://dictionaryapi.com/api/v3/references/collegiate/json/'
        + parse.quote(word), {'key': api_key}, f'mw_{cache_name}.json.gz',
        cachedir, proxy)


def request_mw_audio(
    url: str,
    cachedir: Path,
    proxy: ty.Optional[str],
) -> Path:
    _, _, audio_name = parse.urlparse(url).path.rpartition('/')
    return utils.request_web_data_blob_cached(url, {}, f'mw_{audio_name}',
                                              cachedir, proxy)


def parse_audio_url(name: str) -> str:
    """
    Parse audio basename as URL according to
    https://dictionaryapi.com/products/json#sec-2.prs .

    :param name: the audio basename
    :return: the audio URL
    """
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
    return (f'https://media.merriam-webster.com/audio/prons/en/us/mp3/'
            f'{subdir}/{name}.mp3')


WordEntry = collections.namedtuple(
    'WordEntry', ['id_', 'word', 'fl', 'prs_url', 'shortdef', 'dict_url'])


def parse_json_resp_item(resp_item) -> WordEntry:
    id_ = resp_item['meta']['id']
    hw = resp_item['hwi']['hw']
    fl = resp_item.get('fl', '??')
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


def generate_response_items_no_such_word(candidate_words: ty.List[str]):
    if candidate_words:
        title = 'No such word! Do you mean one of:'
        subtitle = 'Select one word and command+c to copy'
    else:
        title = 'No such word!'
        subtitle = ''
    items = [
        {
            'title': title,
            'subtitle': subtitle,
            'valid': False,
            'icon': {
                'path': 'error-icon.png',
            },
        },
    ]
    for w in candidate_words:
        items.append({
            'title': w,
            'valid': False,
            'text': {
                'copy': w,
            },
        })
    return items


def generate_response_items(entries: ty.List[WordEntry]):
    resp = []
    speaker_emoji = chr(128264)
    for entry in entries:
        if entry.prs_url:
            title = '{} ({}) {}'.format(entry.word, entry.fl, speaker_emoji)
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
                'copy': entry.word.replace('*', ''),
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

    if cache_timeout:
        utils.rm_obsolete_cache(cachedir, cache_timeout)

    resp = request_mw_dictionary(api_key, query, cachedir, proxy)
    if not resp:
        return generate_response_items_no_such_word([]), None
    local_entries = []
    try:
        for entry in map(parse_json_resp_item, resp):
            if entry.prs_url:
                prs_local_path = request_mw_audio(entry.prs_url, cachedir,
                                                  proxy)
            else:
                prs_local_path = None
            local_entries.append(
                WordEntry(entry.id_, entry.word, entry.fl, prs_local_path,
                          entry.shortdef, entry.dict_url))
        return generate_response_items(local_entries), None
    except TypeError:
        # `resp` could be a list of candidate words (strings)
        return generate_response_items_no_such_word(resp), None


if __name__ == '__main__':
    main()
