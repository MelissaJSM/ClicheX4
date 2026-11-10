"""Shibuki 현재PL02 등장126..142/원US/역사출처 읽기 조사. 자원쓰기 없음."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,render
H=D.parent/'shibuki_audit';O=D/'shibuki_ultimate_arrival_relations01';O.mkdir(exist_ok=True)
PBS=(0,5,6,7,8);REFS=list(range(126,143));sha=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}

def load(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def full(ar,n):
 z=ar.layer(n)[0].copy()
 for pb in(8,5,7,6):z=over(z,ar.layer(n,pb)[0])
 return z
def over(bg,fg):return np.where(fg>0,fg,bg).astype(np.uint8)
def shift(z,dx=0,dy=0):
 v=np.zeros_like(z);y,x=np.nonzero(z);v[y+dy,x+dx]=z[y,x];return v
def diff(a,b,ignore=None):
 m=a!=b
 if ignore is not None:m&=~ignore
 y,x=np.nonzero(m)
 return {'different_pixels':len(x),'bbox_world':[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None}
def save_array(name,z):
 p=O/f'{name}.npy';np.save(p,z);return {'path':rel(p),'sha256':sha(p.read_bytes()),'indexed_sha256':sha(z.tobytes()),'opaque':int(np.count_nonzero(z))}

p=H/'prepared_ultimate_hurt02/PL02_U.ARC';blob=load(p);assert sha(blob)=='b43e021b70c055d142521d1c679bef323d76b0b30bf27b41c9988815330b2e94';a=Archive(blob)
priorpath=H/'prepared_ultimate_ladder01/PL02_U.ARC';prior=Archive(load(priorpath));assert sha(prior.data)=='03a675626035b93ad2e2feef8dd643365ed8a3e1a61a1eb02a476063e2c55e8a'
histpath=ROOT/'work/overhaul_20261105/sprites/ver_buki_riko/baseline/PL02_U.ARC';hist=Archive(load(histpath))
original,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',));us=Archive(original['PL02_U.ARC'])
rows=[]
for n in REFS:
 assert raw(a,0,n)==raw(prior,0,n)
 f=a.banks[0]['frames'][n];layers={}
 for pb in PBS:
  assert [sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(prior,pb,n)]
  assert np.array_equal(a.layer(n,pb)[0],prior.layer(n,pb)[0])
  z=a.layer(n,pb)[0];slots={q['record_offset']for q in parts(a,pb,n)}
  aliases=[j for j in range(237)if j!=n and slots&{q['record_offset']for q in parts(a,pb,j)}]
  layers[str(pb)]={'parts':parts(a,pb,n),'opaque':int(np.count_nonzero(z)),'sha256':sha(z.tobytes()),'record_storage_overlap_owners':aliases}
 rows.append({'ref':n,'stream_offset':f['offset'],'tile_count':f['tile_count'],
              'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],
              'layers':layers,'historical_base_diff':diff(a.layer(n)[0],hist.layer(n)[0]),'historical_full_diff':diff(full(a,n),full(hist,n))})

fxs={};effects=[]
for n in(136,137):
 ps=[q for q in parts(hist,0,n)if q['tile']==7];fx=render(hist,n,0,ps);fxs[n]=fx
 e={'ref':n,'historical_parts':ps,'historical_whole_tile7_sha256':sha(tile(hist,n,7).tobytes()),'source':save_array(f'effect_{n}',fx),'forms':{}}
 for mask,form in((0,'after'),(15,'before')):
  z=a.layer(n)[0]if mask==0 else full(a,n)
  e['forms'][form]={'source_pixels_preserved':int(np.count_nonzero((fx>0)&(z==fx))),'source_pixels_occluded_or_different':int(np.count_nonzero((fx>0)&(z!=fx)))}
 effects.append(e)

relations=[]
for s,t in((135,136),(138,139)):
 fx=fxs.get(t,np.zeros((384,384),np.uint8));q={'source':s,'target':t,'tested_translation':[0,-1],'current_forms':{},'current_layer_differences':{}}
 for mask,form in((0,'after'),(15,'before')):
  x=a.layer(s)[0]if mask==0 else full(a,s);y=a.layer(t)[0]if mask==0 else full(a,t);moved=shift(x,dy=-1)
  q['current_forms'][form]={'whole_shift':diff(moved,y),'shift_then_historical_effect':diff(over(moved,fx),y),'body_outside_effect':diff(moved,y,fx>0)}
 for pb in PBS:q['current_layer_differences'][str(pb)]=diff(shift(a.layer(s,pb)[0],dy=-1),a.layer(t,pb)[0])
 ufx=render(us,t,0,[z for z in parts(us,0,t)if z['tile']==7])if t==136 else np.zeros((384,384),np.uint8)
 q['original_US_forms']={}
 for mask,form in((0,'base'),(15,'full_armor')):
  x=us.layer(s)[0]if mask==0 else full(us,s);y=us.layer(t)[0]if mask==0 else full(us,t)
  q['original_US_forms'][form]={'whole_shift':diff(shift(x,dy=-1),y),'shift_plus_original_effect':diff(over(shift(x,dy=-1),ufx),y)}
 relations.append(q)

alias=[]
for mask,form in((0,'after'),(15,'before')):
 for s,t in((133,135),(135,136),(136,137),(137,138),(138,139)):
  x=a.layer(s)[0]if mask==0 else full(a,s);y=a.layer(t)[0]if mask==0 else full(a,t)
  fx=fxs.get(t,np.zeros((384,384),np.uint8))
  candidates=[]
  for dx in range(-3,4):
   for dy in range(-3,4):
    pred=over(shift(x,dx,dy),fx);m=int(np.count_nonzero(pred!=y));candidates.append((m,dx,dy))
  m,dx,dy=min(candidates)
  alias.append({'source':s,'target':t,'form':form,'best_translation_within3':[dx,dy],'different_pixels_after_fx':m,'exact':m==0})

rules=[]
orb=hist.layer(129)[0];r134={'ref':134,'source129':save_array('effect_134_orb',orb),'forms':{}}
for mask,form in((0,'after'),(15,'before')):
 body=a.layer(133)[0]if mask==0 else full(a,133);actual=a.layer(134)[0]if mask==0 else full(a,134)
 r134['forms'][form]={'current133_over_historical129':diff(over(orb,body),actual),'outside_body_preserved':diff(orb,actual,body>0)}
rules.append(r134)
ps131=parts(hist,0,131)[:16];fx131=render(hist,131,0,ps131);histbody=render(hist,131,0,parts(hist,0,131)[16:24]);vals,cnt=np.unique(histbody[histbody>0],return_counts=True);light=int(vals[cnt.argmax()])
pred131=np.where(a.layer(133)[0]>0,light,fx131).astype(np.uint8)
rules.append({'ref':131,'light_index':light,'source_effect_parts':ps131,'source_effect':save_array('effect_131',fx131),
              'current133_alpha_plus_historical_first16':diff(pred131,a.layer(131)[0]),'current132_vs_pure_effect':diff(fx131,a.layer(132)[0]),
              'current131_vs132':diff(a.layer(131)[0],a.layer(132)[0]),'current_before_vs_after':diff(full(a,131),a.layer(131)[0])})
normalized=ROOT/'work/overhaul_20261105/sprites/shibuki_preultimate/normalized/000.png';load(normalized);idlehist=np.asarray(Image.open(normalized))
ps140=[q for q in parts(hist,0,140)if q['tile']==8];fx140=render(hist,140,0,ps140);old140=full(hist,140);vals,cnt=np.unique(old140[(old140>0)&(fx140==0)],return_counts=True);light140=int(vals[cnt.argmax()]);pred140=np.where(idlehist>0,light140,fx140).astype(np.uint8)
rules.append({'ref':140,'light_index':light140,'source_effect_parts':ps140,'effect':save_array('effect_140',fx140),
              'historical_normalized_idle_rule':diff(pred140,a.layer(140)[0]),'current_idle_alpha_vs_historical':diff(a.layer(0)[0]>0,idlehist>0),
              'current_idle_alpha_rule':diff(np.where(a.layer(0)[0]>0,light140,fx140),a.layer(140)[0]),
              'before_vs_after':diff(full(a,140),a.layer(140)[0])})

terminal=[]
for n in(141,142):
 rr={'ref':n,'layers':{},'forms':{}}
 for pb in PBS:rr['layers'][str(pb)]=diff(a.layer(n,pb)[0],a.layer(0,pb)[0])
 for mask,form in((0,'after'),(15,'before')):
  idle=a.layer(0)[0]if mask==0 else full(a,0);target=a.layer(n)[0]if mask==0 else full(a,n);extra=np.where(idle==0,target,0).astype(np.uint8)
  rr['forms'][form]={'body_inside_idle':diff(idle,target,idle==0),'external_pixels':int(np.count_nonzero(extra)), 'external':save_array(f'{n}_{form}_external',extra)}
 if n==141:
  idle=a.layer(0)[0];fx=np.where(idle==0,a.layer(141)[0],0).astype(np.uint8);matched=[]
  for q in parts(a,0,141):
   pr=render(a,141,0,[q])
   if pr.any()and np.array_equal(np.where(fx>0,pr,0),pr):matched.append(q)
  rr['current_effect_only_parts']=matched
 terminal.append(rr)

# 130 predates the newer133. Preserve its actual background; do not claim that
# a formula has reconstructed it unless the original historical source agrees.
oldmeta_path=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14/art.json';oldmeta=json.loads(load(oldmeta_path));mp=np.array(oldmeta['effect_index_mapping'],np.uint8)
original_base_path=ROOT/'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc';original_base=Archive(load(original_base_path))
bg=original_base.layer(130)[0].copy();bg[np.isin(bg,(5,8))]=14;bg=mp[bg]
body130_path=ROOT/'work/ver_buki_riko/shibuki_art/remaining_v1/production14/frame_133.png';load(body130_path);oldbody=np.zeros((384,384),np.uint8);oldbody[80:240,80:240]=np.asarray(Image.open(body130_path))
pred130=over(bg,np.where(oldbody>0,9,0).astype(np.uint8));actual130=a.layer(130)[0];delta=pred130!=actual130
yy,xx=np.nonzero(delta);delta_cells=[{'x':int(x-160),'y':int(y-160),'predicted':int(pred130[y,x]),'current':int(actual130[y,x])}for y,x in zip(yy,xx)]
rules.append({'ref':130,'source_background':save_array('effect_130_historical_background',bg),'old_body':save_array('effect_130_historical_body',oldbody),
              'historical_rule_comparison':diff(pred130,actual130),'current_vs_baseline':diff(actual130,hist.layer(130)[0]),
              'mismatches_outside_historical_body':int(np.count_nonzero(delta&(oldbody==0))),
              'mismatch_cells':delta_cells,'current133_alpha_vs_historical':diff(a.layer(133)[0]>0,oldbody>0),
              'same_rule_new133_difference':diff(over(bg,np.where(a.layer(133)[0]>0,9,0)),actual130)})

sheets=[]
for i,ns in enumerate(([126,127,128,129],[130,131,132,134],[133,135,136,137],[138,139,141,142],[0,140])):
 cw,ch=392,476;board=Image.new('RGB',(cw*len(ns),ch*2),'#263345');draw=ImageDraw.Draw(board)
 for row,(mask,form)in enumerate(((15,'before'),(0,'after'))):
  for col,n in enumerate(ns):
   im=a.composite(n,mask)[0].crop((112,96,208,208)).resize((384,448),Image.Resampling.NEAREST);x,y=col*cw,row*ch
   board.paste(im,(x+4,y+22),im);draw.text((x+4,y+4),f'{n} {form}',fill='white')
 p2=O/f'current_{i:02}.png';board.save(p2);sheets.append({'path':rel(p2),'sha256':sha(p2.read_bytes()),'refs':list(ns)})
tablepath=ROOT/'work/sprite_consistency_20261105/coverage/ver_buki_riko/x_animations.json';table=json.loads(load(tablepath));seq=[q for q in table['animations']if any(s['frame']in REFS for s in q['steps'])]
for code in('scripts/overhaul_sprites_state_layers.py','scripts/ultimate_arrival_jacket.py','scripts/fix_shibuki_arrival_terminal.py'):load(ROOT/code)
report={'scope':'현재Shibuki Ultimate126..142 몸체/광선/번개/공유관계 읽기.새그림/ARC/MIPS/게임수정없음.',
        'source':rel(p),'source_sha256':sha(blob),'previous03a675_selected_raw_layers_records_exact':True,
        'original_US_PL02_sha256':sha(us.data),'historical_baseline_sha256':sha(hist.data),
        'frames':rows,'historical136137_effects':effects,'translation_relations':relations,'best_nearby_body_relations':alias,
        'reconstructed_or_tested_rules':rules,'terminal141142':terminal,
        'animation_table':rel(tablepath),'linked_animation_ids':[q['id']for q in seq],
        'sheets':sheets,'sheets_actually_viewed':False,'tracked_sources':tracked,
        'limits':['현재그림 exact관계와 원US관계는각각기록했다. 새기본형수용아트를Ultimate의상으로바꾸는정책은원US복원과별개다.',
                  '130식은비교결과차이가0인경우만완전재현이다.잔여색수정은외부효과로임의삭제하지않는다.',
                  '실제애니메이션호출/실기/새후보수용은이보고서범위밖이다.']}
for name,h in tracked.items():assert sha((ROOT/name).read_bytes())==h
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha256':sha((O/'report.json').read_bytes()),'effects':effects,'relations':relations,'aliases':alias,'rules':[{k:v for k,v in q.items()if k not in('source_effect_parts','mismatch_cells')}for q in rules],'terminals':terminal},ensure_ascii=False))
