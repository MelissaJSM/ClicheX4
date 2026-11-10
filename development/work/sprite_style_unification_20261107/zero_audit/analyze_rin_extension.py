"""Read-only native feasibility and continuity inventory for Rin's four new keys."""
from pathlib import Path
import sys, json, hashlib, struct, importlib.util
from collections import defaultdict
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
D=Path(__file__).parent;OUT=D/'rin_extension';OUT.mkdir(exist_ok=True)
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.overhaul_sprites_audit import render,rgba
from scripts.build_rin_motion import SCOPES
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import frame_coverage
spec=importlib.util.spec_from_file_location('rear_packer',D/'riko_restore/pack_rear_head.py');packer=importlib.util.module_from_spec(spec);spec.loader.exec_module(packer)
def sha(b):return hashlib.sha256(b).hexdigest()
def bounds(a):
 y,x=np.nonzero(a);return [int(x.min()),int(y.min()),int(x.max()+1),int(y.max()+1)]if len(x)else None
def skin_components(a):
 labels,n=ndimage.label(np.isin(a,[12,13,14]));out=[]
 for i in range(1,n+1):
  m=labels==i
  if m.sum()>=3:out.append({'bounds':bounds(m),'pixels':int(m.sum())})
 return out
parent=ROOT/'out/ver_rin_nana/sprite_reaudit_20261106_v1/rin_nana.bin';parent_sha=sha(parent.read_bytes());assert parent_sha=='f9762868ea6a5c3e9ce65708a07bfbff3762cd98c6a057f78b584525fb48c720'
arc=read_disc(parent,('PL01_U.ARC',))[0]['PL01_U.ARC'];g,c=entry(arc,2),entry(arc,3);pal=struct.unpack_from('<16H',entry(arc,9));black=struct.unpack_from('<16H',entry(arc,9),13*32)
art=ROOT/'work/sprite_style_unification_20261107/rin/locomotion01';inputs=json.loads((art/'inputs.json').read_text('utf8'));reg=json.loads((art/'native/registration.json').read_text('utf8'));assert inputs['source_sha256']==parent_sha and inputs['archive_sha256']==sha(arc);assert reg['source_art_sha256']==sha((art/'generated.png').read_bytes())
bank=graphics_bank(g,0);shared=defaultdict(list)
for f in bank['frames']:shared[f['offset']].append(f['index'])
groups={'run':[*range(7,21),3,4],'dash':list(range(44,53)),'ground':sorted(SCOPES['ground'])};worlds={n:render(arc,0,0,n)[0]for n in set(sum(groups.values(),[]))|{147}};keys=[8,14,49,95];targets={n:np.array(Image.open(art/'native'/f'b0_{n:03d}_indices.png'))for n in keys};records=[]
for n in keys:
 f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;cp=composition_frame(c,0,n);cov,sz,bb=frame_coverage(raw,f['tile_count'],cp);safe=np.zeros((384,384),bool);safe[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.array([bool(v)for v in cov]).reshape(sz[1],sz[0]);new=targets[n];old=worlds[n];outside=np.argwhere((new>0)&~safe);record={'ref':n,'source_png':str((art/'native'/f'b0_{n:03d}_indices.png').relative_to(ROOT)),'png_sha256':sha((art/'native'/f'b0_{n:03d}_indices.png').read_bytes()),'old_bounds':bounds(old),'new_bounds':bounds(new),'floor_delta':bounds(new)[3]-bounds(old)[3],'part_count':len(cp['parts']),'tile_count':f['tile_count'],'raw_shared_refs':shared[f['offset']],'current_exact_display_refs':[q for q,v in worlds.items()if np.array_equal(old,v)],'outside_existing_coverage':outside[:,[1,0]].tolist(),'skin_components_before':skin_components(old),'skin_components_after':skin_components(new)}
 try:
  assert not len(outside),'Art outside original parts'
  crop=new[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]];edited=packer.edit_visible_set(raw,f['tile_count'],[(cp,crop.tobytes(),sz)]);record['visible_native_edit_possible']=True;record['new_gpu_boundary_alpha']=[]
  before=np.frombuffer(indexed_atlas(raw,f['tile_count'])[0],np.uint8).reshape(-1,256);after=np.frombuffer(indexed_atlas(edited,f['tile_count'])[0],np.uint8).reshape(-1,256)
  for p in cp['parts']:
   t=p['tile'];yy,xx=t//16*16,t%16*16
   if t%16==0 and np.any((before[yy:yy+16,xx]==0)&(after[yy:yy+16,xx]>0)):record['new_gpu_boundary_alpha'].append({'tile':t,'edge':'first_column'})
   if p['flip_y']and t//16%16==0 and np.any((before[yy,xx:xx+16]==0)&(after[yy,xx:xx+16]>0)):record['new_gpu_boundary_alpha'].append({'tile':t,'edge':'flipped_first_row'})
 except (ValueError,AssertionError)as e:record['visible_native_edit_possible']=False;record['packing_blocker']=str(e)
 records.append(record)
inventory=[]
for group,ns in groups.items():
 legacy=ROOT/'work/ver_rin_nana/style_revision/v3'/group;hist=json.loads((legacy/'registered.json').read_text('utf8'));seen={};items=[]
 for n in ns:
  a=worlds[n];key=sha(a.tobytes());same=seen.get(key);seen.setdefault(key,n);f=bank['frames'][n];rec=hist['frames'].get(str(n));sources=[]
  for k,r in hist['frames'].items():
   p=legacy/r['file'];im=np.array(Image.open(p));bb=r['bounds'];w=np.zeros((384,384),np.uint8);w[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=im
   if np.array_equal(a,w):sources.append(int(k))
  inventory.append({'group':group,'ref':n,'current_unique_alias':same,'historical_native_exact_refs':sources,'raw_shared_refs':shared[f['offset']],'tile_count':f['tile_count'],'registered':rec,'source_dir':str(legacy.relative_to(ROOT))});items.append((str(n)+(' NEW'if n in targets else ''),targets.get(n,a)))
 # One source-independent review sheet for current sequence; new keys shown separately.
 for start in range(0,len(ns),12):
  subset=ns[start:start+12];cw,ch=320,344;board=Image.new('RGB',(cw*4,ch*((len(subset)+3)//4)),'#64717b');draw=ImageDraw.Draw(board)
  for i,n in enumerate(subset):
   p=rgba(worlds[n],pal).crop((120,120,200,200)).resize((320,320),Image.Resampling.NEAREST);x=i%4*cw;y=i//4*ch;board.paste(p,(x,y+24),p);draw.text((x+5,y+5),f'{group} {n}',fill='white')
  board.save(OUT/f'{group}_current_{start//12:02d}.png')
 report={'source_bin':str(parent.relative_to(ROOT)),'source_bin_sha256':parent_sha,'arc_sha256':sha(arc),'new_art_sha256':reg['source_art_sha256'],'keys':records,'inventory':inventory,'runtime_verified':False,'game_changed':False}
(OUT/'analysis.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'keys':[{k:r.get(k)for k in('ref','tile_count','raw_shared_refs','outside_existing_coverage','visible_native_edit_possible','packing_blocker','new_gpu_boundary_alpha')}for r in records],'groups':{group:len(ns)for group,ns in groups.items()}}))
