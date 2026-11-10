"""체이서28: 새몸4와 원리본·원진동을 고정32타일/은행 범위에서 결합한다."""
from pathlib import Path
import sys,json,hashlib,struct,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from scripts.prepare_rin_run import connected_groups
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,compose_indices
from src.psx_frame_edit import edit_frame_set,frame_coverage,_apply_writes
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
R=Path(__file__).parent/'rin_extension';P=R/'prepared_ride_heads02/PL01_U.ARC';A=R/'chaser_contacts_probe_v1';O=R/'prepared_chaser01'
SOURCE='c82e6230bcc687e2cc851a88735b695b04636b9fce3baddcf4c771abf81e265b';sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def world(raw,count,c):
 if not c['parts']:return np.zeros((384,384),np.uint8)
 px,sz,bb,_=compose_indices(raw,count,c,allowed_cluts={0});v=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);z=np.zeros((384,384),np.uint8);z[bb[1]+160:bb[3]+160,bb[0]+160:bb[2]+160]=v;return z
def crop(z,c):
 x=min(p['x']for p in c['parts'])+160;y=min(p['y']for p in c['parts'])+160;r=max(p['x']for p in c['parts'])+176;b=max(p['y']for p in c['parts'])+176;v=z[y:b,x:r];assert np.count_nonzero(v)==np.count_nonzero(z),'Opaque outside body bounds';return v.tobytes(),(r-x,b-y)
def build(arc,overrides=None):
 assert sha(arc)==SOURCE,'Source hash mismatch';j=read(R/'chaser_detail01/inputs.json');reg=read(A/'registration.json');targets={}
 for r in reg['records']:
  n=r['ref'];p=A/f'b1_{n:03}_body_indices.png';assert sha(p.read_bytes())==r['output_sha256'],'Source art hash mismatch';z=np.array(Image.open(p));assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15;targets[n]=z
 if overrides is not None:targets=overrides
 assert set(targets)=={14,22,30,38},'Missing body';g=entry(arc,2);oldparts=entry(arc,3);parts=bytearray(oldparts);fs=graphics_bank(g,1)['frames'];codes={};allworld={};proofs=[];permitted=set();bodytargets={}
 moves={14:{12:(1,0)},22:{15:(1,0)},30:{},38:{28:(1,0),15:(1,0)}}
 for m in j['masters']:
  base=m['ref'];ids=m['body_aliases'];owned=set(m['body_tiles']);f=fs[base];count=f['tile_count'];assert count==32;assert [q['index']for q in fs if q['offset']==f['offset']]==ids
  raw=decode_stream(g,f['offset'],f['limit'],count*128).data;z=targets[base];assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15;cs={n:composition_frame(oldparts,5,n)for n in ids}
  for n,c in cs.items():
   for p in c['parts']:
    if p['tile']in moves[base]:
     dx,dy=moves[base][p['tile']];assert -128<=p['x']+dx<=127 and -128<=p['y']+dy<=127;parts[p['record_offset']+2]=(p['x']+dx)&255;parts[p['record_offset']+3]=(p['y']+dy)&255;permitted|={p['record_offset']+2,p['record_offset']+3}
  c=composition_frame(parts,5,base);sub={**c,'parts':[p for p in c['parts']if p['tile']in owned]};coverage,_,_=frame_coverage(raw,count,sub);seeded=_apply_writes(raw,dict.fromkeys({s for a in coverage for s in a},0));px,sz=crop(z,sub);nr=edit_frame_set(seeded,count,[(sub,px,sz)],overlap_policy='equal_sources')
  oldatlas=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);newatlas=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256)
  for t in set(range(count))-owned:
   ty,tx=t//16*16,t%16*16;assert np.array_equal(oldatlas[ty:ty+16,tx:tx+16],newatlas[ty:ty+16,tx:tx+16]),'Original ribbon/unused tile changed'
  code=encode_stream(nr);phase_reports=[]
  for n in ids:
   cc=composition_frame(parts,5,n);oc=cs[n];phase=j['frames'][f'b1_{n:03}']['ribbon_phase'];dy=j['frames'][f'b1_{n:03}']['original_bob_y'];body=np.roll(z,dy,axis=0);bodytargets[n]=body;tail=world(raw,count,{**oc,'parts':[p for p in oc['parts']if p['tile']not in owned]});assert np.array_equal(tail,world(nr,count,{**cc,'parts':[p for p in cc['parts']if p['tile']not in owned]}))
   assert np.array_equal(body,world(nr,count,{**cc,'parts':[p for p in cc['parts']if p['tile']in owned]})),'Shared body bob changed';combined=np.where(body,body,tail).astype(np.uint8);assert np.array_equal(combined,world(nr,count,cc)),'Actual draw order differs';components=[len(group)for group in connected_groups(combined>0)];assert len(components)==1,('Ribbon/body disconnected',n,components)
   for p in cc['parts']:
    t=p['tile'];tile=newatlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    assert not(t%16==0 and tile[:,0].any()),'GPU U0 first-column';assert not(p['flip_y']and tile[0].any()),'GPU flipY first-row'
   codes[n]=code;allworld[n]=combined;phase_reports.append({'ref':n,'phase':phase,'bob_y':dy,'body_exact':True,'original_ribbon_exact':True,'single_connected_component':True,'parts':len(cc['parts'])})
  proofs.append({'master':base,'shared_refs':ids,'tile_count':count,'body_tiles':sorted(owned),'all_other_tiles_exact':True,'changed_window_translations':moves[base],'native_ribbon_and_bob':phase_reports})
 ng,rp=repack_graphics_bank(g,1,codes);out=bytearray(arc)
 for eid,data in((2,ng),(3,bytes(parts))):
  e=next(e for e in psx_arc(arc)if int(e['type'],16)==eid);assert len(data)==e['size'];out[e['offset']:e['offset']+e['size']]=data
 out=bytes(out);diff={i for i,(v,w)in enumerate(zip(oldparts,parts))if v!=w};assert diff<=permitted
 for e in psx_arc(arc):
  if int(e['type'],16)not in(2,3):assert out[e['offset']:e['offset']+e['size']]==arc[e['offset']:e['offset']+e['size']]
 same_raw=same_display=0;gpu=0
 for b in(0,1):
  for f,h in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];assert f['tile_count']==h['tile_count'];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,h['offset'],h['limit'],h['tile_count']*128).data
   if b==1 and n in allworld:assert raw!=nr;gpu+=len(composition_frame(parts,5,n)['parts'])
   else:assert raw==nr;same_raw+=1;oc=composition_frame(oldparts,b*5,n);nc=composition_frame(parts,b*5,n);assert oc==nc
   if b==1 and 42<=n<=49:continue
   v=render(out,b,b*5,n)[0]
   if b==1 and n in allworld:assert np.array_equal(v,allworld[n])and not np.array_equal(v,render(arc,b,b*5,n)[0])
   else:assert np.array_equal(v,render(arc,b,b*5,n)[0]);same_display+=1
 return out,{'passed':True,'raw_count':444,'non_target_raw_exact':same_raw,'display_count':436,'non_target_display_exact':same_display,'partial8_exact':True,'all_other_entries_exact':True,'only_selected_part_xy_changed_bytes':len(diff),'groups':proofs,'gpu_parts':gpu,'repack':rp},allworld,bodytargets
