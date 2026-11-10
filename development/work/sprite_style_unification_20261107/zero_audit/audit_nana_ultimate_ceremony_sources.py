"""Current Nana ceremony bodies/FX and historical deterministic rules, read only."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import binary_dilation
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from src.psx_player import composition_frame,decode_stream,compose_indices,indexed_atlas
D=Path(__file__).parent;N=D.parent/'nana_audit';O=D/'nana_ultimate_ceremony_sources01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def read(p):
 b=p.read_bytes();tracked[rel(p)]=sha(b);return b
PBS=(0,5,6,7,8);REFS=[*range(126,143),*range(156,162),*range(204,208)]
p=N/'ultimate_hurt_repaint/packed_hurt_candidate_v1/PL02_U.ARC';blob=read(p)
assert sha(blob)=='c9e68442829a7f149ae86317c88172e27dbce545e454687b98310fad28ef83a5'
prior=N/'rising_repaint/packed_ultimate_candidate_v1/PL02_U.ARC';pb=read(prior)
assert sha(pb)=='4132738ac872750507538cd8d150e13a510422df81cea99b502e7371b6753cd9'
a=Archive(blob);previous=Archive(pb)
histpath=ROOT/'work/overhaul_20261105/sprites/ver_rin_nana/baseline/PL02_U.ARC';hist=Archive(read(histpath))
folder=ROOT/'work/overhaul_20261105/sprites/nana_preultimate'
original,_=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',));us=Archive(original['PL02_U.ARC'])
def raw(ar,n):
 f=ar.banks[0]['frames'][n];return decode_stream(ar.g,f['offset'],f['limit'],f['tile_count']*128).data
def parts(ar,n,pb=0):return composition_frame(ar.c,pb,n)['parts']
def render(ar,n,ps):
 out=np.zeros((384,384),np.uint8)
 if not ps:return out
 f=ar.banks[0]['frames'][n];px,sz,bb,_=compose_indices(raw(ar,n),f['tile_count'],{'parts':ps},allowed_cluts={0,1,2,3})
 v=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);y,x=np.nonzero(v);out[y+bb[1]+160,x+bb[0]+160]=v[y,x];return out
def full(ar,n):
 v=ar.layer(n)[0].copy();over=np.zeros_like(v)
 for pb in(8,5,7,6):
  w=ar.layer(n,pb)[0];v[w>0]=w[w>0];over[w>0]=w[w>0]
 return v,over
def shift(v,dx=0,dy=0):
 out=np.zeros_like(v);y,x=np.nonzero(v);assert np.all((y+dy>=0)&(y+dy<384)&(x+dx>=0)&(x+dx<384));out[y+dy,x+dx]=v[y,x];return out
def box(m):
 y,x=np.nonzero(m);return[int(x.min()-160),int(y.min()-160),int(x.max()-159),int(y.max()-159)]if len(x)else None
def diff(v,w):
 m=np.any(v!=w,axis=2)if v.ndim==3 else v!=w;return{'different_pixels':int(m.sum()),'bbox_world':box(m)}
def overlay(bg,fg):
 z=bg.copy();z[fg>0]=fg[fg>0];return z
def normalized(n):
 f=folder/f'normalized/{n:03}.png';read(f);v=np.asarray(Image.open(f));assert v.shape==(384,384);return v
rows=[]
for n in REFS:
 f=a.banks[0]['frames'][n];assert raw(a,n)==raw(previous,n)
 for b in PBS:
  sig=lambda ps:[(q['flags'],q['tile'],q['x'],q['y'])for q in ps]
  assert sig(parts(a,n,b))==sig(parts(previous,n,b)) and np.array_equal(a.layer(n,b)[0],previous.layer(n,b)[0]),(n,b)
 rows.append({'ref':n,'stream':f['offset'],'tile_count':f['tile_count'],'raw_owners':[q['index']for q in a.banks[0]['frames']if q['offset']==f['offset']],
  'layers':{str(b):{'parts':parts(a,n,b),'opaque':int(np.count_nonzero(a.layer(n,b)[0])),'sha256':sha(a.layer(n,b)[0].tobytes())}for b in PBS},
  'base_vs_full':diff(a.layer(n)[0],full(a,n)[0])})
reconstruction=[]
def record(n,label,pred,target=None,**extra):
 dest=a.layer(n)[0]if target is None else target
 reconstruction.append({'ref':n,'rule':label,'comparison':diff(pred,dest),**extra})
 return pred

# Later C04 rules: source silhouettes and original energy components.
orb=hist.layer(129)[0];record(134,'current133 over historical129 energy',overlay(orb,a.layer(133)[0]),
 external_effect_pixels=int(np.count_nonzero((orb>0)&(a.layer(133)[0]==0))))
fx131=render(hist,131,parts(hist,131)[:16]);body131=render(hist,131,parts(hist,131)[16:24]);v,c=np.unique(body131[body131>0],return_counts=True);light131=int(v[c.argmax()])
pred131=np.where(a.layer(133)[0]>0,light131,fx131).astype(np.uint8)
record(131,'current133 alpha at source light index over historical first16 energy records',pred131,light_index=light131,energy_pixels=int(np.count_nonzero(fx131)),
 visible_body_color_contribution=diff(pred131,fx131),current132_vs_energy_only=diff(a.layer(132)[0],fx131),current131_vs132=diff(a.layer(131)[0],a.layer(132)[0]))
fx140=render(hist,140,[q for q in parts(hist,140)if q['tile']==8]);old140=full(hist,140)[0];v,c=np.unique(old140[(old140>0)&(fx140==0)],return_counts=True);light140=int(v[c.argmax()])
record(140,'historical normalized idle0 alpha plus original tile8 energy',np.where(normalized(0)>0,light140,fx140).astype(np.uint8),light_index=light140,
 current_idle_alpha_diff=diff(normalized(0)>0,a.layer(0)[0]>0),effect_pixels=int(np.count_nonzero(fx140)))

slanted=[]
for n in(136,137):
 ps=[q for q in parts(hist,n)if q['tile']==7];fx=render(hist,n,ps);np.save(O/f'effect_{n}_historical_tile7.npy',fx)
 match=(a.layer(n)[0][fx>0]==fx[fx>0]);v=fx[fx>0]
 slanted.append({'ref':n,'source_parts':ps,'source_pixels':int(np.count_nonzero(fx)),'source_sha256':sha(fx.tobytes()),
  'current_base_source_exact':bool(match.all()),'current_full_source_exact':bool(np.array_equal(full(a,n)[0][fx>0],fx[fx>0])),
  'source_index_counts':dict(zip(map(int,np.unique(v)),map(int,np.unique(v,return_counts=True)[1]))),
  'source_path':rel(O/f'effect_{n}_historical_tile7.npy')})

# The early 130 deliberately lets repeated native shell tiles occlude the body.
fxmap=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8)
oldsrc=ROOT/'work/ver_rin_nana/nana_art/arrival_v1/production02/frame_133.png';small=np.asarray(Image.open(oldsrc));read(oldsrc);oldbody=np.zeros((384,384),np.uint8);oldbody[80:240,80:240]=small
old130=overlay(fxmap[us.layer(129)[0]%16],np.where(oldbody>0,13,0).astype(np.uint8));native130=fxmap[us.layer(130)[0]%16]
currentbody130=overlay(fxmap[us.layer(129)[0]%16],np.where(a.layer(133)[0]>0,13,0).astype(np.uint8))
counts=collections.Counter(q['tile']for q in parts(us,130));rects=[]
for q in parts(us,130):
 if counts[q['tile']]>1:
  x,y=q['x']+160,q['y']+160;old130[y:y+16,x:x+16]=native130[y:y+16,x:x+16];currentbody130[y:y+16,x:x+16]=native130[y:y+16,x:x+16];rects.append([q['x'],q['y'],q['x']+16,q['y']+16])
record(130,'old production02 133 alpha under repeated original130 shell windows',old130,
 old133_current133_diff=diff(oldbody,a.layer(133)[0]),old133_historical133_diff=diff(oldbody,hist.layer(133)[0]),
 repeated_original_tile_windows=rects,current_vs_baseline=diff(a.layer(130)[0],hist.layer(130)[0]),
 current133_replacement_under_same_shell=diff(currentbody130,a.layer(130)[0]))

# Preserve original armor coverage when reproducing the old return override.
nb156=normalized(156);oldb157=hist.layer(157)[0];oldfull157,over157=full(hist,157)
body=shift(nb156,dy=-1);mask=body>0;inner=binary_dilation(mask,np.ones((3,3)));outer=binary_dilation(mask,np.ones((3,3)),iterations=2)
pre157=np.where(inner,7,np.where(outer,13,0)).astype(np.uint8);pre157[mask]=body[mask];pre157[over157==0]=oldb157[over157==0]
record(157,'normalized156 y-1 + Chebyshev halos 7/13 with original uncovered base',pre157,
 normalized156_vs_current_base=diff(nb156,a.layer(156)[0]),current_full_vs_historical_full=diff(full(a,157)[0],oldfull157),
 current_base_body_interior={'different_pixels':int(np.count_nonzero(mask&(a.layer(157)[0]!=body))),
  'bbox_world':box(mask&(a.layer(157)[0]!=body)),
  'changed_cells':[{'x':int(x-160),'y':int(y-160),'source156_yminus1':int(body[y,x]),'current157':int(a.layer(157)[0][y,x])}for y,x in zip(*np.nonzero(mask&(a.layer(157)[0]!=body)))]})
# The earlier armor recipe keeps its pre-existing extra aura outside the new halo.
ceremonyp=ROOT/'out/ver_rin_nana/nana_ultimate_ladder_20261104T104212237140Z/PL02_U.ARC';ceremony=Archive(read(ceremonyp))
assert sha(ceremony.data)=='f26be08d15f57687ba489a9b47d8e834abe23b9d53c383bb2e1528b64aab653c'
oldbody157=shift(ceremony.layer(156)[0],dy=-1);oldnative157=ceremony.layer(157)[0]
nativeaura=np.where(oldnative157!=oldbody157,oldnative157,0).astype(np.uint8)
fullbody157=shift(full(a,156)[0],dy=-1);fm=fullbody157>0
inner=binary_dilation(fm,np.ones((3,3)));outer=binary_dilation(fm,np.ones((3,3)),iterations=2)
aura157=np.where(inner,7,np.where(outer,13,0)).astype(np.uint8);aura157[fm]=0
retained=(nativeaura>0)&(aura157==0)&~fm;aura157[retained]=nativeaura[retained]
record(157,'current full156 y-1 + Chebyshev halos7/13 + old uncovered aura',overlay(aura157,fullbody157),target=full(a,157)[0],
 retained_original_aura_pixels=int(np.count_nonzero(retained)),original_aura_pixels=int(np.count_nonzero(nativeaura)))
fx159=hist.layer(159)[0];emap=np.array([0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9],np.uint8)
pre158=overlay(fx159,emap[shift(nb156,dy=-10)%16]);post158=overlay(fx159,emap[shift(full(hist,156)[0],dy=-10)%16]);pre158[post158==0]=0
record(158,'normalized156 y-10 energy map over historical159, clipped only to historical post158 alpha',pre158,
 mapping=emap.tolist(),historical159_pixels=int(np.count_nonzero(fx159)))
record(158,'historical full156 y-10 energy map over historical159 (full form)',post158,target=full(a,158)[0],
 current_full156_vs_historical_full156=diff(full(a,156)[0],full(hist,156)[0]))

relations=[]
for source,target,dx,dy in((138,139,0,-1),(156,157,0,-1),(156,158,0,-10),(0,141,0,0),(0,142,0,0)):
 forms={}
 for mask,label in((0,'after'),(15,'before')):
  s=a.layer(source)[0]if mask==0 else full(a,source)[0];t=a.layer(target)[0]if mask==0 else full(a,target)[0];s=shift(s,dx,dy)
  forms[label]={'whole':diff(s,t),'inside_source_pixels_different':int(np.count_nonzero((s>0)&(s!=t))),
    'outside_source_pixels':int(np.count_nonzero((s==0)&(t>0)))}
 relations.append({'source':source,'target':target,'translation':[dx,dy],'forms':forms})

# Exact and translated body aliases; different source angles are not guessed aliases.
bodyids=[133,135,136,137,138,139,156,204,205,206,207];aliases=[]
for form in(0,15):
 for i,s in enumerate(bodyids):
  x=a.layer(s)[0]if form==0 else full(a,s)[0]
  for t in bodyids[i+1:]:
   y=a.layer(t)[0]if form==0 else full(a,t)[0]
   for dy in range(-2,3):
    for dx in range(-2,3):
     if np.array_equal(shift(x,dx,dy),y):aliases.append({'mask':form,'source':s,'target':t,'translation':[dx,dy]})
mirrors=[]
for form in(0,15):
 for i,s in enumerate(bodyids):
  x=a.layer(s)[0]if form==0 else full(a,s)[0];xb=box(x>0);xs=x[xb[1]+160:xb[3]+160,xb[0]+160:xb[2]+160]
  for t in bodyids[i+1:]:
   y=a.layer(t)[0]if form==0 else full(a,t)[0];yb=box(y>0);ys=y[yb[1]+160:yb[3]+160,yb[0]+160:yb[2]+160]
   if xs.shape==ys.shape and np.array_equal(xs[:,::-1],ys):mirrors.append({'mask':form,'source':s,'target':t,'world_x_k':yb[0]+xb[2]-1,'dy':yb[1]-xb[1]})

# Existing native source table is unchanged; cite it rather than rerunning CPU.
tablep=ROOT/'work/sprite_consistency_20261105/coverage/ver_rin_nana/x_animations.json'
table=json.loads(read(tablep));seq=[q for q in table['animations']if any(s['frame']in REFS for s in q['steps'])]
images=[]
for i,ns in enumerate(([130,131,133,134],[135,136,137,140],[138,139,141,142],[156,157,158,159],[204,205,206,207])):
 cw,ch=270,380;board=Image.new('RGB',(cw*4,ch*2),'#263345');dr=ImageDraw.Draw(board)
 for row,mask in enumerate((0,15)):
  for col,n in enumerate(ns):
   im=a.composite(n,mask,1)[0].crop((128,106,192,194)).resize((256,352),Image.Resampling.NEAREST)
   board.paste(im,(col*cw+7,row*ch+23),im);dr.text((col*cw+7,row*ch+4),f'Nana U {n} mask{mask}',fill='white')
 q=O/f'current_{i:02}.png';board.save(q);images.append({'path':rel(q),'sha256':sha(q.read_bytes()),'refs':list(ns)})
for f in('scripts/normalize_nana_arrival.py','scripts/normalize_nana_victory.py','scripts/overhaul_sprites_state_layers.py','scripts/prepare_nana_ultimate_ceremony.py'):read(ROOT/f)
report={'scope':'현재Nana Ultimate 등장·승리·귀환의기존표시/몸체/별도FX 및역사파생규칙을읽었다. 새원화/ARC/CPU/게임실행없음.',
 'source':rel(p),'source_sha256':sha(blob),'prior_4132_target_refs_unchanged':True,
 'tracked_sources':tracked,'original_PL02_sha256':sha(original['PL02_U.ARC']),
 'frames':rows,'reconstructed_rules':reconstruction,'historical_tile7_effects':slanted,'current_relations':relations,
 'exact_body_translation_aliases_within2px':aliases,'exact_display_mirrors':mirrors,'linked_animation_ids':[q['id']for q in seq],
 'linked_animation_table':rel(tablep),'sheets':images,'actual_sheet_views':True,
 'view_notes':'현재after/before의130131133134·135136137140·138139141142·156157158159·204205206207 비교5판40표시를실제열람했다. 구체/빛실루엣·발광테두리와몸체를구분했다. 새원화수용이나실기판정은포함하지않았다.',
 'classification':{
  'ordinary_body_or_body_with_weapon':[133,135,138,139,156,204,205,206,207],
  'body_plus_separate_tile7_effect':[136,137],
  'derived_from_133':[130,131,134],
  'derived_from_idle0':[140,141,142],
  'derived_from_156':[157,158],
  'existing_pure_energy_or_shell':[126,127,128,129,132,159,160,161],
  'known_current_body_mismatches':['130은옛133실루엣','139 after는138 y-1과153px차이','141 after는idle0몸225px차이'],
  'not_a_completion_percentage':True
 },
 'conclusions':[
  '134는현재133(각폼의상)+과거129 구체다. 기본색인합성이exact이며before overlay5도133과동일하다.133수정시134 몸체를함께동기화하고원구체를별도로보호한다.',
  '131은현재133 alpha를색13으로과거131 첫16 energy기록위에놓은것과exact이다.132는그energy만표시하며131과raw를공유한다.131몸체로달라지는가시색892px가있으므로새133교체의실제연동대상이다.132를몸체사본으로바꾸지않는다.',
  '130은더이른production02의133 alpha를색13으로구체위에놓은뒤원래반복shell8창이가리는규칙으로exact이다.현재133으로같은규칙을계산하면270px달라지므로단순순수FX가아니다.새133작업에서130의구체가림을보호하면서실루엣을별도동기화할필요가있다.',
  '136/137의흰선은과거baseline tile7의46픽셀씩색13이며현재두폼에exact로남았다.136은(0,4),(-16,4)파트,137은(-16,-8),(0,-8) flipY파트다.원화몸체와분리한npy와원기록을제공한다.',
  '140은현재idle0 alpha색13+과거tile8의46픽셀효과로exact이다.새133몸체를복사하지않는다.142는양폼idle0 exact이며raw0/92/142공유를보호한다.',
  '138→139 world_y-1은before만exact이다.현재after는153픽셀의의상/얼굴주변차이가있다.141도before는idle0+12먼지exact이지만after는idle몸225픽셀차이가있어등장끝연결의잔여다.새작업에서는현재의상차이를원래반동/효과라고임의보존하지않는다.',
  '157 before는156 y-1 몸과Chebyshev1/2팽창색7/13로exact이며원추가오라잔여는0이다.after는같은윤곽규칙에과거overlay가없는영역의base를유지하여exact이고몸내부(14,-8)한셀8→7의역사예외가있다.새몸체제작시이예외를미확인상태로자동확대하지않는다.',
  '158은156 y-10을에너지맵[0,5,6,7,8,5,6,7,8,9,8,9,13,13,9,9]으로바꾸고과거159 에너지1875px위에합성한것과두폼exact이다.별도신규몸체포즈를추정하지않는다.현재after에는before158 alpha밖만0으로제한한역사규칙도있다.',
  '204~207과133/135/136/137/138/156은현재표시를같은몸체로간주할exact반전또는±2px평행이동관계를찾지못했다.확인된것은before138→139뿐이다.원래서로다른팔/권총위치와자세를보호하여개별원화또는명시적부위등록으로다룬다.'
 ],
 'limitations':['원화 재양자화·MIPS·게임 실행은 하지 않았다.','새133/135의상은아직이보고서에포함하지않았다.','현재몸표시exact관계와원작몸동작/효과의관계는같은뜻이아니다.']}
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'sha':sha((O/'report.json').read_bytes()),'rules':reconstruction,'tile7':slanted,'aliases':aliases,
 'layers':[(r['ref'],{b:v['opaque']for b,v in r['layers'].items()})for r in rows]},ensure_ascii=False))
