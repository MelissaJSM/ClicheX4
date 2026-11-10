"""Read-only emulator RAM discovery using five exact native executable anchors."""
from pathlib import Path
import argparse,json,sys,ctypes,hashlib
from ctypes import wintypes
R=Path(__file__).resolve().parent;ROOT=R.parents[2];sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
from scripts.capture_poc_memory import Region
from scripts.audit_sprite_consistency_coverage import read_assets,exe_slice
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--session',type=Path,required=True);p.add_argument('--sha256',required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();session=a.session.resolve();out=a.output.resolve();assert not out.exists()and out.is_relative_to(R)
rec=json.loads((session/'session.local.json').read_text('utf8'));cue=Path(rec['cue']);game=cue.with_suffix('.bin');assert sha(game)==rec['bin_sha256']==a.sha256
exe=read_assets(game,['SLUS_005.61'])[0]['SLUS_005.61'];anchors=[0x1540c,0x15ecc,0x233c8,0x23400,0xea20c];needles={n:exe_slice(exe,n|0x80000000,48)for n in anchors}
proc=ReadOnlyProcess(rec);k=proc.k;k.VirtualQueryEx.argtypes=[wintypes.HANDLE,ctypes.c_void_p,ctypes.POINTER(Region),ctypes.c_size_t];candidates=set();scanned=0
try:
 address=0
 while address<0x80000000:
  region=Region()
  if not k.VirtualQueryEx(proc.h,address,ctypes.byref(region),ctypes.sizeof(region)):break
  start=region.base or 0;end=start+region.size
  if end<=address:break
  if region.state==0x1000 and not region.protect&0x100 and region.protect&0xff in (2,4,8,0x20,0x40,0x80):
   for offset in range(start,min(end,0x80000000),1024*1024):
    try:blob=proc.read(offset,min(1024*1024+48,end-offset))
    except (ValueError,OSError):continue
    scanned+=len(blob);at=blob.find(needles[anchors[0]])
    while at>=0:
     base=offset+at-anchors[0]
     if base>0:
      try:
       if all(proc.read(base+n,48)==needle for n,needle in needles.items()):candidates.add(base)
      except (ValueError,OSError):pass
     at=blob.find(needles[anchors[0]],at+1)
  address=end
finally:proc.close()
assert len(candidates)==1,sorted(candidates)
report={'session':str(a.session),'pid':rec['pid'],'disc_sha256':a.sha256,'ram_base':next(iter(candidates)),'five_native_anchors_exact':True,'bytes_scanned':scanned,'memory_written':False,'keys_sent':False}
out.write_text(json.dumps(report,indent=2)+'\n','utf8');print(json.dumps(report))
