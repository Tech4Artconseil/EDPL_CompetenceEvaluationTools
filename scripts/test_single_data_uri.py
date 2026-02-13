import re, base64, os, hashlib, time

# Standalone helper (no project imports)
def save_data_uri_to_file(data_uri: str, prefix='photo', max_bytes=3*1024*1024):
    m = re.match(r'^data:([\w/+-\.]+);base64,(.*)$', data_uri, re.S)
    if not m:
        return None, 'not_data_uri'
    mime = m.group(1)
    b64 = m.group(2)
    b64_stripped = re.sub(r'\s+', '', b64)
    try:
        raw = base64.b64decode(b64_stripped)
    except Exception as e:
        return None, f'decode_error:{e}'
    if len(raw) > max_bytes:
        return None, 'too_large'
    mime_map = {
        'image/jpeg': 'jpg', 'image/jpg': 'jpg', 'image/png': 'png',
        'image/gif': 'gif', 'image/webp': 'webp'
    }
    ext = mime_map.get(mime.lower(), 'jpg')
    pkg_dir = os.getcwd()
    out_dir = os.path.join(pkg_dir, 'static', 'uploads', 'trombi')
    os.makedirs(out_dir, exist_ok=True)
    h = hashlib.sha1(raw).hexdigest()[:10]
    fname = f"{prefix}_{int(time.time())}_{h}.{ext}"
    fpath = os.path.join(out_dir, fname)
    with open(fpath, 'wb') as f:
        f.write(raw)
    web_path = f"/static/uploads/trombi/{fname}"
    return web_path, fpath

# Collez ici le data-URI brut fourni (conserve les sauts de ligne)
data = """data:image/jpeg;base64,/9j/4AAQSkZJRgABAgAAAQAB 
AAD/2wBDAAgGBgcGBQgHBwcJCQgKDBQNDAsLDBkSEw8UHRofHh0aHBwgJC4nICIsIxwcKDcpLDAxNDQ0Hyc5PTgyPC4zNDL/ 
2wBDAQkJCQwLDBgNDRgyIRwhMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjIyMjL/wAAR 
CACJAGQDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQID 
AAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNk 
ZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl 
5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAEC 
AxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpj 
ZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk 
5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwD0UigLT8UuPyrILiBaXbmngUoFIVxoWl28U8Y3AdCTgZrEuPF+g2ufM1GP 
aCV3xq0iZGMjcoIJGRkDpkZ6jIM2McUm2qd1rNhb2QuftdvtJ2gmVcbtpYA89SO3/wBbJpOt2GroVhmVbhCyyW7sokQqcElQ 
TxnH5igC2VwDTcVYK0wrQFyLbTSKlI4puBQFyEgH1oqTFFA7km2lxTsegoxVWIFAokZYoy7cKOp9BTlFcT8Q/Ec2i6SYEDKZ 
gVztU5IxxgnOOc9D0APDUWGld2Oa8d/EiGKWaw0SYNN5ZjuLmNAfMPTajf3VJbB7k8ereb/6df3Cv5Ujx5/1e0sOOvI68Enj 
mt3wP4Y/4SfVri+u9728ch3biSJG98jmvZV0i0tY1WO3iULgDCDoKznVUNEdVKhzK54X9m1BLWUS2lyQT8uPmPQ/eHfHHI7E 
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"""

web_path, fpath = save_data_uri_to_file(data)
print('web_path:', web_path)
print('fpath:', fpath)
print('exists:', os.path.exists(fpath))
if os.path.exists(fpath):
    print('size:', os.path.getsize(fpath))
