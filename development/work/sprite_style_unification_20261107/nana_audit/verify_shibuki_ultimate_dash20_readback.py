"""시부키 Ultimate 전후 대시20 별도 reader. 제작/패킹 함수는 호출하지 않는다."""
from pathlib import Path
import sys,json,hashlib,struct,collections
import numpy as np
from PIL import Image
N=Path(__file__).resolve().parent;ROOT=N.parents[2];sys.path.insert(0,str(ROOT))
from scripts.export_x_consistency import Archive
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,decode_stream,composition_frame,indexed_atlas,compose_indices
sha=lambda b:hashlib.sha256(b).hexdigest()
H=ROOT/'work/sprite_style_unification_20261107/shibuki_audit';P=H/'prepared_ultimate_dash01';B=H/'prepared_ultimate_air01';T=H/'ultimate_dash_complete_targets01';PARTS=(0,5,6,7,8);REFS=(*range(67,85),93,94)
def records(c,b,n):return b''.join(struct.pack('<BBbb',p['flags'],p['tile'],p['x'],p['y'])for p in composition_frame(c,b,n)['parts'])
def raw(a,b,n):
 f=a.banks[b]['frames'][n];q=decode_stream(a.g,f['offset'],f['limit'],f['tile_count']*128);assert q.serialize()==a.g[q.start:q.end];return q.data
def comp_target(a,layers,mask,arm):
 r=np.array(a.rgba(layers[0])).copy()
 for bit,pb in((8,8),(1,5),(4,7),(2,6)):
  if mask&bit:
   q=np.array(a.rgba(layers[pb],32 if pb==7 and arm==2 else 16));m=q[:,:,3]>0;r[m]=q[m]
 return r
