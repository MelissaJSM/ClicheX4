import json,sys,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.build_nana_run import validate,configure_scope
configure_scope('air')
from scripts.prepare_nana_idle_shot import write
source=ROOT/'work/ver_rin_nana/nana_air/20261029T065945420508Z';out=ROOT/'work/ver_rin_nana/nana_air/rejection_checks_v1';out.mkdir(exist_ok=False);rows=[]
for case in ('wrong_parent','wrong_frame_scope','changed_style','tampered_arc'):
    a=out/case/'a';b=out/case/'b';a.mkdir(parents=True);b.mkdir();r=json.loads((source/'recipe.json').read_text('utf8'))
    if case=='wrong_parent':r['parent_bin_sha256']='0'*64
    elif case=='wrong_frame_scope':r['changed_bitmap_references'][0]=[0,85]
    elif case=='changed_style':r['master_sha256']='0'*64
    else:
        raw=bytearray((source/'modified.arc').read_bytes());raw[-1]^=1;(a/'modified.arc').write_bytes(raw);shutil.copyfile(source/'modified.arc',b/'modified.arc')
    for p in (a,b):write(p/'recipe.json',r)
    try:validate(a,b)
    except ValueError as e:rows.append({'case':case,'rejected_before_disc_write':True,'error':str(e)})
    else:raise AssertionError('Accepted '+case)
write(out/'results.json',rows);print(json.dumps(rows))
