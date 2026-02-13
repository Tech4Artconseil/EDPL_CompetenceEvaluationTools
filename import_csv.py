from flask import Blueprint, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
import csv
import io
from Data_Models import Db, Studnt, StudntGrp, Skill, Evaluat, Score
try:
    from bs4 import BeautifulSoup
    have_bs4 = True
except Exception:
    BeautifulSoup = None
    have_bs4 = False
try:
    from PIL import Image as _PILImage
    have_pillow = True
except Exception:
    _PILImage = None
    have_pillow = False
import re
from urllib.parse import urljoin, urlparse, parse_qs

import difflib
import unicodedata
import os
import time
import base64
# Blueprint for importer routes
from flask import Blueprint as _Blueprint
importer_bp = _Blueprint('importer', __name__, url_prefix='/admin/import')
@importer_bp.route('/studnts', methods=['GET', 'POST'])
def import_studnts():
    if request.method == 'POST':
        # Confirmed import (second step): form contains serialized rows
        if request.form.get('confirm') == '1':
            # force_group override id (optional)
            force_gid = request.form.get('force_group')
            try:
                force_gid = int(force_gid) if force_gid else None
            except Exception:
                force_gid = None

            # reconstruct rows
            rows = []
            i = 0
            while True:
                name = request.form.get(f'row_{i}_name')
                email = request.form.get(f'row_{i}_email')
                group_val = request.form.get(f'row_{i}_group')
                photo_val = request.form.get(f'row_{i}_photo')
                if name is None and email is None and group_val is None and photo_val is None:
                    break
                rows.append({'name': (name or '').strip(), 'email': (email or '').strip(), 'group': (group_val or '').strip(), 'photo': (photo_val or '').strip()})
                i += 1

            # perform import using rows
            created = 0
            updated = 0
            errors = []

            # ensure default group exists
            default_group = StudntGrp.query.first()
            if not default_group:
                default_group = StudntGrp(Name='Imported')
                Db.session.add(default_group)
                Db.session.commit()

            for idx, r in enumerate(rows, start=1):
                name = r['name']
                email = r['email']
                group_val = r['group']
                photo_val = (r.get('photo') or '').strip()

                # normalize/remove surrounding quotes
                if photo_val and photo_val.startswith('"') and photo_val.endswith('"'):
                    photo_val = photo_val[1:-1]
                photo_val = (photo_val or '').strip()

                # If the CSV contains a data-URI image, decode and save it as a file
                if photo_val and photo_val.lower().startswith('data:image/'):
                    saved = _save_data_uri_to_file(photo_val)
                    if saved:
                        photo_val = saved
                    else:
                        errors.append(f'Line {idx}: failed to save photo from data-URI')

                if not name:
                    errors.append(f'Line {idx}: missing name')
                    continue

                if not _is_valid_email(email):
                    email = _generate_email_from_name(name, suffix=str(idx))

                # determine target group: forced override wins, else parsed value
                group = None
                if force_gid:
                    group = StudntGrp.query.get(force_gid)
                else:
                    group = _find_group_by_name(group_val) if group_val else None
                if not group:
                    group = default_group

                existing = Studnt.query.filter_by(Email=email).first()
                if existing:
                    existing.Name = name
                    # update photo url if provided
                    if photo_val:
                        existing.Photo_Url = photo_val
                    existing.Group_Id = group.Id
                    Db.session.flush()
                    if existing.Group_Id:
                        _create_scores_for_student(existing.Id, existing.Group_Id)
                    updated += 1
                else:
                    new = Studnt(Name=name, Email=email, Photo_Url=photo_val or None, Group_Id=group.Id)
                    Db.session.add(new)
                    Db.session.flush()
                    if new.Group_Id:
                        _create_scores_for_student(new.Id, new.Group_Id)
                    created += 1

            Db.session.commit()
            return render_template('admin_import_result.html', resource='studnts', created=created, updated=updated, errors=errors)

        # initial upload -> build preview
        f = request.files.get('csvfile')
        if not f:
            flash('No file uploaded', 'error')
            return redirect(url_for('importer.import_studnts'))

        raw = f.stream.read()
        try:
            text = raw.decode('utf-8-sig')
        except Exception:
            text = raw.decode('latin-1')

        # Try to detect delimiter and presence of header (robust fallback)
        sample = text[:8192]
        dialect = None
        delimiter = ','
        has_header = False
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
            has_header = sniffer.has_header(sample)
        except Exception:
            # fallback: choose the most frequent candidate delimiter on sample
            cand = [',', ';', '\t', '|']
            counts = {c: sample.count(c) for c in cand}
            # prefer semicolon for regional Excel exports when counts are similar
            if counts.get(';', 0) >= counts.get(',', 0) and counts.get(';', 0) > 0:
                delimiter = ';'
            else:
                delimiter = max(counts, key=counts.get)
            has_header = False

        stream = io.StringIO(text)
        created = 0
        updated = 0
        errors = []

        # prepare preview rows
        preview_rows = []

        if has_header:
            # DictReader may fail on malformed CSVs; try it but fallback to manual parsing on error
            try:
                reader = csv.DictReader(stream, delimiter=delimiter)
                for i, row in enumerate(reader, start=1):
                    # case-insensitive header lookup
                    h = {k.strip().lower(): (v or '').strip() for k, v in row.items()}
                    name = h.get('name') or h.get('nom') or h.get('fullname')
                    email = (h.get('email') or h.get('mail') or '').strip()
                    group_val = h.get('group') or h.get('group_name') or h.get('group_id')
                    photo_val = h.get('photo') or h.get('photo_url') or h.get('photourl') or h.get('image') or h.get('image_url') or ''
                    if not name:
                        errors.append(f'Line {i}: missing name')
                        preview_rows.append({'name': '', 'email': email, 'group': group_val, 'photo': ''})
                        continue
                    # validate email or generate synthetic one
                    if not _is_valid_email(email):
                        email = _generate_email_from_name(name, suffix=str(i))

                    preview_rows.append({'name': name, 'email': email, 'group': group_val, 'photo': (photo_val or '').strip()})
            except csv.Error:
                # fallback: parse raw text lines manually using chosen delimiter
                stream2 = io.StringIO(text)
                for i, line in enumerate(stream2.read().splitlines(), start=1):
                    if not line or line.strip() == '':
                        continue
                    cols = [c.strip() for c in line.split(delimiter)]
                    if len(cols) < 2:
                        errors.append(f'Line {i}: not enough columns')
                        preview_rows.append({'name': '', 'email': '', 'group': '', 'photo': ''})
                        continue
                    name = cols[0]
                    email = cols[1]
                    group_val = cols[2] if len(cols) >= 3 else None
                    photo_val = cols[3] if len(cols) >= 4 else ''
                    # remove surrounding quotes if present
                    if photo_val and photo_val.startswith('"') and photo_val.endswith('"'):
                        photo_val = photo_val[1:-1]
                    if not name:
                        errors.append(f'Line {i}: missing name')
                        preview_rows.append({'name': '', 'email': email, 'group': group_val, 'photo': ''})
                        continue
                    email = (email or '').strip()
                    if not _is_valid_email(email):
                        email = _generate_email_from_name(name, suffix=str(i))
                    preview_rows.append({'name': name, 'email': email, 'group': group_val, 'photo': (photo_val or '').strip()})
        else:
            # No header: parse rows by position. Accept 2-4 columns: Name;Email;Group;Photo
            # Use csv.reader but fallback to manual parsing on csv.Error (unquoted newlines etc.)
            try:
                reader = csv.reader(stream, delimiter=delimiter)
                for i, cols in enumerate(reader, start=1):
                    # skip empty lines
                    if not cols or all((not c or c.strip() == '') for c in cols):
                        continue
                    # normalize columns
                    cols = [c.strip() for c in cols]
                    if len(cols) >= 2:
                        name = cols[0]
                        email = cols[1]
                        group_val = cols[2] if len(cols) >= 3 else None
                        photo_val = cols[3] if len(cols) >= 4 else None
                    else:
                        errors.append(f'Line {i}: not enough columns')
                        preview_rows.append({'name': '', 'email': '', 'group': '', 'photo': ''})
                        continue

                    if not name:
                        errors.append(f'Line {i}: missing name')
                        preview_rows.append({'name': '', 'email': email, 'group': group_val, 'photo': ''})
                        continue
                    email = (email or '').strip()
                    if not _is_valid_email(email):
                        email = _generate_email_from_name(name, suffix=str(i))

                    preview_rows.append({'name': name, 'email': email, 'group': group_val, 'photo': (photo_val or '').strip()})
            except csv.Error:
                # fallback: more tolerant line-by-line split using detected delimiter
                stream2 = io.StringIO(text)
                for i, line in enumerate(stream2.read().splitlines(), start=1):
                    if not line or line.strip() == '':
                        continue
                    cols = [c.strip() for c in line.split(delimiter)]
                    if len(cols) < 2:
                        errors.append(f'Line {i}: not enough columns')
                        preview_rows.append({'name': '', 'email': '', 'group': '', 'photo': ''})
                        continue
                    name = cols[0]
                    email = cols[1]
                    group_val = cols[2] if len(cols) >= 3 else None
                    photo_val = cols[3] if len(cols) >= 4 else ''
                    # remove surrounding quotes if present
                    if photo_val and photo_val.startswith('"') and photo_val.endswith('"'):
                        photo_val = photo_val[1:-1]
                    if not name:
                        errors.append(f'Line {i}: missing name')
                        preview_rows.append({'name': '', 'email': email, 'group': group_val, 'photo': ''})
                        continue
                    email = (email or '').strip()
                    if not _is_valid_email(email):
                        email = _generate_email_from_name(name, suffix=str(i))
                    preview_rows.append({'name': name, 'email': email, 'group': group_val, 'photo': (photo_val or '').strip()})
        # pass groups for dropdown (allow forcing target group)
        groups = StudntGrp.query.order_by(StudntGrp.Name).all()
        return render_template('admin_import_preview.html', rows=preview_rows, groups=groups, errors=errors)

    return render_template('admin_import.html', resource='studnts')