def main():
 old=(B/'PL02_U.ARC').read_bytes();new=(P/'PL02_U.ARC').read_bytes();assert sha(old)=='3ae1d8d56c595b04e59abf735ac377ab381c73673c2eaade99679031f3fc65f7';assert sha(new)=='bdcf0f648e2102a208307e21a941b53439a2f342014e69981a6de156a4dfbdfb';a=Archive(old);z=Archive(new);counts=collections.Counter()
 prop=json.loads((P/'proposal.json').read_text('utf8'));assert prop['sequential_parent']['sha256']==sha(old)and prop['files']['PL02_U.ARC']['after']==sha(new);lock=json.loads((T/'LOCK.json').read_text('utf8'));assert sha((T/'LOCK.json').read_bytes())==prop['target_lock_sha256'];assert sha((T/'targets.json').read_bytes())==lock['target_manifest_sha256']
 for name,dg in lock['files'].items():assert sha((T/name).read_bytes())==dg
 for name,dg in lock['sources'].items():assert sha((H/name).read_bytes())==dg
 target={n:{pb:np.array(Image.open(T/f'{n:03}_bank{pb}_indices.png'))for pb in PARTS}for n in REFS}
 ea,ez=psx_arc(old),psx_arc(new);assert len(ea)==len(ez);assert all(all(q[k]==r[k]for k in('index','type','offset','size'))for q,r in zip(ea,ez));allow=np.zeros(len(old),bool);protected=[]
 for q in ea:
  s,e=q['offset'],q['offset']+q['size']
  if int(q['type'],16)in(2,3):allow[s:e]=True
  else:assert old[s:e]==new[s:e];protected.append(q['index'])
 assert not np.any((np.frombuffer(old,np.uint8)!=np.frombuffer(new,np.uint8))&~allow)
 assert bank_offsets(a.g,allow_aliases=True)==bank_offsets(z.g,allow_aliases=True)and bank_offsets(a.c)==bank_offsets(z.c)
 changes=[]
 for b,(ob,nb)in enumerate(zip(a.banks,z.banks)):
  assert (ob['base'],ob['end'],len(ob['frames']))==(nb['base'],nb['end'],len(nb['frames']))
  for f,nf in zip(ob['frames'],nb['frames']):
   n=f['index'];r,nr=raw(a,b,n),raw(z,b,n);counts['raw']+=1
   if b==0 and n in REFS:assert nf['tile_count']==32;changes.append([b,n]);counts['selected_raw']+=1
   else:assert r==nr and f['tile_count']==nf['tile_count'];counts['non_target_raw_exact']+=1
 for b in range(len(bank_offsets(a.c))):
  assert composition_frame(a.c,b,0)['bank_frame_count']==composition_frame(z.c,b,0)['bank_frame_count']
  for n in range(composition_frame(a.c,b,0)['bank_frame_count']):
   if b in PARTS and n in REFS:continue
   assert records(a.c,b,n)==records(z.c,b,n);counts['non_target_composition_exact']+=1
 for n in range(237):
  if n in(105,*range(175,183)):continue
  for pb in PARTS:
   v=z.layer(n,pb)[0]
   if n in REFS:assert np.array_equal(v,target[n][pb]);counts['target_layers_exact']+=1
   else:assert np.array_equal(v,a.layer(n,pb)[0]);counts['non_target_layers_exact']+=1
 for n in REFS:
  f=z.banks[0]['frames'][n];atlas=np.frombuffer(indexed_atlas(raw(z,0,n),f['tile_count'])[0],np.uint8).reshape(-1,256)
  for pb in PARTS:
   for p in composition_frame(z.c,pb,n)['parts']:
    t=p['tile'];yy,xx=t//16*16,t%16*16;part=atlas[yy:yy+16,xx:xx+16];assert t<f['tile_count']
    if t%16==0:assert not part[:,0].any()
    if p['flip_y']:assert not part[0].any()
    counts['gpu_parts']+=1
  for mask in range(16):
   for arm in(1,2):assert np.array_equal(np.array(z.composite(n,mask,arm)[0]),comp_target(z,target[n],mask,arm));counts['partial_rgba_exact']+=1
 # 원34 총열60+11투명 보호영역을 각 목표위치로 독립 평행복원.
 G=H/'ultimate_dash_barrel_guard01';gm=json.loads((G/'report.json').read_text('utf8'));master=np.array(Image.open(G/'master_indices.png'));mm=np.array(Image.open(G/'master_mask.png'))>0;assert gm['parent_sha256']==sha(old)and sha((ROOT/gm['master_mask_source']).read_bytes())==gm['master_mask_sha256']
 assert (master[mm]>0).sum()==60 and mm.sum()==71;assert np.array_equal(np.array(a.rgba(master))[mm],np.array(a.composite(34,0)[0])[mm])
 gunproof=[]
 for n in(68,70,72,76,78,80,82,84):
  rows=[r for r in gm['rows']if r['shot_ref']==n];assert len(rows)==2;dx,dy=rows[0]['translation'];assert rows[1]['translation']==[dx,dy];expected=np.roll(master,(dy,dx),(0,1));mask=np.roll(mm,(dy,dx),(0,1));stored=np.array(Image.open(G/f'{n:03}_indices.png'));guard=np.array(Image.open(G/f'{n:03}_mask.png'))>0;assert np.array_equal(expected,stored)and np.array_equal(mask,guard)
  for m in range(16):
   for arm in(1,2):assert np.array_equal(np.array(z.composite(n,m,arm)[0])[mask],np.array(z.rgba(expected))[mask]);counts['canonical_barrel_rgba']+=1
  gunproof.append({'ref':n,'translation':[dx,dy],'opaque':60,'transparent_guard':11})
 # 原US 속도선9개 기록/실제16x16 타일/54가시텍셀을 원몸체와 분리 대조.
 sm=json.loads((H/'ultimate_dash_streak_audit01/report.json').read_text('utf8'));origdata=(ROOT/sm['original']).read_bytes();assert sha(origdata)==sm['original_sha256'];orig=Archive(origdata);effects=[]
 for n,body in((73,71),(74,72)):
  cp=composition_frame(orig.c,0,n);tail={**cp,'parts':cp['parts'][-9:]};assert records(z.c,0,n)[-36:]==records(orig.c,0,n)[-36:];f=orig.banks[0]['frames'][n];r=raw(orig,0,n);px,size,bb,_=compose_indices(r,f['tile_count'],tail,allowed_cluts={0,1,2,3});small=np.frombuffer(px,np.uint8).reshape(size[1],size[0]);ar=np.zeros((384,384),np.uint8);ar[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160]=small;assert np.count_nonzero(ar)==54
  expected=z.layer(body)[0].copy();expected[ar>0]=ar[ar>0];assert np.array_equal(expected,z.layer(n)[0])
  oa=np.frombuffer(indexed_atlas(r,f['tile_count'])[0],np.uint8).reshape(-1,256)[:16,96:112];za=np.frombuffer(indexed_atlas(raw(z,0,n),32)[0],np.uint8).reshape(32,256)[:16,96:112];assert np.array_equal(oa,za);effects.append({'ref':n,'parts':9,'visible_pixels':54,'real_tile6_sha256':sha(oa.tobytes())})
 result={'passed':True,'candidate_sha256':sha(new),'parent_sha256':sha(old),'producer_functions_called':False,'counts':dict(counts),'changed_scope':changes,'target_lock_sha256':sha((T/'LOCK.json').read_bytes()),'canonical34_barrels':gunproof,'original_us_speed_lines':effects,'protected_entry_indices':protected,'palette_audio_timing_other_entries_exact':True,'archive_directory_padding_exact':True,'original_bank_boundaries_exact':True,'new_gpu_boundary_alpha':0,'source_generation_reconstructed':False,'visual_review_performed':False,'native_mips_run_here':False,'runtime_verified':False,'scope':'목표100층과 준비ARC 별도reader·640부분합성·원34총열·US속도선·비대상 보존 확인. 원화미술/실게임/CPU는 별도증거이며 여기서 제작패킹 함수를 실행하지 않았다.'}
 out=N/'shibuki_ultimate_dash_independent';out.mkdir(exist_ok=True);(out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'passed':True,'counts':dict(counts),'sha256':sha((out/'report.json').read_bytes())}))
if __name__=='__main__':main()
