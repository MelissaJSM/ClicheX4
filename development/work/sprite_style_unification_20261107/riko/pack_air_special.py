"""검토한 공중 의상2키와 동일 표시 사본을 원래 데이터 경계 안에 등록한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107';Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as engine
P=W/'riko/prepared_burst_final_v1/PL01_U.ARC';PSHA='e871006eed3473bfe6716fc676fb0e4d638c62846de545186dd0de0f6a17e7fc'
ART=W/'riko/air_special_cloth04/registered01';OUT=W/'riko/prepared_air_special_v1'
assert not OUT.exists();arc=P.read_bytes();assert engine.native.sha(arc)==PSHA
reg=json.loads((ART/'registration.json').read_text('utf8'));assert reg['source_sha256']==PSHA
def clipped(a):
    y,x=np.nonzero(a)
    if not len(x):return None
    p=(int(x.min()),int(y.min()));part=a[y.min():y.max()+1,x.min():x.max()+1]
    return part.tobytes(),part.shape,p
masters={};oldmasters={}
for r in reg['frames']:
    path=ROOT/r['target'];assert engine.native.sha(path.read_bytes())==r['target_sha256']
    key=(r['bank'],r['ref']);masters[key]=np.array(Image.open(path));oldmasters[key]=clipped(engine.native.render(arc,key[0],key[0]*5,key[1])[0])
targets={};keys={}
for bank in (0,1):
    for f in engine.native.graphics_bank(engine.native.entry(arc,2),bank)['frames']:
        n=f['index']
        if bank==1 and 42<=n<=49:continue
        found=clipped(engine.native.render(arc,bank,bank*5,n)[0])
        if found is None:continue
        for k,m in oldmasters.items():
            if found[:2]==m[:2]:
                dx,dy=found[2][0]-m[2][0],found[2][1]-m[2][1];keys[bank,n]=(k[1],dx,dy);targets[bank,n]=engine.shifted(masters[k],dx,dy)
artkeys=dict(keys)
for bank,n in list(keys):
    b=engine.native.graphics_bank(engine.native.entry(arc,2),bank);off=b['frames'][n]['offset']
    for f in b['frames']:
        if f['offset']!=off or (bank,f['index']) in targets:continue
        k=(bank,f['index']);assert not(bank==1 and 42<=k[1]<=49)
        keys[k]=(None,0,0);targets[k]=engine.native.render(arc,bank,bank*5,k[1])[0].copy()
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.OUT=OUT;engine.CACHE=W/'riko/air_special_cache';engine.KEYS=keys
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return {k:v.copy()for k,v in targets.items()}
engine.get_targets=expected
original_pack=engine.pack_frame
def pack(c,b,n,raw,count,target):
    if (b,n) not in artkeys:return raw,engine.records(c,b*5,n),{'type':'preserved_shared_support'}
    return original_pack(c,b,n,raw,count,target)
engine.pack_frame=pack
out,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert out==again
proof.pop('heads_preserved_pixels_per_reference',None)
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out);engine.KEYS=artkeys;engine.boards(arc,out)
report={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':PSHA,'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),
    'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in artkeys],
    'shared_support_refs':[f'b{b}_{n:03}'for b,n in keys if (b,n) not in artkeys],
    'registration':reg,'verification':proof,'reproducible':True,'static_texture_unchanged':True,
    'static_recipe_parts_hash_requires_rebind':True,'gameplay_runtime_verified':False}
(OUT/'proposal.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
from rebind_air_static import bind_static
bind_static()
print(json.dumps({'sha256':report['after_sha256'],'new_refs':report['new_art_refs'],'layouts':proof['layouts']}))
