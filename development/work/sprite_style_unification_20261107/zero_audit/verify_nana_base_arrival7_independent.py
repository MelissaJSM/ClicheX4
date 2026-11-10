"""Nana base/Fourth 등장7 독립 원화·효과·부분층 reader. 제작 함수 미호출."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;B=D.parent;S=B/'root_nana_arrival';T=S/'joint_targets01';P=S/'packed_arrival01';O=D/'nana_base_arrival7_independent01';O.mkdir(exist_ok=True)
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.c01_audio_build import read_disc
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons,render
PBS=(0,5,6,7,8);REFS={130,131,133,134,135,136,137};BODIES=(133,135,136,137);RESERVED={105,*range(175,183)}
tracked={};sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def blob(p):
 v=p.read_bytes();h=sha(v);r=rel(p)
 if r in tracked:assert tracked[r]==h,(r,'changed during read')
 tracked[r]=h;return v
def js(p):return json.loads(blob(p))
def png(p):blob(p);return np.array(Image.open(p))
def poly(p):return polygons([p])
def overlay(bg,fg):return np.where(fg>0,fg,bg).astype(np.uint8)
oldp=B/'root_nana_recoil/packed_recoil03/PL00_U.ARC';newp=P/'PL00_U.ARC';old,new=blob(oldp),blob(newp)
assert sha(old)=='ef69d0a13ad11ede874f2642bd9df719cbb2d864798801867b6738f728df6df4'
assert sha(new)=='9599ca5fc21828df5ef4d865eafab4d27aa06a7b2391873a063c887120e70f91'
a,b=Archive(old),Archive(new);meta=js(T/'manifest.json');bm=js(S/'body_targets02/manifest.json')
assert meta['parent_sha256']==bm['parent_sha256']==sha(old)and set(meta['refs'])==REFS
assert sha((S/'body_targets02/manifest.json').read_bytes())==meta['source_body_manifest_sha256']
registered={};quant=[]
for page in ('a','b'):
 regp=S/f'registered_{page}01';reg=js(regp/'manifest.json');imeta=js(S/f'inputs_{page}01/manifest.json')
 art=S/f'art_{page}01/generated.png';assert sha(blob(art))==reg['source_sha256'];image=Image.open(art).convert('RGBA');assert list(image.size)==reg['source_size']
 src=Archive(blob(ROOT/imeta['parent_arc']));assert sha(src.data)==reg['parent_sha256']and src.p==a.p
 for q in reg['frames']:
  form,n=q['form'],q['ref'];palstart=16 if form=='fourth'else 0
  for pb in PBS:assert np.array_equal(src.layer(n,pb)[0],a.layer(n,pb)[0])
  pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[palstart:palstart+16]],np.float32)
  rgba=np.array(image.crop(q['source_crop']));rgb=rgba[:,:,:3].astype(np.float32);alpha=rgba[:,:,3].astype(np.float32)/255;ix=np.empty(alpha.shape,np.uint8)
  for y in range(len(ix)):ix[y]=1+np.square(rgb[y,:,None,:]-pal[None,1:,:]).sum(2).argmin(1)
  green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(rgba[:,:,3]>=128);green[len(green)//2:]=False;ix[green]=14
  weights=np.stack([np.asarray(Image.fromarray(np.where(ix==i,alpha,0).astype(np.float32),'F').resize((96,96),Image.Resampling.BOX))for i in range(1,16)])
  coverage=np.asarray(Image.fromarray(alpha,'F').resize((96,96),Image.Resampling.BOX));small=1+weights.argmax(0).astype(np.uint8);small[coverage<.5]=0
  eyes=weights[13].copy();eyes[coverage<.5]=0;eyes[48:]=0
  if eyes.max()>.015:small[np.unravel_index(eyes.argmax(),eyes.shape)]=14
  z=np.zeros((384,384),np.uint8);z[112:208,112:208]=small
  assert sha(z.tobytes())==q['indices_sha256']and np.array_equal(z,png(regp/f'{form}_{n:03}_indices.png'))
  assert sha(color(a,z,palstart).tobytes())==q['rgba_sha256'];registered[form,n]=z
  quant.append({'ref':n,'form':form,'source':rel(art),'crop':q['source_crop'],'fixed96_exact':True})
Y,X=np.indices((384,384));Y-=160;X-=160;target={};bodyproof=[]
for n in BODIES:
 q=next(q for q in bm['frames']if q['ref']==n);base=registered['base',n].copy();fourth=registered['fourth',n].copy();grip=poly(q['shared_grip_polygon']);fourth[grip]=base[grip]
 face=poly([[-7,-19],[-4,-19],[-1,-15],[-1,-10],[-6,-10],[-7,-14]])if n==137 else np.zeros(base.shape,bool);fourth[face]=base[face]
 source=fourth.copy()
 for lk in q['same_row_new_leg_registration']:
  x,y=lk['dst'];sx,sy=lk['src'];assert y==sy and 5<=y<=22 and source[sy+160,sx+160]==lk['index'];fourth[y+160,x+160]=lk['index']
 inherited=[[int(x-160),int(y-160),int(base[y,x])]for y,x in np.argwhere((base>0)&(fourth==0))];assert inherited==q['new_base_shared_outer_pixels']
 owner=np.full(base.shape,6,np.uint8)
 if n==133:
  owner[Y>=8]=8;owner[(X>=4)&(Y>=0)]=8;owner[(X>=-8)&(X<=5)&(Y<=1)]=5;owner[(X>=5)&(Y<=2)]=5;owner[poly([[2,0],[9,0],[12,11],[5,11],[2,7]])]=7
 else:
  owner[(Y>=5)|((X>=7)&(Y>=-11))]=8;owner[(X>=-9)&(X<=8)&(Y<=-7)]=5;owner[(X>=8)&(Y<=-10)]=5;owner[poly([[1,-9],[9,-6],[11,4],[6,7],[2,2]])]=7;owner[(X>=7)&(Y<=4)]=5
 owner[grip]=7;owner[face]=5
 assert np.array_equal(owner,png(S/'body_targets02'/f'owner_{n:03}.png'))and np.array_equal(fourth,png(S/'body_targets02'/f'fourth_body_{n:03}.png'))
 full=np.where(fourth,fourth,base).astype(np.uint8);diff=((full!=base)|(np.array([a.words[i]!=a.words[16+i]for i in range(16)])[full]&(fourth>0)))&(full>0)
 ls={0:base,**{pb:np.where(diff&(owner==pb),full,0).astype(np.uint8)for pb in PBS[1:]}}
 for pb,v in ls.items():assert np.array_equal(v,png(S/'body_targets02'/f'layer{pb}_{n:03}.png'))and sha(v.tobytes())==q['layer_hashes'][str(pb)];target[n,pb]=v.copy()
 bodyproof.append({'ref':n,'same_row_source_links':len(q['same_row_new_leg_registration']),'base_inherited_boundary':inherited,'new_grip_shared':True,'owner_reconstructed':True,'rear_veil_owner5':n!=133})
rules={q['ref']:q for q in meta['rules']};fxproof=[]
for n in(136,137):
 ps=[q for q in parts(a,0,n)if q['tile']==7];fx=render(a,n,0,ps);assert np.count_nonzero(fx)==46 and sha(fx.tobytes())==rules[n]['effect_sha256']
 assert[sig(q)for q in ps]==[sig(q)for q in rules[n]['source_parts']]
 target[n,0]=overlay(target[n,0],fx)
 for pb in PBS[1:]:target[n,pb][fx>0]=0
 assert a.words[13]==a.words[29]==a.words[45];fxproof.append({'ref':n,'source_effect_tile7_sha256':sha(tile(a,n,7).tobytes()),'46pixels_exact':True,'top_layer_no_armor_occlusion':True,'source_records':[sig(q)for q in ps]})
orb=a.layer(129)[0];assert np.array_equal(overlay(orb,a.layer(133)[0]),a.layer(134)[0])
assert sha(orb.tobytes())==rules[134]['effect_sha256']
for pb in PBS:target[134,pb]=overlay(orb,target[133,pb])if pb==0 else target[133,pb].copy()
fx131=render(a,131,0,parts(a,0,131)[:16]);assert np.array_equal(fx131,a.layer(132)[0])and sha(fx131.tobytes())==rules[131]['effect_sha256']
assert np.array_equal(np.where(a.layer(133)[0]>0,13,fx131),a.layer(131)[0]);target[131,0]=np.where(target[133,0]>0,13,fx131).astype(np.uint8)
assets,_=read_disc(ROOT/'MegaMan X4.bin',('PL00_U.ARC',));us=Archive(assets['PL00_U.ARC']);assert sha(us.data)==rules[130]['original_arc_sha256']
mapping=np.array([0,5,1,10,12,9,7,5,13,9,6,1,8,7,6,5],np.uint8);assert mapping.tolist()==rules[130]['color_map']
bg=mapping[us.layer(129)[0]%16];shell=mapping[us.layer(130)[0]%16];hist=np.zeros((384,384),np.uint8);hist[80:240,80:240]=png(ROOT/'work/ver_rin_nana/nana_art/arrival_v1/production02/frame_133.png')
old130=overlay(bg,np.where(hist>0,13,0).astype(np.uint8));target[130,0]=overlay(bg,np.where(target[133,0]>0,13,0).astype(np.uint8))
tc=collections.Counter(q['tile']for q in parts(us,0,130));rects=[]
for q in parts(us,0,130):
 if tc[q['tile']]>1:
  x,y=q['x']+160,q['y']+160;old130[y:y+16,x:x+16]=shell[y:y+16,x:x+16];target[130,0][y:y+16,x:x+16]=shell[y:y+16,x:x+16];rects.append([x-160,y-160,x-144,y-144])
assert np.array_equal(old130,a.layer(130)[0])and rects==rules[130]['shell_rectangles']
for n in(130,131):
 for pb in PBS[1:]:target[n,pb]=np.zeros((384,384),np.uint8)
for q in meta['frames']:
 n=q['ref']
 for pb in PBS:assert np.array_equal(target[n,pb],png(T/f'layer{pb}_{n:03}.png'))and sha(target[n,pb].tobytes())==q['layer_hashes'][str(pb)]
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
  assert np.array_equal(b.layer(n,pb)[0],target[n,pb]if n in REFS else a.layer(n,pb)[0]);counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 length=composition_frame(a.c,pb,0)['bank_frame_count'];assert length==composition_frame(b.c,pb,0)['bank_frame_count']
 slots={q['record_offset']for n in REFS if n<length and pb in PBS for q in parts(a,pb,n)}
 for n in range(length):
  op,np_=parts(a,pb,n),parts(b,pb,n)
  if pb not in PBS or n not in REFS:
   assert[sig(q)for q in op]==[sig(q)for q in np_];counts['non_target_compositions_exact']+=1
   hit=slots&{q['record_offset']for q in op}
   if hit:shared.append({'bank':pb,'ref':n,'parent_shared_record_offsets':sorted(hit),'all_records_exact':True})
  else:
   for q in np_:
    t=q['tile']+q['page']*256;assert 0<=t<32 and not q['unknown_flags'];v=tile(b,n,t)
    assert not(t%16==0 and v[:,0].any())and not(q['flip_y']and t//16==0 and v[0].any());counts['GPU_parts_checked']+=1
for n in REFS:
 for mask in range(16):
  for arm in(1,2):
   expected=color(b,target[n,0])
   for bit,pb in((8,8),(1,5),(4,7),(2,6)):
    if mask&bit:
     z=color(b,target[n,pb],32 if pb==7 and arm==2 else 16);m=z[:,:,3]>0;expected[m]=z[m]
   assert np.array_equal(expected,np.asarray(b.composite(n,mask,arm)[0]));counts['partial_RGBA_exact']+=1
assert a.banks[0]['frames'][131]['offset']==a.banks[0]['frames'][132]['offset']and b.banks[0]['frames'][131]['offset']!=b.banks[0]['frames'][132]['offset']
for n in(132,146,51):
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:assert[sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(b,pb,n)]
for n in(135,136,137):
 assert len(parts(b,5,n))==3 and sig(parts(b,5,n)[0])==sig(parts(a,5,146)[-1])
 assert[sig(q)for q in parts(b,5,n)]==[sig(q)for q in parts(b,5,135)]
for n in(133,134):assert[sig(q)for q in parts(b,5,n)]==[sig(q)for q in parts(a,5,51)]
boards=[]
def board(ns,partial=False):
 panels=[(b,m,l)for m,l in((1,'head'),(2,'body'),(4,'arms'),(8,'legs'),(10,'body+legs'))]if partial else[(a,0,'old base'),(b,0,'new base'),(a,15,'old Fourth'),(b,15,'new Fourth')]
 pics=[ar.composite(n,m)[0]for n in ns for ar,m,l in panels];bb=[q.getbbox()for q in pics];box=(min(q[0]for q in bb)-4,min(q[1]for q in bb)-4,max(q[2]for q in bb)+4,max(q[3]for q in bb)+4);scale=3 if min(ns)<132 else 4
 cw=(box[2]-box[0])*scale+8;ch=(box[3]-box[1])*scale+26;im=Image.new('RGB',(cw*len(panels),ch*len(ns)),'#263345');dr=ImageDraw.Draw(im)
 for row,n in enumerate(ns):
  for col,(ar,m,title)in enumerate(panels):
   p=ar.composite(n,m)[0].crop(box).resize(((box[2]-box[0])*scale,(box[3]-box[1])*scale),Image.Resampling.NEAREST);im.paste(p,(col*cw+4,row*ch+23),p);dr.text((col*cw+4,row*ch+3),f'{n} {title}',fill='white')
 p=O/f'{"partial"if partial else"readback"}_{ns[0]}.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':box,'no_opaque_pixels_clipped':True})
for ns in((130,131),(133,134),(135,136),(137,)):board(ns)
for ns in((133,135),(136,137)):board(ns,True)
assert counts['raw_checked']==508 and counts['non_target_raw_exact']==501 and counts['target_layers_exact']==35 and counts['non_target_layers_exact']==1105 and counts['non_target_compositions_exact']==1752 and counts['partial_RGBA_exact']==224
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
r={'passed':True,'scope':'새원화8셀 면적투표→손/얼굴공통·동일행다리·부분소유→역사효과와35층→실제ARC 독립읽기','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'source_cells':quant,'body_reconstruction':bodyproof,'effect_proof':fxproof,'historical130_parent_exact':True,'130_shell_windows':rects,'131_parent_rule_exact_and_132_preserved':True,'134_parent_orb_rule_exact':True,'counts':dict(counts),'shared_non_target_record_owners':shared,
 'head_records':{'135_136_137_first_record_equals_parent146_tail':True,'three_record_sequences_equal':True,'133_134_records_equal_parent51':True,'all_new_head_pixels_exact_to_new_art_layers':True,'51_146_raw_all_layers_records_preserved':True,'reused_old_head_art':False},
 'preserved':['전체ARC길이/외부항목/은행경계','비대상501raw와1105층/1752조립','팔레트·음향·다른13그래픽은행bytes','132순수효과raw/조립/표시','146/51기존머리그림'],
 'readback_sheets':boards,'readback_actually_viewed':False,'tracked_inputs':tracked,'producer_functions_called':False,'native_MIPS_run_here':False,'runtime_verified':False,'all_arrival_completed':False,
 'limits':['224대상RGBA와비대상1105층/팔레트를대조했으며제작자7296전수RGBA검사를반복하지않았다.','제작중native/원표/재현및루트최종열람은별도결속필요.','인접138139/140141142와사격권총기능은이후보신규대상이아니다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts)}))
