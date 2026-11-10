"""새 사격 팔 국소 등록과 공통 얼굴/하체/고정 버스터 연결의 검토 후보."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
from scipy.ndimage import label
D=Path(__file__).resolve().parent;W=D.parent;ROOT=W.parents[1]
sys.path[:0]=[str(D),str(ROOT),str(W/'nana_audit/native_restore')]
from prepare_body_layers04 import Archive,comp,box,Y,X
from preview_restore import helper
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=W/'shibuki_audit/prepared_nova_strike_base01/PL00_U.ARC';assert sha(p)=='36d4d0293abc77052c476e0495f4f4542ca75471c7a149f200e4bdb8f4e1bd4e'
a=Archive(p.read_bytes());out=D/'shot_composed01';out.mkdir(exist_ok=False)
bodymeta={r['ref']:r for r in json.loads((D/'body_layers_probe04/manifest.json').read_text('utf8'))['frames']}
changes={222:[[-32,-29,-8,1],[-10,-6,-5,1]],224:[[-33,-19,-10,2],[-11,-7,-5,2]],226:[[-24,-14,-9,3],[-11,-6,-4,3]],228:[[-24,-14,-9,6],[-11,-6,-5,6]],230:[[-29,-30,-9,2],[-11,-7,-5,2]]}
guns={222:[-32,-14,-17,-5],224:[-33,-14,-19,-4],226:[-24,-15,-10,-6],228:[-24,-15,-7,-6],230:[-29,-16,-14,-7]}
arm_y={222:-7,224:-6,226:-5,228:-5,230:-7}
records=[]
for n in(222,224,226,228,230):
 ls={pb:np.array(Image.open(D/f'body_layers_probe04/layer{pb}_{n-1:03}.png'))for pb in(0,5,6,7,8)}
 before={pb:z.copy()for pb,z in ls.items()};face=box(bodymeta[n-1]['shared_face']);edit=np.zeros((384,384),bool)
 for b in changes[n]:edit|=box(b)
 edit&=~face
 source={f:np.array(Image.open(D/f'shot_registered01/{f}_{n}_source_indices.png'))for f in('base_legs','fourth')}
 clear=box(guns[n]);gun=np.array(Image.open(D/f'shot_inputs01/{n}_gun_indices.png'));guard=np.array(Image.open(D/f'shot_inputs01/{n}_gun_guard.png'))>0
 # 새 원화의 총 대신 수용된 모듈의 모양과 투명 영역을 사용한다.
 for z in source.values():z[clear & ~face]=0
 ls[0][edit]=source['base_legs'][edit]
 for pb in(5,6,7):ls[pb][edit]=0
 arm=edit&(Y>=arm_y[n]);f=source['fourth'];b=source['base_legs']
 shared_skin=arm&((f==9)|np.isin(b,(12,13)))
 ls[7][arm&~shared_skin]=f[arm&~shared_skin]
 # 고정 모듈은 의상 공통0층에 놓고 다른 층에서는 제외한다.
 ls[0][guard]=gun[guard]
 for pb in(5,6,7,8):ls[pb][guard]=0
 assert np.array_equal(ls[8],before[8])
 assert np.array_equal(ls[0][face&~guard],before[0][face&~guard])
 for pb,z in ls.items():Image.fromarray(z).save(out/f'layer{pb}_{n:03}.png')
 Image.fromarray((edit*255).astype(np.uint8)).save(out/f'edit_{n}.png')
 rows=[]
 for form,m in(('base_legs',8),('fourth',15)):
  rows.append((f'{form} {n}',[('idle',a.composite(0,m)[0]),('new body',comp(a,before,m)),('new local arm and fixed cannon',comp(a,ls,m)),('old shot',a.composite(n,m)[0])]))
 helper.grid(rows,out/f'comparison_{n}.png',5)
 helper.grid([(f'shot{n}',[(f'mask{m}',comp(a,ls,m))for m in(8,9,10,12,13,14,15)])],out/f'partial_{n}.png',5)
 stats=[{'mask':m,'components8':int(label(np.array(comp(a,ls,m))[:,:,3]>0,np.ones((3,3)))[1])}for m in range(8,16)]
 records.append({'ref':n,'edit_windows':changes[n],'generated_cannon_excluded':guns[n],'skin_common':int(shared_skin.sum()),'common_face_preserved_except_fixed_cannon':True,'common_leg_exact':True,'partial_components':stats,'layer_hashes':{str(pb):sha(out/f'layer{pb}_{n:03}.png')for pb in ls}})
(out/'manifest.json').write_text(json.dumps({'records':records,'native_packed':False,'runtime_verified':False,'scope':'부분 팔 합성 진단. 얼굴·다리·버스터 보호 검사 후 미술 검토가 필요하다.'},ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps([{'ref':r['ref'],'components':[v['components8']for v in r['partial_components']]}for r in records]))
