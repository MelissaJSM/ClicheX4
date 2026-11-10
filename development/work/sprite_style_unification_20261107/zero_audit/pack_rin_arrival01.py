"""새 등장5와 원규칙 섬광2를 현재 고정은행/기존 타일수 안에 패킹한다."""
from pathlib import Path
import sys,json,hashlib,struct,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas,compose_indices
from src.psx_frame_edit import edit_frame_set,frame_coverage,_apply_writes
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
R=Path(__file__).parent/'rin_extension';P=R/'prepared_chaser01/PL01_U.ARC';A=R/'arrival_contacts_probe_v3';O=R/'prepared_arrival01';SOURCE='99603ab0c003149a4fa415b3dcea78a0967a3be615d226471888bb3ece092a11'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def flashes(body):
 mask=body>0;expanded=mask.copy()
 for dy in range(-2,3):
  for dx in range(-2,3):
   if abs(dx)+abs(dy)<=2:expanded|=np.roll(np.roll(mask,dy,0),dx,1)
 return {247:np.where(mask,11,np.where(expanded,10,0)).astype(np.uint8),248:np.where(mask,11,0).astype(np.uint8)}
def crop(z,c):
 x=min(p['x']for p in c['parts'])+160;y=min(p['y']for p in c['parts'])+160;r=max(p['x']for p in c['parts'])+176;b=max(p['y']for p in c['parts'])+176;v=z[y:b,x:r];assert np.count_nonzero(v)==np.count_nonzero(z),'Opaque outside parts bounds';return v.tobytes(),(r-x,b-y)
