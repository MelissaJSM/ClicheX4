import ctypes,json,struct,sys,shutil,subprocess,time,gzip
from pathlib import Path
from datetime import datetime,timezone
from ctypes import wintypes
R=Path.cwd();sys.path.insert(0,str(R))
from scripts.project import digest
D=R/'work/ver_rin_nana/nana_ultimate_armor'
c=json.loads((R/'projects/ver_rin_nana/current_build.json').read_text('utf8'));pid=c['emulator_pid'];ram=17374752
k=ctypes.WinDLL('kernel32');k.OpenProcess.argtypes=[wintypes.DWORD,wintypes.BOOL,wintypes.DWORD];k.OpenProcess.restype=wintypes.HANDLE;k.ReadProcessMemory.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)];k.CloseHandle.argtypes=[wintypes.HANDLE];h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t();assert k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) and got.value==n;return b.raw
def player():
 anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100');assert read(ram+0x11a2f8,len(anchor))==anchor
 p=read(ram+0x1418c8,228);return dict(pid=pid,character=p[2],animation=p[0x17],frame=p[0x47],hp=p[0x5c],armor=p[0xa7],ultimate=read(ram+0x1721f7,1)[0],world=[struct.unpack_from('<i',p,z)[0]/65536 for z in(8,12)])
if __name__=='__main__':
 p=player();print(json.dumps(p))
 if len(sys.argv)>1 and sys.argv[1]=='save':
  assert p['character']==0 and ((p['animation']==5 and p['frame'] in(0,115,116,117,118,119)) or (p['animation']==6 and p['frame'] in range(120,126))) and p['armor']==15 and p['ultimate']==1,'Wait for full armor idle'
  e=R/'work/ver_rin_nana/emulator';back=R/'work/ver_rin_nana/checkpoints'/('before_ultimate_ladder_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));back.mkdir();records=[]
  for folder in('sstates','memcards'):
   shutil.copytree(e/folder,back/folder)
   for f in(e/folder).rglob('*'):
    if f.is_file():
     dest=back/f.relative_to(e);assert digest(f)==digest(dest);records.append(dict(path=f.relative_to(R).as_posix(),copy=dest.relative_to(R).as_posix(),sha256=digest(f)))
  (back/'backup.json').write_text(json.dumps(records,indent=2),encoding='utf8')
  subprocess.run([sys.executable,'scripts/emulator_session.py','--project','ver_rin_nana','key','--session',c['current_session'],'--scan','0x3b'],check=True)
  time.sleep(.4);state=e/'sstates/SLUS_005.61.000';dest=back/'current_progress'/state.name;dest.parent.mkdir();shutil.copy2(state,dest);raw=gzip.decompress(dest.read_bytes());anchor=bytes.fromhex('150001000c0001922a0001930c00019436000100');pos=raw.find(anchor)-0x11a2f8;assert pos>0;s=raw[pos+0x1418c8:pos+0x1418c8+228]
  saved=dict(source=dest.relative_to(R).as_posix(),source_sha256=digest(dest),backup=back.relative_to(R).as_posix(),character=s[2],animation=s[0x17],frame=s[0x47],hp=s[0x5c],armor=s[0xa7],ultimate=raw[pos+0x1721f7],world=[struct.unpack_from('<i',s,z)[0]/65536 for z in(8,12)])
  assert ((saved['animation']==5 and saved['frame'] in(0,115,116,117,118,119)) or (saved['animation']==6 and saved['frame'] in range(120,126))),'Saved nonidle'
  now=player();assert all(now[x]==saved[x] for x in('character','hp','armor','ultimate','world')),'Progress changed while saving'
  (D/'ladder_saved_progress.json').write_text(json.dumps(saved,indent=2),encoding='utf8');print(json.dumps(saved))
 k.CloseHandle(h)
