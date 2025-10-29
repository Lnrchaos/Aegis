from __future__ import annotations
from typing import Any, List, Dict, Optional, Callable
import base64
import binascii
import hashlib
import hmac
import os
import json
import time
from urllib.parse import urlencode, quote_plus, unquote_plus, urlparse, urljoin
from urllib import robotparser

import requests
from bs4 import BeautifulSoup

from .runtime import NativeFunction
from .security import SECURITY_FUNCTIONS


def _wrap(fn: Callable[..., Any]):
    def inner(args: List[Any]):
        return fn(*args)
    nf = NativeFunction(name=fn.__name__, func=inner)
    return nf


# -------------------- HTTP --------------------

def make_http() -> Dict[str, Any]:
    def to_resp(r: requests.Response) -> Dict[str, Any]:
        text = r.text
        headers = {k: v for k, v in r.headers.items()}
        try:
            js = r.json()
        except Exception:
            js = None
        return {
            "status": r.status_code,
            "headers": headers,
            "text": text,
            "json": js,
        }

    def get(url: str, headers: Dict[str, str] = None):
        r = requests.get(url, headers=headers)
        return to_resp(r)

    def post(url: str, data: Any = None, json_body: Any = None, headers: Dict[str, str] = None):
        r = requests.post(url, data=data, json=json_body, headers=headers)
        return to_resp(r)

    def fetch(opts: Dict[str, Any]):
        method = opts.get("method", "GET").upper()
        url = opts["url"]
        headers = opts.get("headers")
        params = opts.get("params")
        data = opts.get("data")
        json_body = opts.get("json")
        r = requests.request(method, url, headers=headers, params=params, data=data, json=json_body)
        return to_resp(r)

    def session():
        s = requests.Session()

        def s_get(url: str, headers: Dict[str, str] = None):
            return to_resp(s.get(url, headers=headers))

        def s_post(url: str, data: Any = None, json_body: Any = None, headers: Dict[str, str] = None):
            return to_resp(s.post(url, data=data, json=json_body, headers=headers))

        def s_fetch(opts: Dict[str, Any]):
            method = opts.get("method", "GET").upper()
            url = opts["url"]
            headers = opts.get("headers")
            params = opts.get("params")
            data = opts.get("data")
            json_body = opts.get("json")
            r = s.request(method, url, headers=headers, params=params, data=data, json=json_body)
            return to_resp(r)

        return {
            "get": _wrap(s_get),
            "post": _wrap(s_post),
            "fetch": _wrap(s_fetch),
        }

    def batch(reqs: List[Dict[str, Any]]):
        results = []
        for req in reqs:
            results.append(fetch(req))
        return results

    # robots.txt helper with cache
    robots_cache: Dict[str, robotparser.RobotFileParser] = {}

    def robots_can_fetch(user_agent: str, url: str):
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        rb = robots_cache.get(base)
        if rb is None:
            rb = robotparser.RobotFileParser()
            rb.set_url(urljoin(base, "/robots.txt"))
            try:
                rb.read()
            except Exception:
                pass
            robots_cache[base] = rb
        return bool(rb.can_fetch(user_agent, url))

    return {
        "get": _wrap(get),
        "post": _wrap(post),
        "fetch": _wrap(fetch),
        "session": _wrap(session),
        "batch": _wrap(batch),
        "robots_can_fetch": _wrap(robots_can_fetch),
    }


# -------------------- HTML --------------------

class _NodeWrapper:
    def __init__(self, el):
        self._el = el

    def as_object(self) -> Dict[str, Any]:
        def css(selector: str):
            return [ _NodeWrapper(e).as_object() for e in self._el.select(selector) ]

        def text():
            return self._el.get_text()

        def attr(name: str):
            return self._el.get(name)

        def html():
            return str(self._el)

        return {
            "css": _wrap(css),
            "text": _wrap(text),
            "attr": _wrap(attr),
            "html": _wrap(html),
        }


def make_html() -> Dict[str, Any]:
    def parse_html(html_str: str):
        soup = BeautifulSoup(html_str, "html.parser")
        return _NodeWrapper(soup).as_object()

    return {
        "parse": _wrap(parse_html),
    }


# -------------------- CRYPTO --------------------

def make_crypto() -> Dict[str, Any]:
    def sha256(data: Any):
        return hashlib.sha256(_to_bytes(data)).hexdigest()

    def sha1(data: Any):
        return hashlib.sha1(_to_bytes(data)).hexdigest()

    def md5(data: Any):
        return hashlib.md5(_to_bytes(data)).hexdigest()

    def hmac_sha256(key: Any, data: Any):
        return hmac.new(_to_bytes(key), _to_bytes(data), hashlib.sha256).hexdigest()

    def random_bytes(n: int):
        return binascii.hexlify(os.urandom(int(n))).decode()

    return {
        "sha256": _wrap(sha256),
        "sha1": _wrap(sha1),
        "md5": _wrap(md5),
        "hmac_sha256": _wrap(hmac_sha256),
        "random_bytes": _wrap(random_bytes),
    }


