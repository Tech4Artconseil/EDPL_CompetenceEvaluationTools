#!/usr/bin/env python3
import sys
import os
import argparse
import csv
import io

# Ensure we can import the module in the package
pkg_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, pkg_dir)

try:
    from import_csv import _save_data_uri_to_file
except Exception:
    # Fallback lightweight implementation so the test script can run
    import base64
    import re
    import time

    def _simple_secure_filename(name: str) -> str:
        name = os.path.basename(name)
        name = re.sub(r'[^A-Za-z0-9._-]', '_', name)
        return name

    def _save_data_uri_to_file(data_uri: str, prefix: str = 'photo', max_bytes: int = 3 * 1024 * 1024) -> str:
        if not data_uri or not data_uri.lower().startswith('data:image/'):
            return None
        m = re.match(r'^data:(image/[^;]+);base64,(.+)$', data_uri, re.I | re.S)
        if not m:
            return None
        mime = m.group(1).lower()
        b64 = m.group(2)
        b64 = re.sub(r'\s+', '', b64)
        try:
            raw = base64.b64decode(b64, validate=True)
        except Exception:
            try:
                raw = base64.b64decode(b64)
            except Exception:
                return None
        if len(raw) > max_bytes:
            return None

        ext_map = {'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png', 'image/gif': 'gif', 'image/webp': 'webp'}
        ext = ext_map.get(mime, 'jpg')
        filename = f"{prefix}_{int(time.time() * 1000)}.{ext}"
        filename = _simple_secure_filename(filename)
        folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'trombi'))
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception:
            return None
        path = os.path.join(folder, filename)
        try:
            with open(path, 'wb') as fh:
                fh.write(raw)
        except Exception:
            return None
        return f'/static/uploads/trombi/{filename}'


def find_data_uri_in_csv(path):
    with open(path, 'rb') as f:
        raw = f.read()
    try:
        text = raw.decode('utf-8-sig')
    except Exception:
        text = raw.decode('latin-1')
    # detect simple delimiter
    sample = text[:8192]
    delim = ','
    try:
        from csv import Sniffer
        s = Sniffer()
        d = s.sniff(sample)
        delim = d.delimiter
    except Exception:
        for c in (',', ';', '\t', '|'):
            if c in sample:
                delim = c
                break
    print('Detected delimiter:', delim)
    stream = io.StringIO(text)
    reader = csv.reader(stream, delimiter=delim)
    for lineno, cols in enumerate(reader, start=1):
        if not cols or all((not c or c.strip() == '') for c in cols):
            continue
        for ci, col in enumerate(cols, start=1):
            cval = (col or '').strip()
            # remove surrounding quotes added by some exporters
            if (cval.startswith('"') and cval.endswith('"')) or (cval.startswith("'") and cval.endswith("'")):
                cval = cval[1:-1]
            cval = cval.strip()
            if cval.lower().startswith('data:image/'):
                return lineno, ci, cval
    return None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('csv', nargs='?', help='Path to CSV file to test')
    args = parser.parse_args()

    csv_path = args.csv
    if not csv_path:
        print('Please provide a CSV path as first argument.')
        sys.exit(2)
    if not os.path.exists(csv_path):
        print('CSV not found:', csv_path)
        sys.exit(2)

    found = find_data_uri_in_csv(csv_path)
    if not found:
        print('No data:image/... found in CSV')
        sys.exit(0)
    lineno, colidx, data_uri = found
    print(f'Found data-URI at line {lineno} col {colidx}, len={len(data_uri)}')

    # use a fixed prefix for testing so filename is easy to find
    def debug_save_data_uri(data_uri, prefix='TESTimage'):
        print('Calling helper _save_data_uri_to_file...')
        try:
            res = _save_data_uri_to_file(data_uri, prefix=prefix)
        except Exception as e:
            print('Helper raised exception:', repr(e))
            res = None
        if res:
            print('Helper returned path:', res)
            return res

        print('Helper returned None — running manual debug steps')
        import re, base64, time
        m = re.match(r'^data:(image/[^;]+);base64,(.+)$', data_uri, re.I | re.S)
        if not m:
            print('Regex did not match data URI')
            return None
        mime = m.group(1).lower()
        b64 = m.group(2)
        b64 = re.sub(r'\s+', '', b64)
        print('Base64 length after whitespace removal:', len(b64))
        # support base64url variants
        b64 = b64.replace('-', '+').replace('_', '/')
        # detect invalid characters but DO NOT remove them (removal may corrupt data)
        import re as _re
        invalid = [(i, ch) for i, ch in enumerate(b64) if not _re.match(r'[A-Za-z0-9+/=]', ch)]
        if invalid:
            print('Found invalid base64 characters (index, char) sample:', invalid[:10])
            print('Total invalid chars:', len(invalid))
            # do not strip them; we'll try decoding with padding and report errors
        else:
            print('No invalid base64 characters found')
        # fix missing padding: base64 length must be multiple of 4
        mod = len(b64) % 4
        if mod != 0:
            pad = 4 - mod
            b64 += '=' * pad
            print(f'Added padding: {pad} (= chars)')
        try:
            raw = base64.b64decode(b64, validate=True)
            print('Decoded with validate=True, bytes:', len(raw))
        except Exception as e:
            print('validate decode failed:', repr(e))
            try:
                raw = base64.b64decode(b64)
                print('Decoded with fallback, bytes:', len(raw))
            except Exception as e2:
                print('Fallback decode failed:', repr(e2))
                return None

        # check size
        max_bytes = 3 * 1024 * 1024
        if len(raw) > max_bytes:
            print('Decoded image too large:', len(raw), '>', max_bytes)
            return None

        ext_map = {'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png', 'image/gif': 'gif', 'image/webp': 'webp'}
        ext = ext_map.get(mime, None)
        if not ext:
            try:
                import imghdr
                guessed = imghdr.what(None, h=raw)
                print('imghdr guessed:', guessed)
                if guessed:
                    ext = 'jpg' if guessed == 'jpeg' else guessed
            except Exception as e:
                print('imghdr failed:', repr(e))
        if not ext:
            ext = 'bin'

        filename = f"{prefix}_{int(time.time() * 1000)}.{ext}"
        try:
            from werkzeug.utils import secure_filename as _wf
            filename = _wf(filename)
        except Exception:
            filename = ''.join(c if c.isalnum() or c in '._-' else '_' for c in filename)

        folder = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads', 'trombi'))
        print('Target folder:', folder)
        try:
            os.makedirs(folder, exist_ok=True)
        except Exception as e:
            print('Failed to make folder:', repr(e))
            return None
        path = os.path.join(folder, filename)
        print('Will write file:', path)
        try:
            with open(path, 'wb') as fh:
                fh.write(raw)
        except Exception as e:
            print('Failed to write file:', repr(e))
            return None
        print('Wrote bytes:', os.path.getsize(path))
        return f'/static/uploads/trombi/{filename}'

    saved = debug_save_data_uri(data_uri, prefix='TESTimage')
    if saved:
        filename = os.path.basename(saved)
        fs_path = os.path.join(pkg_dir, 'static', 'uploads', 'trombi', filename)
        print('Saved web path:', saved)
        print('Filesystem path:', fs_path)
        print('Exists:', os.path.exists(fs_path))
        if os.path.exists(fs_path):
            print('Size bytes:', os.path.getsize(fs_path))
    else:
        print('Save failed (helper returned None)')


if __name__ == '__main__':
    main()
