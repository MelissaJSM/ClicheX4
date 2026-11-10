"""Nana Ultimate 88/89/97 독립 reader. 제작 함수 호출 및 자원 수정 없음."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color,polygons
N=D.parent/'nana_audit';U=N/'ultimate_standing_repaint';P=U/'packed_standing_candidate_v1';T=U/'targets_probe_v2';C=U/'common_probe_v3';O=D/'nana_ultimate_standing3_independent01'
PBS=(0,5,6,7,8);REFS={88,89,97};RESERVED={105,*range(175,183)}
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();tracked={}
def readb(p):
 v=p.read_bytes();tracked[rel(p)]=sha(v);return v
def readj(p):return json.loads(readb(p))
def png(p):readb(p);return np.asarray(Image.open(p))
oldp=N/'ultimate_ladder_repaint/packed_first7_diagnostic_v1/PL02_U.ARC';newp=P/'PL02_U.ARC';old,new=readb(oldp),readb(newp)
assert sha(old)=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
assert sha(new)=='0e69e9e3823c95bfce5b10746f77c587cd6f9e177cdd69b04938e868f3b77331'
a,b=Archive(old),Archive(new);lock=readj(P/'INPUT_FROZEN.json')
assert sha(readb(P/'INPUT_FROZEN.json'))=='874cfc761ec521ec06f9880b15aa78a8be73c15c1c67d7fdc65672ec0eb918c0'
assert lock['parent_sha256']==sha(old)and lock['candidate_sha256']==sha(new)
for q in lock['files']:assert sha(readb(ROOT/q['path']))==q['sha256'],q['path']
meta=readj(T/'manifest.json');assert set(meta['refs'])==REFS and meta['parent_arc_sha256']==sha(old)
assert sha(readb(T/'manifest.json'))==lock['target_manifest_sha256']
cm=readj(C/'manifest.json');assert cm['parent_arc_sha256']==sha(old)
source=U/'a_v1/generated.png';assert sha(readb(source))==cm['source_art_sha256'];im=Image.open(source).convert('RGBA');assert im.size==(1254,1254)
rgb=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words],np.float32);counts=collections.Counter()
def source_vote(cell,pal,world,excluded):
 ar=np.array(cell);available=np.array([i for i in range(1,16)if i not in excluded]);alpha=ar[:,:,3].astype(np.float32)/255;labels=np.empty(ar.shape[:2],np.uint8)
 for y in range(len(labels)):
  delta=ar[y,:,:3].astype(np.float32)[:,None,:]-pal[available][None,:,:]
  labels[y]=available[np.square(delta).sum(2).argmin(1)]
 x,y=world;x+=48;y+=48
 votes=[float(np.array(Image.fromarray(np.where(labels==v,alpha,0).astype(np.float32)).resize((96,96),Image.Resampling.BOX))[y,x])for v in available]
 return int(available[np.argmax(votes)])
body={};source_rows=[]
for rec in cm['frames']:
 n=rec['ref'];col=0 if n==89 else 1;corrected={}
 for row,form in enumerate(('before','after')):
  z=png(U/f'first_registered_v1/{form}_{n:03}_indices.png').copy();eye=next(q for q in rec['eye_registration']if q['form']==form);x,y=eye['world']
  assert z[y+160,x+160]==z[y+161,x+160]==14
  cell=im.crop((col*627,row*627,(col+1)*627,(row+1)*627));pal=rgb[16:32]if form=='before'else rgb[:16]
  val=source_vote(cell,pal,(x,y),{14,15});assert val==eye['source_vote']and val in(1,2)
  z[y+160,x+160]=val;corrected[form]=z;counts['iris_source_sample_rebuilt']+=1
 bef=corrected['before'];donor=corrected['after'];common=bef.copy();cell=im.crop((col*627,0,(col+1)*627,627))
 assert sorted(tuple(q['world'])for q in rec['palette15_face_semantic'])==sorted((int(x-160),int(y-160))for y,x in np.argwhere(bef==15))
 for q in rec['palette15_face_semantic']:
  x,y=q['world'];assert bef[y+160,x+160]==15
  val=source_vote(cell,rgb[:16],(x,y),{15});assert val==q['after_index'];common[y+160,x+160]=val;counts['palette15_source_sample_rebuilt']+=1
 mask=polygons([rec['costume_polygon']])
 for q in rec['source_boundary_links']:
  x,y=q['world'];assert bef[y+160,x+160]==q['before_index']and donor[y+160,x+160]==q['source_after_index'];mask[y+160,x+160]=True;counts['cuff_boundary_source_cells']+=1
 aft=common.copy();aft[mask]=donor[mask];hands=polygons([rec['shared_hand_polygon']]);aft[hands]=common[hands]
 for name,z in [('before',bef),('after',aft),('donor',donor),('costume_mask',mask.astype(np.uint8)*255),('outside',((aft>0)&(bef==0)).astype(np.uint8)*255)]:assert np.array_equal(z,png(C/f'{name}_{n:03}_indices.png'))
 assert np.array_equal(hands,png(C/f'shared_hand_mask_{n:03}.png')>0)
 assert not np.any((aft>0)&(bef==0))and label(bef>0,np.ones((3,3)))[1]==label(aft>0,np.ones((3,3)))[1]==1
 body['before',n],body['after',n]=bef,aft
 source_rows.append({'ref':n,'shared_hand_and_diagonal_gun_window_exact':True,'source_only_cuff_boundary_cells':len(rec['source_boundary_links']),'iris_lower_cell_preserved':True,'wholebody_translation':[0,0]})
fxmeta=meta['original_effect_source'];fxpath=ROOT/fxmeta['npy'];assert sha(readb(fxpath))==fxmeta['npy_sha256']
audit=readj(ROOT/fxmeta['report']);assert sha(readb(ROOT/fxmeta['report']))==fxmeta['report_sha256']=='6c5ebd4f5b8af48b4185fe9bf27e0881651b39f91afe3c296b88001a96ec0007'
fx=np.load(fxpath);assert fx.shape==(384,384)and fx.dtype==np.uint8 and np.count_nonzero(fx)==83 and set(np.unique(fx))=={0,12}
original=next(q for q in audit['relations']if q['archive']=='original_US'and q['source']==89 and q['target']==88)
assert original['layers']['0']['parts_target'][6:8]==[[0,7,-19,-26],[0,8,-3,-26]]and original['layers']['0']['parts_target'][8]==[0,4,-26,7]
assert not fx[167:183,134:150].any();fm=fx>0
for form in('before','after'):
 z=body[form,89];assert not z[:,0].any();v=np.zeros_like(z);v[:,:-1]=z[:,1:];v[fm]=fx[fm];body[form,88]=v
target={}
for n in sorted(REFS):
 bef,aft=body['before',n],body['after',n]
 assert np.array_equal(bef,png(T/f'before_{n:03}_indices.png'))and np.array_equal(aft,png(T/f'after_{n:03}_indices.png'))
 target[n,0]=aft;target[n,5]=np.where(np.all(color(a,bef,16)==color(a,aft),axis=2),0,bef).astype(np.uint8)
 for pb in(6,7,8):target[n,pb]=np.zeros_like(aft)
 for pb in PBS:assert np.array_equal(target[n,pb],png(T/f'layer{pb}_{n:03}.png'))and sha(target[n,pb].tobytes())==meta['targets'][str(n)][str(pb)]
assert len(old)==len(new)and a.p==b.p
ae,be=psx_arc(old),psx_arc(new);assert [(q['type'],q['offset'],q['size'])for q in ae]==[(q['type'],q['offset'],q['size'])for q in be]
allow=np.zeros(len(old),bool)
for q in ae:
 if int(q['type'],16)in(2,3):allow[q['offset']:q['offset']+q['size']]=True
assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ab,bb)in enumerate(zip(a.banks,b.banks)):
 assert (ab['base'],ab['end'],len(ab['frames']))==(bb['base'],bb['end'],len(bb['frames']))
 if gb:assert a.g[ab['base']:ab['end']]==b.g[bb['base']:bb['end']];counts['other_graphics_banks_byte_exact']+=1
 for f,g in zip(ab['frames'],bb['frames']):
  n=f['index'];assert n==g['index'];counts['raw_checked']+=1
  if gb==0 and n in REFS:assert g['tile_count']==32
  else:assert raw(a,gb,n)==raw(b,gb,n)and f['tile_count']==g['tile_count'];counts['non_target_raw_exact']+=1
assert b.banks[0]['frames'][88]['offset']==b.banks[0]['frames'][89]['offset']!=b.banks[0]['frames'][97]['offset']
reserved=[]
for n in range(237):
 for pb in PBS:
  if n in RESERVED:
   try:b.layer(n,pb)
   except(ValueError,IndexError)as ex:
    try:a.layer(n,pb)
    except(ValueError,IndexError)as ex2:assert type(ex)==type(ex2)and str(ex)==str(ex2)
    else:raise AssertionError('new invalid layer')
    reserved.append({'ref':n,'layer':pb,'state':'same_render_exception'});continue
   assert np.array_equal(b.layer(n,pb)[0],a.layer(n,pb)[0]);counts['reserved_layers_renderable_exact']+=1;reserved.append({'ref':n,'layer':pb,'state':'rendered_exact'});continue
  want=target[n,pb]if n in REFS else a.layer(n,pb)[0]
  assert np.array_equal(b.layer(n,pb)[0],want),(n,pb);counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
shared=[]
for pb in range(len(bank_offsets(a.c))):
 oldparts={n:parts(a,pb,n)for n in range(composition_frame(a.c,pb,0)['bank_frame_count'])}
 addr={q['record_offset']for n in REFS if n in oldparts and pb in PBS for q in oldparts[n]}
 for n,op in oldparts.items():
  bp=parts(b,pb,n)
  if pb in PBS and n in REFS:
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
   actual=np.asarray(b.composite(n,mask,arm)[0]);assert np.array_equal(expected,actual);counts['partial_RGBA_exact']+=1
   if n==88:
    assert np.array_equal(actual[fm],color(a,fx,16 if mask&1 else 0)[fm]);counts['original_effect_RGBA_83texels_exact']+=1
 for form,mask,pal in(('before',15,16),('after',0,0)):assert np.array_equal(color(b,body[form,n],pal),np.asarray(b.composite(n,mask)[0]))
O.mkdir(exist_ok=True);sheets=[]
for form in('before','after'):
 mask=15 if form=='before'else 0;box=(125,126,189,187);w,h=box[2]-box[0],box[3]-box[1];cw,ch=w*5+10,h*5+26;board=Image.new('RGB',(cw*3,ch*3),'#263345');dr=ImageDraw.Draw(board)
 for row,n in enumerate(sorted(REFS)):
  for col,(caption,im)in enumerate((('old',a.composite(n,mask)[0]),('new',b.composite(n,mask)[0]),('idle',b.composite(0,mask)[0]))):
   bb=im.getbbox();assert box[0]<=bb[0]and box[1]<=bb[1]and box[2]>=bb[2]and box[3]>=bb[3]
   x,y=col*cw,row*ch;dr.text((x+4,y+4),f'{n} {form} {caption}',fill='white');v=im.crop(box).resize((w*5,h*5),Image.Resampling.NEAREST);board.paste(v,(x+4,y+22),v)
 p=O/f'{form}_readback.png';board.save(p);sheets.append({'path':rel(p),'sha256':sha(p.read_bytes()),'no_clipping':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==509 and counts['target_layers_exact']==15 and counts['non_target_layers_exact']==1125 and counts['partial_RGBA_exact']==96 and len(reserved)==45
for p,hsh in tracked.items():assert sha((ROOT/p).read_bytes())==hsh,p
report={'passed':True,'scope':'Nana Ultimate 88/89/97 등록→홍채·의상·공통손→15층 및 원83texel 효과 독립 읽기 검사','candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'input_frozen_sha256':sha((P/'INPUT_FROZEN.json').read_bytes()),'locked_inputs':len(lock['files']),'counts':dict(counts),'source_reconstruction':source_rows,'effect':{'source_report_sha256':fxmeta['report_sha256'],'source_npy_sha256':fxmeta['npy_sha256'],'world_texels':83,'indices':[12],'original_tile_storage_preserved_claim':False,'original_world_shape_color_position_exact':True,'body_policy':'88 = 새89 X−1,Y불변. 효과83셀 이외는 새몸 그대로이며 옛 after의 효과밖105셀은 복사하지 않음.'},'shared_stream88_89_and_independent97':True,'old_shared_non_target_compositions':shared,'other_entries_audio_palette_bank_boundaries_exact':True,'part_counts':{str(n):{str(pb):len(parts(b,pb,n))for pb in PBS}for n in sorted(REFS)},'reserved45_layers_preserved':reserved,'readback_sheets':sheets,'readback_actually_viewed':False,'inputs':tracked,'producer_functions_called':False,'native_MIPS_executed_here':False,'runtime_verified':False,'user_accepted':False,'limitations':['최초 생성4셀의 전체 재양자화는 제작자 별도 근거로 둔다. 고정등록 이후 홍채/팔레트15/커프의 실제 생성원화 표본과 의상·공통손은 직접 재계산했다.','원83효과는 앞선 독립 원US 추출의 해시 고정 numpy와 원파트 기록을 재사용했다. 이번에 원BIN 전체 추출을 반복하지 않았다.','96부분RGBA와 비대상1125층/팔레트 불변 검사이며 전체7296RGBA 재실행은 아니다.','원MIPS·원표·게임 실기·사용자 수용은 별도다.']}
(O/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'report_sha256':sha((O/'report.json').read_bytes())}))
