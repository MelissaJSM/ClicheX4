"""탑승 머리19만 기존 단일타일에 기록. 모든 조립 바이트를 보존한다."""
from pathlib import Path
import sys,json,hashlib,struct,shutil
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,decode_stream,composition_frame,indexed_atlas
from src.psx_frame_edit import edit_frame_set
from src.psx_compress import encode_stream
from src.psx_bank_repack import repack_graphics_bank
D=Path(__file__).parent/'rin_extension';P=D/'prepared_bank1_recovery128/PL01_U.ARC';A=D/'ride_head_registered_v3';O=D/'prepared_ride_heads02'
SOURCE='07ec6077969f17d08c51ffd8e4326b476e1c6ab5635bea8420faee9528b39a89';ART='251194b9e4ab9f58983d41a1e81b3a1bd44978cff585e475c782c7e1764bfc7a'
sha=lambda b:hashlib.sha256(b).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix();read=lambda p:json.loads(p.read_text('utf8'))
def build(arc,overrides=None):
 assert sha(arc)==SOURCE,'Changed source';j=read(A/'registration.json');assert j['source_arc_sha256']==SOURCE and j['generated_sha256']==ART
 info=read(D/'ride_head01/inputs.json');targets={}
 for r in j['registered_refs']:
  n=int(r['key'][3:]);p=A/(r['key']+'_indices.png');assert sha(p.read_bytes())==r['output_sha256'],'Changed source art';z=np.array(Image.open(p));assert z.shape==(384,384)and z.dtype==np.uint8 and z.max()<=15
  targets[n]=z
 if overrides is not None:targets=overrides
 ids=set(range(66,86))-{80};assert set(targets)==ids,'Incomplete heads'
 g=entry(arc,2);parts=entry(arc,3);groups={}
 for f in graphics_bank(g,1)['frames']:groups.setdefault(f['offset'],[]).append(f)
 codes={};affected=set();proofs=[];oldraw={};newraw={}
 for off,refs in groups.items():
  selected=[f for f in refs if f['index']in ids]
  if not selected:continue
  f=refs[0];count=f['tile_count'];raw=decode_stream(g,off,f['limit'],count*128).data;edits=[];support=[]
  for q in refs:
   n=q['index'];c=composition_frame(parts,5,n)
   if n not in ids:support.append(c);continue
   assert len(c['parts'])==1;p=c['parts'][0];x,y=p['x']+160,p['y']+160;z=targets[n];assert z.dtype==np.uint8 and z.max()<=15
   tile=z[y:y+16,x:x+16];outside=z.copy();outside[y:y+16,x:x+16]=0;assert not outside.any(),'Opaque outside source tile';assert not(p['tile']%16==0 and tile[:,0].any()),'GPU first column';assert not(p['flip_y']and tile[0].any()),'GPU first row'
   edits.append((c,tile.tobytes(),(16,16)))
  nr=edit_frame_set(raw,count,edits,preserved_compositions=support);code=encode_stream(nr)
  for q in refs:codes[q['index']]=code;affected.add(q['index'])
  aa=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);zz=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256)
  owned={p['tile']for q in selected for p in composition_frame(parts,5,q['index'])['parts']};protected={p['tile']for c in support for p in c['parts']}
  for t in(set(range(count))-owned)|protected:
   y,x=t//16*16,t%16*16;assert np.array_equal(aa[y:y+16,x:x+16],zz[y:y+16,x:x+16])
  proofs.append({'group':[q['index']for q in refs],'selected':[q['index']for q in selected],'tile_count':count,'edited_tiles':sorted(owned),'all_non_owned_tiles_exact':True,'support_full_tiles_exact':sorted(protected)})
 ng,rp=repack_graphics_bank(g,1,codes);e=next(e for e in psx_arc(arc)if int(e['type'],16)==2);out=bytearray(arc);out[e['offset']:e['offset']+e['size']]=ng;out=bytes(out);assert len(out)==len(arc)
 for e in psx_arc(arc):
  if int(e['type'],16)!=2:assert out[e['offset']:e['offset']+e['size']]==arc[e['offset']:e['offset']+e['size']]
 raw_same=display_same=0;changedraw=[]
 for b in(0,1):
  for f,h in zip(graphics_bank(g,b)['frames'],graphics_bank(ng,b)['frames']):
   n=f['index'];assert f['tile_count']==h['tile_count'];r=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;s=decode_stream(ng,h['offset'],h['limit'],h['tile_count']*128).data
   if r==s:raw_same+=1
   else:changedraw.append(f'b{b}_{n:03}');assert b==1 and n in affected
   if b==1 and 42<=n<=49:assert r==s;continue
   old=render(arc,b,b*5,n)[0];new=render(out,b,b*5,n)[0]
   if b==1 and n in ids:assert np.array_equal(new,targets[n])and not np.array_equal(old,new)
   else:assert np.array_equal(old,new);display_same+=1
 assert not render(out,1,5,80)[0].any()
 return out,{'passed':True,'raw_count':444,'display_count':436,'unchanged_raw_count':raw_same,'unchanged_display_count':display_same,'changed_raw_refs':changedraw,'actual_changed_display_refs':[f'b1_{n:03}'for n in sorted(ids)],'all_parts_entry_exact':entry(out,3)==parts,'all_non_graphics_entries_exact':True,'partial_vram8_raw_exact':True,'blank80_exact':True,'gpu_single_tile19_first_column_safe':True,'groups':proofs,'repack':rp}
