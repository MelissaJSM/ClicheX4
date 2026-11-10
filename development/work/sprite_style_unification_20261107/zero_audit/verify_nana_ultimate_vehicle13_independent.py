"""Ultimate 차량13: 생성8고정셀·새소유·9Y별칭→65층→자원 독립 reader."""
from pathlib import Path
import collections, hashlib, json, sys
import numpy as np
from PIL import Image, ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;N=D.parent/'nana_audit'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
U=N/'ultimate_vehicle_repaint';P=U/'packed_vehicle_candidate_v1';T=U/'targets_v1';C=U/'common_probe_v2';O=D/'nana_ultimate_vehicle13_independent01'
PBS=(0,5,6,7,8);REFS=tuple(range(162,175));KEYS=(162,166,170,174);RESERVED={105,*range(175,183)}
DY={162:0,163:1,164:3,165:-1,166:0,167:1,168:3,169:-1,170:0,171:1,172:2,173:-1,174:0}
sha=lambda z:hashlib.sha256(z).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 z=p.read_bytes();tracked[rel(p)]=sha(z);return z
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def shift(z,dy):
 out=np.zeros_like(z);yy,xx=np.nonzero(z);assert not len(yy)or min(yy+dy)>=0 and max(yy+dy)<384;out[yy+dy,xx]=z[yy,xx];return out
oldp=N/'ultimate_special_finish_repaint/packed_special_candidate_v1/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='56a3aeb489229d85bb72205bd14f866b4444ff5daa8e1bc7f91c82e9b3c46fc0'
assert sha(new)=='94326933d0dd62ccd7a5904019cae9fd36fc068a6acde8941d6bf8ff363666ca'
lock=js(P/'INPUT_FROZEN.json');assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)and len(lock['files'])==160
for q in lock['files']:assert sha(blob(ROOT/q['path']))==q['sha256'],q['path']
meta=js(T/'manifest.json');cm=js(C/'manifest.json');ct=js(U/'contacts_probe_v1/manifest.json')
assert sha(blob(T/'manifest.json'))==lock['target_manifest_sha256'] and meta['parent_arc_sha256']==sha(old) and meta['refs']==list(REFS)
assert sha(blob(C/'manifest.json'))==meta['common_manifest_sha256']and sha(blob(oldp.parent/'FROZEN.json'))==meta['parent_frozen_sha256']
relation=js(ROOT/meta['source_relation_evidence']['path']);assert sha(blob(ROOT/meta['source_relation_evidence']['path']))==meta['source_relation_evidence']['sha256']
# Inputs preceded the special4 pack. Verify its palette and all vehicle layers,
# rather than assuming the old working parent equals the final pack parent.
imeta=js(U/'a_inputs_v1/manifest.json');prior=Archive(blob(ROOT/imeta['parent_arc']))
assert sha(blob(ROOT/imeta['parent_arc']))==imeta['parent_arc_sha256']and prior.p==a.p
for n in REFS:
 assert raw(prior,0,n)==raw(a,0,n)
 for pb in PBS:assert np.array_equal(prior.layer(n,pb)[0],a.layer(n,pb)[0])and [sig(q)for q in parts(prior,pb,n)]==[sig(q)for q in parts(a,pb,n)]
