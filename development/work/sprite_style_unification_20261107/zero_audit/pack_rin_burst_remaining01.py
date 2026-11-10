"""낙봉파 잔여9를 원4공유stream/타일수에 패킹하고 원구체 월드화소를 보존한다."""
from pathlib import Path
import sys,json,hashlib,struct,shutil
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).parent;ROOT=D.parents[2];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(D))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.discover_inputs import psx_arc
from scripts.register_rin_style_revision import repack_windows
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,compose_indices
from src.psx_frame_edit import edit_frame_set,frame_coverage,_apply_writes
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
from pack_rin_arrival01 import crop
from inspect_rin_burst_pack import targets as load_targets
R=D/'rin_extension';P=R/'prepared_arrival01/PL01_U.ARC';O=R/'prepared_burst_remaining01';SOURCE='adf3b9475dd95cad5ff53ba627e4461dc9cb7ec18d202482b59744b0587c0322';sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'));GROUPS=[[177,178,179],[180,181],[186,187],[188,189]]
def build(arc,overrides=None):
 assert sha(arc)==SOURCE,'Wrong parent hash';targets=load_targets()if overrides is None else overrides;assert set(targets)=={177,178,179,180,181,186,187,188,189}
 for z in targets.values():assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15
 g=entry(arc,2);oldp=entry(arc,3);parts=bytearray(oldp);fs=graphics_bank(g,1)['frames'];permitted=set();moves=[]
 for n in (177,179,188,189):
  z=targets[n];y,x=np.nonzero(z);l,t,r,b=int(x.min()),int(y.min()),int(x.max())+1,int(y.max())+1;revised=repack_windows(parts,5,n,z[t:b,l:r],l-160,t-160);assert revised is not None,('No same-count windows',n)
  for a,p in zip(composition_frame(parts,5,n)['parts'],composition_frame(revised,5,n)['parts']):
   for off in(2,3):permitted.add(p['record_offset']+off)
   if(a['x'],a['y'])!=(p['x'],p['y']):moves.append({'ref':n,'tile':p['tile'],'old_xy':[a['x'],a['y']],'new_xy':[p['x'],p['y']]})
  parts=revised
 codes={};groups=[]
 for ids in GROUPS:
  f=fs[ids[0]];assert [q['index']for q in fs if q['offset']==f['offset']]==ids;count=f['tile_count'];assert count<=32;raw=decode_stream(g,f['offset'],f['limit'],count*128).data;edited=[];cells=set()
  for n in ids:
   c=composition_frame(parts,5,n);cov,sz,bb=frame_coverage(raw,count,c);cells|={s for a in cov for s in a};px,size=crop(targets[n],c);bad=[(i%sz[0]+160+bb[0],i//sz[0]+160+bb[1])for i,(value,s)in enumerate(zip(px,cov))if value and not s];assert not bad,('Uncovered artwork',n,bad);edited.append((c,px,size))
  seed=_apply_writes(raw,dict.fromkeys(cells,0));nr=edit_frame_set(seed,count,edited,overlap_policy='equal_sources');code=encode_stream(nr);oa=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);na=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256);gpu=[]
  for n in ids:
   c=composition_frame(parts,5,n);px,sz,bb,_=compose_indices(nr,count,c);z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);assert np.array_equal(z,targets[n])
   for p in c['parts']:
    t=p['tile'];y,x=t//16*16,t%16*16;nt=na[y:y+16,x:x+16];ot=oa[y:y+16,x:x+16];assert not(t%16==0 and np.any((nt[:,0]>0)&(ot[:,0]==0))),('New GPU U0',n,t);assert not(p['flip_y']and np.any((nt[0]>0)&(ot[0]==0))),('New GPU V0',n,t);gpu.append({'ref':n,'tile':t,'safe':True})
   codes[n]=code
  for i in range(len(raw)*2):
   if(i//2,i%2*4)not in cells:assert(raw[i//2]>>(i%2*4)&15)==(nr[i//2]>>(i%2*4)&15)
  groups.append({'refs':ids,'tile_count':count,'shared_stream':True,'encoded_bytes':len(code),'gpu_parts':len(gpu),'unconsumed_nibbles_exact':True})
 ng,rp=repack_graphics_bank(g,1,codes);out=bytearray(arc)
 for eid,data in((2,ng),(3,bytes(parts))):
  e=next(e for e in psx_arc(arc)if int(e['type'],16)==eid);assert len(data)==e['size'];out[e['offset']:e['offset']+e['size']]=data
 out=bytes(out);diff={i for i,(x,y)in enumerate(zip(oldp,parts))if x!=y};assert diff<=permitted
 for e in psx_arc(arc):
  if int(e['type'],16)not in(2,3):assert out[e['offset']:e['offset']+e['size']]==arc[e['offset']:e['offset']+e['size']]
 same_raw=same_display=0
 for b in(0,1):
  for f,h in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];assert f['tile_count']==h['tile_count'];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,h['offset'],h['limit'],h['tile_count']*128).data
   if b==1 and n in targets:assert raw!=nr
   else:assert raw==nr;same_raw+=1;assert composition_frame(oldp,b*5,n)==composition_frame(parts,b*5,n)
   if b==1 and 42<=n<=49:continue
   z=render(out,b,b*5,n)[0]
   if b==1 and n in targets:assert np.array_equal(z,targets[n])and not np.array_equal(z,render(arc,b,b*5,n)[0])
   else:assert np.array_equal(z,render(arc,b,b*5,n)[0]);same_display+=1
 assert same_raw==435 and same_display==427
 effects=[]
 for n in range(177,182):
  fx=np.array(Image.open(R/'burst_remaining_probe01'/f'b1_{n:03}_effect_indices.png'));assert np.array_equal(render(out,1,5,n)[0][fx>0],render(arc,1,5,n)[0][fx>0]);effects.append({'ref':n,'pixels':int(np.count_nonzero(fx)),'original_world_indices_exact':True})
 return out,{'passed':True,'raw_count':444,'non_target_raw_exact':same_raw,'display_count':436,'non_target_display_exact':same_display,'partial8_exact':True,'groups':groups,'only_tile_window_xy_bytes':len(diff),'tile_window_moves':moves,'original_charge_effect':effects,'palette_sound_static_other_entries_exact':True,'repack':rp},targets
