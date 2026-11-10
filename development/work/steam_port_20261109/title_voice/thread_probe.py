"""Briefly sample verified RXC1 threads; never write process memory."""
from pathlib import Path
import ctypes,struct,json,sys,subprocess,time
from ctypes import wintypes as T
R=Path(__file__).resolve().parents[3];sys.path.insert(0,str(R))
from scripts.steam_runtime import game_window
D=Path(__file__).parent
_,(_,pid,_)=game_window()
k=ctypes.WinDLL('kernel32',use_last_error=True)
k.OpenProcess.argtypes=[T.DWORD,T.BOOL,T.DWORD];k.OpenProcess.restype=T.HANDLE
k.OpenThread.argtypes=[T.DWORD,T.BOOL,T.DWORD];k.OpenThread.restype=T.HANDLE
k.ReadProcessMemory.argtypes=[T.HANDLE,ctypes.c_void_p,ctypes.c_void_p,ctypes.c_size_t,ctypes.POINTER(ctypes.c_size_t)]
k.Wow64GetThreadContext.argtypes=[T.HANDLE,ctypes.c_void_p]
k.SuspendThread.argtypes=[T.HANDLE];k.ResumeThread.argtypes=[T.HANDLE];k.CloseHandle.argtypes=[T.HANDLE]
h=k.OpenProcess(0x410,False,pid)
def read(a,n):
 b=ctypes.create_string_buffer(n);got=ctypes.c_size_t()
 return b.raw if a and k.ReadProcessMemory(h,a,b,n,ctypes.byref(got)) and got.value==n else b''
def u32(a):
 b=read(a,4);return struct.unpack('<I',b)[0] if len(b)==4 else 0
rows=[]
ids=json.loads(subprocess.run(['powershell','-NoProfile','-Command',f'@((Get-Process -Id {pid}).Threads | ForEach-Object {{$_.Id}}) | ConvertTo-Json -Compress'],capture_output=True,text=True,check=True).stdout)
try:
 for tid in ids:
  t=k.OpenThread(0x4a,False,tid)
  if not t:continue
  suspended=False
  try:
   previous=k.SuspendThread(t)
   if previous==0xffffffff:continue
   suspended=True
   buf=ctypes.create_string_buffer(716);struct.pack_into('<I',buf,0,0x10007)
   if not k.Wow64GetThreadContext(t,buf):continue
   regs={name:struct.unpack_from('<I',buf,off)[0] for name,off in [('edi',156),('esi',160),('ebx',164),('edx',168),('ecx',172),('eax',176),('ebp',180),('eip',184),('esp',196)]}
   stack=read(regs['esp'],1024)
   candidates=[hex(v[0]) for v in struct.iter_unpack('<I',stack) if 0x401000<=v[0]<=0xf00000]
   rows.append({'tid':tid,'prior_suspend':previous,'regs':{n:hex(v) for n,v in regs.items()},'image_stack_candidates':candidates[:45]})
  finally:
   if suspended:k.ResumeThread(t)
   k.CloseHandle(t)
 engine=u32(0x1b9b140);audio=u32(0x1b9b3ac);app=u32(0x1b43a08)
 report={'pid':pid,'write_process_memory':False,'engine':hex(engine),'audio':hex(audio),'app':hex(app),
  'region_bytes':read(app+0x78,8).hex(),'audio_words':[hex(v[0]) for v in struct.iter_unpack('<I',read(audio,128))],
  'threads':rows}
 out=D/(sys.argv[1] if len(sys.argv)>1 else 'threads_black.json')
 out.write_text(json.dumps(report,indent=2),'utf8')
 print(json.dumps({**report,'threads':[r for r in rows if len(r['image_stack_candidates'])>2]}))
finally:k.CloseHandle(h)
