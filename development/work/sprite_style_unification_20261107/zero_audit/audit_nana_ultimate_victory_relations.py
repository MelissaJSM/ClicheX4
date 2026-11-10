"""Nana Ultimate 승리204..207의 저장/동작/효과 관계. 읽기 전용."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,render
N=D.parent/'nana_audit';O=D/'nana_ultimate_victory_relations01';O.mkdir(exist_ok=True)
PBS=(0,5,6,7,8);REFS=(204,205,206,207);tracked={}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def load(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def full(ar,n):
 v=ar.layer(n)[0].copy()
 for pb in(8,5,7,6):w=ar.layer(n,pb)[0];v[w>0]=w[w>0]
 return v
def shift(v,dx,dy):
 out=np.zeros_like(v);y,x=np.nonzero(v);out[y+dy,x+dx]=v[y,x];return out
def box(m):
 y,x=np.nonzero(m);return [int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
def diff(a,b):
 m=a!=b;return {'count':int(m.sum()),'bbox_halfopen_world':box(m)}
source=N/'ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC'
a=Archive(load(source));assert sha(a.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
prior=Archive(load(N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC'))
hist=Archive(load(ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC'))
usdata,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',));us=Archive(usdata['PL02_U.ARC'])
sourceinfo=[]
for filename in('generated_first.png','prompt.txt'):
 p=ROOT/'work/ver_rin_nana/nana_ultimate_armor/ceremony_v1'/filename
 v=load(p);sourceinfo.append({'path':rel(p),'sha256':sha(v)})
for path in('scripts/normalize_nana_victory.py','scripts/prepare_nana_ultimate_ceremony.py','scripts/prepare_nana_ultimate_victory_edge.py','work/research/decomp/src/main/player.c'):
 load(ROOT/path)
rows=[]
for n in REFS:
 f=a.banks[0]['frames'][n];layers={};assert raw(a,0,n)==raw(prior,0,n)
 for pb in PBS:
  cp=parts(a,pb,n);assert [sig(q)for q in cp]==[sig(q)for q in parts(prior,pb,n)]
  z=a.layer(n,pb)[0];assert np.array_equal(z,prior.layer(n,pb)[0])
  slots={q['record_offset']for q in cp}
  owners=[j for j in range(237)if j!=n and slots&{q['record_offset']for q in parts(a,pb,j)}]
  layers[str(pb)]={'parts':cp,'opaque':int(np.count_nonzero(z)),'bbox':box(z>0),'cluts':sorted({q['clut']for q in cp}),
   'record_storage_overlap_owners':owners,'indexed_sha256':sha(z.tobytes())}
 normalized=ROOT/f'work/overhaul_20261105/sprites/nana_preultimate/normalized/{n:03}.png'
 load(normalized);norm=np.asarray(Image.open(normalized))
 rows.append({'ref':n,'offset':f['offset'],'tile_count':f['tile_count'],
  'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],
  'layers':layers,'base_vs_normalized':diff(a.layer(n)[0],norm),'before_vs_historical':diff(full(a,n),full(hist,n)),
  'current_base_vs_before':diff(a.layer(n)[0],full(a,n)),
  'original_US_raw_owners':[q['index']for q in us.banks[0]['frames']if q['offset']==us.banks[0]['frames'][n]['offset']],
  'original_US_parts':{str(pb):parts(us,pb,n)for pb in PBS}})
relations=[]
for ar,name in((a,'current'),(us,'original_US')):
 for mask,form in((0,'after_or_base'),(15,'before_or_full')):
  for i,s in enumerate(REFS):
   for t in REFS[i+1:]:
    x=ar.layer(s)[0]if mask==0 else full(ar,s);y=ar.layer(t)[0]if mask==0 else full(ar,t)
    candidates=[]
    for dx in range(-4,5):
     for dy in range(-4,5):candidates.append((int(np.count_nonzero(shift(x,dx,dy)!=y)),dx,dy))
    count,dx,dy=min(candidates);layersame=[pb for pb in PBS if np.array_equal(ar.layer(s,pb)[0],ar.layer(t,pb)[0])]
    relations.append({'archive':name,'form':form,'source':s,'target':t,'whole_diff':diff(x,y),
     'best_shift_within4':[dx,dy],'best_shift_difference':count,'exact_layer_same_origin':layersame,
     'lower_y_ge5_diff':diff(x[165:],y[165:])['count'],
     'lower_y_ge12_diff':diff(x[172:],y[172:])['count']})
tablepath=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json'
table=json.loads(load(tablepath));linked=[q for q in table['animations']if any(s['frame']in REFS for s in q['steps'])]
seq39=next(q for q in table['animations']if q['id']==39);seq40=next(q for q in table['animations']if q['id']==40)
assert [q['frame']for q in seq39['steps']]==[81,204,205,206,207,207]
boards=[]
def board(name,ar,ids):
 cw,ch=288,400;im=Image.new('RGB',(cw*len(ids),ch*2),'#263345');dr=ImageDraw.Draw(im)
 for r,mask in enumerate((15,0)):
  for c,n in enumerate(ids):
   pic=ar.composite(n,mask,1)[0].crop((126,104,194,196)).resize((272,368),Image.Resampling.NEAREST)
   x,y=c*cw,r*ch;im.paste(pic,(x+8,y+24),pic);dr.text((x+8,y+5),f'{n} mask{mask}',fill='white')
 p=O/f'{name}.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes()),'refs':list(ids)})
board('current_victory',a,REFS);board('original_US_victory',us,REFS);board('sequence39_connections',a,(81,204,205,206,207,156))
report={'scope':'Nana Ultimate204..207만 최신c721 자원/역사원화/원표39/40과 원코드를 읽었다. 신규 제작·패킹·실기 없음.',
 'source':rel(source),'source_sha256':sha(a.data),'original_US_sha256':sha(us.data),
 'selected_raw_layers_records_unchanged_from_c9e684':True,'frames':rows,'pair_relations':relations,
 'historical_source':sourceinfo,'animation_source':rel(tablepath),'animations_containing_victory_refs':linked,
 'following_stage_clear_animation':seq40,'source_callers':[
 {'path':'work/research/decomp/src/main/player.c','function':'player_script_victory','lines':[1108,1131],
  'behavior':'item_step4에원표39시작. event0x80은기존 func_8001540C(0,0x21,0) 호출. 상대step0에서script종료후idle.'},
 {'path':'work/research/decomp/src/main/player.c','function':'player_stage_clear','lines':[1133,1156],
  'behavior':'D_80173C84==0일때39시작. 같은event호출유지. 상대step0이면원표40설정후beam_out.'}],
 'boards':boards,'boards_actually_viewed':False,'tracked_sources':tracked,
 'limitations':['원표/디컴파일코드는기존로컬자료이며이조사에서실제MIPS나게임을실행하지않았다.',
 '같은raw stream,같은조립레코드주소,같은표시그림은서로다른공유관계다.',
 '빈손204/205와권총206/207은역사원화와프롬프트에따른Nana디자인이며원US캐릭터의무기형태복원주장이아니다.']}
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'sha256':sha((O/'report.json').read_bytes()),'rows':[{k:v for k,v in r.items()if k not in('layers','original_US_parts')}for r in rows],
 'current_pairs':[q for q in relations if q['archive']=='current'],'boards':boards},ensure_ascii=False))
