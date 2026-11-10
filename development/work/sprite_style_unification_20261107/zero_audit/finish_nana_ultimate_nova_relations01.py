"""노바 관계3판 실제열람 및 원US 준비변형의 제한을 보충한다."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[2];O=D/'nana_ultimate_nova_relations01';sys.path[:0]=[str(ROOT),str(D)]
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from verify_shibuki_ultimate_hurt13_independent import parts,sig,tile,render
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();r=json.loads((O/'report.json').read_text('utf8'));assert sha(O/'report.json')=='f61cdbe3df69a329b939e2468dcc2cfb1a5b0754fb303e2e82db9b08e5cc240e'
for q in r['readback_sheets']:assert sha(ROOT/q['path'])==q['sha256']
raw,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',));a=Archive(raw['PL02_U.ARC']);variants=[]
for n,m,pb in((213,214,0),(215,216,0),(215,216,5)):
 oldps,newps=parts(a,pb,n),parts(a,pb,m);oldtiles={q['tile']+q['page']*256 for q in oldps};newunique=[q for q in newps if q['tile']+q['page']*256 not in oldtiles]
 z=render(a,m,pb,newunique);p=O/f'US_variant_{m}_layer{pb}.npy';assert not p.exists();np.save(p,z)
 old,new=a.layer(n,pb)[0],a.layer(m,pb)[0];external=(new>0)&(old==0)
 variants.append({'pair':[n,m],'layer':pb,'new_only_tile_numbers':sorted({q['tile']+q['page']*256 for q in newunique}),'new_only_records':newunique,'tile_hashes':{str(t):hashlib.sha256(tile(a,m,t).tobytes()).hexdigest()for t in sorted({q['tile']+q['page']*256 for q in newunique})},'variant_parts_render':p.relative_to(ROOT).as_posix(),'variant_parts_render_sha256':sha(p),'different_cells':int((old!=new).sum()),'opaque_only_in_second':int(external.sum()),'opaque_only_in_first':int(((old>0)&(new==0)).sum()),'all_variant_tiles_are_effect_not_proven':True})
c={'parent_report_sha256':sha(O/'report.json'),'actually_viewed_sheets':r['readback_sheets'],'original_US_preparation_variants':variants,'observations':['原US213/214 비교에서214의손주변흰섬광이추가되어보이고,현재두Nana자세는역사공통제작으로같다.원214의0층tile7/8/9는213에없는변형기록이다.그타일전체를순수이펙트라고단정하지않고원조립/색인을별도추출했다.','原US215/216은머리/상체의색·형상변형이다.0층tile8..11과5층tile21..24가다르고피부/몸체까지포함하는영역이므로차이셀을모두외부효과로복사하면안된다.','현재218/220 층판에서효과가새머릿결끝일부와겹치는모습이보인다.새217을제작할때몸체실루엣과효과구멍을함께검토할이유이며,원코드/속도/판정수정의근거는아니다.','219의구형실루엣과최신727px머리몸의동일규칙진단은윤곽이달라진다.이는이번에그림을변경한것이아니라향후동기화범위를보여주는진단이다.'],'production_guidance':['213=214/215=216은현재수용된역사제작정책으로분명히표시할것.원US상세/섬광복원으로부르지말고,원준비흰섬광까지복원하려면새몸과의가림을별도후보로검토할것.','217/218/220 새몸을동일원점으로공유하되218/220 기존외부효과의형상/색/위치를보호하고새몸알파와겹치는구간의새가림정책을분리할것.','219의683px원seed와정확Manhattan2규칙이확인되었으므로신규몸에같은규칙을적용한검증을별도로남길것.현재overlay전체동일성과새실루엣동일성을동시에주장하지말것.'],'runtime_verified':False,'new_MIPS_executed':False,'art_changed':False}
p=O/'conclusions.json';assert not p.exists();p.write_text(json.dumps(c,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'conclusions_sha256':sha(p),'variants':[{k:q[k]for k in('pair','layer','new_only_tile_numbers','different_cells','opaque_only_in_second')}for q in variants]}))
