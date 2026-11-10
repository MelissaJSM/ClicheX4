from pathlib import Path
import sys,json
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1];H=W/'shibuki_audit';sys.path[:0]=[str(ROOT),str(H)]
from optimize_hurt_tile_storage import optimize
from native_pose_pack import need,sha
source=D/'sharing_probe03/area32';out=D/'sharing_optimized03';out.mkdir(exist_ok=False)
recipe=json.loads((source/'recipe.json').read_text('utf8'));rows=[]
for g in recipe['groups']:
 n=g['refs'][0]
 if n not in(221,225,229):continue
 raw=(source/f'{n}.raw').read_bytes();need(sha(raw)==g['sha256'],'Source raw hash')
 nr,mp,proof=optimize(raw,[],6);rr=[[(mp[t],x,y,f)for t,x,y,f in q]for q in g['assignments']]
 (out/f'{n}.raw').write_bytes(nr);proof.update(refs=g['refs'],mapping=mp,assignments=rr)
 (out/f'{n}.json').write_text(json.dumps(proof,indent=2)+'\n','utf8');rows.append(proof)
 print(json.dumps({'ref':n,'before':proof['before'],'after':proof['after'],'saved':proof['saved']}),flush=True)
(out/'report.json').write_text(json.dumps({'groups':rows,'arc_written':False,'target_pixels_changed':False},indent=2)+'\n','utf8')