@importer_bp.route('/skills', methods=['GET', 'POST'])
def import_skills():
    if request.method == 'POST':
        f = request.files.get('csvfile')
        if not f:
            flash('No file uploaded', 'error')
            return redirect(url_for('importer.import_skills'))

        raw = f.stream.read()
        try:
            text = raw.decode('utf-8-sig')
        except Exception:
            text = raw.decode('latin-1')

        sample = text[:4096]
        delimiter = ','
        has_header = False
        try:
            sniffer = csv.Sniffer()
            dialect = sniffer.sniff(sample)
            delimiter = dialect.delimiter
            has_header = sniffer.has_header(sample)
        except Exception:
            if ';' in sample:
                delimiter = ';'
            else:
                delimiter = ','
            has_header = False

        stream = io.StringIO(text)
        created = 0
        updated = 0
        errors = []

        if has_header:
            reader = csv.DictReader(stream, delimiter=delimiter)
            for i, row in enumerate(reader, start=1):
                h = {k.strip().lower(): (v or '').strip() for k, v in row.items()}
                code = h.get('code') or h.get('code')
                descrip = h.get('descrip') or h.get('description') or h.get('desc') or ''
                skillset = h.get('skillset_id') or h.get('skillset')
                if not code or not skillset:
                    errors.append(f'Line {i}: missing code or skillset_id')
                    continue

                existing = Skill.query.filter_by(Code=code, SkillSet_Id=skillset).first()
                if existing:
                    existing.Descrip = descrip or existing.Descrip
                    updated += 1
                else:
                    new = Skill(Code=code, Descrip=descrip or '', SkillSet_Id=skillset)
                    Db.session.add(new)
                    created += 1
        else:
            reader = csv.reader(stream, delimiter=delimiter)
            for i, cols in enumerate(reader, start=1):
                if not cols or all((not c or c.strip()=='') for c in cols):
                    continue
                cols = [c.strip() for c in cols]
                # Support two common no-header layouts:
                # - three columns: Code; Descrip; SkillSet_Id
                # - four columns: Id; SkillSet_Id; Code; Descrip
                if len(cols) >= 4:
                    # assume: ID, SkillSet_Id, Code, Descrip
                    # ignore ID column
                    skillset = cols[1]
                    code = cols[2]
                    descrip = cols[3]
                elif len(cols) >= 3:
                    # assume: Code, Descrip, SkillSet_Id
                    code = cols[0]
                    descrip = cols[1]
                    skillset = cols[2]
                elif len(cols) == 2:
                    # minimal: Code, Descrip (no skillset)
                    code = cols[0]
                    descrip = cols[1]
                    skillset = None
                else:
                    errors.append(f'Line {i}: not enough columns')
                    continue

                if not code or not skillset:
                    errors.append(f'Line {i}: missing code or skillset_id')
                    continue

                existing = Skill.query.filter_by(Code=code, SkillSet_Id=skillset).first()
                if existing:
                    existing.Descrip = descrip or existing.Descrip
                    updated += 1
                else:
                    new = Skill(Code=code, Descrip=descrip or '', SkillSet_Id=skillset)
                    Db.session.add(new)
                    created += 1

        Db.session.commit()
        return render_template('admin_import_result.html', resource='skills', created=created, updated=updated, errors=errors)

    return render_template('admin_import.html', resource='skills')


