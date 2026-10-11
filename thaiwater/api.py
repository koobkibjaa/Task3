
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import config

_session = None


def get_session():
    global _session
    if _session is None:
        retry = Retry(total=3, backoff_factor=2, status_forcelist=[429, 500, 502, 503, 504], allowed_methods=["GET"])
        _session = requests.Session()
        _session.mount("https://", HTTPAdapter(max_retries=retry))
    return _session


def get_json(url, params=None):
    response = get_session().get(url, params=params, timeout=config.TIMEOUT)
    response.raise_for_status()
    return response.json()
