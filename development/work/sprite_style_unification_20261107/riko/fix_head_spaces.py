"""의상 등록 후 머리 내부 빈 공간도 원래 값으로 보존한다."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];W=ROOT/'work/sprite_style_unification_20261107';Z=W/'zero_audit'
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(Z))
import pack_riko_cloth as engine
from scripts.overhaul_sprites_audit import render
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash
P=W/'riko/prepared_air_v2/PL01_U.ARC';PSHA='de487c1a512bb75ed9a774a99ea2e7347564a8365358a1f7677178701b0c6453'
OUT=W/'riko/prepared_head_spaces_v1';assert not OUT.exists() and file_hash(P)==PSHA
arc=P.read_bytes();original=(Z/'riko_restore/prepared_rear_v1/PL01_U.ARC').read_bytes()
rows=json.loads((W/'riko/head_negative_audit.json').read_text('utf8'));targets={};keys={}
front=np.array(Image.open(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/riko_idle147_indexed.png'))[:19,12:35]
negative=np.zeros_like(front,bool)
for y,row in enumerate(front):
    xs=np.where(row>0)[0]
    if len(xs):negative[y,xs.min():xs.max()+1]=row[xs.min():xs.max()+1]==0
for r in rows:
    b,n,x,y=r['bank'],r['ref'],*r['origin']
    mask=np.zeros((384,384),bool);mask[160+y:179+y,160+x:183+x]=negative
    a=render(arc,b,b*5,n)[0];old=render(original,b,b*5,n)[0];target=a.copy();target[mask]=old[mask]
    assert int(np.count_nonzero(a!=target))==r['diff']==6
    assert not np.any((a!=target)&~mask)
    targets[b,n]=target;keys[b,n]=(133,x+7,y+19)
engine.PARENT=P;engine.PARENT_SHA=PSHA;engine.KEYS=keys;engine.OUT=OUT;engine.CACHE=W/'riko/head_spaces_cache'
def expected(data):
    engine.native.need(engine.native.sha(data)==PSHA,'Wrong parent')
    return {k:v.copy() for k,v in targets.items()}
engine.get_targets=expected
result,proof=engine.build(arc,targets);again,_=engine.build(arc,targets);assert result==again
assert entry(result,3)==entry(arc,3),'Composition must stay exact for this source-pixel correction'
proof.pop('heads_preserved_pixels_per_reference',None)
proof['only_original_head_internal_pixels_restored']=True
proof['changed_display_pixels']=60
OUT.mkdir();(OUT/'PL01_U.ARC').write_bytes(result);engine.boards(arc,result)
for (b,n),a in targets.items():Image.fromarray(a).save(OUT/f'b{b}_{n:03d}_indices.png')
report={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':PSHA,
        'resource':str((OUT/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(result),
        'target_references':[f'b{b}_{n:03d}' for b,n in keys],'verification':proof,
        'reproducible':True,'game_changed':False,'runtime_verified':False,'cumulative_ref_count':72}
(OUT/'proposal.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':report['after_sha256'],'head_internal_pixels':60,'cumulative_refs':72}))
