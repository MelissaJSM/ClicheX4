import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_pilot import prepare
cases=[('character/ver_rin_nana','out/ver_rin_nana/should_not_exist'),
       ('work/ver_rin_nana/nana_art/pilot_v4','out/ver_rin_nana/nana_pilot_v9'),
       ('work/ver_rin_nana/nana_art/pilot_v4','out/ver_buki_riko/should_not_exist')]
rejected=[]
for a,b in cases:
    try:prepare(ROOT/a,ROOT/b)
    except ValueError as e:rejected.append(str(e))
    else:raise AssertionError('Unsafe path accepted')
assert not (ROOT/'out/ver_rin_nana/should_not_exist').exists()
assert not (ROOT/'out/ver_buki_riko/should_not_exist').exists()
a=ROOT/'out/ver_rin_nana/nana_pilot_v9';b=ROOT/'out/ver_rin_nana/nana_pilot_v9_reproduced'
files=sorted(p.name for p in a.iterdir() if p.is_file())
assert files==sorted(p.name for p in b.iterdir() if p.is_file())
assert all((a/f).read_bytes()==(b/f).read_bytes() for f in files)
report={'unsafe_input_rejections':rejected,'reproduced_files':len(files),
        'files':{f:hashlib.sha256((a/f).read_bytes()).hexdigest() for f in files},
        'game_applied':False}
(ROOT/'work/ver_rin_nana/nana_art/pilot_verification.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print('Reproduced files:',len(files),'Rejected unsafe/collision cases:',len(rejected))
