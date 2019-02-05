import re

def get_registration_name(line):
    reg_exp = r"Registered Name / Nama Berdaftar .(.*)$"
    match = re.match(reg_exp, line)
    try:
        return match.group(1)
    except:
        return ''


def get_date(line):
    reg_exp = r"Date of Incorporation / Tarikh Penubuhan : (\d+ / \d+ / \d+)"
    match = re.match(reg_exp, line)
    try:
        return match.group(1)
    except:
        return ''

def fetch_fields(gv, obj):
    for line in gv.list:
        if 'Registered' in line:
            obj.name = get_registration_name(line)
        elif 'Incorporation' in line:
            obj.date = get_date(line)
    
    return obj


