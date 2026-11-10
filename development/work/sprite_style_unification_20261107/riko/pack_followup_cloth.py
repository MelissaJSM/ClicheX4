"""착지1과 지상3타9의 새 의상을 원래공유·검손 변형과 함께 넣는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107';Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as engine
P=W/'riko/prepared_air_special_v1/PL01_U.ARC';PSHA='4e751c0e13d6f68bbb02f285493fee75c263c7cc995a96615332935c358e7615'
OUT=W/'riko/prepared_followup_cloth_v1';ART=W/'riko/saber_targets01';assert not OUT.exists();ART.mkdir(exist_ok=False)
arc=P.read_bytes();assert engine.native.sha(arc)==PSHA
masters={};sources=[]
for folder in ['followup_cloth05/registered03','saber_continuation06/registered01']:
    reg=json.loads((W/'riko'/folder/'registration.json').read_text('utf8'));assert reg['source_sha256']==PSHA;sources.append(reg)
    for r in reg['frames']:
        if r['ref']==230:continue # The rest of this separate attack family is still being drawn.
        p=ROOT/r['target'];assert engine.native.sha(p.read_bytes())==r['target_sha256'];masters[r['bank'],r['ref']]=np.array(Image.open(p))
derived=[]
for key,n,dx in [(113,115,1),(113,117,1),(113,119,1),(121,123,0),(125,127,0)]:
    before=engine.shifted(engine.native.render(arc,0,0,key)[0],dx,0);old=engine.native.render(arc,0,0,n)[0]
    delta=before!=old;y,x=np.nonzero(delta)
    assert len(x)>0 and x.min()>=137 and x.max()<=142 and y.min()>=163 and y.max()<=168
    target=engine.shifted(masters[0,key],dx,0);target[delta]=old[delta]
    masters[0,n]=target;derived.append(dict(ref=n,master=key,translation=[dx,0],hand_variant_pixels=int(delta.sum()),all_other_source_pixels_exact=True))
for (b,n),a in masters.items():Image.fromarray(a).save(ART/f'b{b}_{n:03}_indices.png')
assert sorted(n for b,n in masters)==[34,*range(111,128,2)]
targets={k:v.copy()for k,v in masters.items()};keys={k:(k[1],0,0)for k in masters}
for b,n in list(keys):
    bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);offset=bank['frames'][n]['offset']
    for f in bank['frames']:
        if f['offset']!=offset or (b,f['index'])in targets:continue
        k=(b,f['index']);keys[k]=(None,0,0);targets[k]=engine.native.render(arc,b,b*5,k[1])[0].copy()
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.OUT=OUT;engine.KEYS=keys;engine.CACHE=W/'riko/followup_pack_cache'
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return {k:v.copy()for k,v in targets.items()}
engine.get_targets=expected;original=engine.pack_frame
def pack(c,b,n,raw,count,target):
    if (b,n)not in masters:return raw,engine.records(c,b*5,n),dict(type='preserved_shared_support')
    return original(c,b,n,raw,count,target)
engine.pack_frame=pack
out,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert out==again
proof.pop('heads_preserved_pixels_per_reference',None)
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:keys[k]for k in masters};engine.boards(arc,out)
report=dict(source_arc=str(P.relative_to(ROOT)),source_arc_sha256=PSHA,resource=str((OUT/'PL01_U.ARC').relative_to(ROOT)),after_sha256=engine.native.sha(out),
    target_references=[f'b{b}_{n:03}'for b,n in sorted(masters)],shared_support_refs=[f'b{b}_{n:03}'for b,n in keys if (b,n)not in masters],
    artwork=str(ART.relative_to(ROOT)),source_art=sources,derived_hand_variants=derived,verification=proof,reproducible=True,
    held_art_not_packed=['b0_230'],runtime_verified=False,full_art_unification_complete=False)
(OUT/'proposal.json').write_text(json.dumps(report,indent=2)+'\n','utf8')
print(json.dumps({'after_sha256':report['after_sha256'],'targets':report['target_references'],'counts':proof['counts']}))