@importer_bp.route('/from_html', methods=['GET', 'POST'])
def import_from_html():
    """Upload an HTML file and extract names, emails and image URLs."""
    if request.method == 'POST':
        if not have_bs4:
            flash('beautifulsoup4 is not installed on the server. Install via `pip install beautifulsoup4`', 'error')
            return redirect(url_for('importer.import_from_html'))

        # Accept either an uploaded file (`htmlfile`) or pasted HTML source (`htmlsource`)
        htmlsource = request.form.get('htmlsource')
        base_url = request.form.get('base_url') or ''
        if htmlsource and htmlsource.strip():
            html = htmlsource
        else:
            f = request.files.get('htmlfile')
            if not f:
                flash('No HTML file uploaded or source provided', 'error')
                return redirect(url_for('importer.import_from_html'))
            html = f.stream.read().decode('utf-8', errors='replace')
        soup = BeautifulSoup(html, 'html.parser')

        # Extract emails via mailto and regex
        emails = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:'):
                emails.add(href.split(':', 1)[1].split('?')[0])
        # regex search in text
        for m in re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', soup.get_text()):
            emails.add(m)

        # Extract images (resolve relative URLs if base_url provided)
        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            full = urljoin(base_url, src) if base_url else src
            images.append({'src': full, 'alt': img.get('alt', '')})

        # Heuristic for names: alt attributes, elements with class/id containing 'name' or 'nom', headings
        names = set()
        # alt attributes
        for img in soup.find_all('img'):
            alt = (img.get('alt') or '').strip()
            if alt:
                names.add(alt)
        # class/id containing name/nom
        for tag in soup.find_all(True, attrs={'class': True}):
            cl = ' '.join(tag.get('class'))
            if re.search(r'\b(name|nom)\b', cl, re.I):
                text = tag.get_text(strip=True)
                if text:
                    names.add(text)
        for tag in soup.find_all(True, id=True):
            if re.search(r'\b(name|nom)\b', tag.get('id'), re.I):
                text = tag.get_text(strip=True)
                if text:
                    names.add(text)
        # headings
        for h in ('h1','h2','h3'):
            for tag in soup.find_all(h):
                t = tag.get_text(strip=True)
                if t and len(t) < 80 and not re.search(r'@', t):
                    names.add(t)

        result = {
            'emails': sorted(emails),
            'images': images,
            'names': sorted(names)
        }
        groups = StudntGrp.query.order_by(StudntGrp.Name).all()
        return render_template('admin_import_html_result.html', result=result, groups=groups)

    return render_template('admin_import_html.html')


