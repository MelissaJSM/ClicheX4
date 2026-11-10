from pathlib import Path
D=Path(__file__).parent
prefix=r'''"""Ultimate 특수4: 고정 등록원화 이후의 의미합성/총/파생/자원 독립 reader."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
N=D.parent/'nana_audit';U=N/'ultimate_special_finish_repaint';P=U/'packed_special_candidate_v1';T=U/'targets_v1';C=U/'common_probe_v2';O=D/'nana_ultimate_special4_independent01'
PBS=(0,5,6,7,8);REFS=(95,96,98,99);RESERVED={105,*range(175,183)}
sha=lambda v:hashlib.sha256(v).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
oldp=N/'ultimate_recoil_repaint/packed_recoil_candidate_v1/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=blob(oldp),blob(newp)
assert sha(old)=='ce61617f541fd59a5a3ab0b26bba6ce88cc7740bf5f9d4719c9acb129783c8d0'
assert sha(new)=='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0'
a,b=Archive(old),Archive(new);lock=js(P/'INPUT_FROZEN.json')
assert lock['parent_sha256']==sha(old)and lock['candidate_sha256']==sha(new)and len(lock['files'])==139
for q in lock['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
meta=js(T/'manifest.json');cm=js(C/'manifest.json')
assert meta['parent_arc_sha256']==cm['parent_sha256']==sha(old)and meta['refs']==list(REFS)
assert sha(blob(T/'manifest.json'))==lock['target_manifest_sha256']
assert sha(blob(C/'manifest.json'))==meta['common_manifest_sha256']
assert sha(blob(oldp.parent/'FROZEN.json'))==meta['parent_frozen_sha256']
producer_source=js(T/'source_reconstruction.json')
assert producer_source['passed']and producer_source['target_manifest_sha256']==sha(blob(T/'manifest.json'))
Y,X=np.indices((384,384));Y-=160;X-=160
counts=collections.Counter();body={};source_rows=[]
original85=a.layer(85)[0];gun=np.where((X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(original85,range(1,10)),original85,0).astype(np.uint8)
assert np.count_nonzero(gun)==20
case=np.zeros_like(gun);case[1:,:-3]=gun[:-1,3:]
hand_proof=js(U/'hand98_local_probe_v1/manifest.json');local={}
for form in('before','after'):
 z=png(U/f'contacts_probe_v1/{form}_098_indices.png');donor=png(U/f'hand98_registered_v1/{form}_098_indices.png')
 box=(X>=-23)&(X<=-12)&(Y>=-7)&(Y<=2);skin=box&np.isin(donor,(10,11,12,13));visible=(case>0)&~skin
 z[box]=donor[box];z[visible]=case[visible]
 q=next(q for q in hand_proof['frames']if q['form']==form)
 assert q['source_cells']==[[int(x-160),int(y-160),int(donor[y,x])]for y,x in np.argwhere(box)]
 assert q['canonical_visible']==int(visible.sum())==18 and q['skin_occluded']==int(((case>0)&skin).sum())==2
 assert q['contact8']==int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())
 assert np.array_equal(z,png(U/f'hand98_local_probe_v1/{form}_098_indices.png'))
 local[form]=z
palette=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[:16]],np.float32)
cell=Image.open(U/'a_v1/generated.png').convert('RGBA').crop((0,0,627,627))
def palette_vote(world):
 ar=np.array(cell);al=ar[:,:,3].astype(np.float32)/255;idx=np.empty(al.shape,np.uint8)
 for y in range(len(idx)):
  idx[y]=1+np.square(ar[y,:,:3].astype(np.float32)[:,None,:]-palette[1:15][None,:,:]).sum(2).argmin(1)
 x,y=world;x+=48;y+=48
 votes={str(i):float(np.asarray(Image.fromarray(np.where(idx==i,al,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))[y,x])for i in range(1,15)}
 return int(max(votes,key=votes.get)),votes
for n in(95,98):
 rec=next(q for q in cm['frames']if q['ref']==n)
 bp,dp=ROOT/rec['before_source'],ROOT/rec['after_donor']
 assert sha(blob(bp))==rec['before_source_sha256']and sha(blob(dp))==rec['after_donor_sha256']
 before,donor=png(bp),png(dp);after=before.copy()
 for q in rec['palette15_source']:
  x,y=q['world'];assert before[y+160,x+160]==15
  v,votes=palette_vote(q['source_world']);assert v==q['index']and votes==q['votes'];after[y+160,x+160]=v
 mask=polygons([rec['costume_polygon']])
 for q in rec['source_boundary_links']:
  x,y=q['world'];assert before[y+160,x+160]==q['before_index']and donor[y+160,x+160]==q['source_after_index'];mask[y+160,x+160]=True;counts['source_boundary_cells']+=1
 for q in rec['shared_hand_outline_links']:
  x,y=q['world'];assert before[y+160,x+160]==0 and donor[y+160,x+160]==q['source_after_index']==3
  before[y+160,x+160]=after[y+160,x+160]=donor[y+160,x+160];counts['common_hand_outline_cells']+=1
 after[mask]=donor[mask]
 if n==95:shared=(X<=-13)&(X>=-21)&(Y>=-8)&(Y<=1)
 else:shared=(case>0)|((X>=-23)&(X<=-17)&(Y>=-7)&(Y<=-2)&np.isin(before,(10,11,12,13)))
 assert rec['shared_source_cells']==[[int(x-160),int(y-160),int(before[y,x])]for y,x in np.argwhere(shared)]
 after[shared]=before[shared]
 for tag,z in(('before',before),('after',after),('donor',donor),('costume_mask',mask.astype(np.uint8)*255),('shared_mask',shared.astype(np.uint8)*255),('outside',((after>0)&(before==0)).astype(np.uint8)*255)):
  assert np.array_equal(z,png(C/f'{tag}_{n:03}_indices.png'))
 assert not np.any((after>0)&(before==0))and label(before>0,np.ones((3,3)))[1]==label(after>0,np.ones((3,3)))[1]==1
 for dx in(0,1):
  for form,z in(('before',before),('after',after)):body[form,n+dx]=np.roll(z,dx,1)
 source_rows.append({'ref':n,'registered_before_hash':sha(bp.read_bytes()),'registered_donor_hash':sha(dp.read_bytes()),'boundary_cells':len(rec['source_boundary_links']),'new_hand_common_cells':len(rec['shared_hand_outline_links']),'95_diagonal_not_canonical':n==95,'98_module_translation':[-3,1]if n==98 else None,'98_visible_occluded':[18,2]if n==98 else None})
target={}
for n in REFS:
 before,after=body['before',n],body['after',n];target[n,0]=after
 pd=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[before];target[n,5]=np.where((before!=after)|pd,before,0).astype(np.uint8)
 for pb in(6,7,8):target[n,pb]=np.zeros_like(after)
 for pb in PBS:
  assert np.array_equal(target[n,pb],png(T/f'layer{pb}_{n:03}.png'))and sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]
'''
old=(D/'verify_nana_ultimate_recoil2_independent.py').read_text('utf8')
generic=old[old.index('assert len(old)==len(new)'):old.index('O.mkdir(exist_ok=True);sheets=[]')]
generic=generic.replace("==[n]","==([95,96]if n in(95,96)else[98,99])")
tail=r'''
O.mkdir(exist_ok=False);sheets=[]
for n in REFS:
 box=(120,127,194,188);w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*5+10,h*5+26
 board=Image.new('RGB',(cw*3,ch*2),'#263345');draw=ImageDraw.Draw(board)
 for row,(form,mask)in enumerate((('before',15),('after',0))):
  for col,(caption,im)in enumerate((('old',a.composite(n,mask)[0]),('new',b.composite(n,mask)[0]),('idle',b.composite(0,mask)[0]))):
   bb=im.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   x,y=col*cw,row*ch;draw.text((x+4,y+4),f'{n} {form} {caption}',fill='white');z=im.crop(box).resize((w*5,h*5),Image.Resampling.NEAREST);board.paste(z,(x+4,y+22),z)
 p=O/f'readback_{n}.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==508 and counts['target_layers_exact']==20 and counts['partial_RGBA_exact']==128
assert counts['source_boundary_cells']==53 and counts['common_hand_outline_cells']==1 and len(reserved)==45
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'Ultimate 특수4의 고정 등록원화 이후 의미합성/정본총/새사선총/파생→20층→후보자원 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_frozen_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'locked_inputs':len(lock['files']),'counts':dict(counts),'source_registration':source_rows,'new_alias_policy':'96=95 X+1,99=98 X+1. 현재 옛 after와 동일 복원이라는 뜻이 아니다.','shared_raw_groups':[[95,96],[98,99]],'nonselected_shared_compositions':shared,'reserved':reserved,'palette_audio_other_entries_bank_boundaries_exact':True,'source_reconstruction_existing_evidence':{'path':rel(T/'source_reconstruction.json'),'sha256':sha((T/'source_reconstruction.json').read_bytes()),'executed_here':False},'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'four_decoded_hashes_match':True,'executed_here':False},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['원화12셀의 고정96 재양자화 전체를 새로 실행하지 않았다. 잠금139개를 확인하고 고정등록 이후 의상53셀/공통손1셀/98손과정본/팔레트15 표본1셀을 직접 재구성했다.','대상128RGBA·1120비대상층/1771조립/508raw를 직접 대조했다. 제작자 전체7296RGBA 재실행은 아니다.','원MIPS 기존결과를 후보와 결속했으며 새MIPS/브라우저/실기는 실행하지 않았다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
'''
(D/'verify_nana_ultimate_special4_independent.py').write_text(prefix+generic+tail,'utf8')
