"""Nana 기본/포스 특수4 독립 원화→자원 reader. 제작 모듈 미호출."""
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
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
S=B/'root_nana_special';T=S/'joint_layers04';P=S/'packed_special02';O=D/'nana_base_special4_independent01'
PBS=(0,5,6,7,8);REFS={95,96,98,99};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def blob(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def poly(p):return polygons([p])
def spans(row):
 xs=np.flatnonzero(row);return []if not len(xs)else np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)
Y,X=np.indices((384,384));Y-=160;X-=160
oldp=B/'root_nana_lowhp/packed_lowhp01/PL00_U.ARC';newp=P/'PL00_U.ARC'
old,new=blob(oldp),blob(newp);a,b=Archive(old),Archive(new)
assert sha(old)=='ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16'
assert sha(new)=='f2a968791b3411642a64bec9eb384a7f4b6a6d4e45be928a17b39262676f3648'
meta=js(T/'manifest.json');reg=js(S/'registered01/manifest.json')
assert meta['parent_sha256']==reg['parent_sha256']==sha(old)
art=S/'art01/generated.png';blob(art);assert sha(art.read_bytes())==reg['source_sha256']=='57d4627ed5a08b98f208cd8a27e40cee7979df1729940b6486f82504c15ebf3c'
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
donorp=B/'nana_audit/ultimate_ceremony_repaint/packed_arrival_candidate_v1/PL02_U.ARC';donor=Archive(blob(donorp))
assert sha(donor.data)=='c721ddee3292a88f6d1dbffb49bc79d1a82e08b3d6913cb501dc406800aa23c9'
sourcegun=donor.layer(85)[0];gm=(X>=-22)&(X<=-15)&(Y>=-11)&(Y<=-6)&np.isin(sourcegun,range(1,10))
assert gm.sum()==20 and np.array_equal(donor.words[:15],a.words[:15])
case=np.zeros((384,384),np.uint8)
for y,x in np.argwhere(gm):case[y+1,x-3]=sourcegun[y,x]
target={};proof=[];bodies={}
for entry in meta['source_registration']:
 n=entry['ref'];pair={}
 for q in entry['contact_registration'][:2]:
  z=registered[q['form'],n].copy();assert sha(blob(ROOT/q['source']))==q['source_sha256']
  s,e=q['shoe_source_rows'];ds,de=q['shoe_destination_rows'];assert(ds,de)==(s-1,e-1)
  donorrows=z[s:e].copy();z[ds:e]=0;z[ds:de]=donorrows;pair[q['form']]=z
 base,fourth=pair['base'],pair['fourth']
 if n==95:
  shared=poly(entry['weapon']['shared_module_polygon']);fourth[shared]=base[shared]
 else:
  for q in entry['contact_registration'][2:]:
   z=pair[q['form']];original=z.copy()
   rm=(X>=-27)&(X<=-18)&(Y>=-11)&(Y<=-3)&((Y<=-7)|(X<=-22))&np.isin(z,range(1,10))
   skin=(X>=-23)&(X<=-18)&(Y>=-8)&(Y<=-3)&np.isin(z,(10,11,12,13))
   coords=lambda m:[[int(x-160),int(y-160),int(original[y,x])]for y,x in np.argwhere(m)]
   assert coords(rm)==q['gun_removed']and coords(skin)==q['preserved_skin']
   z[rm]=0;v=(case>0)&~skin;z[v]=case[v];z[skin]=original[skin]
   assert int(v.sum())==q['visible_case_texels']
   assert int(((case>0)&binary_dilation(skin,np.ones((3,3)))).sum())==q['case_hand_contact8']
   assert np.array_equal(z[~(rm|(case>0))],original[~(rm|(case>0))])
  shared=(X>=-27)&(X<=-16)&(Y>=-11)&(Y<=-2);fourth[shared]=base[shared]
 # 각 다리의 같은 원화 행을 최대2px 국소 확장한 링크를 독립 계산.
 src=fourth.copy();links=[];low=3 if n==95 else 10;region=(Y>=low)&(Y<=22)&(X>=-18)&(X<=16)
 for y in range(160+low,183):
  runs=spans((src[y]>0)&region[y]);groups={}
  for gap in spans((base[y]>0)&(fourth[y]==0)&region[y]):
   near=min(runs,key=lambda q:np.abs(q[:,None]-gap).min());groups.setdefault((int(near[0]),int(near[-1])),[]).append(gap)
  for(l,r),gaps in groups.items():
   lo=min(l,*(int(g[0])for g in gaps));hi=max(r,*(int(g[-1])for g in gaps));dest=np.arange(lo,hi+1)
   assert max(l-lo,hi-r)<=2 and len(dest)<=max(3,2*(r-l+1))
   sx=np.arange(l,r+1)[np.rint(np.linspace(0,r-l,len(dest))).astype(int)];fourth[y,dest]=src[y,sx]
   links.extend({'destination':[int(x-160),y-160],'source':[int(s-160),y-160],'index':int(src[y,s])}for x,s in zip(dest,sx))
 assert links==entry['leg_registration']
 own=np.full((384,384),6,np.uint8)
 if n==95:
  own[(Y>=-1)|((X>=7)&(Y>=-15))]=8
  own[poly([[-20,1],[-7,-13],[-3,-10],[-9,-1]])]=7
  own[poly([[7,-10],[18,-9],[19,-1],[8,-1]])]=7
  own[(Y<-14)&(X>=-9)&(X<7)]=5
  own[poly([[6,-25],[10,-22],[14,-17],[17,-10],[18,2],[7,2],[7,-13]])]=8
  assert np.all(own[(Y==-14)&(X>=-9)&(X<7)&(own!=8)]==6)
 else:
  own[(Y>=6)|((X>=9)&(Y>=1))]=8
  own[poly([[-28,-12],[-15,-12],[-3,-5],[-3,1],[-16,-2],[-27,-2]])]=7
  own[poly([[4,-5],[16,-10],[22,-10],[22,0],[7,2]])]=7
  own[poly([[-9,-20],[7,-20],[12,-9],[8,-5],[-9,-4]])]=5
  own[poly([[8,-6],[12,-4],[16,-3],[20,-2],[20,9],[8,10],[5,-1]])]=8
 full=np.where(fourth,fourth,base).astype(np.uint8)
 paldiff=np.array([a.words[i]!=a.words[i+16]for i in range(16)])[full]
 diff=((full!=base)|((fourth>0)&paldiff))&(full>0)
 ls={0:base,**{pb:np.where(diff&(own==pb),full,0).astype(np.uint8)for pb in(5,6,7,8)}}
 for n2,dx in((n,0),(n+1,1)):
  for pb,z in ls.items():
   v=np.roll(z,dx,1);assert np.array_equal(v,png(T/f'layer{pb}_{n2:03}.png'));target[n2,pb]=v
   frame=next(q for q in meta['frames']if q['ref']==n2);assert sha(v.tobytes())==frame['layer_hashes'][str(pb)]
  assert np.array_equal(np.roll(own,dx,1),png(T/f'owner_{n2:03}.png'))
  bodies[n2]=(np.roll(base,dx,1),np.roll(fourth,dx,1))
 proof.append({'ref':n,'shoe_rows_exact':True,'same_row_leg_links':len(links),'source_pixels_only':True,
               'weapon':entry['weapon'],'ownership_reconstructed':True})

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
   assert len(qs)<=16
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
 for mask in(0,15):
  bb,ff=bodies[n];expected=color(b,bb)
  if mask:m=ff>0;expected[m]=color(b,ff,16)[m]
  assert np.array_equal(expected,np.asarray(b.composite(n,mask,1)[0]))
