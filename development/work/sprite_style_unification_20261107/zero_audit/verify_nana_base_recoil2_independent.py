"""Nana 기본/포스 정지3 독립 원화→자원 reader. 제작 모듈 미호출."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons,render
S=B/'root_nana_recoil';T=S/'joint_layers02';P=S/'packed_recoil03';O=D/'nana_base_recoil2_independent01'
PBS=(0,5,6,7,8);REFS={90,91};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def poly(p):return polygons([p])
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
Y,X=np.indices((384,384));Y-=160;X-=160
oldp=B/'nana_audit/base_settle_repaint/packed_settle_candidate_v1/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='15d01f06aee14e3264d7ce41d1358a530147e4a3464d3ac949b64cde5085a775'
assert sha(new)=='ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4'
meta=js(T/'manifest.json');reg=js(S/'registered01/manifest.json')
assert meta['parent_sha256']==sha(old)
assert reg['parent_sha256']==meta['source_parent_sha256']
source_parent=Archive(blob(ROOT/js(S/'inputs01/manifest.json')['parent_arc']))
assert sha(source_parent.data)==reg['parent_sha256'] and source_parent.p==a.p
for n in REFS:
 for pb in PBS:assert np.array_equal(a.layer(n,pb)[0],source_parent.layer(n,pb)[0])
art=S/'art01/generated.png';blob(art);assert sha(art.read_bytes())==reg['source_sha256']=='2d7bc4ab502eeb79f498f87d89cb1e5c840cc4381e7af7d531699b52dccbf9e6'
image=Image.open(art).convert('RGBA');assert list(image.size)==reg['source_size']
registered={};quant=[]
# 원 RGB/alpha의 최근접 색인별 면적투표를 직접 재계산한다.
for q in reg['frames']:
 form,n=q['form'],q['ref'];palstart=16 if form=='fourth'else 0
 pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[palstart:palstart+16]],np.float32)
 rgba=np.array(image.crop(q['source_crop']));rgb=rgba[:,:,:3].astype(np.float32);alpha=rgba[:,:,3].astype(np.float32)/255
 ix=np.empty(alpha.shape,np.uint8)
 for y in range(len(ix)):ix[y]=1+np.square(rgb[y,:,None,:]-pal[None,1:,:]).sum(2).argmin(1)
 green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(rgba[:,:,3]>=128);green[len(green)//2:]=False;ix[green]=14
 weights=np.stack([np.asarray(Image.fromarray(np.where(ix==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
 coverage=np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
 small=1+weights.argmax(0).astype(np.uint8);small[coverage<.5]=0
 eyes=weights[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
 if eyes.max()>.015:small[np.unravel_index(eyes.argmax(),eyes.shape)]=14
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=small
 assert sha(z.tobytes())==q['indices_sha256']
 assert np.array_equal(z,png(S/'registered01'/f'{form}_{n:03}_indices.png'))
 assert sha(color(a,z,palstart).tobytes())==q['rgba_sha256']
 registered[form,n]=z;quant.append({'form':form,'ref':n,'crop':q['source_crop'],'fixed96_vote_exact':True})


donorpath=B/'nana_audit/ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC'
donor=Archive(blob(donorpath));assert sha(donor.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
z=donor.layer(85)[0];gm=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(z,range(1,10))
gun=np.where(gm,z,0).astype(np.uint8);assert np.count_nonzero(gun)==20
case=np.zeros_like(gun);case[:,:-2]=gun[:,2:]
target={};proof=[];bodies={};eyes=[]
for n in sorted(REFS):
 base,fourth=registered['base',n].copy(),registered['fourth',n].copy()
 q=next(q for q in meta['source_registration']if q['ref']==n)
 if n==90:
  shared=poly([[-22,-20],[-14,-20],[-11,-13],[-14,-9],[-18,-11]])
  fourth[shared]=base[shared];weapons={'method':'새 base 사선 권총·손을 양폼 공유','polygon':q['weapon']['polygon']}
 else:
  registrations=[]
  for form,body in(('base',base),('fourth',fourth)):
   original=body.copy();skin=(X>=-22)&(X<=-17)&(Y>=-9)&(Y<=-6)&np.isin(body,(10,11,12,13))
   remove=(X>=-25)&(X<=-17)&(Y>=-13)&(Y<=-7)&((Y<=-10)|(X<=-20))&np.isin(body,range(1,10))
   body[remove]=0;visible=(case>0)&~skin;body[visible]=case[visible];body[skin]=original[skin]
   rec={'form':form,'removed':[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(remove)],'skin_preserved':int(skin.sum()),'gun_hand_contact8':int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())}
   assert rec==next(x for x in q['weapon']['registrations']if x['form']==form)
   registrations.append(rec)
  shared=(X>=-25)&(X<=-16)&(Y>=-13)&(Y<=-5);fourth[shared]=base[shared]
  weapons={'method':'정본85 20색인 texel x−2 평행이동, 새 피부/손가림 보존','source':rel(donorpath),'translation':[-2,0],'registrations':registrations}
 source=fourth.copy();region=(Y>=8)&(Y<=22)&(X>=-18)&(X<=16);links=[]
 for y in range(168,183):
  runs=spans((source[y]>0)&region[y]);groups={}
  for gap in spans((base[y]>0)&(fourth[y]==0)&region[y]):
   assert runs
   near=min(runs,key=lambda r:np.abs(r[:,None]-gap).min());groups.setdefault((int(near[0]),int(near[-1])),[]).append(gap)
  for(l,r),gaps in groups.items():
   lo=min(l,*(int(g[0])for g in gaps));hi=max(r,*(int(g[-1])for g in gaps));dest=np.arange(lo,hi+1)
   assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1))
   sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)]
   fourth[y,dest]=source[y,sx]
   links.extend({'destination':[int(x-160),y-160],'source':[int(xx-160),y-160],'index':int(source[y,xx])}for x,xx in zip(dest,sx))
 assert links==q['leg_registration']
 owner=np.full(base.shape,6,np.uint8);owner[(Y>=5)|((X>=7)&(Y>=-15))]=8
 left=[[-24,-21],[-13,-21],[-9,-12],[-3,-7],[-4,-2],[-17,-7]]if n==90 else[[-26,-14],[-15,-14],[-11,-9],[-3,-8],[-3,-2],[-16,-4],[-22,-6]]
 owner[poly(left)]=7;owner[poly([[3,-8],[12,-7],[14,6],[7,8],[3,2]])]=7
 owner[(X>=-9)&(X<=6)&(Y>=-21)&(Y<=-6)]=5
 owner[(X>=7)&(Y<=-16)]=5;owner[(X>=7)&(X<=13)&(Y>=-15)&(Y<=-9)]=5;owner[shared]=7
 full=np.where(fourth,fourth,base).astype(np.uint8)
 pd=np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]
 diff=((full!=base)|((fourth>0)&pd))&(full>0)
 ls={0:base,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 frame=next(q for q in meta['frames']if q['ref']==n)
 for pb,v in ls.items():
  assert np.array_equal(v,png(T/f'layer{pb}_{n:03}.png'))and sha(v.tobytes())==frame['layer_hashes'][str(pb)]
  target[n,pb]=v
 assert np.array_equal(owner,png(T/f'owner_{n:03}.png'))
 for form,body in(('base',base),('fourth',fourth)):
  original=registered[form,n];mask=(original==14)&(Y<0)
  assert np.array_equal(body[mask],original[mask]);eyes.append({'ref':n,'form':form,'authored_eye_pixels_exact':int(mask.sum())})
 bodies[n]=(base.copy(),fourth.copy());proof.append({'ref':n,'weapon':weapons,'same_row_leg_links':len(links),'row_wise_max_extension':2,'owner_exact':True})
counts=collections.Counter();assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new);assert[(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for q in ae:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
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
 aps={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
 addresses={q['record_offset']for n in REFS if n in aps and pb in PBS for q in aps[n]}
 for n,ps in aps.items():
  qs=parts(b,pb,n)
  if pb in PBS and n in REFS:
   assert 0<len(qs)<=256
   for q in qs:
    t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0;v=tile(b,n,t)
    assert not(t%16==0 and v[:,0].any())and not(q['flip_y']and t//16==0 and v[0].any());counts['GPU_parts_checked']+=1
  else:
   assert[sig(q)for q in ps]==[sig(q)for q in qs];counts['non_target_compositions_exact']+=1
   overlaps=sorted(addresses&{q['record_offset']for q in ps})
   if overlaps:shared.append({'bank':pb,'ref':n,'old_shared_offsets':overlaps,'entire_nonselected_records_exact':True})
for n in sorted(REFS):
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   actual=np.asarray(b.composite(n,mask,arm)[0]);assert np.array_equal(expected,actual)
   assert label(actual[:,:,3]>0,np.ones((3,3)))[1]==1
   counts['partial_RGBA_exact']+=1
 for mask in (0,15):
  bb,ff=bodies[n];expected=color(b,bb)
  if mask:m=ff>0;expected[m]=color(b,ff,16)[m]
  assert np.array_equal(expected,np.asarray(b.composite(n,mask,1)[0]))

headrecords=[sig(q)for q in parts(a,5,9)];assert len(headrecords)==2
head_proof=[]
for n in sorted(REFS):
 assert [sig(q)for q in parts(b,5,n)]==headrecords
 assert len({q['tile']for q in parts(b,5,n)})==2
 assert np.array_equal(render(b,n,5,parts(b,5,n)),target[n,5])
 assert not np.array_equal(target[n,5],a.layer(9,5)[0])
 assert [f['index']for f in a.banks[0]['frames']if f['offset']==a.banks[0]['frames'][n]['offset']]==[n]
 assert [f['index']for f in b.banks[0]['frames']if f['offset']==b.banks[0]['frames'][n]['offset']]==[n]
 head_proof.append({'ref':n,'same_two_records_as_parent9':headrecords,'new_head_equals_authored_target':True,'old9_bitmap_not_reused':True,'independent_stream':True,'tiles':[q['tile']for q in parts(b,5,n)]})
assert raw(a,0,9)==raw(b,0,9)
for pb in PBS:assert [sig(q)for q in parts(a,pb,9)]==[sig(q)for q in parts(b,pb,9)]and np.array_equal(a.layer(9,pb)[0],b.layer(9,pb)[0])
nativep=S/'recoil_components_native_checks.json';native=js(nativep);assert native['passed']
nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
def board(items,name,cols,scale):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];x0=min(q[0]for q in boxes)-4;y0=min(q[1]for q in boxes)-4;x1=max(q[2]for q in boxes)+4;y1=max(q[3]for q in boxes)+4
 cw=(x1-x0)*scale+12;ch=(y1-y0)*scale+26;im=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x,y=i%cols*cw,i//cols*ch;v=pic.crop((x0,y0,x1,y1)).resize(((x1-x0)*scale,(y1-y0)*scale),Image.Resampling.NEAREST);im.paste(v,(x+6,y+22),v);dr.text((x+6,y+4),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_opaque_pixels_clipped':True})
for n in sorted(REFS):board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))],f'full_{n:03}.png',4,5)
for n in sorted(REFS):board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body legs'))],f'partial_{n:03}.png',5,5)

assert counts['raw_checked']==508 and counts['non_target_raw_exact']==506 and counts['partial_RGBA_exact']==64 and counts['target_layers_exact']==10
for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
report={'passed':True,'scope':'나나 기본/포스90·91 생성 원화 재양자화→무기/같은행 다리/부분소유→실제자원 독립 읽기',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent':rel(oldp),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),
 'counts':dict(counts),'source_quantization':quant,'source_registration':proof,'authored_eyes':eyes,'reused_head_records_only':head_proof,'parent9_raw_all_layers_all_records_exact':True,
 'nonselected_shared_compositions':shared,'other_entries_palette_audio_bank_boundaries_exact':True,
 'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'two_new_decoded_hashes_match':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,
 'limitations':['대상64 RGBA와 비대상1130층/1777조립/506raw를 대조했다. 제작자7296 전조합 재실행은 아니다.','원MIPS 기존결과를 현재후보 및 두 decoded hash에 결속했으며 새실행·브라우저·실기는 하지 않았다.','완료율이나 전체캐릭터 완료를 뜻하지 않는다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
