"""Read-only identification of US ice technique body and weapon composition banks."""
from pathlib import Path
import sys,json,ctypes,struct,time
from ctypes import wintypes
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,digest
from scripts.emulator_session import checked_window
from scripts.discover_inputs import psx_arc
from src.psx_player import graphics_bank,bank_offsets
from src.epsxe_state import framebuffer
D=Path(__file__).parent
P=Path(sys.argv[1]).resolve()
prior=json.loads(P.read_text());checked_window(prior['pid'])
B=Path(prior['source_build']);m=json.loads((B/'manifest.json').read_text());assert digest(B/'modified.arc')==m['modified_archive_sha256']
arc=(B/'modified.arc').read_bytes()
def entry(n):
 e=next(e for e in psx_arc(arc) if e['type']==hex(n));return arc[e['offset']:e['offset']+e['size']]
gfx,parts=entry(2),entry(3);off=bank_offsets(parts)
k=ctypes.WinDLL('kernel32');k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE
k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE]
h=k.OpenProcess(0x410,False,prior['pid']);base=prior['ram_host_address'];video=prior['vram_host_address']
def read(a,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
 if not k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) or got.value!=n:raise ValueError('Short read')
 return b.raw
out=new_run(ROOT,'ver_buki_riko','dashslash_identification');rows=[];seen=set()
try:
 p=read(base+0x1418c8,0xe4);ptr=struct.unpack_from('<I',p,0x38)[0]&0x1fffff;b=graphics_bank(gfx,0)
 assert p[2]==1 and p[0xb9]&0x80 and read(base+ptr,b['end']-b['base'])==gfx[b['base']:b['end']]
 start=time.monotonic()
 while time.monotonic()-start<15:
  p=read(base+0x1418c8,0xe4);w=read(base+0x1406f8,0x9c0);v=read(base+0x13e510,0xe00)
  if p[0x17] in (104,):
   visuals=[]
   for i in range(32):
    obj=v[i*0x70:(i+1)*0x70]
    if obj[0]:
     ptr=struct.unpack_from('<I',obj,0x3c)[0]&0x1fffff;matches=[]
     if ptr:
      for bi,o in enumerate(off):
       want=parts[o:off[bi+1] if bi+1<len(off) else len(parts)]
       if ptr+len(want)<=0x200000 and read(base+ptr,len(want))==want:matches.append(bi)
     visuals.append({'index':i,'active':obj[0],'id':obj[1],'subtype':obj[2],'x':struct.unpack_from('<i',obj,8)[0]/65536,'y':struct.unpack_from('<i',obj,12)[0]/65536,'animation':obj[0x17],'frame':obj[0x47],'parts_pointer':ptr,'exact_composition_banks':matches,'texture_word':struct.unpack_from('<H',obj,0x40)[0],'clut_word':struct.unpack_from('<H',obj,0x42)[0]})
   weapons=[]
   for i in range(16):
    obj=w[i*0x9c:(i+1)*0x9c]
    if obj[0] and obj[1] in (0x1d,):
     ptr=struct.unpack_from('<I',obj,0x3c)[0]&0x1fffff;matches=[]
     for bi,o in enumerate(off):
      want=parts[o:off[bi+1] if bi+1<len(off) else len(parts)]
      if read(base+ptr,len(want))==want:matches.append(bi)
     weapons.append({'index':i,'active':obj[0],'id':obj[1],'x':struct.unpack_from('<i',obj,8)[0]/65536,'y':struct.unpack_from('<i',obj,12)[0]/65536,'animation':obj[0x17],'frame':obj[0x47],'parts_pointer':ptr,'exact_composition_banks':matches,'texture_word':struct.unpack_from('<H',obj,0x40)[0],'clut_word':struct.unpack_from('<H',obj,0x42)[0]})
   key=(p[0x17],p[0x47],tuple((v['id'],v['subtype'],v['frame']) for v in visuals),tuple((w['frame'],tuple(w['exact_composition_banks'])) for w in weapons))
   if key not in seen:
    seen.add(key);n=len(rows);raw=read(video,1048576)
    (out/f'vram_{n:02d}.bin').write_bytes(raw);(out/f'player_{n:02d}.bin').write_bytes(p);(out/f'weapons_{n:02d}.bin').write_bytes(w);(out/f'visuals_{n:02d}.bin').write_bytes(v)
    for page in (0,256):framebuffer(raw,0,page).save(out/f'actual_{n:02d}_{page}.png')
    rows.append({'seconds':time.monotonic()-start,'animation':p[0x17],'frame':p[0x47],'weapons':weapons,'visuals':visuals})
  time.sleep(.004)
finally:k.CloseHandle(h)
write_json(out/'identification.local.json',{'source_build':str(B),'bin_sha256':m['modified_bin']['sha256'],'pid':prior['pid'],'baseline':str(P),'rows':rows,'input_sent':False,'process_memory_written':False})
(D/'runtime_layers_path.json').write_text(json.dumps({'output':str(out)}),'utf8')
print(json.dumps({'output':str(out),'body_frames':sorted({r['frame'] for r in rows}),'weapon_banks':sorted({b for r in rows for w in r['weapons'] for b in w['exact_composition_banks']})}))

