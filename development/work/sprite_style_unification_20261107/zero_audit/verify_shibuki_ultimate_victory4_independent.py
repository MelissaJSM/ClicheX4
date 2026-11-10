"""Shibuki Ultimate 승리4 고정 등록→공통·국소정합→실제ARC 독립 reader."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
H=D.parent/'shibuki_audit';P=H/'prepared_ultimate_victory01';T=H/'ultimate_victory_targets01';O=D/'shibuki_ultimate_victory4_independent01'
PBS=(0,5,6,7,8);REFS={204,205,206,207};RESERVED={105,*range(175,183)}
sha=lambda x:hashlib.sha256(x).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def readj(p):return json.loads(readb(p))
def png(p):readb(p);return np.asarray(Image.open(p))
def poly(v):return polygons([v])
def shift(z,dy):
 out=np.zeros_like(z)
 if dy==1:out[1:]=z[:-1]
 elif dy==-1:out[:-1]=z[1:]
 else:raise ValueError(dy)
 return out
oldp=H/'prepared_ultimate_arrival_partial01/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=readb(oldp),readb(newp)
assert sha(old)=='3e55b972c007731a8446c8478336c6def303e0dc5ed4ab5d6a52856471327138'
assert sha(new)=='ec7a6847ec8de42a3b25c1d0b87fdc96330bc61488c2296426ab24cbe9cfa9b8'
a,b=Archive(old),Archive(new);proposal=readj(P/'proposal.json');lock=readj(P/'SOURCE_LOCK.json')
assert sha(readb(P/'SOURCE_LOCK.json'))==proposal['target_lock']['sha256']
assert lock['parent_sha256']==sha(old) and lock['candidate_sha256']==sha(new)
for p,h in lock['files'].items():assert sha(readb(ROOT/p))==h,p
meta=readj(T/'manifest.json');assert set(meta['refs'])==REFS and meta['parent_sha256']==sha(old)
assert sha(readb(T/'manifest.json'))==proposal['targets']['sha256']
for p,h in meta['source_files'].items():assert sha(readb(ROOT/p))==h,p
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.int32)
lut=np.r_[0,1+((rgb[17:32,None]-rgb[None,1:16])**2).sum(2).argmin(1)].astype(np.uint8)
inv=np.r_[0,1+((rgb[1:16,None]-rgb[None,17:32])**2).sum(2).argmin(1)].astype(np.uint8)
yy,xx=np.indices((384,384));yy-=160;xx-=160
body={};sources=[]
for n in sorted(REFS):
 first=n<206;s=H/('ultimate_victory_native01'if first else'ultimate_victory_native02')
 c=H/('ultimate_victory_common_probe02'if first else'ultimate_victory_late_common02');cm=readj(c/'report.json')
 assert cm['palette_before_to_after']==lut.tolist()
 assert sha(readb(s/'report.json'))==cm['source_report_sha256']
 before=png(s/f'before_{n:03}_indices.png').copy();initial=png(s/f'after_{n:03}_indices.png');aft=initial.copy()
 arm=np.zeros_like(aft,bool)
 if n==204:
  donor=png(H/'ultimate_victory204_arm_native01/after_204_indices.png');arm=(xx>=-24)&(xx<=-5)&(yy>=-6)&(yy<=5);aft[arm]=donor[arm]
 elif n==206:
  donor=png(H/'ultimate_victory206_arm_native01/after_206_indices.png');arm=poly([(4,-18),(9,-18),(10,-13),(7,-11),(6,-7),(3,-2),(-1,-2),(1,-6),(2,-10),(2,-13)]);aft[arm]=donor[arm]
 assert np.array_equal(aft[~arm],initial[~arm])
 if first:
  assert cm['palette_after_to_before']==inv.tolist()
  addition=(before==0)&(aft>0)&(xx>=-16)&(xx<=-12)&(yy>=1)&(yy<=6)
  before[addition]=inv[aft][addition]
  head=poly([(-16,-25),(8,-25),(10,-18),(8,-12),(9,-7),(6,-3),(2,-3),(-1,-4),(-7,-4),(-11,-5),(-15,-9),(-17,-13)])
  head|=poly([(6,-14),(12,-14),(12,-9),(15,-5),(12,-4),(13,-1),(16,1),(14,4),(15,8),(12,10),(11,14),(7,14),(8,10),(6,8),(8,5),(7,1),(7,-3),(5,-7)])
  if n==205:head[(xx<-8)&(yy>-16)]=False
  legs=poly([(-12,9),(-7,9),(-3,12),(-6,16),(-6,23),(-16,23),(-16,17),(-11,14)])|poly([(-1,9),(4,9),(5,11),(9,15),(9,18),(13,20),(13,23),(6,23),(3,18),(0,15),(-1,12)])
  hands=((xx>=-24)&(xx<=-18)&(yy>=-7)&(yy<=-2))if n==204 else((xx>=-13)&(xx<=-6)&(yy>=-18)&(yy<=-11))
  hands|=(xx>=-1)&(xx<=4)&(yy>=2)&(yy<=7);hands&=np.isin(before,(10,11,12,13))
  if n==204:hands|=((xx>=-24)&(xx<=-19)&(yy>=-7)&(yy<=-1))|((xx==-18)&(yy>=-5)&(yy<=-2))
  common=head|legs|hands
  extra={'before_braid_addition':addition}
 else:
  head=poly([(-17,-26),(4,-26),(6,-20),(5,-16),(4,-14),(3,-11),(2,-8),(-1,-5),(-4,-3),(-8,-5),(-13,-8),(-17,-13)])
  head|=poly([(10,-10),(13,-8),(14,-1),(13,4),(14,8),(9,13),(7,14),(6,11),(7,8),(6,4),(7,0),(5,-3),(7,-5),(9,-4)])
  if n==207:head[(xx>=3)&(yy>=-21)&(yy<=-7)]=False
  legs=poly([(-11,9),(-6,9),(-4,10),(-5,13),(-8,16),(-8,18),(-5,20),(-5,24),(-16,24),(-16,19),(-12,16),(-11,13)])|poly([(-1,9),(4,9),(5,12),(7,15),(7,18),(10,19),(10,24),(2,24),(1,18),(-2,15),(-2,11)])
  legs|=(xx==-12)&(yy==13)
  hands=((xx>=4)&(xx<=9)&(yy>=-18)&(yy<=-14))if n==206 else((xx>=1)&(xx<=10)&(yy>=-29)&(yy<=-22))
  hands|=(xx>=-15)&(xx<=-9)&(yy>=-3)&(yy<=1)
  foot=(((xx>=-16)&(xx<=-4))|((xx>=0)&(xx<=10)))&(yy>=16)
  footold=before.copy();dst=shift(foot,1);before[foot&(yy>16)]=0;before[dst]=shift(footold,1)[dst]
  assert np.array_equal(before[(yy==16)&foot],footold[(yy==16)&foot])
  assert np.array_equal(before[dst],shift(footold,1)[dst])
  raised=np.zeros_like(foot)
  if n==207:
   raised=(xx>=0)&(xx<=11)&(yy<=-21);handold=before.copy();dsthand=shift(raised,-1);before[raised&(yy<-21)]=0;before[dsthand]=shift(handold,-1)[dsthand]
   assert np.array_equal(before[raised&(yy==-21)],handold[raised&(yy==-21)])
   assert np.array_equal(before[dsthand],shift(handold,-1)[dsthand])
  # 제작 마스크는 canvas 끝에서 roll하지만 원화 가장자리는 완전히 비어 있다.
  # 실제 pixels는 비순환 이동으로 재구성하고 저장마스크의 빈 wrap행만 대조한다.
  assert not footold[-1].any()
  if n==207:assert not handold[0].any()
  common=head|legs|hands|foot|np.roll(foot,1,axis=0)|raised|np.roll(raised,-1,axis=0)
  extra={'foot_source':foot,'raised_hand_source':raised}
 aft[common]=lut[before][common]
 masks={'head':head,'legs':legs,'hands':hands,'common':common,'after_arm_donor':arm,**extra}
 for name,m in masks.items():assert np.array_equal(m,png(c/f'{n:03}_{name}_mask.png')>0),(n,name)
 assert np.array_equal(before,png(c/f'before_{n:03}_indices.png'))
 assert np.array_equal(aft,png(c/f'after_{n:03}_indices.png'))
 assert not np.any((aft>0)&(before==0))
 assert label(aft>0,np.ones((3,3)))[1]==1
 body['before',n],body['after',n]=before,aft
 sources.append({'ref':n,'registered_pair':rel(s),'common_and_local_masks_reconstructed':True,'local_arm_donor':n in(204,206),'braid_source_cells':int(addition.sum())if first else 0,'foot_yplus1':not first,'hand_yminus1':n==207,'seam_rows_preserved':[]if first else[16]+([-21]if n==207 else[]),'old_body_overlaid':False})

target={}
for n in sorted(REFS):
 bef,aft=body['before',n],body['after',n]
 equal=np.all(color(a,bef,16)==color(a,aft),axis=2)
 target[n,0]=aft;target[n,5]=np.where(equal,0,bef).astype(np.uint8)
 for pb in(6,7,8):target[n,pb]=np.zeros_like(aft)
 for pb in PBS:
  assert np.array_equal(target[n,pb],png(T/f'{n:03}_bank{pb}_indices.png'))
  assert sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]

counts=collections.Counter();assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new)
assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for q in ae:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)
assert bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert (ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']];counts['other_graphics_banks_byte_exact']+=1
 for f,g in zip(ab['frames'],bb['frames']):
  n=f['index'];assert n==g['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert g['tile_count']==32
  else:assert raw(a,gb,n)==raw(b,gb,n)and f['tile_count']==g['tile_count'];counts['non_target_raw_exact']+=1
for n in range(237):
 if n in RESERVED:continue
 for pb in PBS:
  want=target[n,pb]if n in REFS else a.layer(n,pb)[0]
  assert np.array_equal(b.layer(n,pb)[0],want),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 oldparts={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
 addr={q['record_offset']for n in REFS if n in oldparts and pb in PBS for q in oldparts[n]}
 for n,op in oldparts.items():
  bp=parts(b,pb,n)
  if pb in PBS and n in REFS:
   assert len(bp)<=256
   for q in bp:
    t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0
    v=tile(b,n,t);assert not(t%16==0 and v[:,0].any());assert not(q['flip_y']and t//16==0 and v[0].any());counts['GPU_parts_checked']+=1
  else:
   assert [sig(q)for q in op]==[sig(q)for q in bp];counts['non_target_compositions_exact']+=1
   overlap=sorted(addr&{q['record_offset']for q in op})
   if overlap:shared.append({'bank':pb,'ref':n,'parent_shared_record_offsets':overlap,'whole_semantics_exact':True})
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   assert np.array_equal(expected,np.asarray(b.composite(n,mask,arm)[0]));counts['partial_RGBA_exact']+=1
 for f,mask,pal in(('before',15,16),('after',0,0)):
  assert np.array_equal(color(b,body[f,n],pal),np.asarray(b.composite(n,mask)[0]))
O.mkdir(exist_ok=True);sheets=[]
for i,ns in enumerate(((204,205),(206,207))):
 pics=[(f'{n} {caption}',ar.composite(n,mask)[0])for n in ns for ar,mask,caption in((a,15,'old before'),(b,15,'new before'),(a,0,'old after'),(b,0,'new after'))]
 boxes=[im.getbbox()for _,im in pics];box=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3)
 w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*5+10,h*5+26;board=Image.new('RGB',(cw*4,ch*2),'#263345');dr=ImageDraw.Draw(board)
 for k,(caption,im)in enumerate(pics):
  x,y=k%4*cw,k//4*ch;dr.text((x+4,y+4),caption,fill='white');v=im.crop(box).resize((w*5,h*5),Image.Resampling.NEAREST);board.paste(v,(x+4,y+22),v)
 p=O/f'readback_{i:02}.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==508 and counts['target_layers_exact']==20 and counts['non_target_layers_exact']==1120 and counts['partial_RGBA_exact']==128
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'Shibuki Ultimate 승리4 고정등록8·국소팔2→새머리/사지/손·발 정합→20층 독립검사','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'source_lock_sha256':sha((P/'SOURCE_LOCK.json').read_bytes()),'locked_inputs':len(lock['files']),'counts':dict(counts),'source_reconstruction':sources,'old_shared_non_target_compositions':shared,'other_entries_audio_palette_bank_boundaries_exact':True,'part_counts':{str(n):{str(pb):len(parts(b,pb,n))for pb in PBS}for n in sorted(REFS)},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'native_MIPS_executed_here':False,'runtime_verified':False,'user_accepted':False,'limitations':['최초 생성원화 재양자화는 반복하지 않고 잠긴 고정등록 이후 공통부·국소팔·접속행/발/손 정합을 독립재구성했다.','대상128RGBA와 비대상1120층/팔레트 불변을 검사했으며 제작자 전체7296RGBA 재실행이 아니다.','원MIPS/원표 재생·실기·사용자수용은 별도이다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))
