"""고정 길이 대화 자원과 표시 선택부의 검증된 후보를 준비한다. BIN 쓰기 없음."""
from pathlib import Path
import sys,struct,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];H=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from scripts.prepare_riko_ui import entry,replace_entry
from src.psx_ui_atlas import aliased_composition,tile_pixels,write_tile,local_composition
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_korean_font import Assembly
from src.psx_disc import file_hash

PRIMARY_SIZE=1376
START,END=0x80022954,0x800229a0
def sha(b):return hashlib.sha256(b).hexdigest()
def off(a):return a-0x80010000+2048
def write(p,j):p.write_text(json.dumps(j,ensure_ascii=False,indent=2)+'\n','utf8')
def selector():
 a=Assembly();i=a.imm;b=a.branch
 i(15,'a0','zero',0x8017);i(36,'v0','a0',0x2207);i(36,'v1','a0',0x2203)
 i(12,'a1','v0',3);a.shift(0,'a1','a1',1)
 b(5,'v1','zero','done');i(36,'v1','a0',0x21f7)
 a.nop();b(4,'v1','zero','done');a.nop()
 i(35,'v1','s0',0x3c);a.reg(0x2b,'a1','zero','v0');a.shift(0,'a1','a1',1)
 i(9,'v1','v1',PRIMARY_SIZE);i(43,'v1','s0',0x3c)
 a.label('done');i(40,'a1','s0',0x54)
 while len(a.words)<(END-START)//4:a.nop()
 out=a.finish();assert len(out)==END-START;return out

def bank(ids,targets,allocate):
 headers=[];records=bytearray();known={}
 for n in ids:
  a=targets[n];key=a.tobytes()
  if key not in known:
   known[key]=(len(ids)*4+len(records))//4
   for y in range(0,96,16):
    for x in range(0,112,16):
     tile=allocate(a[y:y+16,x:x+16].tobytes());assert tile<256
     records+=struct.pack('<BBbb',0,tile,x-56,y-48)
  headers.append((known[key]<<16)|42)
 # Primary first frame starts at word8 even if later frames alias it.
 return struct.pack('<'+'I'*len(headers),*headers)+records

