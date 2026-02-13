import os
import time
import re
import base64
import unicodedata
from datetime import date
from werkzeug.utils import secure_filename
try:
    from PIL import Image as _PILImage
    have_pillow = True
except Exception:
    _PILImage = None
    have_pillow = False


def _get_photo_type(photo_val):
    p = (photo_val or '').strip()
    if not p:
        return 'empty'
    pl = p.lower()
    if pl.startswith('data:image/'):
        return 'data'
    if pl.startswith('http://') or pl.startswith('https://'):
        return 'uri'
    return 'other'


def _normalize_name_for_filename(name: str) -> str:
    if not name:
        return ''
    # lowercase, remove accents, keep only alnum
    s = unicodedata.normalize('NFKD', name)
    s = ''.join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = ''.join(ch for ch in s if ch.isalnum())
    return s


def _save_data_uri_to_file(data_uri: str, prefix: str = 'photo', student_name: str = None, max_bytes: int = 3 * 1024 * 1024) -> str:
    """Decode a data:image/...;base64,... URI and save it under static/uploads/trombi.

    Returns the web path ("/static/uploads/trombi/<file>") on success, or None on failure.
    """
    print('[IMPORT_CSV] _save_data_uri_to_file: start')
    if not data_uri or not data_uri.lower().startswith('data:image/'):
        print('[IMPORT_CSV] data_uri missing or not image')
        return None
    m = re.match(r'^data:(image/[^;]+);base64,(.+)$', data_uri, re.I | re.S)
    if not m:
        print('[IMPORT_CSV] regex did not match data URI format')
        return None
    mime = m.group(1).lower()
    b64 = m.group(2)
    print(f'[IMPORT_CSV] mime detected: {mime}')
    if (b64.startswith('"') and b64.endswith('"')) or (b64.startswith("'") and b64.endswith("'")):
        b64 = b64[1:-1]
    b64 = re.sub(r'\s+', '', b64)
    b64 = b64.replace('-', '+').replace('_', '/')
    b64 = b64.replace('"', '').replace("'", '')
    mod = len(b64) % 4
    if mod != 0:
        pad = 4 - mod
        b64 += '=' * pad
        print(f'[IMPORT_CSV] added padding: {pad}')
    print(f'[IMPORT_CSV] base64 length after cleanup: {len(b64)}')
    try:
        raw = base64.b64decode(b64, validate=True)
    except Exception as e:
        print('[IMPORT_CSV] base64 decode validate failed:', repr(e))
        try:
            raw = base64.b64decode(b64)
        except Exception as e2:
            print('[IMPORT_CSV] base64 decode fallback failed:', repr(e2))
            return None
    print(f'[IMPORT_CSV] decoded bytes: {len(raw)}')
    if len(raw) > max_bytes:
        print('[IMPORT_CSV] decoded image exceeds max_bytes')
        return None

    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'trombi'))
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print('[IMPORT_CSV] failed to create folder:', repr(e))
        return None

    timestamp = int(time.time() * 1000)
    # Determine filename base: prefer student_name if provided, else prefix+timestamp
    today = date.today().strftime('%Y_%m_%d')
    if student_name:
        base = _normalize_name_for_filename(student_name)
        if base:
            filename_base = f"{base}_{today}"
        else:
            filename_base = f"{prefix}_{timestamp}"
    else:
        filename_base = f"{prefix}_{timestamp}"

    # Always save as JPEG to match conversion requirement
    filename = f"{filename_base}.jpg"
    filename = secure_filename(filename)
    path = os.path.join(folder, filename)

    if have_pillow:
        try:
            print('[IMPORT_CSV] Pillow available: validating and converting image to JPEG')
            from io import BytesIO
            bio = BytesIO(raw)
            img = _PILImage.open(bio)
            img.verify()
            bio.seek(0)
            img = _PILImage.open(bio)
            # convert to RGB for JPEG
            if img.mode not in ('RGB', 'L'):
                img = img.convert('RGB')
            img.save(path, format='JPEG', quality=90)
            print('[IMPORT_CSV] saved via Pillow as JPEG:', path)
            return f'/static/uploads/trombi/{filename}'
        except Exception as e:
            print('[IMPORT_CSV] Pillow processing failed:', repr(e))
            # fallback to raw write below
            pass

    # Fallback: write raw decoded bytes with .jpg extension (may not be a true JPEG)
    try:
        with open(path, 'wb') as fh:
            fh.write(raw)
        print('[IMPORT_CSV] saved raw bytes to:', path)
    except Exception as e:
        print('[IMPORT_CSV] failed to write raw bytes:', repr(e))
        return None
    return f'/static/uploads/trombi/{filename}'


def _debug_save_data_uri(data_uri: str, prefix: str = 'photo', student_name: str = None) -> str:
    try:
        print(f"[IMPORT_CSV] debug wrapper: saving data-uri prefix={prefix} student_name={student_name}")
        res = _save_data_uri_to_file(data_uri, prefix=prefix, student_name=student_name)
        print(f"[IMPORT_CSV] debug wrapper: result={res}")
        return res
    except Exception as e:
        print('[IMPORT_CSV] debug wrapper exception:', repr(e))
        return None
