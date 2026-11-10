"""질풍아8을 검기 공유 소비 타일을 보존하며 같은 은행에 등록한다."""
from pathlib import Path
import json,shutil,struct,sys
import numpy as np
D=Path(__file__).parent;sys.path.insert(0,str(D));import probe_dash_saber_pack as core
engine=core.engine;ROOT=engine.ROOT;P=core.P;SHA=core.SHA;A=D/'rin_extension/dash_saber_registered_v1';O=D/'rin_extension/prepared_dash_saber01'
REG=json.loads((A/'registration.json').read_text('utf8'));MAP={(0,n):(0,n)for n in range(158,174,2)};HASHES={r['key']:r['output_sha256']for r in REG['records']};assert REG['source_arc_sha256']==SHA
PRIVATE={}

def pack(c,b,n,raw,count,target):
 if b!=0 or n not in range(168,174):return core.pack(c,b,n,raw,count,target)
 from scripts.prepare_shibuki_armor_motion import identical
 import scripts.prepare_shibuki_armor_motion as motion
 from scripts.prepare_shibuki_ultimate_production import fast_fit
 from scripts.solve_sprite_cover import cover
 master=n-n%2;group=core.shared.GROUPS[b,n];assert group==list(range(168,174))and count==31
 protected={p['tile']for k in group if k%2 for p in engine.native.composition_frame(c,0,k)['parts']}
 owned={p['tile']for k in group if not k%2 for p in engine.native.composition_frame(c,0,k)['parts']};pool=owned-protected
 assert protected=={9,10,11,20,21,30} and len(pool)==25
 key=engine.native.sha(raw+core.shared.ALL[b,master].tobytes()+f'private-pair-{master}-v1'.encode())
 if key not in PRIVATE:
  cache=D/'rin_extension/dash_saber_private_cache_v1';cache.mkdir(exist_ok=True);p=cache/(key+'.json')
  if p.exists():j=json.loads(p.read_text('utf8'));PRIVATE[key]=(bytes.fromhex(j['raw']),bytes.fromhex(j['records']),j['proof'])
  else:
   def fit(mask,limit):
    rr=fast_fit(mask,limit)
    if rr is not None:return rr
    q=cover(mask,limit,20);return q['rects']if q['fits']else None
   motion.fit=fit
   nr,rr=identical(raw,count,core.shared.ALL[b,master][80:240,80:240],pool,12)
   rec=b''.join(struct.pack('<BBbb',0,t,x-80,y-80)for t,x,y in rr)
   aa=np.frombuffer(engine.native.indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);zz=np.frombuffer(engine.native.indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256)
   for t in set(range(count))-pool:
    y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16])
   proof={'type':'private_body_effect_pair_bounded','original_group':group,'pair':[master,master+1],'owned_tile_pool':sorted(pool),'protected_support_tiles':sorted(protected),'all_other_raw_tiles_exact':True,'tile_count':count,'body_parts_before':len(engine.records(c,0,master))//4,'body_parts_after':len(rr),'hidden_global_cleanup':False}
   p.write_text(json.dumps({'raw':nr.hex(),'records':rec.hex(),'proof':proof},indent=2)+'\n','utf8');PRIVATE[key]=(nr,rec,proof)
 nr,rec,proof=PRIVATE[key]
 return nr,rec if n==master else engine.records(c,0,n),proof

def configure(arc):
 core.A=A;core.O=O;core.MAP=MAP;core.HASHES=HASHES;PRIVATE.clear();tt=core.configure(arc);engine.pack_frame=pack;return tt
def main():
 assert not O.exists(),'Use fresh output'
 for r in REG['generated']:engine.native.need(engine.native.sha((ROOT/r['path']).read_bytes())==r['sha256'],'Changed generated art')
 arc=P.read_bytes();tt=configure(arc);out,proof=engine.build(arc,tt);again,_=engine.build(arc,tt);assert out==again
 for k in('heads_preserved_pixels_per_reference','source_3rd_saber9_and_rear28_preserved'):proof.pop(k,None)
 for r in proof['changes']:r.pop('head_preserved',None)
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 from scripts.export_x_consistency import page
 from scripts.overhaul_sprites_audit import render,rgba
 for form,row in(('normal',0),('black',13)):
  pal=struct.unpack_from('<16H',engine.native.entry(out,9),row*32);keys=sorted(MAP)
  for ix in range(0,len(keys),4):
   items=[]
   for b,n in keys[ix:ix+4]:items.extend([(f'b{b}_{n:03} old',rgba(render(arc,b,b*5,n)[0],pal)),(f'b{b}_{n:03} packed',rgba(render(out,b,b*5,n)[0],pal))])
   page(items,rgba(render(out,0,0,147)[0],pal),O/f'{form}_readback_{ix//4:02}.png',cols=2,scale=5)
 recipe=json.loads((P.parent/'static_effects.json').read_text('utf8'));recipe['parts_sha256']=engine.native.sha(engine.native.entry(out,3))
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 rp=O/'static_effects.json';rp.write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 j={'source_arc':str(P.relative_to(ROOT)),'source_arc_sha256':SHA,'resource':str((O/'PL01_U.ARC').relative_to(ROOT)),'after_sha256':engine.native.sha(out),'new_art_refs':[f'b{b}_{n:03}'for b,n in MAP],'shared_support_refs':[f'b{b}_{n:03}'for b,n in tt if(b,n)not in MAP],'native_master_sha256':HASHES,'registration':str((A/'registration.json').relative_to(ROOT)),'registration_sha256':engine.native.sha((A/'registration.json').read_bytes()),'cumulative_main_refs':222,'previous_frozen_art_refs':214,'verification':proof,'static_body_patch':{'recipe':str(rp.relative_to(ROOT)),'sha256':engine.native.sha(rp.read_bytes())},'reproducible':True,'runtime_verified':False,'user_accepted':False,'root_art_review_pending':True,'ready_for_checkpoint_integration':False,'scope':REG['scope']+' 기존214와 다른 모든 몸체·검기·부분VRAM·음향·팔레트·정적효과 보존.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':j['after_sha256'],'support':j['shared_support_refs'],'layouts':proof['layouts']}))
if __name__=='__main__':main()
