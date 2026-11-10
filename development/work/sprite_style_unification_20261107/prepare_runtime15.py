"""Versioned, read-only verification and ordinary controller helpers for RN15."""
from pathlib import Path
import json,hashlib
W=Path(__file__).resolve().parent;ROOT=W.parents[1];R=W/'runtime'
old='6eb124eddf8b77f02339df309701aa6ad14128ca90ec9508e14f0d12296ea87a'
game=ROOT/'out/ver_rin_nana/sprite_style_unification_20261107_v15/rin_nana.bin'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
new=sha(game);assert new==json.loads((game.parent/'manifest.json').read_text('utf8'))['modified_bin']['sha256']
bindings=[]
def save(dest,body):
    if dest.exists(): assert dest.read_text('utf8')==body
    else:dest.write_text(body,'utf8')
    bindings.append({'path':dest.relative_to(ROOT).as_posix(),'sha256':sha(dest)})
for name in ('read_menu','observe','record','play_watch','open_continue'):
    code=(R/f'{name}_rn14.py').read_text('utf8')
    if name in ('read_menu','observe','record'):assert code.count(old)==1
    code=code.replace(old,new).replace('rn14','rn15').replace('checkpoint14','checkpoint15')
    save(R/f'{name}_rn15.py',code)
code=(R/'advance_iris_rn11.py').read_text('utf8').replace('rn11','rn15')
save(R/'advance_iris_rn15.py',code)
save(R/'tools_binding_rn15.json',json.dumps({'bin_sha256':new,'files':bindings,'runtime_verified':False},ensure_ascii=False,indent=2)+'\n')
print(new)
