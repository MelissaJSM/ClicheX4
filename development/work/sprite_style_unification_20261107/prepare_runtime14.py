"""Bind existing ordinary-input and read-only capture tools to a new test BIN."""
from pathlib import Path
import argparse, hashlib, json
W = Path(__file__).resolve().parent
ROOT = W.parents[1]
R = W / 'runtime'
p = argparse.ArgumentParser(); p.add_argument('mode', choices=('br', 'rn')); a = p.parse_args()
mode = {'br': 'ver_buki_riko', 'rn': 'ver_rin_nana'}[a.mode]
stem = {'br': 'shibuki_riko', 'rn': 'rin_nana'}[a.mode]
game = ROOT / 'out' / mode / 'sprite_style_unification_20261107_v14' / (stem + '.bin')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
manifest = json.loads((game.parent / 'manifest.json').read_text('utf8'))
expected = sha(game)
assert expected == manifest['modified_bin']['sha256']
oldsha = {'br': 'b78509ca2a8bc2c67bb2997cba927174df1fcf8cd672a347552bcc25e96c656d',
          'rn': '50fff99ac90d4b6aa57ec94e230920a2f9d049eb3035026f5d56067d382bb28b'}[a.mode]
bound = []
def save(p, text):
    if p.exists():
        assert p.read_text('utf8') == text
    else:
        p.write_text(text, 'utf8')
    bound.append({'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)})
for name in ('read_menu', 'observe', 'record', 'play_watch', 'open_continue'):
    source = R / f'{name}_{a.mode}13.py'
    code = source.read_text('utf8')
    if name in ('read_menu', 'observe', 'record'):
        assert code.count(oldsha) == 1
        code = code.replace(oldsha, expected)
    code = code.replace(a.mode + '13', a.mode + '14').replace('checkpoint13', 'checkpoint14')
    save(R / f'{name}_{a.mode}14.py', code)

code = (R / 'load_fourth13.py').read_text('utf8')
code = code.replace('read_menu_br13.py', f'read_menu_{a.mode}14.py').replace('ver_buki_riko', mode)
code = code.replace('(0,15,2,0)', '(0,15,2,1)').replace('(0,48,2,15,255,0)', '(0,48,2,15,255,1)')
code = code.replace('full-armor', 'acquired-Ultimate')
save(R / f'load_ultimate_{a.mode}14.py', code)
save(R / f'tools_binding_{a.mode}14.json', json.dumps({'bin_sha256': expected, 'files': bound,
    'runtime_verified': False}, ensure_ascii=False, indent=2) + '\n')
print(json.dumps({'mode': mode, 'bin_sha256': expected, 'tools': len(bound)}))