def _normalize_token(s: str) -> str:
    if not s:
        return ''
    s = s.lower()
    s = unicodedata.normalize('NFKD', s)
    s = ''.join(ch for ch in s if ch.isalnum())
    return s


def _find_group_by_name(group_val):
    """Find a StudntGrp by name with tolerant matching.

    Accepts integer ids, exact match, or normalized token match (case/spacing/accents tolerant).
    """
    if not group_val:
        return None
    # try integer id
    try:
        gid = int(str(group_val).strip())
        g = StudntGrp.query.get(gid)
        if g:
            return g
    except Exception:
        pass

    sval = str(group_val).strip()
    # exact match first
    g = StudntGrp.query.filter_by(Name=sval).first()
    if g:
        return g

    # try case-insensitive / normalized match
    token = _normalize_token(sval)
    if not token:
        return None
    for g in StudntGrp.query.all():
        if _normalize_token(g.Name) == token:
            return g
    return None


def _is_valid_email(e: str) -> bool:
    if not e or '@' not in e:
        return False
    e = e.strip()
    # simple sanity checks and reject placeholder patterns
    if re.match(r'^_+@_+\.', e) or e.startswith('_@') or '__' in e:
        return False
    # basic regex
    return bool(re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', e))


def _generate_email_from_name(name: str, suffix: str = None) -> str:
    base = _normalize_token(name) or f'user{int(time.time())}'
    if suffix:
        base = f"{base}_{suffix}"
    candidate = f"{base}@import.local"
    # ensure uniqueness in DB
    i = 1
    while Studnt.query.filter_by(Email=candidate).first():
        candidate = f"{base}_{i}@import.local"
        i += 1
    return candidate


def match_names_images(names, images, emails):
    """Return list of rows matching images to names and emails.

    Each row: {'idx': int, 'image': src or None, 'name': str or '', 'email': str or 'undefined', 'score': float}
    """
    name_list = [n for n in names]
    name_tokens = [_normalize_token(n) for n in name_list]

    # prepare email localparts
    email_locals = []
    for e in emails:
        try:
            local = e.split('@', 1)[0].lower()
        except Exception:
            local = e.lower()
        email_locals.append((e, _normalize_token(local)))

    rows = []
    used_name_idx = set()

    # prioritize trombi images first
    sorted_images = sorted(images, key=lambda it: (0 if '/uploads/trombi/' in it['src'] else 1, it['src']))

    for i, img in enumerate(sorted_images):
        src = img.get('src')
        # extract filename token
        fname = os.path.splitext(os.path.basename(urlparse(src).path))[0]
        ftoken = _normalize_token(fname)

        best_idx = None
        best_score = 0.0
        for ni, nt in enumerate(name_tokens):
            if ni in used_name_idx:
                continue
            score = 0.0
            if nt and ftoken and (nt == ftoken or nt in ftoken or ftoken in nt):
                score = 1.0
            else:
                # fuzzy ratio
                score = difflib.SequenceMatcher(None, nt, ftoken).ratio()
            if score > best_score:
                best_score = score
                best_idx = ni

        matched_name = ''
        if best_idx is not None and best_score >= 0.4:
            matched_name = name_list[best_idx]
            used_name_idx.add(best_idx)

        # find email that matches name token or filename token
        matched_email = 'undefined'
        key_token = _normalize_token(matched_name) or ftoken
        for e, eloc in email_locals:
            if key_token and (key_token in eloc or eloc in key_token):
                matched_email = e
                break

        rows.append({'idx': len(rows), 'image': src, 'name': matched_name, 'email': matched_email, 'score': round(best_score, 2)})

    # any leftover names not matched -> add as rows without image
    for ni, n in enumerate(name_list):
        if ni in used_name_idx:
            continue
        # try to find email
        matched_email = 'undefined'
        nt = name_tokens[ni]
        for e, eloc in email_locals:
            if nt and (nt in eloc or eloc in nt):
                matched_email = e
                break
        rows.append({'idx': len(rows), 'image': None, 'name': n, 'email': matched_email, 'score': 0.0})

    return rows


def _save_data_uri_to_file(data_uri: str, prefix: str = 'photo', max_bytes: int = 3 * 1024 * 1024) -> str:
    """Decode a data:image/...;base64,... URI and save it under static/uploads/trombi.

    Returns the web path ("/static/uploads/trombi/<file>") on success, or None on failure.
    """
    print('[IMPORT_CSV] _save_data_uri_to_file: start')
    if not data_uri or not data_uri.lower().startswith('data:image/'):
        print('[IMPORT_CSV] data_uri missing or not image')
        return None
    # allow newlines inside the base64 payload (use DOTALL)
    m = re.match(r'^data:(image/[^;]+);base64,(.+)$', data_uri, re.I | re.S)
    if not m:
        print('[IMPORT_CSV] regex did not match data URI format')
        return None
    mime = m.group(1).lower()
    b64 = m.group(2)
    print(f'[IMPORT_CSV] mime detected: {mime}')
    # Remove surrounding quotes that may come from CSV quoting
    if (b64.startswith('"') and b64.endswith('"')) or (b64.startswith("'") and b64.endswith("'")):
        b64 = b64[1:-1]
    # remove whitespace/newlines
    b64 = re.sub(r'\s+', '', b64)
    # support base64url
    b64 = b64.replace('-', '+').replace('_', '/')
    # remove stray quote characters if present anywhere
    b64 = b64.replace('"', '').replace("'", '')
    # ensure padding
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

    # If Pillow is available, validate and (re)encode the image using Pillow
    folder = os.path.abspath(os.path.join(os.path.dirname(__file__), 'static', 'uploads', 'trombi'))
    try:
        os.makedirs(folder, exist_ok=True)
    except Exception as e:
        print('[IMPORT_CSV] failed to create folder:', repr(e))
        return None

    timestamp = int(time.time() * 1000)
    # Preferred extension from mime
    ext_map = {
        'image/jpeg': 'jpg',
        'image/jpg': 'jpg',
        'image/png': 'png',
        'image/gif': 'gif',
        'image/webp': 'webp'
    }
    preferred_ext = ext_map.get(mime)

    if have_pillow:
        try:
            print('[IMPORT_CSV] Pillow available: validating image')
            from io import BytesIO
            bio = BytesIO(raw)
            img = _PILImage.open(bio)
            img.verify()  # validate image integrity
            # Re-open for saving (verify() leaves file in unusable state)
            bio.seek(0)
            img = _PILImage.open(bio)
            fmt = img.format or ''
            fmt = fmt.upper()
            print(f'[IMPORT_CSV] Pillow detected format: {fmt}, mode: {getattr(img, "mode", None)}')
            # Map Pillow format to extension
            fmt_to_ext = {'JPEG': 'jpg', 'JPG': 'jpg', 'PNG': 'png', 'GIF': 'gif', 'WEBP': 'webp'}
            ext = fmt_to_ext.get(fmt, preferred_ext or 'bin')
            filename = f"{prefix}_{timestamp}.{ext}"
            filename = secure_filename(filename)
            path = os.path.join(folder, filename)
            # For JPEG ensure mode is suitable
            save_kwargs = {}
            if fmt in ('JPEG', 'JPG') and img.mode in ('RGBA', 'LA'):
                img = img.convert('RGB')
            # Save via Pillow to ensure valid encoding
            img.save(path, format=fmt if fmt else None, **save_kwargs)
            print('[IMPORT_CSV] saved via Pillow:', path)
            return f'/static/uploads/trombi/{filename}'
        except Exception as e:
            print('[IMPORT_CSV] Pillow processing failed:', repr(e))
            # fallback to raw-write if Pillow fails
            pass

    # Fallback: write raw decoded bytes to file using preferred extension or bin
    ext = preferred_ext or 'bin'
    filename = f"{prefix}_{timestamp}.{ext}"
    filename = secure_filename(filename)
    path = os.path.join(folder, filename)
    try:
        with open(path, 'wb') as fh:
            fh.write(raw)
        print('[IMPORT_CSV] saved raw bytes to:', path)
    except Exception as e:
        print('[IMPORT_CSV] failed to write raw bytes:', repr(e))
        return None
    return f'/static/uploads/trombi/{filename}'


def _create_scores_for_student(studnt_id, group_id):
    """Ensure Score rows exist for the given student for all evaluations matching the group.

    For each Evaluat with Group_Id == group_id, create a Score for each Skill in that
    evaluation's SkillSet. Level_Id is left NULL (no level selected yet).
    """
    if not group_id:
        return
    # find evaluations for this group
    evals = Evaluat.query.filter_by(Group_Id=group_id).all()
    for ev in evals:
        # for each skill in that evaluation's skillset
        skills = Skill.query.filter_by(SkillSet_Id=ev.SkillSet_Id).all()
        for sk in skills:
            # don't duplicate
            existing = Score.query.filter_by(Evaluat_Id=ev.Id, Studnt_Id=studnt_id, Skill_Id=sk.Id).first()
            if not existing:
                s = Score(Evaluat_Id=ev.Id, Studnt_Id=studnt_id, Skill_Id=sk.Id, Level_Id=None)
                Db.session.add(s)


@importer_bp.route('/from_html/import', methods=['POST'])
def import_from_html_do_import():
    """Import selected rows from the HTML analysis preview."""
    sel = request.form.getlist('selected')
    if not sel:
        flash('Aucune sélection effectuée.', 'error')
        return redirect(url_for('importer.import_from_html'))

    group_id = request.form.get('group_id')
    new_group = request.form.get('new_group')
    target_group = None
    if group_id:
        try:
            target_group = StudntGrp.query.get(int(group_id))
        except Exception:
            target_group = None
    elif new_group:
        g = StudntGrp.query.filter_by(Name=new_group).first()
        if not g:
            g = StudntGrp(Name=new_group)
            Db.session.add(g)
            Db.session.commit()
        target_group = g

    created = 0
    updated = 0
    for idx in sel:
        try:
            i = int(idx)
        except Exception:
            continue
        email = (request.form.get(f'email_{i}') or '').strip()
        name = (request.form.get(f'name_{i}') or '').strip() or None
        if not _is_valid_email(email):
            # generate synthetic email to satisfy non-null constraint
            email = _generate_email_from_name(name or f'row{i}', suffix=str(i))
        existing = None
        if email:
            existing = Studnt.query.filter_by(Email=email).first()
        if existing:
            if name:
                existing.Name = name
            if target_group:
                existing.Group_Id = target_group.Id
            updated += 1
            if existing.Group_Id:
                _create_scores_for_student(existing.Id, existing.Group_Id)
        else:
            new = Studnt(Name=name or (email.split('@')[0] if email else 'unknown'), Email=email, Group_Id=target_group.Id if target_group else None)
            Db.session.add(new)
            Db.session.flush()
            if new.Group_Id:
                _create_scores_for_student(new.Id, new.Group_Id)
            created += 1

    Db.session.commit()
    return render_template('admin_import_result.html', resource='studnts', created=created, updated=updated, errors=[])


@importer_bp.route('/from_url', methods=['GET', 'POST'])
def import_from_url():
    """Fetch a URL and extract names, emails and images (preview only, no DB import).

    Accepts either POST (form submit) or GET with a `url` query parameter (for linking
    directly from the CSV import page using method=GET).
    """
    # support GET with ?url=... to allow immediate analysis when user clicked a link
    do_fetch = False
    if request.method == 'POST':
        do_fetch = True
    elif request.method == 'GET' and request.args.get('url'):
        do_fetch = True

    if do_fetch:
        if not have_requests:
            flash('`requests` is not installed on the server. Install via `pip install requests`', 'error')
            return redirect(url_for('importer.import_from_url'))
        if not have_bs4:
            flash('`beautifulsoup4` is not installed on the server. Install via `pip install beautifulsoup4`', 'error')
            return redirect(url_for('importer.import_from_url'))
        url = request.form.get('url') or request.args.get('url')
        if not url:
            flash('No URL provided', 'error')
            return redirect(url_for('importer.import_from_url'))

        try:
            resp = requests.get(url, timeout=10)
            resp.raise_for_status()
            html = resp.text
        except Exception as e:
            flash(f'Error fetching URL: {e}', 'error')
            return redirect(url_for('importer.import_from_url'))

        soup = BeautifulSoup(html, 'html.parser')

        # reuse same extraction logic as import_from_html
        emails = set()
        for a in soup.find_all('a', href=True):
            href = a['href']
            if href.startswith('mailto:'):
                emails.add(href.split(':', 1)[1].split('?')[0])
        for m in re.findall(r'[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}', soup.get_text()):
            emails.add(m)

        images = []
        for img in soup.find_all('img'):
            src = img.get('src') or img.get('data-src')
            if not src:
                continue
            full = urljoin(url, src)
            images.append({'src': full, 'alt': img.get('alt', '')})

        names = set()
        for img in soup.find_all('img'):
            alt = (img.get('alt') or '').strip()
            if alt:
                names.add(alt)
        for tag in soup.find_all(True, attrs={'class': True}):
            cl = ' '.join(tag.get('class'))
            if re.search(r'\b(name|nom|user|utilisateur|trombi)\b', cl, re.I):
                text = tag.get_text(strip=True)
                if text:
                    names.add(text)
        for tag in soup.find_all(True, id=True):
            if re.search(r'\b(name|nom|user|utilisateur|trombi)\b', tag.get('id'), re.I):
                text = tag.get_text(strip=True)
                if text:
                    names.add(text)
        for h in ('h1','h2','h3','h4'):
            for tag in soup.find_all(h):
                t = tag.get_text(strip=True)
                if t and len(t) < 120 and not re.search(r'@', t):
                    names.add(t)

        # also try to find profile links like /campus/annuaire/fiche/utilisateur/1234
        profiles = []
        for a in soup.find_all('a', href=True):
            m = re.search(r'/campus/annuaire/fiche/utilisateur/(\d+)', a['href'])
            if m:
                uid = m.group(1)
                text = a.get_text(strip=True)
                profiles.append({'id': uid, 'url': urljoin(url, a['href']), 'label': text})

        # detect 'groupes' param in the URL and try to find a StudntGrp
        detected_group = None
        try:
            qs = parse_qs(urlparse(url).query)
            groupes = qs.get('groupes') or qs.get('groupe') or []
            if groupes:
                grp_name = groupes[0]
                detected_group = _find_group_by_name(grp_name)
        except Exception:
            detected_group = None

        result = {
            'emails': sorted(emails),
            'images': images,
            'names': sorted(names),
            'profiles': profiles,
            'source_url': url,
            'detected_group': detected_group
        }
        # pass available groups for selection
        groups = StudntGrp.query.order_by(StudntGrp.Name).all()
        rows = match_names_images(result['names'], result['images'], result['emails'])
        return render_template('admin_import_html_result.html', result=result, groups=groups, rows=rows)

    return render_template('admin_import_url.html')


@importer_bp.route('/from_url/import', methods=['POST'])
def import_from_url_do_import():
    """Perform import of selected previewed entries into the DB."""
    # Expect indices of selected rows
    sel = request.form.getlist('selected')
    if not sel:
        flash('Aucune sélection effectuée.', 'error')
        return redirect(url_for('importer.import_from_url'))

    # determine target group: either selected existing group id or new_group_name
    group_id = request.form.get('group_id')
    new_group = request.form.get('new_group')
    target_group = None
    if group_id:
        try:
            target_group = StudntGrp.query.get(int(group_id))
        except Exception:
            target_group = None
    elif new_group:
        # create new group
        g = StudntGrp.query.filter_by(Name=new_group).first()
        if not g:
            g = StudntGrp(Name=new_group)
            Db.session.add(g)
            Db.session.commit()
        target_group = g

    created = 0
    updated = 0
    for idx in sel:
        try:
            i = int(idx)
        except Exception:
            continue
        email = request.form.get(f'email_{i}')
        name = request.form.get(f'name_{i}') or None
        if not email:
            continue
        existing = Studnt.query.filter_by(Email=email).first()
        if existing:
            if name:
                existing.Name = name
            if target_group:
                existing.Group_Id = target_group.Id
            updated += 1
            if existing.Group_Id:
                _create_scores_for_student(existing.Id, existing.Group_Id)
        else:
            new = Studnt(Name=name or email.split('@')[0], Email=email, Group_Id=target_group.Id if target_group else None)
            Db.session.add(new)
            created += 1

    Db.session.commit()
    return render_template('admin_import_result.html', resource='studnts', created=created, updated=updated, errors=[])
