import os
import re
from pathlib import Path
from urllib import parse, request
import datetime as dt
import gzip
import json
import shutil
import typing as ty


def get_cachedir() -> ty.Optional[Path]:
    """
    Returns ``None`` if 'cachedir' is not set.

    :raise FileNotFoundError: if 'cachedir' is set but does not exist
    """
    cachedir = os.getenv('cachedir')
    if not cachedir:
        return None
    cachedir = Path(cachedir).expanduser().resolve()
    if not cachedir.is_dir():
        raise FileNotFoundError(
            'cachedir "{}" does not exist'.format(cachedir))
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


def open_web_for_read(url: str, params: dict, proxy: ty.Optional[str]):
    if proxy:
        proxy_handler = request.ProxyHandler({
            'http': proxy,
            'https': proxy,
        })
        opener = request.build_opener(proxy_handler)
    else:
        opener = request.build_opener()
    opener.addheaders = [
        ('User-Agent',
         'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:109.0) '
         'Gecko/20100101 Firefox/109.0'),
    ]
    if params:
        url = '{}?{}'.format(url, parse.urlencode(params))
    return opener.open(url)


def request_web_json_cached(
    url: str,
    params: dict,
    cache_name: str,
    cachedir: ty.Optional[Path],
    cache_timeout: ty.Optional[dt.timedelta],
    proxy: ty.Optional[str],
    compressed: bool = None,
) -> ty.Union[dict, list]:
    """
    Request json response from web or cached file.

    :param url: the URL to request
    :param params: the parameters
    :param cache_name: the basename of the cache to save
    :param cachedir: the base directory for the cache
    :param cache_timeout: the expiration period for the cache; ``None`` means
           to never read from cache
    :param compressed: whether to save cache as gzipped file, default to
           ``True`` if ``cache_name`` ends with '.gz'
    :param proxy: the proxy IP address
    :return: the requested json response
    """
    save_cache = cachedir and cache_timeout
    if compressed is None:
        compressed = cache_name.endswith('.gz')
    if save_cache:
        filename = cachedir / cache_name
        if filename.is_file():
            mdate = dt.datetime.fromtimestamp(os.path.getmtime(filename))
            delta = dt.datetime.now() - mdate
            if delta > cache_timeout:
                os.remove(filename)
        try:
            if compressed:
                with gzip.open(filename, 'rb') as infile:
                    return json.loads(infile.read())
            else:
                with open(filename, 'rb') as infile:
                    return json.load(infile)
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    with open_web_for_read(url, params, proxy) as web:
        resp = json.loads(web.read())
    if not save_cache:
        return resp
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
    cachedir: ty.Optional[Path],
    cache_timeout: ty.Optional[dt.timedelta],
    proxy: ty.Optional[str],
) -> ty.Optional[Path]:
    """
    Request data blob from web or cached file.

    :param url: the URL to request
    :param params: the parameters
    :param cache_name: the basename of the cache to save
    :param cachedir: the base directory for the cache
    :param cache_timeout: the expiration period for the cache; ``None`` means
           to never read from cache
    :param proxy: the proxy IP address
    :return: the path of the downloaded data blob, or ``None`` if ``cachedir``
             is ``None``
    """
    if not cachedir:
        return None
    filename = cachedir / cache_name
    if filename.is_file():
        need_download = False
        if not cache_timeout:
            os.remove(filename)
            need_download = True
        else:
            mdate = dt.datetime.fromtimestamp(os.path.getmtime(filename))
            delta = dt.datetime.now() - mdate
            if delta > cache_timeout:
                os.remove(filename)
                need_download = True
    else:
        need_download = True
    if need_download:
        with open_web_for_read(url, params, proxy) as web, \
             open(filename, 'wb') as outfile:
            shutil.copyfileobj(web, outfile)
    return filename


def validate_filename(name: str, tr_table: ty.Dict[str, str] = None) -> str:
    """
    :param name: the basename to validate
    :param tr_table: a mapping from invalid chars to substitute chars, default
           to {':': '_', '/': '_', '\\\\': '_'}
    :return: validated basename
    """
    if tr_table is None:
        tr_table = {':': '_', '/': '_', '\\': '_'}
    for old, new in tr_table.items():
        name = name.replace(old, new)
    return name


def generate_response_err(err):
    return {
        'items': [
            {
                'title': 'Error occurs: {}'.format(type(err).__name__),
                'subtitle': 'Message: {}'.format(str(err)),
                'valid': False,
                'icon': {
                    'path': 'error-icon.png',
                },
            },
        ],
    }


def response_written(main: ty.Callable):
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