groups=[]
for s,t in((95,96),(98,99)):
 assert b.banks[0]['frames'][s]['offset']==b.banks[0]['frames'][t]['offset']
 for pb in PBS:assert np.array_equal(np.roll(b.layer(s,pb)[0],1,1),b.layer(t,pb)[0])
 groups.append({'refs':[s,t],'shared32_tile_stream':True,'all5_layers_x_plus1':True})
nativep=S/'special_components_native_checks.json';native=js(nativep);assert native['passed']
nr=native['resources']['PL00_U.ARC'];assert nr['candidate_sha256']==sha(new)
checks=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in checks if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']

O.mkdir(exist_ok=True);sheets=[]
for i,ns in enumerate(((95,96),(98,99))):
 cw,ch=392,476;im=Image.new('RGB',(4*cw,2*ch),'#263345');dr=ImageDraw.Draw(im)
 for row,n in enumerate(ns):
  for col,(ar,mask,title)in enumerate(((a,0,'old base'),(b,0,'new base'),(a,15,'old fourth'),(b,15,'new fourth'))):
   pic=ar.composite(n,mask,1)[0].crop((112,96,208,208)).resize((384,448),Image.Resampling.NEAREST);x,y=col*cw,row*ch;im.paste(pic,(x+4,y+22),pic);dr.text((x+4,y+4),f'{n} {title}',fill='white')
 p=O/f'full_readback_{i:02}.png';im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
for n in(95,98):
 cw,ch=320,410;im=Image.new('RGB',(5*cw,ch),'#263345');dr=ImageDraw.Draw(im)
 for col,(mask,title)in enumerate(((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))):
  pic=b.composite(n,mask,2)[0].crop((120,108,200,204)).resize((320,384),Image.Resampling.NEAREST);im.paste(pic,(col*cw,24),pic);dr.text((col*cw+4,4),f'{n} {title}',fill='white')
 p=O/f'partial_{n:03}.png';im.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes())})
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==504 and counts['partial_RGBA_exact']==128
for path,h in tracked.items():assert sha((ROOT/path).read_bytes())==h,path
report={'passed':True,'scope':'Nana 기본/포스95/96/98/99 원화4셀 독립 양자화→접점/동일행다리/소유→20층→실제ARC',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),
 'counts':dict(counts),'source_quantization':quant,'source_registration':proof,'shared_streams':groups,'nonselected_shared_compositions':shared,
 '95_lower_neck_row_y_minus14_body6_owned':True,'other_entries_palette_audio_bank_boundaries_exact':True,
 'native_MIPS_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'four_new_decoded_hashes_match':True,'executed_here':False},
 'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'runtime_verified':False}
report['limitations']=['대상128RGBA와비대상1120층/팔레트불변을검사했다.제작자7296전조합검사는반복하지않았다.','실기와원시간표브라우저재생은별도다.']
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'passed':True,'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
