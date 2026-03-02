import os
import json
import hashlib
from datetime import datetime
import re

def read_json_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None

def write_json_file(file_path, data):
    try:
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return True
    except:
        return False

def safe_filename(filename):
    return re.sub(r'[^a-zA-Z0-9_.-]', '', filename)

def generate_id(prefix=''):
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    random_hash = hashlib.md5(os.urandom(8)).hexdigest()[:6]
    return f"{prefix}{timestamp}{random_hash}"

def format_currency(amount, symbol='₹'):
    try:
        amount = float(amount)
        return f"{symbol}{amount:,.2f}"
    except:
        return f"{symbol}0.00"

def parse_date(date_str, formats=['%d-%m-%Y', '%Y-%m-%d', '%d/%m/%Y']):
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except:
            continue
    return None

def validate_email(email):
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def validate_phone(phone):
    pattern = r'^[6-9]\d{9}$'
    return re.match(pattern, str(phone)) is not None

def chunk_list(lst, chunk_size):
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def merge_dicts(dict1, dict2):
    result = dict1.copy()
    result.update(dict2)
    return result

def get_file_extension(filename):
    if '.' in filename:
        return filename.rsplit('.', 1)[1].lower()
    return ''

def is_allowed_file(filename, allowed_extensions):
    ext = get_file_extension(filename)
    return ext in allowed_extensions