def main():
 assert not O.exists();arc=P.read_bytes();out,v,targets=build(arc);again,_,_=build(arc);assert out==again;O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 for n,z in targets.items():Image.fromarray(z).save(O/f'b1_{n:03}_indices.png')
 for name in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/name,O/name)
 recipe=read(P.parent/'static_effects.json');recipe['parts_sha256']=sha(entry(out,3));(O/'static_effects.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 for form,row in [('normal',0),('black',13)]:
  pal=struct.unpack_from('<16H',entry(out,9),row*32)
  for page,ids in enumerate(([177,178,179],[180,181,186],[187,188,189])):
   sh=Image.new('RGB',(1440,len(ids)*400),'#263142');dr=ImageDraw.Draw(sh)
   for i,n in enumerate(ids):
    for col,(label,z)in enumerate([('idle147',render(out,0,0,147)[0]),(f'{n} old',render(arc,1,5,n)[0]),(f'{n} packed',render(out,1,5,n)[0])]):
     pic=rgba(z,pal).crop((112,112,208,188)).resize((480,380),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*400+20),pic);dr.text((col*480+5,i*400+3),label,fill='white')
   sh.save(O/f'{form}_readback_{page:02}.png')
 q={'source_arc':rel(P),'source_arc_sha256':SOURCE,'resource':rel(O/'PL01_U.ARC'),'after_sha256':sha(out),'new_art_refs':[f'b1_{n:03}'for n in sorted(targets)],'cumulative_main_refs':303,'previous_frozen_art_refs':294,'new_original_masters':7,'reuse177':'원래몸체가정확히같은현재새101+원효과70px','alias187':186,'target_sha256':{str(n):sha((O/f'b1_{n:03}_indices.png').read_bytes())for n in targets},'verification':v,'reproducible':True,'static_body_patch':{'recipe':rel(O/'static_effects.json'),'sha256':sha((O/'static_effects.json').read_bytes())},'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'낙봉파 잔여9. 새로운7몸체+입증된177/101공유와186/187공유. 원구체1064px 월드색인exact, 원타일수/공유4그룹/이전294/부분8/외부정적효과 보존. 그림을 자르지 않고 기존파츠의xy창만 이동.'};(O/'proposal.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out),'counts':[v['non_target_raw_exact'],v['non_target_display_exact']],'slack':v['repack']['remaining_slack'],'xy_bytes':v['only_tile_window_xy_bytes']}));
if __name__=='__main__':main()
