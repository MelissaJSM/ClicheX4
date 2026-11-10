"""Nana138/139 원화등록→총/공통손/동일행다리/머릿결→실제10층 독립 읽기."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
N=D.parent/'nana_audit';U=N/'base_settle_repaint';P=U/'packed_settle_candidate_v1';T=U/'joint_layers_probe_v3';O=D/'nana_base_settle2_independent01'
PBS=(0,5,6,7,8);REFS={138,139};RESERVED={105,*range(175,183)}
sha=lambda x:hashlib.sha256(x).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def readj(p):return json.loads(readb(p))
def png(p):readb(p);return np.asarray(Image.open(p))
def shift(z):
 out=np.zeros_like(z);out[:-1]=z[1:];return out
oldp=D.parent/'root_nana_standing/packed_standing03/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=readb(oldp),readb(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='87cc15efefedd475e0de972587995ad351d3ded1bd38a5c5096d5a3ab441748e'
assert sha(new)=='15d01f06aee14e3264d7ce41d1358a530147e4a3464d3ac949b64cde5085a775'
lock=readj(P/'INPUT_FROZEN.json');assert lock['parent_sha256']==sha(old)and lock['candidate_sha256']==sha(new)
assert sha(readb(P/'INPUT_FROZEN.json'))=='1201dbb282cd7426ce5064c715b421e9d78386d5ba2ae1c7efde4dffb4c6ee08'
for q in lock['files']:assert sha(readb(ROOT/q['path']))==q['sha256'],q['path']
meta=readj(T/'manifest.json');assert sha(readb(T/'manifest.json'))==lock['target_manifest_sha256']
art=Archive(readb(ROOT/meta['art_parent_arc']));assert sha(art.data)==meta['art_parent_sha256']and art.p==a.p
for n in REFS:
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],art.layer(n,pb)[0])
cm=readj(U/'contacts_probe_v1/manifest.json');hm=readj(U/'hair_registered_v1/manifest.json')
assert sha(readb(U/'hair_registered_v1/manifest.json'))==meta['contacts_manifest_sha256']
donor=Archive(readb(ROOT/cm['canonical_donor_path']));assert sha(donor.data)==cm['canonical_donor_sha256']
assert np.array_equal(a.words[:15],donor.words[:15])
yy,xx=np.indices((384,384));yy-=160;xx-=160
dz=donor.layer(85)[0];gm=(xx>=-22)&(xx<=-15)&(yy>=-11)&(yy<=-6)&np.isin(dz,range(1,10))
coords=[[int(x-160),int(y-160),int(dz[y,x])]for y,x in np.argwhere(gm)]
assert coords==cm['canonical20']and len(coords)==20
case=np.zeros_like(dz)
for x,y,v in coords:case[x-9+160,y+2+160]=v
assert np.array_equal(case,png(U/'contacts_probe_v1/canonical_case.png'))
body={};weapons=[]
for q in cm['frames']:
 f=q['form'];src=png(ROOT/q['source_path']);assert sha(readb(ROOT/q['source_path']))==q['source_sha256']
 skin=(xx>=-11)&(xx<-4)&(yy>=-27)&(yy<-23)&np.isin(src,(10,11,12,13))
 remove=(xx>=-11)&(xx<-4)&(yy>=-32)&(yy<-23)&np.isin(src,range(1,10))
 z=src.copy();z[remove]=0;z[(case>0)&~skin]=case[(case>0)&~skin];z[skin]=src[skin]
 assert np.array_equal(z,png(U/f'contacts_probe_v1/{f}_138_weapon.png'))
 assert np.array_equal(skin,png(U/f'contacts_probe_v1/{f}_138_hand.png')>0)
 assert np.array_equal(remove,png(U/f'contacts_probe_v1/{f}_138_removed.png')>0)
 assert np.array_equal(z[~(remove|(case>0))],src[~(remove|(case>0))])
 assert np.array_equal(z[skin],src[skin])
 body[f]=z;weapons.append({'form':f,'canonical20_before_hand_occlusion':20,'visible_canonical_pixels':int(((case>0)&~skin).sum()),'original_new_skin_preserved':int(skin.sum()),'gun_hand_8adjacency':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())})
shared=(xx>=-11)&(xx<-4)&(yy>=-32)&(yy<-23);body['fourth'][shared]=body['base'][shared]
source=body['fourth'].copy()
for q in cm['fourth_same_leg_source_links']:
 x,y=q['destination'];sx,sy=q['source'];assert y==sy and abs(x-sx)<=2 and source[sy+160,sx+160]==q['index']>0
 body['fourth'][y+160,x+160]=source[sy+160,sx+160]
assert len(cm['fourth_same_leg_source_links'])==36 and not cm['registration_rejected_rows']
for f,z in body.items():assert np.array_equal(z,png(U/f'contacts_probe_v1/{f}_138_indices.png'))
assert sha(readb(ROOT/hm['generated_path']))==hm['generated_sha256']
hair=[]
for q in hm['frames']:
 f=q['form'];oldbody=body[f];hd=png(U/f'hair_registered_v1/{f}_donor_138_indices.png')
 assert sha(hd.tobytes())==q['source_indices_sha256']
 m=np.zeros_like(oldbody,bool)
 for sy,(lo,hi)in q['spans'].items():m[int(sy)+160,lo+160:hi+161]=True
 m&=np.isin(oldbody,(5,6,7,8,9));valid=m&np.isin(hd,range(1,10));z=oldbody.copy();z[valid]=hd[valid]
 assert sha(m.tobytes())==q['mask_sha256']and np.array_equal(m,png(U/f'hair_registered_v1/{f}_mask_138_indices.png')>0)
 assert np.array_equal(z>0,oldbody>0)and np.array_equal(z[~m],oldbody[~m])
 changes=[{'world':[int(x-160),int(y-160)],'before':int(oldbody[y,x]),'source':int(hd[y,x])}for y,x in np.argwhere(z!=oldbody)]
 assert changes==q['source_links']and len(changes)==q['changed_cells']
 assert np.array_equal(z,png(U/f'hair_registered_v1/{f}_138_indices.png'))and sha(z.tobytes())==q['output_sha256']
 body[f]=z;hair.append({'form':f,'actual_same_coordinate_donor_cells':len(changes),'whole_alpha_and_outside_head_exact':True})
base,fourth=body['base'],body['fourth'];full=np.where(fourth,fourth,base).astype(np.uint8)
owner=np.full(base.shape,6,np.uint8);owner[(yy>=2)|((xx>=7)&(yy>=-10))]=8;owner[(yy<-11)&(xx>=-7)]=5
owner[(xx>=6)&(yy>=-12)]=8;owner[(xx<=-7)&(yy<-10)]=7
owner[polygons([[(0,-12),(6,-10),(8,-5),(3,-4),(-1,-6)]])]=7
palette_diff=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
change=((full!=base)|((fourth>0)&palette_diff))&(full>0)
layers={0:base,**{pb:np.where(change&(owner==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
assert np.array_equal(owner,png(U/'joint_layers_probe_v2/owner_138.png'))
target={}
for n in sorted(REFS):
 q=next(q for q in meta['frames']if q['ref']==n)
 assert q['translation']==[0,0 if n==138 else -1]
 for pb,z in layers.items():
  target[n,pb]=z if n==138 else shift(z)
  assert np.array_equal(target[n,pb],png(T/f'layer{pb}_{n:03}.png'))and sha(target[n,pb].tobytes())==q['layer_hashes'][str(pb)]
 assert np.array_equal(owner if n==138 else np.roll(owner,-1,axis=0),png(T/f'owner_{n:03}.png'))

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
   assert label(expected[:,:,3]>0,np.ones((3,3)))[1]==1
   if n==139:assert np.array_equal(np.asarray(b.composite(n,mask,arm)[0]),shift(np.asarray(b.composite(138,mask,arm)[0])))

for n in REFS:
 wanted=color(b,base if n==138 else shift(base));fg=color(b,fourth if n==138 else shift(fourth),16);m=fg[:,:,3]>0;wanted[m]=fg[m]
 assert np.array_equal(wanted,np.asarray(b.composite(n,15,1)[0]))
nativep=U/'native_components_v1_native_checks.json';native=readj(nativep);assert native['passed']
nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
def board(items,name,cols):
 boxes=[im.getbbox()for _,im in items];box=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3)
 w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*5+12,h*5+26;out=Image.new('RGB',(cols*cw,((len(items)+cols-1)//cols)*ch),'#263345');dr=ImageDraw.Draw(out)
 for k,(caption,im)in enumerate(items):
  x,y=k%cols*cw,k//cols*ch;dr.text((x+4,y+4),caption,fill='white');v=im.crop(box).resize((w*5,h*5),Image.Resampling.NEAREST);out.paste(v,(x+4,y+22),v)
 p=O/name;out.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
board([(f'{n} {caption}',ar.composite(n,mask)[0])for n in sorted(REFS)for ar,mask,caption in((a,0,'old base'),(b,0,'new base'),(a,15,'old Fourth'),(b,15,'new Fourth'))],'readback.png',4)
board([(f'{n} mask {m}',b.composite(n,m)[0])for n in sorted(REFS)for m in(1,2,4,8,10)],'partial.png',5)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==506 and counts['target_layers_exact']==10 and counts['non_target_layers_exact']==1130 and counts['partial_RGBA_exact']==64
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'Nana138/139 고정몸2+정본총/공통손/동일행36표본/머릿결67셀→10층 독립읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'source_lock_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'locked_inputs':len(lock['files']),'counts':dict(counts),'canonical_weapon':{'source_ref':85,'source_texels':20,'matrix':[[0,1],[1,0]],'translation':[2,-9],'determinant':-1,'description':'직교 반사와 평행이동; 순수90도 회전이라고 부르지 않음','registration':weapons,'new_base_hand_shared_after_registration':True},'same_row_leg_source_links':36,'hair_source_reconstruction':hair,'owner_mask_equal_previous_v2':True,'139_all_layers_and64_RGBA_relation':'138 y−1 exact','old_shared_non_target_compositions':shared,'source_streams':{str(n):{'old_owners':[f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']],'new_offset':b.banks[0]['frames'][n]['offset'],'new_tile_count':b.banks[0]['frames'][n]['tile_count']}for n in sorted(REFS)},'other_entries_palette_audio_bank_boundaries_exact':True,'existing_native_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'two_decoded_hashes_bound':True,'executed_here':False},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,'limitations':['최초 생성원화/머릿결 donor 재양자화는 반복하지 않고 잠긴 등록 색인 이후 원표본 합성과 타깃을 독립 재구성했다.','대상64 RGBA와1130비대상층 보존이며7296 전조합 재실행은 아니다.','새 MIPS/원순서 브라우저/실제 게임 검증은 별도다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))

