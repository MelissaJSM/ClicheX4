from pathlib import Path
import sys,struct,json,hashlib,collections
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.export_x_consistency import page
from src.psx_player import graphics_bank
D=Path(__file__).parent/'rin_extension';O=D/'rear_continuation_analysis';O.mkdir(exist_ok=True)
P=D/'prepared_third_saber_v1/PL01_U.ARC';arc=P.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(arc)=='11d4c88a17983dd3e106d13af3938075803186c59045b0b372b0f813b3aa09ae'
pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
keys=[(0,n)for n in range(178,197)]+[(1,n)for n in(148,150,152,154)]
animations=json.loads((ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/zero_animations.json').read_text('utf8'))
groups=collections.defaultdict(list);items={v:[]for v in('normal','black')};rows=[]
for b,n in keys:
 a,meta=render(arc,b,b*5,n);y,x=np.nonzero(a);box=(int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1));crop=a[box[1]:box[3],box[0]:box[2]];h=sha(crop.tobytes());key=f'b{b}_{n:03}';groups[(crop.shape,h)].append({'key':key,'bbox':box})
 Image.fromarray(a).save(O/f'{key}_indices.png');bank=graphics_bank(entry(arc,2),b);sharing=[f['index']for f in bank['frames']if f['offset']==meta['stream_offset']]
 sequence_ids=[q['id']for q in animations['animations']if q['graphics_bank']==b and any(s['frame']==n for s in q['steps'])]
 rows.append({'key':key,'bbox':box,'opaque_pixels':len(x),'tiles':meta['tile_count'],'shared_stream_refs':sharing,'animation_ids_from_preserved_original_table':sequence_ids,'shape_sha256':h})
 for form,words in[('normal',pal),('black',black)]:items[form].append((key,rgba(a,words)))
for form,words in[('normal',pal),('black',black)]:
 for start in range(0,len(keys),8):page(items[form][start:start+8],rgba(render(arc,0,0,147)[0],words),O/f'{form}_{start//8:02}.png',cols=4,scale=4)
 page([('new rear174',rgba(render(arc,0,0,174)[0],words))]+items[form][:3],rgba(render(arc,0,0,147)[0],words),O/f'{form}_style_compare.png',cols=2,scale=6)
report={'source':str(P.relative_to(ROOT)),'sha256':sha(arc),'refs':rows,'exact_normalized_shape_groups':[v for v in groups.values()],'review_status':'추출 완료; 실제 열람 후 대표 키와 같은 방향 공유 범위를 결정한다.','source_animation_table_scope':'이전 실제 EXE 추출 표를 분류용으로 사용한다. 이번 작업은 시간표를 수정하지 않으며 새로운 라이브 타이밍 검증을 뜻하지 않는다.'}
(O/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'groups':report['exact_normalized_shape_groups'],'refs':rows}))