source_exe=None
for mode in ['ver_rin_nana','ver_buki_riko']:
 h=H/mode;a=json.loads((h/'audit.json').read_text('utf8'));inv=a['inventory'];old={p.name:p.read_bytes()for p in(h/'originals').glob('*.ARC')};new=dict(old);targets={n:np.array(Image.open(h/f'native_proposal/{n:02}.png'))for n in range(12)}
 assert all(t.shape==(96,112) and t.dtype==np.uint8 and t.max()<16 for t in targets.values())
 # Accepted basic portrait is compared using actual source indices.
 p0=entry(old['ST00_00.ARC'],10);g0=entry(old['ST00_00.ARC'],0x10102)[204800:217088]
 for n in ([0,4] if mode=='ver_rin_nana' else range(8)):
  assert compose_static(g0,local_composition(aliased_composition(p0,11,n)))[0]==targets[n].tobytes(),('Accepted portrait changed',mode,n)
 border=entry(old['ST00_00.ARC'],0x10102)[198656:204800];assert tile_pixels(border,12)==tile_pixels(border,13)
 reserved=set()
 for bi in [9,10]:
  for n in range(aliased_composition(p0,bi,0)['bank_frame_count']):reserved.update(r['tile']for r in aliased_composition(p0,bi,n)['parts'])
 reserved.difference_update([13,25,27]);free_border=sorted(set(range(48))-reserved);assert len(free_border)==20
 # Redirect the one duplicate UI tile13 to byte-identical tile12. Every
 # matching border bank was inventoried across the current disc, not inferred.
 border_inv=json.loads((h/'border_inventory.json').read_text('utf8'));border_before=(h/'border_bank.bin').read_bytes();one=struct.pack('<I',4)+border_before;border_after=bytearray(one);changed_border_records=set()
 for n in range(5):
  c=composition_frame(one,0,n)
  for r in c['parts']:
   assert r['page']==0
   if r['tile'] in {13:12,25:21,27:26}:border_after[r['record_offset']+1]={13:12,25:21,27:26}[r['tile']];changed_border_records.add(r['record_offset']+1)
  assert compose_static(border,c)[:3]==compose_static(border,composition_frame(border_after,0,n))[:3]
 for q in border_inv:
  pp=entry(new[q['file']],10);assert pp[q['offset']:q['offset']+q['size']]==border_before
  new[q['file']]=replace_entry(new[q['file']],10,pp[:q['offset']]+bytes(border_after[4:])+pp[q['offset']+q['size']:])
 groups={};gfx_reports=[]
 for q in inv['graphics']:
  original=entry(old[q['file']],q['type']);bstart=original.find(border);assert bstart>=0 and original.find(border,bstart+1)<0
  delta=(q['offset']-bstart)//128;assert delta in [48,96,112]
  texture=bytearray(original[bstart:q['offset']+q['size']]);available=list(range(delta,delta+96))+free_border;allocated={}
  def allocate(pattern):
   if pattern not in allocated:
    assert available,('Native atlas capacity exceeded',mode,q['file'],len(allocated))
    tile=available.pop(0);allocated[pattern]=tile;write_tile(texture,tile,pattern)
   return allocated[pattern]
  primary=bank(list(range(8)),targets,allocate);assert len(primary)<=PRIMARY_SIZE;primary=primary.ljust(PRIMARY_SIZE,b'\0')
  ultimate=bank([8,9,8,9,10,11,10,11],targets,allocate);new_bank=(primary+ultimate).ljust(2976,b'\0');assert len(new_bank)==2976
  if delta in groups:assert groups[delta]['bank']==new_bank
  else:groups[delta]={'bank':new_bank,'texture':bytes(texture)}
  for n in range(12):
   offset=0 if n<8 else PRIMARY_SIZE;idx=n if n<8 else {8:0,9:1,10:4,11:5}[n]
   c=composition_frame(struct.pack('<I',4)+new_bank[offset:],0,idx);got,sz,bounds,_=compose_static(texture,c)
   assert(got,sz,bounds)==(targets[n].tobytes(),(112,96),(-56,-48,56,48))
  # All non-X texture pixels except the certified free border slots stay exact.
  touched=set(allocated.values());allowed_tiles={delta+i for i in range(96)}|set(free_border)
  assert touched<=allowed_tiles
  for i in range(len(texture)//128):
   if i not in allowed_tiles:assert tile_pixels(texture,i)==tile_pixels(original[bstart:],i)
  for n in range(5):assert compose_static(border,composition_frame(one,0,n))[:3]==compose_static(texture,composition_frame(border_after,0,n))[:3]
  new[q['file']]=replace_entry(new[q['file']],q['type'],original[:bstart]+bytes(texture)+original[q['offset']+q['size']:])
  table=entry(new[q['file']],12);values=list(struct.unpack('<'+'I'*(len(table)//4),table));hits=[i for i,v in enumerate(values)if v==q['offset']];assert hits
  for i in hits:values[i]=bstart
  new[q['file']]=replace_entry(new[q['file']],12,struct.pack('<'+'I'*len(values),*values))
  gfx_reports.append({'file':q['file'],'old_texture_base':q['offset'],'new_texture_base':bstart,'delta_tiles':delta,'tiles_allocated':len(allocated),'borrowed_border_tiles':sorted(t for t in allocated.values()if t<48),'other_texture_pixels_preserved':True,'border5_frames_pixel_exact':True,'frames12_indexed_roundtrip':True})
 comp_reports=[]
 for q in inv['compositions']:
  oldp=entry(old[q['file']],10);pp=entry(new[q['file']],10);offsets=list(struct.unpack_from('<'+'I'*(struct.unpack_from('<I',pp)[0]//4),pp));bi=offsets.index(q['offset'])
  delta=48 if q['file']=='ST00_00.ARC' else 112 if q['file']in['ST0B_01.ARC','ST0C_01.ARC','ST0C_U1.ARC'] else 96
  # 57 referenced NPC tiles require the native64-tile block before X; all
  # other NPC portraits here occupy48. This agrees with each graphics table.
  if delta!=48:
   npc=aliased_composition(oldp,bi-1,0);mx=max(r['tile']for n in range(npc['bank_frame_count'])for r in aliased_composition(oldp,bi-1,n)['parts']);assert (mx>=48)==(delta==112)
  blob=groups[delta]['bank'];new[q['file']]=replace_entry(new[q['file']],10,pp[:q['offset']]+blob+pp[q['offset']+q['size']:])
  comp_reports.append({'file':q['file'],'bank_indices':[i for i,o in enumerate(offsets)if o==q['offset']],'delta_tiles':delta,'primary_bytes':PRIMARY_SIZE,'private_ultimate_bank_bytes':704,'total_original_slot_bytes':q['size']})
 exe=(h/'SLUS_005.61').read_bytes();before=exe[off(START):off(END)]
 if source_exe is None:source_exe=before
 else:assert before==source_exe
 new_exe=exe[:off(START)]+selector()+exe[off(END):];assert len(new_exe)==len(exe)
 out=h/'prepared_v2';out.mkdir(exist_ok=False);files=[]
 for name,data in new.items():
  assert len(data)==len(old[name])
  if data!=old[name]:(out/name).write_bytes(data);files.append({'file':name,'before':sha(old[name]),'after':sha(data)})
 (out/'SLUS_005.61').write_bytes(new_exe)
 write(out/'verification.json',{'project':mode,'graphics':gfx_reports,'compositions':comp_reports,'border_duplicate_redirect_records':len(changed_border_records),'border_copies':len(border_inv),'palette_bytes_preserved':True,'gameplay_sprites_unchanged':True,'arc_lengths_preserved':True,'files':files,'exe_display_range':[hex(START),hex(END)],'exe_other_bytes_preserved':True,'parent_sha256':a['pointer']['sha256'],'prepared_not_applied':True})
 print(mode,'prepared',len(files),'ARCs; tiles',sorted({r['tiles_allocated']for r in gfx_reports}),flush=True)
(H/'selector_original.bin').write_bytes(source_exe);(H/'selector_new.bin').write_bytes(selector())
