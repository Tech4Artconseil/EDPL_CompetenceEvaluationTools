"""
Module: image_fetcher
Utilities to generate candidate trombi filenames and check/download remote images.
"""
import requests
import unicodedata
import re
from typing import Optional

BASE_URL = "https://neocampus.lecolededesign.com/uploads/trombi/"
HEADERS = {"User-Agent": "EDPL-ImageFetcher/1.0 (+https://example.local)"}


def normalize(s: str) -> str:
    s = (s or '').strip()
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = s.lower()
    return re.sub(r'[^a-z0-9]', '', s)


def name_parts(full_name: str):
    """Return (first, last) tokens from a full name string."""
    if not full_name:
        return ('', '')
    # remove common delimiters and extra whitespace
    s = full_name.strip().replace(',', ' ').replace(';', ' ')
    parts = [p for p in s.split() if p]
    if not parts:
        return ('', '')
    if len(parts) == 1:
        return (parts[0], parts[0])
    # Heuristic: if the first token looks like a LASTNAME in ALL CAPS and the last token is not,
    # assume format is "LAST FIRST" and swap so we return (first, last).
    first_token = parts[0]
    last_token = parts[-1]
    try:
        is_first_all_upper = first_token.isalpha() and first_token.upper() == first_token
    except Exception:
        is_first_all_upper = False
    try:
        is_last_all_upper = last_token.isalpha() and last_token.upper() == last_token
    except Exception:
        is_last_all_upper = False

    if is_first_all_upper and not is_last_all_upper:
        # treat as LAST FIRST -> swap
        return (last_token, first_token)
    return (first_token, last_token)


def candidates(first: str, last: str):
    f = normalize(first)
    l = normalize(last)
    cand = []
    if f and l:
        cand.append(f[0] + l)          # kaberkane
        cand.append(f + l)             # kenaaberkane
        cand.append(f + '.' + l)       # kena.aberkane
        cand.append(l + f[0])          # aberkank
    else:
        s = normalize(first or last)
        if s:
            cand.append(s)
    # ensure uniqueness preserving order
    seen = set()
    out = []
    for c in cand:
        if c and c not in seen:
            seen.add(c)
            out.append(c)
    return out


def fetch_photo_url(first: str, last: str, extensions=('jpg', 'png')) -> Optional[str]:
    """Try candidate filenames and return the first URL that exists and is an image.

    Does a HEAD request first to be light-weight; falls back to GET if HEAD not allowed.
    """
    for c in candidates(first, last):
        for ext in extensions:
            url = f"{BASE_URL}{c}.{ext}"
            try:
                r = requests.head(url, headers=HEADERS, timeout=8, allow_redirects=True)
                if r.status_code == 200 and r.headers.get('content-type', '').startswith('image'):
                    return url
                # Some servers don't support HEAD; try GET with small range
                if r.status_code in (405, 403, 501):
                    r2 = requests.get(url, headers=HEADERS, timeout=10, stream=True)
                    if r2.status_code == 200 and r2.headers.get('content-type', '').startswith('image'):
                        r2.close()
                        return url
                    r2.close()
            except requests.RequestException:
                continue
    return None
