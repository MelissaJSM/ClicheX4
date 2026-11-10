"""나나 Ultimate 허용 사다리7의 등록→35층→ARC 독립 읽기. 제작함수 미호출."""
from pathlib import Path
import collections,hashlib,json,sys
import numpy as np
from PIL import Image,ImageDraw
from scipy.ndimage import label
ROOT=Path(__file__).resolve().parents[3];D=Path(__file__).parent;N=D.parent/'nana_audit';U=N/'ultimate_ladder_repaint'
sys.path[:0]=[str(ROOT),str(D)]
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,composition_frame,decode_stream
from verify_shibuki_ultimate_hurt13_independent import raw,parts,sig,tile,color
P=U/'packed_first7_diagnostic_v1';T=U/'first7_targets_v1';O=D/'nana_ultimate_ladder_first7_independent01';O.mkdir(exist_ok=True)
REFS={143,144,145,146,147,154,183};HELD={148,149,150,151,152,153,155};PBS=(0,5,6,7,8);RESERVED={105,*range(175,183)}
tracked={};sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()
def load(p):
 b=p.read_bytes();h=sha(b);r=rel(p)
 if r in tracked:assert tracked[r]==h
 tracked[r]=h;return b
def js(p):return json.loads(load(p))
def arr(p):
 load(p);z=np.array(Image.open(p));assert z.shape==(384,384)and z.dtype==np.uint8;return z
def mirror(z,k):
 y,x=np.nonzero(z);v=np.zeros_like(z);v[y,320-x+k]=z[y,x];return v
oldp=N/'ultimate_return_repaint/packed_return_candidate_v1/PL02_U.ARC';newp=P/'PL02_U.ARC'
old,new=load(oldp),load(newp)
assert sha(old)=='493bf2706aae33b64c4ffe70be1576a7ed63b0a4f62c54e89ca5876131392e29'
assert sha(new)=='dcaf1343747fabeab3054c59fc384c3bbd598209eccb6c5a37ac84c1d340d339'
lockp=P/'INPUT_FROZEN.json';lock=js(lockp)
assert lock['candidate_sha256']==sha(new)and lock['parent_sha256']==sha(old)
for q in lock['files']:assert sha(load(ROOT/q['path']))==q['sha256'],q['path']
meta=js(T/'manifest.json');assert sha(load(T/'manifest.json'))==lock['target_manifest_sha256']
assert set(meta['refs'])==REFS and set(meta['remaining_unmodified_refs'])==HELD
a,b=Archive(old),Archive(new);counts=collections.Counter();targets={};full={};source=[]
# 등록된 전후 원화에서 공통층을 독립 재계산한다. 생성13셀의 재양자화는 제작자 별도근거다.
for n in (143,144,146,154,183):
 src=U/('a_grip_probe_v1' if n in(143,144,146)else'c_common_probe_v2')
 bef=arr(src/f'before_{n:03}_indices.png');aft=arr(src/f'after_{n:03}_indices.png').copy();prior=aft.copy()
 rec=next(q for q in meta['frames']if q['ref']==n)
 assert sha(load(ROOT/rec['source_manifest']))==rec['source_manifest_sha256']
 for x0,y0,x1,y1 in rec['shared_new_hand_boxes']:
  w=(slice(y0+160,y1+160),slice(x0+160,x1+160));assert not np.isin(bef[w],(5,6,7,8,9,15)).any();aft[w]=bef[w]
 changed=[{'world':[int(x-160),int(y-160)],'previous':int(prior[y,x]),'new_source_index':int(bef[y,x])}for y,x in np.argwhere(aft!=prior)]
 assert changed==rec['shared_new_hand_links']
 assert not np.any((aft>0)&(bef==0))
 assert label(bef>0,np.ones((3,3)))[1]==label(aft>0,np.ones((3,3)))[1]==1
 for form,z in [('before',bef),('after',aft)]:full[form,n]=z
 targets[n,0]=aft;targets[n,5]=np.where((bef!=aft)|(bef==15),bef,0).astype(np.uint8)
 for pb in(6,7,8):targets[n,pb]=np.zeros_like(bef)
 source.append({'ref':n,'source_folder':rel(src),'common_hand_actual_changes':changed,'before_after_single_component':True,'outside_jacket_alpha':0})
for s,t,k in ((144,145,-1),(146,147,0)):
 for pb in PBS:targets[t,pb]=mirror(targets[s,pb],k)
 for form in('before','after'):full[form,t]=mirror(full[form,s],k)
