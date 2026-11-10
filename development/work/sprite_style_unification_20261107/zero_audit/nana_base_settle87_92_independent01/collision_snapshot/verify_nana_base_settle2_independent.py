"""나나 기본/포스87·92 고정원화와 얼굴/손·부분소유 독립 읽기."""
from pathlib import Path
import collections,hashlib,json,sys,struct
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label,binary_dilation
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;W=D.parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
S=W/'root_nana_shot87';T=S/'joint_targets02';P=S/'packed_settle01';O=D/'nana_base_settle2_independent01'
PBS=(0,5,6,7,8);REFS=(87,92);RESERVED={105,*range(175,183)}
sha=lambda z:hashlib.sha256(z).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def spans(row):
 x=np.flatnonzero(row);return []if not len(x)else np.split(x,np.flatnonzero(np.diff(x)>1)+1)
oldp=W/'root_nana_shot85/packed_shot01/PL00_U.ARC';newp=P/'PL00_U.ARC';old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='d2566605170954eebfeb37938dbea8abb611ac265dae572fe8c4b6c2128ceb61'and sha(new)=='8951948879773266cae0bebd408b411f4806b5652257bba3c50df0212b3c6e10'
meta=js(T/'manifest.json');pm=js(P/'report.json');rm=js(S/'registered01/manifest.json');assert meta['parent_sha256']==rm['parent_sha256']==pm['before']==sha(old)and pm['after']==sha(new)
assert pm['targets_manifest_sha256']==sha(blob(T/'manifest.json'))and meta['refs']==list(REFS)
for fn in('prepare_targets.py','register.py','pack_settle.py'):blob(S/fn)
ap=S/'art01/generated.png';assert sha(blob(ap))==rm['source_sha256']=='523729648a683362fe713ce7705084247cdbff0083613f9ef2c65010688ad661';source=Image.open(ap).convert('RGBA');assert list(source.size)==rm['source_size']==[1254,1254]
registered={};quant=[]
for q in rm['frames']:
 form,n=q['form'],q['ref'];start=16 if form=='fourth'else 0
 pal=np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)
 ar=np.array(source.crop(q['source_crop']));rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255;idx=np.empty(alpha.shape,np.uint8)
 for y in range(len(idx)):idx[y]=1+np.square(rgb[y,:,None]-pal[None,1:]).sum(2).argmin(1)
 eye=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(ar[:,:,3]>=128);eye[len(eye)//2:]=False;idx[eye]=14
 vv=np.stack([np.asarray(Image.fromarray(np.where(idx==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)]);cov=np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
 z96=1+vv.argmax(0).astype(np.uint8);z96[cov<.5]=0;ev=vv[13].copy();ev[cov<.5]=0;ev[48:]=0
 if ev.max()>.015:z96[np.unravel_index(ev.argmax(),ev.shape)]=14
 z=np.zeros((384,384),np.uint8);z[112:208,112:208]=z96;assert sha(z.tobytes())==q['indices_sha256']and sha(color(a,z,start).tobytes())==q['rgba_sha256']and np.array_equal(z,png(S/f'registered01/{form}_{n:03}_indices.png'))
 assert q['body_translation']==[0,0]and not q['bbox_rescale'];registered[form,n]=z;quant.append({'ref':n,'form':form,'source_crop':q['source_crop'],'fixed96_requantized_exact':True})
assert len(registered)==4
Y,X=np.indices((384,384));Y-=160;X-=160
target={};bodies={};sourceproof=[];counts=collections.Counter()
for n in REFS:
 q=next(q for q in meta['source_registration']if q['ref']==n)
 bs=registered['base',n].copy();fs=registered['fourth',n].copy()
 face=(X>=-7)&(X<=1)&(Y>=-16)&(Y<=-8);fs[face]=bs[face]
 hand=(X>=-18)&(X<=-8)&(Y>=0)&(Y<=7)if n==87 else(X>=6)&(X<=12)&(Y>=0)&(Y<=6)
 fs[hand]=bs[hand]
 assert q['shared_face_bbox']==[-7,-16,2,-7]and q['shared_new_hand_bbox']==([-18,0,-7,8]if n==87 else[6,0,13,7])
 donor=fs.copy();links=[];max_ext=0
 for y in range(168,183):
  for gap in spans((bs[y]>0)&(fs[y]==0)):
   sr=min(spans(donor[y]>0),key=lambda r:np.min(np.abs(r[:,None]-gap)));lo=min(int(sr[0]),int(gap[0]));hi=max(int(sr[-1]),int(gap[-1]));ext=max(int(sr[0])-lo,hi-int(sr[-1]));max_ext=max(max_ext,ext);assert ext<=2
   dst=np.arange(lo,hi+1);assert len(dst)<=max(3,2*len(sr));sx=sr[np.rint(np.linspace(0,len(sr)-1,len(dst))).astype(int)];fs[y,dst]=donor[y,sx]
   links.extend({'dst':[int(x-160),y-160],'src':[int(xx-160),y-160],'index':int(donor[y,xx])}for x,xx in zip(dst,sx))
 assert links==q['leg_registration'];full=np.where(fs,fs,bs).astype(np.uint8);owner=np.full(bs.shape,6,np.uint8)
 owner[(Y>=5)|((X>=7)&(Y>=-8))]=8;owner[(Y<=-6)&(X>=-10)]=5
 owner[(X<=-5)&(Y>=-5)&(Y<=5)]=7;owner[(X>=5)&(X<=12)&(Y>=-5)&(Y<=6)]=7
 owner[(X>=12)&(Y>=-7)&(Y<=6)]=5;owner[face]=5;owner[hand]=7
 assert np.array_equal(owner,png(T/f'owner_{n:03}.png'))
 diff=((full!=bs)|np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full])&(full>0)
 ls={0:bs,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 frame=next(e for e in meta['frames']if e['ref']==n)
 for pb,z in ls.items():target[n,pb]=z;assert sha(z.tobytes())==frame['layer_hashes'][str(pb)]and np.array_equal(z,png(T/f'layer{pb}_{n:03}.png'))
 for f,z in(('base',bs),('fourth',full)):
  actual=np.argwhere((z==14)&(Y<0));assert actual.tolist()==[[148,156]],(n,f,actual.tolist())
  assert int(np.max(np.nonzero(z)[0])-160)==22
 bodies[n]=bs,full;sourceproof.append({'ref':n,'same_row_leg_links':len(links),'max_horizontal_extension':max_ext,'common_face_hand_exact':True,'owner_map_reconstructed':True,'iris_world':[-4,-12],'floor_y':22})
assert target[92,5][166,173]>0 and target[92,8][166,173]==0
assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new);assert [(e['type'],e['offset'],e['size'])for e in ae]==[(e['type'],e['offset'],e['size'])for e in be]
allow=np.zeros(len(old),bool)
for e in ae:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert bf['tile_count']==32
  else:assert af['tile_count']==bf['tile_count']and raw(a,gb,n)==raw(b,gb,n);counts['non_target_raw_exact']+=1
groups=[]
for n in REFS:
 for ar in(a,b):assert [f['index']for f in ar.banks[0]['frames']if f['offset']==ar.banks[0]['frames'][n]['offset']]==[n]
 groups.append({'ref':n,'parent_offset':a.banks[0]['frames'][n]['offset'],'new_offset':b.banks[0]['frames'][n]['offset'],'external_raw_owner':False})
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   vals=[]
   for ar in(a,b):
    try:vals.append(('renderable',ar.layer(n,pb)[0]))
    except Exception as ex:vals.append((type(ex).__name__,str(ex)))
   assert vals[0][0]==vals[1][0]
   if vals[0][0]=='renderable':assert np.array_equal(vals[0][1],vals[1][1]);counts['reserved_renderable_exact']+=1
   else:assert vals[0][1]==vals[1][1];counts['reserved_same_exception']+=1
   reserved.append({'ref':n,'layer':pb,'state':vals[0][0]});continue
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 aps={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])};addresses={q['record_offset']for n in REFS if n in aps and pb in PBS for q in aps[n]}
 for n,ps in aps.items():
  qs=parts(b,pb,n)
  if pb in PBS and n in REFS:
   for q in qs:
    t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0;value=tile(b,n,t);assert not(t%16==0 and value[:,0].any())and not(q['flip_y']and t//16==0 and value[0].any());counts['GPU_parts_checked']+=1
  else:
   assert[sig(q)for q in ps]==[sig(q)for q in qs];counts['non_target_compositions_exact']+=1
   overlap=sorted(addresses&{q['record_offset']for q in ps})
   if overlap:shared.append({'bank':pb,'ref':n,'old_shared_offsets':overlap,'nonselected_records_exact':True})
head=pm['head_record_sharing'];original=parts(a,5,head['source_tail_ref']);new_head=parts(b,5,87)
raw_records=lambda ps:b''.join(struct.pack('<BBbb',q['flags'],q['tile'],q['x'],q['y'])for q in ps)
old_tail=bytes.fromhex(head['shared_existing_tail']);assert raw_records(original).endswith(old_tail)and raw_records(new_head)==bytes.fromhex(head['new_common_head_records'])and raw_records(parts(b,5,92))==raw_records(new_head)
assert raw_records(new_head).startswith(old_tail)and len(new_head)==6 and head['additional_records']==0
for n in REFS:
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   actual=np.asarray(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,expected)and label(actual[:,:,3]>0,np.ones((3,3)))[1]==1;counts['partial_RGBA_exact']+=1
 for mask in(0,15):
  bs,full=bodies[n];expected=color(b,bs)
  if mask:m=full>0;expected[m]=color(b,full,16)[m]
  assert np.array_equal(expected,np.asarray(b.composite(n,mask,1)[0]))
nativep=S/'settle_components_native_checks.json';nm=js(nativep);assert nm['passed'];res=nm['resources']['PL00_U.ARC'];assert res['candidate_sha256']==sha(new)
checks=next(q for q in res['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
O.mkdir(exist_ok=True);sheets=[]
def board(items,name,cols,scale=6):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];box=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3);w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*scale+10,h*scale+25
 im=Image.new('RGB',(cw*cols,ch*((len(items)+cols-1)//cols)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x,y=i%cols*cw,i//cols*ch;z=pic.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST);im.paste(z,(x+5,y+22),z);dr.text((x+5,y+3),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'no_opaque_clipping':True})
for n in REFS:
 board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))],f'full_{n}.png',4)
 board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))],f'partial_{n}.png',5,5)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==506 and counts['target_layers_exact']==10 and counts['non_target_layers_exact']==1130 and counts['non_target_compositions_exact']==1777 and counts['partial_RGBA_exact']==64
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'Nana base/Fourth87/92 independent source4->10layers->ARC audit','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'counts':dict(counts),'source_quantization':quant,'source_registration':sourceproof,'raw_groups':groups,'head_storage':{**head,'parent85_record_suffix_exact':True,'same6_records_for_both_new_heads':True,'new_head_pixels_exact_target':True,'old_head_art_reused_claimed':False},'nonselected_shared_compositions':shared,'reserved':reserved,'all_entries_palette_audio_bank_boundaries_exact':True,'native_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'decoded2_hashes_independently_rebound':True,'executed_here':False},'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':[]}
report['scope']='나나 기본/포스87·92 생성4고정셀→새얼굴/손·같은행 다리/10소유층→후보자원 독립 읽기'
report['limits']=['생성4셀을 고정96 면적투표로 직접 재양자화하고 같은행 다리표본·새얼굴/손 공유 및92 베일1셀의 head 소유를 재구성했다.','64부분RGBA·506비대상raw·1130층·1777조립을 독립 대조했다. 제작자7296전체RGBA 검사를 다시 실행한 것은 아니다.','기존85 머리의6개 레코드를 공유하되 실제픽셀은 새87/92 목표층과 exact이며 옛머리 그림을 복사한 것이 아니다.','원MIPS는 root 기존결과와 후보 디코드2해시를 결속했으며 새MIPS/실기/원표브라우저는 실행하지 않았다.']
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