counts=collections.Counter();Y,X=np.indices((384,384));Y-=160;X-=160
pal={f:np.array([[((int(w)>>s)&31)*255//31 for s in(0,5,10)]for w in a.words[start:start+16]],np.float32)for f,start in(('before',16),('after',0))}
registered={};cells={};quant=[];vote_cache={}
def vote_arrays(cell,palette,excluded=(),green=False):
 ar=np.array(cell);rgb=ar[:,:,:3].astype(np.float32);alpha=ar[:,:,3].astype(np.float32)/255
 avail=np.array([v for v in range(1,16)if v not in excluded]);idx=np.empty(alpha.shape,np.uint8)
 for y in range(len(idx)):idx[y]=avail[np.square(rgb[y,:,None]-palette[None,avail]).sum(2).argmin(1)]
 if green:
  eye=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(ar[:,:,3]>=128);eye[len(eye)//2:]=False;idx[eye]=14
 votes=np.stack([np.asarray(Image.fromarray(np.where(idx==v,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for v in avail])
 coverage=np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX))
 return avail,votes,coverage
for page,ns in(('a',(162,166)),('b',(170,174))):
 ap=U/f'{page}_v1/generated.png';rm=js(U/f'{page}_registered_v1/manifest.json');assert sha(blob(ap))==rm['source_art_sha256'];source=Image.open(ap).convert('RGBA');assert source.size==(1254,1254)
 for q in rm['frames']:
  form,n=q['form'],q['ref'];assert n in ns and q['translation']==[0,0]and q['source_native_scale']==[96,627]
  cell=source.crop(q['source_crop']);av,votes,coverage=vote_arrays(cell,pal[form],green=True)
  z96=av[votes.argmax(0)].astype(np.uint8);z96[coverage<.5]=0;eyes=votes[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
  if eyes.max()>.015:z96[np.unravel_index(eyes.argmax(),eyes.shape)]=14
  z=np.zeros((384,384),np.uint8);z[112:208,112:208]=z96
  assert sha(z.tobytes())==q['target_sha256']and np.array_equal(z,png(U/f'{page}_registered_v1/{form}_{n:03}_indices.png'))
  registered[form,n]=z;cells[form,n]=cell;quant.append({'ref':n,'form':form,'source_image':rel(ap),'source_crop':q['source_crop'],'fixed96_requantized_exact':True,'whole_body_translation':[0,0]})
assert len(registered)==8
def vote(sourceform,n,renderform,world,excluded):
 k=(sourceform,n,renderform,tuple(excluded))
 if k not in vote_cache:vote_cache[k]=vote_arrays(cells[sourceform,n],pal[renderform],excluded)
 av,votes,_=vote_cache[k];x,y=world;x+=48;y+=48
 return int(av[votes[:,y,x].argmax()]),{str(int(v)):float(votes[i,y,x])for i,v in enumerate(av)}
contacts={};sourceproof=[]
for q in ct['frames']:
 f,n=q['form'],q['ref'];z=registered[f,n].copy();assert sha(z.tobytes())==q['source_sha256']
 for e in q['iris_source_registration']:
  x,y=e['world'];assert z[y+160,x+160]==14;v,vv=vote(f,n,f,(x,y),(14,15));assert v==e['value']and vv==e['votes'];z[y+160,x+160]=v
  xx,yy=e['original_iris_preserved_at'];assert z[yy+160,xx+160]==14;counts['iris_source_samples']+=1
 if n==170:masks=[((X<=-11)&(Y>=-7)&(Y<=-2),-1,-1), (Y>=8,0,-1)]
 elif n==174:masks=[((X<=-9)&(Y>=-12)&(Y<=-5),0,-1), ((X>=-5)&(Y>=7),0,-1)]
 else:masks=[]
 assert len(masks)==len(q['rigid_pieces'])
 for (mask,dx,dy),r in zip(masks,q['rigid_pieces']):
  p=r['data'];assert p['translation']==[dx,dy]
  assert p['source_cells']==[[int(x-160),int(y-160),int(z[y,x])]for y,x in np.argwhere(mask&(z>0))]
  piece=np.where(mask,z,0);z[mask]=0;dest=np.roll(np.roll(piece,dy,0),dx,1);hit=dest>0;assert int((hit&(z>0)).sum())==p['overlap'];z[hit]=dest[hit];counts['rigid_source_pieces']+=1
 assert sha(z.tobytes())==q['target_sha256']and np.array_equal(z,png(U/f'contacts_probe_v1/{f}_{n:03}_indices.png'))
 contacts[f,n]=z
bodies={};target={};aliases=[]
for q in cm['frames']:
 n=q['ref'];before=contacts['before',n];donor=contacts['after',n];after=before.copy();mask=polygons([q['polygon']])
 for e in q['palette15_source']:
  x,y=e['world'];v,vv=vote('before',n,'after',(x,y),(15,));assert before[y+160,x+160]==15 and v==e['index']and vv==e['votes'];after[y+160,x+160]=v;counts['palette15_source_samples']+=1
 for e in q['source_boundary_links']:
  x,y=e['world'];assert int(before[y+160,x+160])==e['before_index']and int(donor[y+160,x+160])==e['after_source_index'];mask[y+160,x+160]=True;counts['source_boundary_cells']+=1
 after[mask]=donor[mask]
 if n==162:hand=(X<=-16)&(X>=-22)&(Y>=-1)&(Y<=2)
 elif n==166:hand=(X<=-16)&(X>=-22)&(Y>=1)&(Y<=5)
 elif n==170:hand=(X<=-15)&(X>=-20)&(Y>=-7)&(Y<=-4)
 else:hand=(X<=-11)&(X>=-17)&(Y>=-13)&(Y<=-6)
 assert q['shared_hand_cells']==[[int(x-160),int(y-160),int(before[y,x])]for y,x in np.argwhere(hand)]
 after[hand]=before[hand];assert not np.any((after>0)&(before==0))and not q['alpha_clipped']and not q['old_body_copied']
 for tag,z in(('before',before),('after',after),('donor',donor),('costume_mask',mask.astype(np.uint8)*255),('shared_hand_mask',hand.astype(np.uint8)*255),('outside',np.zeros_like(after))):assert np.array_equal(z,png(C/f'{tag}_{n:03}_indices.png'))
 assert label(before>0,np.ones((3,3)))[1]==label(after>0,np.ones((3,3)))[1]==1
 pd=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[before];base={0:after,5:np.where((before!=after)|pd,before,0).astype(np.uint8),6:np.zeros_like(after),7:np.zeros_like(after),8:np.zeros_like(after)}
 for nn in([n]if n==174 else range(n,n+4)):
  dy=DY[nn];frame=next(q for q in meta['frames']if q['ref']==nn);assert frame['source_key']==n and frame['translation']==[0,dy]
  for pb in PBS:
   target[nn,pb]=shift(base[pb],dy);assert np.array_equal(target[nn,pb],png(T/f'layer{pb}_{nn:03}.png'))and sha(target[nn,pb].tobytes())==frame['layer_hashes'][str(pb)]==meta['targets'][str(nn)][str(pb)]
  for f,z in(('before',before),('after',after)):bodies[f,nn]=shift(z,dy)
  assert np.array_equal(np.asarray(a.composite(nn,15)[0]),np.roll(np.asarray(a.composite(n,15)[0]),dy,0))
  aliases.append({'ref':nn,'source_key':n,'dy':dy,'old_before_RGBA_exact':True,'old_after_restoration_claimed':False})
 sourceproof.append({'ref':n,'source_boundary_cells':len(q['source_boundary_links']),'before_after_single_component':True,'after_outside_before_pixels':0,'shared_hand_mask_exact':True})
assert counts['iris_source_samples']==4 and counts['rigid_source_pieces']==8 and counts['source_boundary_cells']==18 and len(target)==65
assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for e in ae:
 if int(e['type'],16)in(2,3):allow[e['offset']:e['offset']+e['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert(ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']]
 for af,bf in zip(ab['frames'],bb['frames']):
  n=af['index'];assert n==bf['index']and af['tile_count']==bf['tile_count'];counts['raw_checked']+=1
  if gb or n not in REFS:assert raw(a,gb,n)==raw(b,gb,n);counts['non_target_raw_exact']+=1
groups=[]
for k,tc in((162,32),(166,28),(170,32),(174,13)):
 ns=[k]if k==174 else list(range(k,k+4))
 for ar in(a,b):
  assert [f['index']for f in ar.banks[0]['frames']if f['offset']==ar.banks[0]['frames'][k]['offset']]==ns
  assert all(ar.banks[0]['frames'][n]['tile_count']==tc for n in ns)
 groups.append({'refs':ns,'tile_count':tc,'parent_offset':a.banks[0]['frames'][k]['offset'],'candidate_offset':b.banks[0]['frames'][k]['offset'],'no_external_raw_owner':True})
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
    t=q['tile']+q['page']*256;assert 0<=t<b.banks[0]['frames'][n]['tile_count']and q['unknown_flags']==0;value=tile(b,n,t)
    assert not(t%16==0 and value[:,0].any())and not(q['flip_y']and t//16==0 and value[0].any());counts['GPU_parts_checked']+=1
  else:
   assert[sig(q)for q in ps]==[sig(q)for q in qs];counts['non_target_compositions_exact']+=1
   overlap=sorted(addresses&{q['record_offset']for q in ps})
   if overlap:shared.append({'bank':pb,'ref':n,'old_shared_offsets':overlap,'nonselected_records_exact':True})
for n in REFS:
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     v=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=v[:,:,3]>0;expected[m]=v[m]
   actual=np.asarray(b.composite(n,mask,arm)[0]);assert np.array_equal(actual,expected)and np.array_equal(actual,color(b,bodies['before'if mask&1 else'after',n],16 if mask&1 else 0))
   assert label(actual[:,:,3]>0,np.ones((3,3)))[1]==1;counts['partial_RGBA_exact']+=1
O.mkdir(exist_ok=False);sheets=[]
def board(items,name,columns,scale=6):
 boxes=[im.getbbox()for _,im in items if im.getbbox()];box=(min(q[0]for q in boxes)-3,min(q[1]for q in boxes)-3,max(q[2]for q in boxes)+3,max(q[3]for q in boxes)+3);w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*scale+10,h*scale+25
 im=Image.new('RGB',(cw*columns,ch*((len(items)+columns-1)//columns)),'#263345');dr=ImageDraw.Draw(im)
 for i,(title,pic)in enumerate(items):
  x,y=i%columns*cw,i//columns*ch;z=pic.crop(box).resize((w*scale,h*scale),Image.Resampling.NEAREST);im.paste(z,(x+5,y+22),z);dr.text((x+5,y+3),title,fill='white')
 p=O/name;im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'same_origin':True,'no_opaque_clipping':True})
for n in KEYS:
 board([(f'{n} {title}',ar.composite(n,mask,1)[0])for ar,mask,title in((a,15,'old jacket'),(b,15,'new jacket'),(a,0,'old bare'),(b,0,'new bare'))],f'full_{n}.png',4)
 board([(f'{n} {title}',b.composite(n,mask,2)[0])for mask,title in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))],f'partial_{n}.png',5,5)
for k in KEYS[:-1]:board([(f'{n} m{m}',b.composite(n,m)[0])for m in(15,0)for n in range(k,k+4)],f'alias_{k}.png',4,5)
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==499 and counts['target_layers_exact']==65 and counts['non_target_layers_exact']==1075 and counts['non_target_compositions_exact']==1726 and counts['partial_RGBA_exact']==416
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
report={'passed':True,'scope':'나나 Ultimate 차량13 생성8고정셀→국소정합/새의상 공통화→9Y별칭/65층→실제자원 독립 읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_frozen_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'locked_inputs':len(lock['files']),'counts':dict(counts),'source_quantization':quant,'source_registration':sourceproof,'new_aliases':aliases,'shared_raw_groups':groups,'nonselected_shared_compositions':shared,'reserved':reserved,'entry_length_palette_audio_other_entries_bank_boundaries_exact':True,'source_relation_evidence':meta['source_relation_evidence'],'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'new_native_MIPS_performed':False,'runtime_verified':False,'user_accepted':False,'overall_complete':False,'limits':['4新몸체의 원래9Y별칭을 새 두폼 공통정책으로 적용한 것으로 현재 옛after의 개별등록 차이 exact 복원은 아니다.','독립 전수는 대상416부분RGBA/499비대상raw/1075비대상층/1726조립이다. 제작자7296전체RGBA 재실행과 구분한다.','그림 없이 가려진 전체타일까지 읽는 저장검사와 최종게임화면/손잡이·페달 접점실기는 구분한다.','새MIPS/원표브라우저/게임은 실행하지 않았다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'sheets':len(sheets)}))
