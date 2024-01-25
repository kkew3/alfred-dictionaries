import os
import re
from pathlib import Path
import datetime as dt
import gzip
import json
import typing as ty

import requests
from fake_useragent import UserAgent


def get_cachedir() -> Path:
    """
    Returns the cache directory, which will be created if not exists.
    """
    try:
        cachedir = Path(os.environ['alfred_workflow_cache'])
    except KeyError as err:
        raise ValueError('alfred workflow bundle id not set') from err
    cachedir.mkdir(exist_ok=True)
    return cachedir


def get_cache_timeout() -> ty.Optional[dt.timedelta]:
    """
    Returns ``None`` if 'cache_timeout' is not set.

    :raise ValueError: if 'cache_timeout' is set but cannot be parsed
    """
    cache_timeout = os.getenv('cache_timeout')
    if not cache_timeout:
        return None
    try:
        return dt.timedelta(seconds=int(cache_timeout))
    except ValueError:
        pass
    m = re.match(r'(\d+)\s*([wdhms]?)', cache_timeout)
    if not m:
        raise ValueError(
            'invalid `cache_timeout` value "{}"'.format(cache_timeout))
    value = int(m.group(1))
    unit = m.group(2) or 's'
    unit_sec = {
        'w': 3600 * 24 * 7,
        'd': 3600 * 24,
        'h': 3600,
        'm': 60,
        's': 1,
    }[unit]
    return dt.timedelta(seconds=value * unit_sec)


def get_mw_api_key() -> ty.Optional[str]:
    """
    Returns ``None`` if the API key is not set.
    """
    return os.getenv('mw_api_key')


def get_proxy() -> ty.Optional[str]:
    """
    Returns ``None`` if 'proxy' is not set.
    """
    return os.getenv('proxy')


def rm_obsolete_cache(cachedir: Path, cache_timeout: dt.timedelta):
    now = dt.datetime.now()
    for cachefile in cachedir.iterdir():
        mt = os.path.getmtime(cachefile)
        if now - dt.datetime.fromtimestamp(mt) > cache_timeout:
            cachefile.unlink()


def open_web_for_read(
    url: str,
    params: dict,
    proxy: ty.Optional[str],
):
    """
    Return a ``requests`` response object.
    """
    headers = {'user-agent': UserAgent().safari}
    proxies = {'http': proxy, 'https': proxy} if proxy else {}
    return requests.get(
        url, params, headers=headers, proxies=proxies, stream=True)


def request_web_json_cached(
    url: str,
    params: dict,
    cache_name: str,
    cachedir: Path,
    proxy: ty.Optional[str],
    compressed: bool = None,
) -> ty.Union[dict, list]:
    """
    Request json response from web or cached file.

    :param url: the URL to request
    :param params: the parameters
    :param cache_name: the basename of the cache to save
    :param cachedir: the base directory for the cache
    :param compressed: whether to save cache as gzipped file, where ``None``
           means saving as gzipped file if ``cache_name`` ends with '.gz'
    :param proxy: the proxy IP address
    :return: the requested json response
    """
    if compressed is None:
        compressed = cache_name.endswith('.gz')
    filename = cachedir / cache_name
    # try to load from cache
    try:
        if compressed:
            with gzip.open(filename, 'rb') as infile:
                return json.loads(infile.read())
        else:
            with open(filename, 'rb') as infile:
                return json.load(infile)
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # read from web
    with open_web_for_read(url, params, proxy) as web:
        resp = web.json()
    # save cache
    if compressed:
        with gzip.open(filename, 'wb') as outfile:
            outfile.write(json.dumps(resp).encode('utf-8'))
    else:
        with open(filename, 'w', encoding='utf-8') as outfile:
            json.dump(resp, outfile)
    return resp


def request_web_data_blob_cached(
    url: str,
    params: dict,
    cache_name: str,
    cachedir: Path,
    proxy: ty.Optional[str],
) -> Path:
    """
    Request data blob from web or cached file.

    :param url: the URL to request
    :param params: the parameters
    :param cache_name: the basename of the cache to save
    :param cachedir: the base directory for the cache
    :param proxy: the proxy IP address
    :return: the path of the downloaded data blob, or ``None`` if ``cachedir``
             is ``None``
    """
    filename = cachedir / cache_name
    if not filename.is_file():
        with open_web_for_read(url, params, proxy) as web, \
             open(filename, 'wb') as outfile:
            for chunk in web.iter_content(1048576):
                outfile.write(chunk)
    return filename


def generate_response_err(err):
    return {
        'items': [
            {
                'title': f'Error occurs: {type(err).__name__}',
                'subtitle': f'Message: {err}',
                'valid': False,
                'icon': {
                    'path': 'error-icon.png',
                },
            },
        ],
    }


def response_written(main: ty.Callable[[], ty.Tuple[list, ty.Optional[dict]]]):
    """
    This is a decorator. The decorated function should return Alfred items dict
    and an optional variables dict, which will be written to stdout as Alfred
    json.
    """
    def _wrapper():
        try:
            items, variables = main()
        except Exception as err:
            resp = generate_response_err(err)
        else:
            resp = {'items': items}
            if variables:
                resp['variables'] = variables
        print(json.dumps(resp), end='')

    return _wrapper


def applescript_as_cmd(applescript: str, *argv) -> ty.List[str]:
    """
    Rewrite a piece of applescript as ``osascript`` command line.
    """
    cmd = ['osascript']
    for line in filter(None, applescript.split('\n')):
        cmd.extend(['-e', line.strip()])
    cmd.extend(argv)
    return cmd