def build(arc,overrides=None):
 assert sha(arc)==SOURCE,'Wrong parent hash';reg=read(A/'registration.json');targets={}
 for rec in reg['records']:
  n=rec['ref'];p=A/f'b0_{n:03}_indices.png';assert sha(p.read_bytes())==rec['output_sha256'],'Art source hash mismatch';targets[n]=np.array(Image.open(p))
 if overrides is not None:targets=overrides
 assert set(targets)==set(range(249,254)),'Missing arrival body'
 for z in targets.values():assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15,'Invalid indexed source'
 parent_flashes=flashes(render(arc,0,0,249)[0])
 for n,z in parent_flashes.items():assert np.array_equal(z,render(arc,0,0,n)[0]),'Parent flash rule not exact'
 targets={**flashes(targets[249]),**targets};g=entry(arc,2);oldp=entry(arc,3);parts=bytearray(oldp);fs=graphics_bank(g,0)['frames'];permitted=set();moves={252:{5:(-1,0),6:(-1,0),7:(-1,0)},253:{17:(-2,0),18:(-2,0),19:(-2,0)}}
 for n,tiles in moves.items():
  c=composition_frame(parts,0,n)
  for p in c['parts']:
   if p['tile']in tiles:
    dx,dy=tiles[p['tile']];parts[p['record_offset']+2]=(p['x']+dx)&255;parts[p['record_offset']+3]=(p['y']+dy)&255;permitted|={p['record_offset']+2,p['record_offset']+3}
 codes={};groups=[]
 for ids in([247,248],[249,250],[251],[252,253]):
  f=fs[ids[0]];assert [q['index']for q in fs if q['offset']==f['offset']]==ids;count=f['tile_count'];assert count<=32;raw=decode_stream(g,f['offset'],f['limit'],count*128).data;edited=[];cells=set()
  for n in ids:
   c=composition_frame(parts,0,n);cover,sz,bb=frame_coverage(raw,count,c);cells|={s for a in cover for s in a};px,size=crop(targets[n],c);bad=[(i%sz[0]+160+bb[0],i//sz[0]+160+bb[1])for i,(value,src)in enumerate(zip(px,cover))if value and not src];assert not bad,('Uncovered indexed artwork',n,bad);edited.append((c,px,size))
  seed=_apply_writes(raw,dict.fromkeys(cells,0));nr=edit_frame_set(seed,count,edited,overlap_policy='equal_sources');code=encode_stream(nr);oldatlas=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);atlas=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256);gpu=[]
  for n in ids:
   c=composition_frame(parts,0,n);px,sz,bb,_=compose_indices(nr,count,c);z=np.zeros((384,384),np.uint8);z[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(px,np.uint8).reshape(sz[1],sz[0]);assert np.array_equal(z,targets[n]),('Readback differs',n)
   for p in c['parts']:
    t=p['tile'];tile=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16];ot=oldatlas[t//16*16:t//16*16+16,t%16*16:t%16*16+16]
    assert not(t%16==0 and np.any((tile[:,0]>0)&(ot[:,0]==0))),('New GPU U0',n,t);assert not(p['flip_y']and np.any((tile[0]>0)&(ot[0]==0))),('New GPU V0',n,t);gpu.append({'ref':n,'tile':t,'safe':True})
   codes[n]=code
  # Every nibble not consumed by these selected compositions is retained.
  before=np.frombuffer(raw,np.uint8);after=np.frombuffer(nr,np.uint8)
  for i in range(len(raw)*2):
   if (i//2,i%2*4) not in cells:assert ((int(before[i//2])>>(i%2*4))&15)==((int(after[i//2])>>(i%2*4))&15)
  groups.append({'refs':ids,'tile_count':count,'shared_stream':True,'encoded_bytes':len(code),'gpu_parts':len(gpu),'unconsumed_nibbles_exact':True})
 ng,rp=repack_graphics_bank(g,0,codes);out=bytearray(arc)
 for eid,data in((2,ng),(3,bytes(parts))):
  e=next(e for e in psx_arc(arc)if int(e['type'],16)==eid);assert len(data)==e['size'];out[e['offset']:e['offset']+e['size']]=data
 out=bytes(out);diff={i for i,(x,y)in enumerate(zip(oldp,parts))if x!=y};assert diff<=permitted
 for e in psx_arc(arc):
  if int(e['type'],16)not in(2,3):assert out[e['offset']:e['offset']+e['size']]==arc[e['offset']:e['offset']+e['size']]
 same_raw=same_display=0
 for b in(0,1):
  for f,h in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];assert f['tile_count']==h['tile_count'];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;nr=decode_stream(ng,h['offset'],h['limit'],h['tile_count']*128).data
   if b==0 and n in targets:assert raw!=nr
   else:assert raw==nr;same_raw+=1;assert composition_frame(oldp,b*5,n)==composition_frame(parts,b*5,n)
   if b==1 and 42<=n<=49:continue
   z=render(out,b,b*5,n)[0]
   if b==0 and n in targets:assert np.array_equal(z,targets[n])and not np.array_equal(z,render(arc,b,b*5,n)[0])
   else:assert np.array_equal(z,render(arc,b,b*5,n)[0]);same_display+=1
 assert same_raw==437 and same_display==429
 return out,{'passed':True,'raw_count':444,'non_target_raw_exact':same_raw,'display_count':436,'non_target_display_exact':same_display,'partial8_exact':True,'groups':groups,'only_tile_window_xy_bytes':len(diff),'tile_window_moves':moves,'parent_flash_rule_exact':True,'new_flash_rule_exact':True,'pure_beam53_60_exact':True,'palette_sound_other_entries_exact':True,'repack':rp},targets
def main():
 assert not O.exists();arc=P.read_bytes();out,v,targets=build(arc);again,_,_=build(arc);assert out==again;O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 for n,z in targets.items():Image.fromarray(z).save(O/f'b0_{n:03}_indices.png')
 for name in('palette.bin','effect_23.png','effect_24.png'):shutil.copyfile(P.parent/name,O/name)
 recipe=read(P.parent/'static_effects.json');recipe['parts_sha256']=sha(entry(out,3));(O/'static_effects.json').write_text(json.dumps(recipe,ensure_ascii=False,indent=2)+'\n','utf8')
 for form,row in [('normal',0),('black',13)]:
  pal=struct.unpack_from('<16H',entry(out,9),row*32)
  for page,ids in enumerate(([247,248,249,250],[251,252,253])):
   sh=Image.new('RGB',(1440,len(ids)*352),(28,34,45));dr=ImageDraw.Draw(sh)
   for i,n in enumerate(ids):
    for col,(label,z)in enumerate([('idle147',render(out,0,0,147)[0]),(f'{n} old',render(arc,0,0,n)[0]),(f'{n} packed',render(out,0,0,n)[0])]):
     pic=rgba(z,pal).crop((112,120,208,190)).resize((480,350),Image.Resampling.NEAREST);sh.paste(pic,(col*480,i*352+20),pic);dr.text((col*480+5,i*352+3),label,fill='white')
   sh.save(O/f'{form}_readback_{page:02}.png')
 q={'source_arc':rel(P),'source_arc_sha256':SOURCE,'resource':rel(O/'PL01_U.ARC'),'after_sha256':sha(out),'new_art_refs':[f'b0_{n:03}'for n in sorted(targets)],'new_original_art_bodies':5,'derived_flash_refs':[247,248],'cumulative_main_refs':294,'previous_frozen_art_refs':287,'registration':rel(A/'registration.json'),'registration_sha256':sha((A/'registration.json').read_bytes()),'verification':v,'reproducible':True,'static_body_patch':{'recipe':rel(O/'static_effects.json'),'sha256':sha((O/'static_effects.json').read_bytes())},'root_art_review_pending':True,'runtime_verified':False,'user_accepted':False,'ready_for_checkpoint_integration':False,'scope':'등장5새몸체와 원247/248섬광규칙파생2. 원타일수/공유4그룹/비대상·기존287·부분VRAM8·원순수빛53..60·팔레트·음향 보존. 새발끝을 자르지 않고252/253 타일창 두곳만x−1/−2이동. 원래시간표/판정불변.'}
 q['scope']=q['scope'].replace('타일창 두곳만','하단 타일창 각3곳(총6곳)만')
 (O/'proposal.json').write_text(json.dumps(q,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'sha256':sha(out),'counts':[v['non_target_raw_exact'],v['non_target_display_exact']],'slack':v['repack']['remaining_slack'],'parts_bytes':v['only_tile_window_xy_bytes']}))
if __name__=='__main__':main()
