"""Pack full portraits without cutting art; certify unused/duplicate NPC tiles."""
from pathlib import Path
import argparse,json,struct,sys,hashlib
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_ui_atlas import aliased_composition,tile_pixels,write_tile,local_composition
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_disc import file_hash
def sha(b):return hashlib.sha256(b).hexdigest()
def load(p):return json.loads(p.read_text('utf8'))
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
PAIRS={'ST00_00.ARC':['ST00_00.ARC'],'ST00_01.ARC':['ST00_01.ARC'],'ST0_1_1.ARC':['ST00_01.ARC'],'ST09_00.ARC':['ST09_00.ARC'],'STA_0_1.ARC':['ST0A_00.ARC'],'ST0B_00.ARC':['ST0B_00.ARC'],'ST0B_0X.ARC':['ST0B_0X.ARC'],'STB_1_1.ARC':['ST0B_01.ARC'],'STC_1_1.ARC':['ST0C_01.ARC','ST0C_U1.ARC']}
ap=argparse.ArgumentParser();ap.add_argument('--mode',required=True,choices=['ver_rin_nana','ver_buki_riko']);ap.add_argument('--art',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);a=ap.parse_args();out=a.output;out.mkdir(exist_ok=False)
prev=ROOT/'work/armor_dialogue_20261108'/a.mode;inv=load(prev/'audit.json')['inventory'];prior=load(prev/'prepared_v2/verification.json');pointer=load(ROOT/f'projects/{a.mode}/current_build.json');bin=ROOT/Path(pointer['cue']).with_suffix('.bin');assert file_hash(bin)==pointer['sha256']
names=sorted(set(PAIRS)|{n for v in PAIRS.values()for n in v});old,records=read_disc(bin,names);new=dict(old)
targets={n:np.array(Image.open(a.art/f'{n:02}.png'))for n in range(12)};assert all(t.shape==(96,112)and t.max()<16 for t in targets.values())
unique_patterns={t[y:y+16,x:x+16].tobytes()for t in targets.values()for y in range(0,96,16)for x in range(0,112,16)}
extra_needed=max(0,len(unique_patterns)-116)
border_used={r['tile']for bank in [9,10]for n in range(aliased_composition(entry(old['ST00_00.ARC'],10),bank,0)['bank_frame_count'])for r in aliased_composition(entry(old['ST00_00.ARC'],10),bank,n)['parts']};border_free=sorted(set(range(48))-border_used);assert len(border_free)==20
pending={};reports=[]
for q in inv['graphics']:
 name=q['file'];r=next(r for r in prior['graphics']if r['file']==name);start=r['new_texture_base'];delta=r['delta_tiles'];g=entry(old[name],q['type']);cap=64 if delta==112 else 48
 npc_start=q['offset']+q['size'] if delta==48 else q['offset']-cap*128
 npc_tex=g[npc_start:npc_start+cap*128];assert len(npc_tex)==cap*128
 counterparts=[];used=set()
 for n in PAIRS[name]:
  pp=entry(old[n],10);xq=next(x for x in inv['compositions']if x['file']==n);offs=list(struct.unpack_from('<'+'I'*(struct.unpack_from('<I',pp)[0]//4),pp));xb=offs.index(xq['offset']);nb=13 if delta==48 else xb-1
  cs=[aliased_composition(pp,nb,i)for i in range(aliased_composition(pp,nb,0)['bank_frame_count'])]
  assert all(t['page']==0 for c in cs for t in c['parts']);used.update(t['tile']for c in cs for t in c['parts']);counterparts.append((n,xq,nb,cs))
 known={};remap={}
 for i in sorted(used):
  pat=tile_pixels(npc_tex,i)
  if pat in known:remap[i]=known[pat]
  else:known[pat]=i
 free=(sorted(set(range(cap))-used)+sorted(remap))[:extra_needed]
 assert len(free)==extra_needed,(name,free,extra_needed)
 remap={i:j for i,j in remap.items()if i in free}
 # Only redirects to already byte-identical tiles: other original copies
 # remain visually valid even when their graphic bytes are not modified.
 end=max(q['offset']+q['size'],npc_start+cap*128);texture=bytearray(g[start:end]);npc_base=(npc_start-start)//128
 available=list(range(delta,delta+96))+border_free+[npc_base+t for t in free]
 allocated={}
 def alloc(pat):
  if pat not in allocated:
   assert available,(name,'Native atlas capacity exceeded',len(allocated));idx=available.pop(0);assert idx<256;allocated[pat]=idx;write_tile(texture,idx,pat)
  return allocated[pat]
 def bank(ids):
  headers=[];body=bytearray();seen={}
  for i in ids:
   frame=targets[i];key=frame.tobytes()
   if key not in seen:
    seen[key]=(len(ids)*4+len(body))//4
    for y in range(0,96,16):
     for x in range(0,112,16):body.extend(struct.pack('<BBbb',0,alloc(frame[y:y+16,x:x+16].tobytes()),x-56,y-48))
   headers.append((seen[key]<<16)|42)
  return struct.pack('<'+'I'*len(ids),*headers)+body
 primary=bank(list(range(8)));assert len(primary)<=1376
 xb=(primary.ljust(1376,b'\0')+bank([8,9,8,9,10,11,10,11])).ljust(2976,b'\0');assert len(xb)==2976
 npc_changed=[]
 for n,xq,nb,cs in counterparts:
  pp=bytearray(entry(new[n],10));changes=[]
  for c in cs:
   for t in c['parts']:
    if t['tile']in remap:
     off=t['record_offset']+1;pp[off]=remap[t['tile']];changes.append(off)
  pp[xq['offset']:xq['offset']+xq['size']]=xb
  if n in pending:
   if pending[n]!=bytes(pp):print('CONFLICT',name,n,'free',free,'remap',remap,'different offsets',[i for i,(a,b)in enumerate(zip(pending[n],pp))if a!=b][:20],flush=True)
   assert pending[n]==bytes(pp),('Shared graphics differ',n)
  pending[n]=bytes(pp);npc_changed.append({'file':n,'bank':nb,'redirect_offsets':sorted(set(changes))})
  for i,c in enumerate(cs):assert compose_static(npc_tex,c)[:3]==compose_static(texture[npc_base*128:],aliased_composition(bytes(pp),nb,i))[:3],('NPC rendering changed',n,i)
 for i in range(12):
  at,j=(0,i)if i<8 else(1376,{8:0,9:1,10:4,11:5}[i]);c=composition_frame(struct.pack('<I',4)+xb[at:],0,j)
  got,size,bounds,_=compose_static(texture,c);assert(got,size,bounds)==(targets[i].tobytes(),(112,96),(-56,-48,56,48))
 used_extra=sorted(t-npc_base for t in allocated.values()if npc_base<=t<npc_base+cap)
 assert set(used_extra)<=set(free)
 allowed=set(range(delta,delta+96))|set(border_free)|{npc_base+t for t in used_extra}
 for i in range(len(texture)//128):
  if i not in allowed:assert tile_pixels(texture,i)==tile_pixels(g[start:],i)
 new[name]=replace_entry(new[name],q['type'],g[:start]+texture+g[end:])
 reports.append({'file':name,'type':q['type'],'start':start,'texture_bytes':len(texture),'delta':delta,'patterns':len(allocated),'border_free':border_free,'npc_base':npc_base,'npc_capacity':cap,'npc_duplicate_redirect':remap,'npc_free':free,'npc_borrowed':used_extra,'npc_compositions':npc_changed,'npc_frames_pixel_exact':True,'all12_portraits_pixel_exact':True,'unrelated_tiles_exact':True})
for n,pp in pending.items():new[n]=replace_entry(new[n],10,pp)
files=[]
for n,b in new.items():
 assert len(b)==len(old[n])
 if b!=old[n]:(out/n).write_bytes(b);files.append({'file':n,'before':sha(old[n]),'after':sha(b)})
write(out/'verification.json',{'project':a.mode,'pointer':pointer,'records':records,'files':files,'graphics':reports,'exe_unchanged':True,'palette_unchanged':True,'timing_unchanged':True,'art':a.art.as_posix()});print(a.mode,len(files),'ARCs, patterns',sorted({r['patterns']for r in reports}))