# -------------------- ENCODING --------------------

def make_encoding() -> Dict[str, Any]:
    def base64_encode(data: Any):
        return base64.b64encode(_to_bytes(data)).decode()

    def base64_decode(data: str):
        return base64.b64decode(data.encode()).decode(errors="ignore")

    def hex_encode(data: Any):
        return binascii.hexlify(_to_bytes(data)).decode()

    def hex_decode(data: str):
        return binascii.unhexlify(data.encode()).decode(errors="ignore")

    def url_encode(params: Dict[str, Any]):
        return urlencode(params)

    def url_component_encode(s: str):
        return quote_plus(str(s))

    def url_component_decode(s: str):
        return unquote_plus(s)

    return {
        "base64_encode": _wrap(base64_encode),
        "base64_decode": _wrap(base64_decode),
        "hex_encode": _wrap(hex_encode),
        "hex_decode": _wrap(hex_decode),
        "url_encode": _wrap(url_encode),
        "url_component_encode": _wrap(url_component_encode),
        "url_component_decode": _wrap(url_component_decode),
    }


# -------------------- URL --------------------

def make_url() -> Dict[str, Any]:
    def parse_url(u: str):
        p = urlparse(u)
        return {
            "scheme": p.scheme,
            "host": p.netloc,
            "path": p.path,
            "query": p.query,
            "fragment": p.fragment,
        }

    def join(base: str, rel: str):
        return urljoin(base, rel)

    return {
        "parse": _wrap(parse_url),
        "join": _wrap(join),
    }


# -------------------- REGEX --------------------

def make_regex() -> Dict[str, Any]:
    import re

    def _flags(opts: Optional[Dict[str, bool]] = None) -> int:
        if not opts:
            return 0
        m = 0
        if opts.get("i") or opts.get("ignorecase"):
            m |= re.IGNORECASE
        if opts.get("m") or opts.get("multiline"):
            m |= re.MULTILINE
        if opts.get("s") or opts.get("dotall"):
            m |= re.DOTALL
        return m

    def findall(pattern: str, text: str, flags: Optional[Dict[str, bool]] = None):
        return re.findall(pattern, text, _flags(flags))

    def search(pattern: str, text: str, flags: Optional[Dict[str, bool]] = None):
        m = re.search(pattern, text, _flags(flags))
        if not m:
            return None
        return {"match": m.group(0), "groups": list(m.groups())}

    def match(pattern: str, text: str, flags: Optional[Dict[str, bool]] = None):
        m = re.match(pattern, text, _flags(flags))
        if not m:
            return None
        return {"match": m.group(0), "groups": list(m.groups())}

    def sub(pattern: str, repl: str, text: str, flags: Optional[Dict[str, bool]] = None):
        return re.sub(pattern, repl, text, _flags(flags))

    return {
        "findall": _wrap(findall),
        "search": _wrap(search),
        "match": _wrap(match),
        "sub": _wrap(sub),
    }


# -------------------- FS (guarded) --------------------

def make_fs(flags: Dict[str, bool]) -> Dict[str, Any]:
    def _check():
        if not flags.get("fs", False):
            raise PermissionError("Filesystem access is disabled by sandbox")

    def read_text(path: str, encoding: str = "utf-8"):
        _check()
        with open(path, "r", encoding=encoding) as f:
            return f.read()

    def write_text(path: str, content: str, encoding: str = "utf-8"):
        _check()
        with open(path, "w", encoding=encoding) as f:
            f.write(str(content))
            return True

    return {
        "read_text": _wrap(read_text),
        "write_text": _wrap(write_text),
    }


# -------------------- TIME --------------------

def make_time() -> Dict[str, Any]:
    def now_ms():
        return int(time.time() * 1000)

    def monotonic_ms():
        return int(time.monotonic() * 1000)

    def sleep_ms(ms: int):
        time.sleep(max(0, int(ms)) / 1000.0)
        return True

    return {
        "now_ms": _wrap(now_ms),
        "monotonic_ms": _wrap(monotonic_ms),
        "sleep_ms": _wrap(sleep_ms),
    }


def _to_bytes(data: Any) -> bytes:
    if isinstance(data, bytes):
        return data
    if isinstance(data, str):
        return data.encode()
    return json.dumps(data).encode()


