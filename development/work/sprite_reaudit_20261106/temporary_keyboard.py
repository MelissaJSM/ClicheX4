"""검사 동안만 입력 API 값을 바꾸고 원래 값으로 되돌린다."""
import argparse
import json
from pathlib import Path
import winreg

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=('apply', 'restore'))
args = parser.parse_args()
path = Path(__file__).parent / 'keyboard_setting.json'
keypath = r'Software\epsxe\config'
with winreg.OpenKey(winreg.HKEY_CURRENT_USER, keypath, 0, winreg.KEY_QUERY_VALUE | winreg.KEY_SET_VALUE) as key:
    current, kind = winreg.QueryValueEx(key, 'PADApiType1')
    if args.action == 'apply':
        assert not path.exists() and current in (1, '1') and kind in (winreg.REG_DWORD, winreg.REG_SZ)
        temporary = '0' if kind == winreg.REG_SZ else 0
        record = {'key': keypath, 'name': 'PADApiType1', 'original': current, 'temporary': temporary, 'type': kind, 'restored': False}
        path.write_text(json.dumps(record, indent=2), 'utf8')
        winreg.SetValueEx(key, 'PADApiType1', 0, kind, temporary)
    else:
        record = json.loads(path.read_text('utf8'))
        assert current == record['temporary'] and not record['restored']
        winreg.SetValueEx(key, record['name'], 0, record['type'], record['original'])
        assert winreg.QueryValueEx(key, record['name'])[0] == record['original']
        record['restored'] = True
        path.write_text(json.dumps(record, indent=2), 'utf8')
print(json.dumps(record))
