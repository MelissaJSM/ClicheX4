"""Bounded native registration of ground follow-through and wall saber19."""
from pathlib import Path
import sys,json,hashlib,shutil,struct
import numpy as np
from PIL import Image
D=Path(__file__).parent;sys.path.insert(0,str(D))
import pack_riko_cloth as engine
sys.path.insert(0,str(D.parent/'riko'))
from lossless_stream_pack import repack
ROOT=engine.ROOT;P=D/'rin_extension/prepared_ground_first_v1/PL01_U.ARC';SHA='cf01c08e17c742983abcd566e08f165c2c48205b453d051ce64ea58ca1a8c0c1'
A=D/'rin_extension/after122_registered_v1';O=D/'rin_extension/prepared_ground_wall_v1'
MAP={(0,n):(0,m)for m,refs in [(71,[71]),(73,[73,75,77,79,81]),(82,[82]),(131,[131,132])]for n in refs}
MAP.update({(1,n):(1,m)for m,refs in[(50,[50]),(51,[51,53]),(54,[54,56]),(57,[57,59,61,63,65])]for n in refs})
reg=json.loads((A/'registration.json').read_text('utf8'));HASHES={r['key']:r['output_sha256']for r in reg['records']};assert reg['source_arc_sha256']==SHA
def targets(arc):
 engine.native.need(engine.native.sha(arc)==SHA,'Wrong Rin122 source')
 masters={}
 for key,h in HASHES.items():
  p=A/(key+'_indices.png');engine.native.need(engine.native.sha(p.read_bytes())==h,'Changed registered art');a=np.array(Image.open(p));engine.native.need(a.shape==(384,384)and a.dtype==np.uint8 and a.max()<=15,'Invalid indexed source');masters[int(key[1]),int(key[3:])]=a
 result={}
 for (b,n),(mb,m)in MAP.items():
  engine.native.need(np.array_equal(engine.native.render(arc,b,b*5,n)[0],engine.native.render(arc,mb,mb*5,m)[0]),'Original exact alias differs');result[b,n]=masters[mb,m].copy()
 g=engine.native.entry(arc,2)
 for b,n in list(result):
  bank=engine.native.graphics_bank(g,b);off=bank['frames'][n]['offset']
  for f in bank['frames']:
   k=b,f['index']
   if f['offset']==off and k not in result:
    engine.native.need(not(b==1 and 42<=k[1]<=49),'Partial raw group');result[k]=engine.native.render(arc,b,b*5,k[1])[0].copy()
 return result
ordinary_pack=engine.pack_frame
GROUPS={};JOINT={}
def joint(c,b,n,raw,count):
 from scripts.prepare_shibuki_armor_remaining import pack_many_patterns
 import scripts.prepare_shibuki_armor_remaining as remaining
 from scripts.prepare_shibuki_ultimate_production import fast_fit
 from scripts.solve_sprite_cover import cover
 group=GROUPS[b,n];selected=[k for k in group if(b,k)in MAP];support=[k for k in group if(b,k)not in MAP]
 key=engine.native.sha(raw+b''.join(engine.records(c,b*5,k)for k in group)+b''.join(ALL[b,k].tobytes()for k in selected)+f'joint-{b}-{group}'.encode())
 if key in JOINT:return JOINT[key]
 cache=D/'rin_extension/after122_joint_cache_v1';cache.mkdir(exist_ok=True);p=cache/(key+'.json')
 if p.exists():
  j=json.loads(p.read_text('utf8'));r=(bytes.fromhex(j['raw']),{int(k):bytes.fromhex(v)for k,v in j['records'].items()},j['proof']);JOINT[key]=r;return r
 support_tiles={v['tile']for k in support for v in engine.native.composition_frame(c,b*5,k)['parts']}
 owned_tiles={v['tile']for k in selected for v in engine.native.composition_frame(c,b*5,k)['parts']};pool=owned_tiles-support_tiles
 print(json.dumps({'joint_group':group,'bank':b,'selected':selected,'pool':sorted(pool),'protected':sorted(support_tiles)}),flush=True)
 def fit(mask,limit):
  rr=fast_fit(mask,limit)
  if rr is not None:return rr
  q=cover(mask,limit,20);return q['rects']if q['fits']else None
 remaining.fit=fit
 lengths=[len(engine.native.composition_frame(c,b*5,k)['parts'])for k in selected]
 nr,rr=pack_many_patterns(raw,count,[ALL[b,k][80:240,80:240]for k in selected],pool,lengths);records={k:engine.records(c,b*5,k)for k in support}
 for k,parts,limit in zip(selected,rr,lengths):
  assert len(parts)<=limit
  while len(parts)<limit:parts.append(parts[-1])
  records[k]=b''.join(struct.pack('<BBbb',flag,t,x-80,y-80)for t,x,y,flag in parts)
 aa=np.frombuffer(engine.native.indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);zz=np.frombuffer(engine.native.indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256)
 for t in set(range(count))-pool:
  y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16])
 proof={'type':'same_original_group_joint_art','group':group,'owned_tile_pool':sorted(pool),'protected_support_tiles':sorted(support_tiles),'all_other_raw_tiles_exact':True,'hidden_global_cleanup':False}
 p.write_text(json.dumps({'raw':nr.hex(),'records':{str(k):v.hex()for k,v in records.items()},'proof':proof},indent=2)+'\n','utf8');r=(nr,records,proof);JOINT[key]=r;return r
def pack(c,b,n,raw,count,target):
 if b==0:
  nr,rr,proof=joint(c,b,n,raw,count);return nr,rr[n],proof
 if(b,n)not in MAP:return raw,engine.records(c,b*5,n),{'type':'shared_support_preserved'}
 return ordinary_pack(c,b,n,raw,count,target)
def configure(arc):
 tt=targets(arc)
 global ALL
 ALL=tt
 for b,n in tt:
  bank=engine.native.graphics_bank(engine.native.entry(arc,2),b);off=bank['frames'][n]['offset'];GROUPS[b,n]=[f['index']for f in bank['frames']if f['offset']==off]
 engine.PARENT=P;engine.PARENT_SHA=SHA;engine.OUT=O;engine.CACHE=D/'rin_extension/after122_pack_cache_v1';engine.KEYS={k:(0,0,0)for k in tt};engine.get_targets=targets;engine.pack_frame=pack;engine.native.packer.repack_raw=repack
 return tt
def main():
 assert not O.exists(),'Use a new output'
 for folder,h in [('ground_followup01','636b6fdab48269d006b26b56e3420a2ad284cd9dfc6e804abca8fa6e4722ffe9'),('wall_saber01','a3680701b91272ca890cd2f885a3feb40ecc40a0785135fba7e5c9ec540d4ad1')]:
  assert engine.native.sha((D/'rin_extension'/folder/'generated.png').read_bytes())==h
 arc=P.read_bytes();tt=configure(arc)
 out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in ('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out);engine.KEYS={k:(0,0,0)for k in MAP};engine.boards(arc,out)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'cumulative_main_refs':141,'previous_frozen_art_refs':122,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'지상 후속9와 벽공격10.새8원화의 정확 같은 모양 공유 확장.기존122·검기·부분VRAM·정적몸체 보존.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
