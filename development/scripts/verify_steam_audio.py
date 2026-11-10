"""Independently verify the cumulative audio assets and native intro branch."""
from pathlib import Path
import sys,json,hashlib,struct,re
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from src.steam_audio import bank_records,sequence_events,stream_records,wave_info
from unicorn import Uc,UC_ARCH_X86,UC_MODE_32,UC_HOOK_CODE
from unicorn.x86_const import *
W=ROOT/'work/steam_port_20261109';O=W/'original'
def sha(b):return hashlib.sha256(b).hexdigest()

def main():
 builds=json.loads((W/'audio_builds.json').read_text());files={r['relative_path']:(ROOT/r['output']).read_bytes() for r in builds}
 assert json.loads((W/'audio/xaudio_format_verification.json').read_text())['passed']
 assert all(sha(files[r['relative_path']])==r['output_sha256'] for r in builds)
 parents={r['target_arc']:r for r in json.loads((W/'audio/parents_pause_v3.json').read_text())};graphics=0;references=0
 for rel,b in files.items():
  if rel.endswith('.arc'):
   a=SteamArc(b);a.validate_stream_order()
   if Path(rel).name in parents:
    p=parents[Path(rel).name];old=SteamArc((ROOT/p['output']).read_bytes(),p['output_sha256'])
    assert set(old.by_key)==set(a.by_key)
    for e in old.entries:
     if '\\sound\\' not in e.name: assert a.by_key[e.key].payload==e.payload;graphics+=1
   else:
    old=SteamArc((O/rel).read_bytes())
    for e in old.entries:
     if '\\sound\\' not in e.name and e.payload[:4]!=b'RLST': assert a.by_key[e.key].payload==e.payload;graphics+=1
   # Resolve all bank waveform paths in the final archive or original loose files.
   for e in a.entries:
    if e.payload[:4]!=b'SBKR':continue
    for name,at,record in bank_records(e.payload):
     matches=[x for x in a.entries if x.name==name and x.payload[:4]==b'RIFF']
     external='nativeDX10/'+name.replace('\\','/')+'.xsew'
     sample=matches[0].payload if matches else files.get(external,(O/external).read_bytes())
     wave_info(sample);references+=1
   if Path(rel).name.startswith(('st','onpare')):
    jp=SteamArc((O/rel.replace('_eng','')).read_bytes())
    assert all(a.by_key[e.key].payload==e.payload for e in jp.entries if '\\sound\\' in e.name)
  elif rel.endswith('.stqr'):
   old=(O/rel).read_bytes();mask=bytearray(len(b));original=stream_records(old)
   for row in stream_records(b):
    clip='nativeDX10/'+row['name'].replace('\\','/')+'.sngw'
    payload=files.get(clip,(O/clip).read_bytes());assert row['size']==len(payload)
    if clip in files:
     for i in range(row['offset']+4,row['offset']+36):mask[i]=1
    else:assert row==original[(row['offset']-56)//36]
   assert len(old)==len(b) and all(x==y or mask[i] for i,(x,y) in enumerate(zip(old,b)))
 # Execute native intro selection with real tables, stubbing only external APIs.
 text=(W/'runtime/code/text.bin').read_bytes();exe=(O/'RXC1.exe').read_bytes()
 assert sha(text)=='38ff6b3ca58e7f4119b8ff5082bd0ad68429134eb90ffd3074da77341148e6cc'
 at=0x987ec9;original=text[at-0x401000:at-0x401000+2];assert original==bytes.fromhex('725e')
 table=exe[0x1ada510-0x401200:0x1ada510-0x401200+39]
 u=Uc(UC_ARCH_X86,UC_MODE_32);u.mem_map(0x400000,0x1c00000);u.mem_write(0x401000,text);u.mem_write(0x1ada510,table)
 u.mem_map(0x3000000,0x20000);stack=0x301f000;stop=0x3000010;obj=0x3001000
 calls=[];region=0;rng=0
 def intercept(m,a,n,d):
  pops={0x75e840:4,0x97a440:0,0x97aca0:0,0x988160:4,0x97f080:0,0x97f060:0,0x9863d0:4,0x7d50d0:4}
  if a not in pops:return
  sp=m.reg_read(UC_X86_REG_ESP);ret=struct.unpack('<I',m.mem_read(sp,4))[0]
  arg=struct.unpack('<I',m.mem_read(sp+4,4))[0]
  if a==0x75e840:m.reg_write(UC_X86_REG_EAX,region)
  elif a==0x97aca0:m.reg_write(UC_X86_REG_EAX,rng)
  elif a in (0x988160,0x9863d0,0x7d50d0):calls.append((a,arg))
  else:m.reg_write(UC_X86_REG_EAX,obj+512)
  m.reg_write(UC_X86_REG_ESP,sp+4+pops[a]);m.reg_write(UC_X86_REG_EIP,ret)
 u.hook_add(UC_HOOK_CODE,intercept)
 def run(patch,boss):
  u.mem_write(at,b'\x90\x90' if patch else original);u.ctl_remove_cache(0x987e60,0x987f60)
  u.mem_write(stack,struct.pack('<II',stop,boss));u.reg_write(UC_X86_REG_ESP,stack);u.reg_write(UC_X86_REG_ECX,obj)
  u.reg_write(UC_X86_REG_ESI,0x11223344);u.reg_write(UC_X86_REG_EBX,0x55667788);calls.clear()
  u.emu_start(0x987e60,stop,count=1000)
  assert u.reg_read(UC_X86_REG_ESP)==stack+8 and u.reg_read(UC_X86_REG_ESI)==0x11223344 and u.reg_read(UC_X86_REG_EBX)==0x55667788
  return list(calls)
 cases=0
 for region in (0,1,2):
  for boss in range(13):
   for rng in range(256):
    old=run(False,boss);new=run(True,boss)
    if region==1 or boss>=8:assert old==new
    else:
     assert not any(a==0x988160 for a,v in old)
     assert new==[(0x988160,table[boss*3+rng%3]),(0x9863d0,1),(0x7d50d0,0)]
    cases+=1
 result={'passed':True,'files':len(files),'preserved_nonaudio_entries':graphics,'resolved_wave_references':references,'native_intro_cases':cases,'patch_address':hex(at),'before':original.hex(),'after':'9090','playing_completion_function_preserved':True,'actual_game_audio_heard':False}
 (W/'audio/independent_verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