def main():
 assert not O.exists();assert sha((D/'ride_head75_crown_fix02/generated.png').read_bytes())==ART;arc=P.read_bytes();out,v=build(arc);again,_=build(arc);assert out==again
 O.mkdir();(O/'PL01_U.ARC').write_bytes(out)
 for f in('palette.bin','effect_23.png','effect_24.png','static_effects.json'):shutil.copyfile(P.parent/f,O/f)
 ids=sorted(set(range(66,86))-{80})
 for form,row in [('normal',0),('black',13)]:
  pal=struct.unpack_from('<16H',entry(arc,9),row*32)
  for offset in range(0,len(ids),10):
   subset=ids[offset:offset+10];sheet=Image.new('RGB',(1600,360*2),(28,34,45));dr=ImageDraw.Draw(sheet)
   for i,n in enumerate(subset):
    x=i%5*320;y=i//5*360;p=composition_frame(entry(arc,3),5,n)['parts'][0];cx,cy=p['x']+160,p['y']+160
    for k,z in enumerate([render(arc,1,5,n)[0],render(out,1,5,n)[0]]):
     pic=rgba(z[cy:cy+16,cx:cx+16],pal).resize((144,144),Image.Resampling.NEAREST);sheet.paste(pic,(x+k*160,y+30),pic)
    dr.text((x+5,y+5),f'{n} old -> new',fill='white')
   sheet.save(O/f'{form}_readback_{offset//10:02}.png')
 j={'source_arc':rel(P),'source_arc_sha256':SOURCE,'resource':rel(O/'PL01_U.ARC'),'after_sha256':sha(out),'new_art_refs':[f'b1_{n:03}'for n in ids],'cumulative_main_refs':259,'previous_frozen_art_refs':240,'registration':rel(A/'registration.json'),'registration_sha256':sha((A/'registration.json').read_bytes()),'generated_sha256':ART,'verification':v,'reproducible':True,'static_body_patch':{'recipe':rel(O/'static_effects.json'),'sha256':sha((O/'static_effects.json').read_bytes())},'root_art_review_pending':True,'ready_for_checkpoint_integration':False,'runtime_verified':False,'user_accepted':False,'scope':'다섯 작은 머리 원화→탑승19참조. 원래 조립 전체/부분8/빈80/팔레트·음향·정적자원 보존.12px 머리높이는 미술 검토 중.'}
 (O/'proposal.json').write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps({'arc':sha(out),'non_target_raw':v['unchanged_raw_count'],'non_target_display':v['unchanged_display_count'],'slack':v['repack']['remaining_slack']}))
if __name__=='__main__':main()