for n in REFS:
 for pb in PBS:
  v=arr(T/f'layer{pb}_{n:03}.png');assert np.array_equal(v,targets[n,pb]);assert sha(v.tobytes())==meta['targets'][str(n)][str(pb)]
  counts['registered_target_layers_reconstructed']+=1
 for form in('before','after'):assert np.array_equal(arr(T/f'{form}_{n:03}_indices.png'),full[form,n])
assert len(old)==len(new)
assert [{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(old)]==[{k:v for k,v in e.items()if k!='sha256'}for e in psx_arc(new)]
keep=np.ones(len(old),bool)
for e in psx_arc(old):
 if e['type']in('0x2','0x3'):keep[e['offset']:e['offset']+e['size']]=False
assert np.array_equal(np.frombuffer(old,np.uint8)[keep],np.frombuffer(new,np.uint8)[keep]);assert a.p==b.p
assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(b.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(b.c)
for gb,(ob,nb) in enumerate(zip(a.banks,b.banks)):
 assert (ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames']))
 if gb:assert a.g[ob['base']:ob['end']]==b.g[nb['base']:nb['end']]
 for x,y in zip(ob['frames'],nb['frames']):
  n=x['index'];assert n==y['index'];rx=decode_stream(a.g,x['offset'],x['limit'],x['tile_count']*128);ry=decode_stream(b.g,y['offset'],y['limit'],y['tile_count']*128)
  assert rx.serialize()==a.g[rx.start:rx.end]and ry.serialize()==b.g[ry.start:ry.end]
  counts['raw_checked']+=1
  if gb or n not in REFS:
   assert rx.data==ry.data and x['tile_count']==y['tile_count'];counts['non_target_raw_exact']+=1
  else:assert y['tile_count']==32
groups=[]
for n in sorted(REFS):
 oo=[q['index']for q in a.banks[0]['frames']if q['offset']==a.banks[0]['frames'][n]['offset']]
 nn=[q['index']for q in b.banks[0]['frames']if q['offset']==b.banks[0]['frames'][n]['offset']]
 assert oo==nn and set(nn)<=REFS
 if n==min(nn):groups.append({'refs':nn,'parent_tiles':a.banks[0]['frames'][n]['tile_count'],'new_tiles':32,'new_raw_sha256':sha(raw(b,0,n))})
shared=[]
for pb in range(len(bank_offsets(a.c))):
 length=composition_frame(a.c,pb,0)['bank_frame_count'];assert length==composition_frame(b.c,pb,0)['bank_frame_count']
 selectedslots={q['record_offset']for n in REFS if n<length and pb in PBS for q in parts(a,pb,n)}
 for n in range(length):
  op,np_=parts(a,pb,n),parts(b,pb,n)
  if pb not in PBS or n not in REFS:
   assert [sig(q)for q in op]==[sig(q)for q in np_],(pb,n);counts['non_target_compositions_exact']+=1
   sharedslots=selectedslots&{q['record_offset']for q in op}
   if sharedslots:shared.append({'bank':pb,'ref':n,'parent_shared_record_offsets':sorted(sharedslots),'all_semantics_exact':True})
  else:
   for q in np_:
    t=q['tile']+q['page']*256;assert 0<=t<32 and q['unknown_flags']==0;v=tile(b,n,t)
    assert not(t%16==0 and v[:,0].any())and not(q['flip_y']and t//16==0 and v[0].any())
    if pb in(6,7,8):assert not v.any()
    counts['GPU_parts_checked']+=1
for n in range(237):
 if n in RESERVED:continue
 for pb in PBS:
  want=targets[n,pb]if n in REFS else a.layer(n,pb)[0];assert np.array_equal(b.layer(n,pb)[0],want),(n,pb)
  counts['target_layers_exact'if n in REFS else'non_target_layers_exact']+=1
 if n not in REFS:continue
 for mask in range(16):
  for arm in (1,2):
   wanted=color(b,full['before'if mask&1 else'after',n],16 if mask&1 else 0)
   assert np.array_equal(wanted,np.asarray(b.composite(n,mask,arm)[0]));counts['partial_RGBA_exact']+=1
for s,t,k in((144,145,-1),(146,147,0)):
 for pb in PBS:assert np.array_equal(mirror(b.layer(s,pb)[0],k),b.layer(t,pb)[0])
# 모든 보류7은 표시뿐 아니라 전체raw와 각조립도 보존됐음을 별도로 기록.
for n in HELD:
 assert raw(a,0,n)==raw(b,0,n)
 for pb in PBS:assert [sig(q)for q in parts(a,pb,n)]==[sig(q)for q in parts(b,pb,n)]
 for mask in range(16):
  for arm in(1,2):assert a.composite(n,mask,arm)[0].tobytes()==b.composite(n,mask,arm)[0].tobytes();counts['held_RGBA_exact']+=1
nativep=U/'native_first7_components_v1_native_checks.json';native=js(nativep);assert native['passed']
nr=native['resources']['PL02_U.ARC'];assert nr['candidate_sha256']==sha(new)
nd=next(q for q in nr['banks']if q['bank']==0)['native_decoder_checks']
for n in REFS:
 q=next(q for q in nd if q['frame']==n);assert q['decoded_sha256']==sha(raw(b,0,n))and q['buffer_outside_and_unused_tail_preserved']
boards=[]
for page,ns in enumerate(((143,144,145),(146,147,154),(183,)),1):
 pics=[a.composite(n,m)[0]for n in ns for m in(15,0)]+[b.composite(n,m)[0]for n in ns for m in(15,0)];boxes=[p.getbbox()for p in pics]
 box=(min(p[0]for p in boxes)-4,min(p[1]for p in boxes)-4,max(p[2]for p in boxes)+4,max(p[3]for p in boxes)+4)
 cw=(box[2]-box[0])*4+8;ch=(box[3]-box[1])*4+26;im=Image.new('RGB',(cw*4,ch*len(ns)),'#273443');dr=ImageDraw.Draw(im)
 for row,n in enumerate(ns):
  for col,(ar,mask,title)in enumerate(((a,15,'old before'),(b,15,'new before'),(a,0,'old after'),(b,0,'new after'))):
   p=ar.composite(n,mask)[0].crop(box).resize(((box[2]-box[0])*4,(box[3]-box[1])*4),Image.Resampling.NEAREST)
   im.paste(p,(col*cw+4,row*ch+23),p);dr.text((col*cw+4,row*ch+3),f'{n} {title}',fill='white')
 p=O/f'readback_{page}.png';im.save(p);boards.append({'path':rel(p),'sha256':sha(p.read_bytes()),'crop':box,'no_opaque_pixels_clipped':True})
assert counts['raw_checked']==512 and counts['non_target_raw_exact']==505 and counts['non_target_layers_exact']==1105
assert counts['target_layers_exact']==35 and counts['non_target_compositions_exact']==1756 and counts['GPU_parts_checked']==89 and counts['partial_RGBA_exact']==224
for p,h in tracked.items():assert sha((ROOT/p).read_bytes())==h,p
r={'passed':True,'scope':'허용 사다리5몸체+2반전 등록원화→35목표층→실제ARC 독립읽기. 생성13셀 재양자화/실기 아님.',
 'candidate':rel(newp),'candidate_sha256':sha(new),'parent_sha256':sha(old),'input_lock_sha256':sha(lockp.read_bytes()),'locked_inputs_checked':len(lock['files']),'target_manifest_sha256':sha((T/'manifest.json').read_bytes()),'counts':dict(counts),'source_registration_reconstruction':source,'shared_groups':groups,'shared_non_target_records_preserved':shared,
 'mirrors':[{'source':144,'target':145,'world_x':'-x-1','y_unchanged':True},{'source':146,'target':147,'world_x':'-x','y_unchanged':True}],
 'mirror_policy':'새양폼공통반전. 부모before관계와일치하나부모after159/244px차이를완전복원한주장은아님.',
 'held_refs_raw_layers_compositions_exact':sorted(HELD),'preserved':['ARC길이/항목및은행경계','기타13그래픽은행전체bytes','전체팔레트/음향/조립외항목','사격150/155기존총과몸체','기존조립공유비대상'],
 'native_existing_evidence':{'path':rel(nativep),'sha256':sha(nativep.read_bytes()),'seven_decoded_hashes_bound':True,'executed_here':False},
 'readback_sheets':boards,'readback_actually_viewed':False,'tracked_inputs':tracked,'producer_functions_called':False,'runtime_verified':False,'all_ladder_completed':False,
 'limits':['제작자7296전수RGBA를반복하지않고224대상+224보류RGBA/기타1105층과팔레트보존으로대조했다.','원화13셀재양자화·원순서재생·새MIPS/실기·사용자수용은별도.','149151153및연동4는그대로남아사다리14전체완료가아니다.']}
(O/'report.json').write_text(json.dumps(r,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'report_sha256':sha((O/'report.json').read_bytes()),'counts':dict(counts),'locked':len(lock['files'])}))