def main():
 assert not O.exists();arc=P.read_bytes();out,v,worlds,bodies=build(arc);again,_,_,_=build(arc);assert out==again;O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 for f in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/f,O/f)
 recipe=read(P.parent/'static_effects.json');recipe['parts_sha256']=sha(entry(out,3));(O/'static_effects.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 for n,z in worlds.items():Image.fromarray(z).save(O/f'b1_{n:03}_indices.png');Image.fromarray(bodies[n]).save(O/f'b1_{n:03}_body_indices.png')
 for form,row in [('normal',0),('black',13)]:
  pal=struct.unpack_from('<16H',entry(out,9),row*32)
  for at in range(0,len(worlds),8):
   subset=list(worlds)[at:at+8];sheet=Image.new('RGB',(1536,4*280),(28,34,45));dr=ImageDraw.Draw(sheet)
   for i,n in enumerate(subset):
    x=i%2*768;y=i//2*280
    for k,z in enumerate([render(arc,1,5,n)[0],render(out,1,5,n)[0]]):
     pic=rgba(z,pal).crop((112,120,208,184)).resize((384,256),Image.Resampling.NEAREST);sheet.paste(pic,(x+k*384,y+24),pic)
    dr.text((x+5,y+5),f'{n} old / new',fill='white')
   sheet.save(O/f'{form}_readback_{at//8:02}.png')
 q={'source_arc':rel(P),'source_arc_sha256':SOURCE,'resource':rel(O/'PL01_U.ARC'),'after_sha256':sha(out),'new_art_refs':[f'b1_{n:03}'for n in sorted(worlds)],'cumulative_main_refs':287,'previous_frozen_art_refs':259,'registration':rel(A/'registration.json'),'registration_sha256':sha((A/'registration.json').read_bytes()),'verification':v,'reproducible':True,'static_body_patch':{'recipe':rel(O/'static_effects.json'),'sha256':sha((O/'static_effects.json').read_bytes())},'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'체이서4 새몸체를 원리본4위상·상하진동에 결합한28참조. 모든 원리본 타일과 비대상·부분VRAM8·소리·팔레트 보존. 원32타일/고정은행, 창4개 x+1만 이동하며 실제 그림 원점은 그대로다.'}
 (O/'proposal.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'arc':sha(out),'raw_same':v['non_target_raw_exact'],'display_same':v['non_target_display_exact'],'parts_bytes':v['only_selected_part_xy_changed_bytes'],'slack':v['repack']['remaining_slack']}))
if __name__=='__main__':main()
