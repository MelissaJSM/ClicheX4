"""Nana 기본/포스 저체력6. 제작/패킹 함수 미호출, 등록원화부터 독립 재구성."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
from scipy.ndimage import label
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame,decode_stream,indexed_atlas
L=D.parent/'root_nana_lowhp';T=L/'joint_layers03';P=L/'packed_lowhp01';O=D/'nana_base_lowhp6_independent01';O.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def read(p):
 v=p.read_bytes();h=sha(v)
 if p in tracked:assert tracked[p]==h,(str(p),'changed')
 tracked[p]=h;return v
def js(p):return json.loads(read(p))
def arr(p):
 read(p);v=np.array(Image.open(p));assert v.shape==(384,384)and v.dtype==np.uint8 and v.max()<16;return v
def sem(cp):return [(q['flags'],q['tile'],q['x'],q['y'])for q in cp['parts']]
def poly(points):
 im=Image.new('L',(384,384));ImageDraw.Draw(im).polygon([(x+160,y+160)for x,y in points],fill=1);return np.array(im)>0
meta=js(T/'manifest.json');pack=js(P/'report.json');reg=js(L/'registered01/manifest.json')
oldpath=ROOT/meta['parent_arc'];newpath=P/'PL00_U.ARC';old,new=read(oldpath),read(newpath)
assert sha(old)==meta['parent_sha256']=='509cc9785cb5eb3dca9f7a8a3fd1d3ea334887a98d3834b9f327266b3c6bbdce'
assert sha(new)=='ac1e35b7131d3909a93ea3466859aa9d7278c431d72defcb261b2b76cd1f6e16'
assert sha(read(T/'manifest.json'))==pack['targets_manifest_sha256']=='8d75f7848da0bba75face966fec5ac2315613cbbab39bfb9098670130c9b1b76'
assert sha(read(L/'art01/generated.png'))==reg['source_sha256']=='b10a077778b2ae3fb9b0390ac34eaf884bd5a12209c9413d96739f6ccb6627b8'
a,b=Archive(old),Archive(new);PBS=(0,5,6,7,8);refs=set(range(120,126));counts=collections.Counter();layers={}
assert set(meta['refs'])==refs==set(pack['refs'])
assert len(old)==len(new)and [{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(old)]==[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(new)]
outside=np.ones(len(old),bool)
for e in psx_arc(old):
 if e['type']in('0x2','0x3'):outside[e['offset']:e['offset']+e['size']]=False
assert np.array_equal(np.frombuffer(old,np.uint8)[outside],np.frombuffer(new,np.uint8)[outside])
assert a.p==b.p and bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
Y,X=np.indices((384,384));Y-=160;X-=160
body={};mouth={};sourceproof=[]
for form in('base','fourth'):
 z=arr(L/f'registered01/{form}_122_indices.png');v=arr(L/f'registered01/{form}_123_indices.png')
 for n,im in((122,z),(123,v)):
  q=next(q for q in reg['frames']if q['form']==form and q['ref']==n);assert sha(im.tobytes())==q['indices_sha256']
 assert z[150,156]==12 and v[150,156]in(1,6);mouth[form]=int(v[150,156])
 w=z.copy();w[178:184,:]=0;w[178:183,:]=z[179:184,:]
 assert np.nonzero(w)[0].max()==182
 body[form]=w;sourceproof.append({'form':form,'source_closed122':sha(z.tobytes()),'source_open123':sha(v.tobytes()),
  'new_shoe_source_rows':[179,184],'new_shoe_dest_rows':[178,183],'mouth_source_world':[-4,-10],'closed':12,'open':mouth[form]})
base=body['base'];fourth=body['fourth'];gun=(X>=-11)&(X<=-5)&(Y>=2)&(Y<=9);fourth[gun]=base[gun]
src=fourth.copy();region=(Y>=10)&(Y<=22)&(X>=-8)&(X<=13);links=[]
def runs(mask):
 xs=np.flatnonzero(mask);return np.split(xs,np.flatnonzero(np.diff(xs)>1)+1)if len(xs)else[]
for y in range(170,183):
 gaps=runs((base[y]>0)&(fourth[y]==0)&region[y]);intervals=runs((fourth[y]>0)&region[y]);groups={}
 for gap in gaps:
  assert intervals
  closest=min(intervals,key=lambda s:np.min(np.abs(s[:,None]-gap)))
  groups.setdefault((int(closest[0]),int(closest[-1])),[]).append(gap)
 for(left,right),group in groups.items():
  lo=min(left,*(int(q[0])for q in group));hi=max(right,*(int(q[-1])for q in group));xx=np.arange(lo,hi+1)
  assert max(left-lo,hi-right)<=2 and len(xx)<=max(3,2*(right-left+1))
  sx=np.arange(left,right+1)[np.rint(np.linspace(0,right-left,len(xx))).astype(int)]
  fourth[y,xx]=src[y,sx]
  links.extend({'dest':[int(x)-160,y-160],'source':[int(s)-160,y-160],'index':int(src[y,s])}for x,s in zip(xx,sx))
assert links==meta['leg_registration'] and not np.any((base>0)&(fourth==0)&region)
own=np.full(base.shape,6,np.uint8);own[(Y>=4)|((X>=5)&(Y>=-7))]=8
own[poly([[-10,-5],[-5,-7],[-3,0],[-4,6],[-8,10],[-11,10]])]=7
own[poly([[-4,-5],[8,-5],[11,0],[8,2],[-4,0]])]=7
own[(X>=-8)&(X<8)&(Y>=-22)&(Y<-6)]=5
veil=poly([[3,-18],[7,-18],[13,-12],[18,-7],[18,9],[8,9],[5,-4]]);own[veil]=8
def cycle(z,d):
 result=np.zeros_like(z)
 for y in range(48):
  step=d if y<35 else round(d*max(0,43-y)/8);s=y-step
  if 0<=s<48:result[y+135,136:184]=z[s+135,136:184]
 assert np.array_equal(result[178:183,136:184],z[178:183,136:184]);return result
read(ROOT/'scripts/prepare_shibuki_idle.py')
sources={};ownership=[]
for q in meta['frames']:
 n=q['ref'];d={120:1,121:1,122:0,123:0,124:-1,125:-1}[n];opened=n%2
 assert q['breathing_delta']==d and q['mouth_open']==bool(opened)
 bb,ff=base.copy(),fourth.copy()
 if opened:bb[150,156]=mouth['base'];ff[150,156]=mouth['fourth']
 bb,ff,owner=cycle(bb,d),cycle(ff,d),cycle(own,d)
 assert np.array_equal(owner,arr(T/f'owner_{n:03}.png'))
 full=np.where(ff,ff,bb).astype(np.uint8);palchange=(a.words[:16]!=a.words[16:32])[full]
 change=((full!=bb)|((ff>0)&palchange))&(full>0)
 expected={0:bb,**{pb:np.where(change&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 for pb in PBS:
  z=arr(T/f'layer{pb}_{n:03}.png');assert sha(z.tobytes())==q['layer_hashes'][str(pb)]and np.array_equal(z,expected[pb]),(n,pb,'source')
  layers[n,pb]=z;counts['registered_source_layers_reconstructed']+=1
 vm=cycle(veil.astype(np.uint8),d)>0;assert not np.any(change&vm&(owner!=8))
 ownership.append({'ref':n,'veil_overlay_texels_in_legs':int(np.count_nonzero(change&vm)),
  'veil_overlay_texels_in_other_equipment':0,'owner_changed_pixels':{str(pb):int(np.count_nonzero(change&(owner==pb)))for pb in PBS[1:]}})
 sources[n]=(bb,ff)
raws={};atlases={};changes=[];groups=[]
for gb,(ob,nb)in enumerate(zip(a.banks,b.banks)):
 assert(ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames']))
 if gb:assert a.g[ob['base']:ob['end']]==b.g[nb['base']:nb['end']];counts['other_graphics_banks_byte_exact']+=1
 for of,nf in zip(ob['frames'],nb['frames']):
  n=of['index'];assert n==nf['index']
  od=decode_stream(a.g,of['offset'],of['limit'],of['tile_count']*128);nd=decode_stream(b.g,nf['offset'],nf['limit'],nf['tile_count']*128)
  assert od.serialize()==a.g[od.start:od.end]and nd.serialize()==b.g[nd.start:nd.end]
  counts['raw_references_checked']+=1
  if gb or n not in refs:
   assert od.data==nd.data and of['tile_count']==nf['tile_count'];counts['non_target_raw_exact']+=1
  else:
   assert nf['tile_count']==32;raws[n]=nd.data;atlases[n]=np.frombuffer(indexed_atlas(nd.data,32)[0],np.uint8).reshape(32,256)
   assert not atlases[n][:,0].any();changes.append({'ref':n,'old_tiles':of['tile_count'],'new_tiles':32,'raw_sha256':sha(nd.data)})
for n in sorted(refs):
 oldowners=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']]
 newowners=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert oldowners==newowners==([n,n+1]if n%2==0 else[n-1,n])
 if n%2==0:groups.append(oldowners)
gpu=[]
for pb in range(len(bank_offsets(a.c))):
 assert composition_frame(a.c,pb,0)['bank_frame_count']==composition_frame(b.c,pb,0)['bank_frame_count']
 for n in range(composition_frame(a.c,pb,0)['bank_frame_count']):
  ca,cb=composition_frame(a.c,pb,n),composition_frame(b.c,pb,n)
  if pb not in PBS or n not in refs:assert sem(ca)==sem(cb),(pb,n,'non-target');counts['non_target_composition_frames_exact']+=1
  else:
   for p in cb['parts']:
    t=p['tile'];assert 0<=t<32;z=atlases[n][t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    u=int(np.count_nonzero(z[:,0]))if t%16==0 else 0;v=int(np.count_nonzero(z[0]))if p['flip_y']and t//16==0 else 0
    assert u==v==0,(pb,n,t,'GPU');gpu.append({'ref':n,'part_bank':pb,'tile':t,'flags':p['flags'],'u_edge_opaque':u,'v_edge_opaque':v});counts['target_GPU_parts_checked']+=1
def composite(ls,mask,arm):
 im=a.rgba(ls[0])
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:im.alpha_composite(a.rgba(ls[pb],32 if pb==7 and arm==2 else 16))
 return im
components=[];mouth_checks=[]
for n in range(237):
 if n in{105,*range(175,183)}:continue
 for pb in PBS:
  if n in refs:assert np.array_equal(b.layer(n,pb)[0],layers[n,pb]);counts['target_layers_exact']+=1
  else:assert np.array_equal(a.layer(n,pb)[0],b.layer(n,pb)[0]);counts['non_target_layers_exact']+=1
 if n not in refs:
  for mask in(0,15):assert a.composite(n,mask)[0].tobytes()==b.composite(n,mask)[0].tobytes();counts['non_target_full_displays_exact']+=1
  continue
 ls={pb:layers[n,pb]for pb in PBS}
 for mask in range(16):
  for arm in(1,2):
   im=b.composite(n,mask,arm)[0];assert im.tobytes()==composite(ls,mask,arm).tobytes();counts['target_partial_RGBA_exact']+=1
   count=label(np.asarray(im)[:,:,3]>0,np.ones((3,3),bool))[1];assert count==1,(n,mask,arm,count);components.append({'ref':n,'mask':mask,'arm':arm,'components8':int(count)})
 bb,ff=sources[n];expected=a.rgba(bb);expected.alpha_composite(a.rgba(ff,16));assert b.composite(n,15,1)[0].tobytes()==expected.tobytes()
 if n%2==0:
  for mask in(0,15):
   z=np.asarray(b.composite(n,mask)[0]);z2=np.asarray(b.composite(n+1,mask)[0]);m=np.any(z!=z2,axis=2);y,x=np.nonzero(m);assert len(x)==1
   assert(x[0]-160,y[0]-160)==(-4,-10+{120:1,122:0,124:-1}[n])
   mouth_checks.append({'pair':[n,n+1],'mask':mask,'only_changed_RGBA_pixel':[int(x[0])-160,int(y[0])-160]})
for mask in(0,15):
 feet=[np.asarray(b.composite(n,mask)[0])[178:183]for n in sorted(refs)];assert all(np.array_equal(feet[0],q)for q in feet[1:])
nativepath=L/'lowhp_components_native_checks.json';native=js(nativepath)
assert native['passed']and native['resources']['PL00_U.ARC']['candidate_sha256']==sha(new)
checks={q['frame']:q for bank in native['resources']['PL00_U.ARC']['banks']if bank['bank']==0 for q in bank['native_decoder_checks']}
for n in refs:assert checks[n]['decoded_sha256']==sha(raws[n])and checks[n]['tiles']==32
font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',13);boards=[]
def board(name,rows):
 cw,ch=264,302;im=Image.new('RGB',(len(rows[0][1])*cw,len(rows)*ch),'#26303c');dr=ImageDraw.Draw(im)
 for ri,(title,pics)in enumerate(rows):
  for ci,(text,pic)in enumerate(pics):
   x,y=ci*cw,ri*ch;dr.text((x+3,y+3),title+' '+text,font=font,fill='white');cut=pic.crop((128,120,192,188)).resize((256,272),Image.Resampling.NEAREST);im.paste(cut,(x,y+25),cut)
 p=O/(name+'.png');im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes()),'world_crop':[-32,-40,32,28],'scale':4})
for i,ns in enumerate(((120,121,122),(123,124,125))):
 board(f'full_readback_{i:02}',[(str(n),[('이전 기본',a.composite(n)[0]),('새 기본',b.composite(n)[0]),('이전 포스',a.composite(n,15)[0]),('새 포스',b.composite(n,15)[0])])for n in ns])
for i,ns in enumerate(((120,121),(122,123),(124,125))):
 board(f'partial_readback_{i:02}',[(str(n),[(text,b.composite(n,mask)[0])for text,mask in(('머리',1),('몸통',2),('팔',4),('다리',8),('몸통 다리',10))])for n in ns])
assert counts['raw_references_checked']==508 and counts['non_target_raw_exact']==502
assert counts['target_layers_exact']==30 and counts['non_target_layers_exact']==1110
assert counts['target_partial_RGBA_exact']==192 and counts['non_target_composition_frames_exact']==1757
for p,h in tracked.items():assert sha(p.read_bytes())==h,str(p)
proof={'passed':True,'scope':'등록4PNG→한점입/신발모듈/포스same-row다리·공통권총/베일legs소유/접지호흡→30층→실제패킹 독립읽기',
 'parent':rel(oldpath),'parent_sha256':sha(old),'candidate':rel(newpath),'candidate_sha256':sha(new),
 'counts':dict(counts),'registered_source_proof':sourceproof,'same_row_leg_registration_links':links,
 'veil_ownership':ownership,'mouth_checks':mouth_checks,'sole_5rows_RGBA_all6_exact':True,'shared_groups':groups,'raw_changes':changes,
 'preserved':{'ARC_length_directory':True,'graphics_and_parts_bank_boundaries':True,'other_graphics_banks_bytes':True,
 'other_entries_palette_audio':True,'non_target_composition_semantics':True,'new_GPU_opaque_edges':0},
 'native_read_only_binding':{'path':rel(nativepath),'sha256':sha(read(nativepath)),'target6_decoded_hashes_match':True,'executed_by_this_agent':False},
 'fresh_sheets':boards,'actually_viewed_in_this_script':False,'producer_functions_called':False,'runtime_verified':False,
 'limits':['생성원화 전체 재양자화는 포함하지 않았고 실제 해시고정 등록PNG부터 재구성했다.',
 '제작7296RGBA전수와 독립192대상조합을 구분한다.비대상1110층/팔레트/조립 보존으로 비대상표시를 보호했다.',
 '원MIPS는 부모가 실행한 결과를6raw에 해시결속했으며 여기서 재실행하지 않았다.',
 '원표동적호흡/실기/사용자수용은 별도다.생성39c7114e는 호출식별자 일부이고 실제원화SHA는b10a0777이다.'],
 'input_hashes':{rel(p):h for p,h in tracked.items()}}
(O/'report.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
(O/'gpu_parts.json').write_text(json.dumps(gpu,indent=2)+'\n',encoding='utf8')
(O/'partial_components.json').write_text(json.dumps(components,indent=2)+'\n',encoding='utf8')
print(json.dumps({'passed':True,'counts':dict(counts),'report':rel(O/'report.json'),'sha256':sha((O/'report.json').read_bytes())},ensure_ascii=False))
