from pathlib import Path
import json, struct, sys, subprocess, hashlib
R=Path(__file__).resolve().parent
ROOT=R.parents[2]
sys.path.insert(0,str(ROOT))
from scripts.observe_sprite_consistency_runtime import ReadOnlyProcess
S=ROOT/'work/ver_buki_riko/emulator_sessions/20261108T014333879732Z'
rec=json.loads((S/'session.local.json').read_text('utf8'))
check=json.loads(subprocess.check_output([sys.executable,str(R/'read_menu_br31.py'),'--session',str(S),'--pid',str(rec['pid']),'--ram-base','19537440'],text=True,encoding='utf8'))
assert check['passed'] and check['engine']['stage']==4
p=ReadOnlyProcess(rec)
try: ram=p.read(19537440,2097152)
finally:p.close()
hits=[]
for address in (0x8010caf4,0x8010cad4,0x8010cacc):
    needle=struct.pack('<I',address); off=0
    while (off:=ram.find(needle,off))>=0:
        hits.append({'pointer':hex(address),'offset':hex(off),'before80_hex':ram[max(0,off-80):off+80].hex()})
        off+=4
dest=R/sys.argv[1]
assert not dest.exists() and dest.suffix=='.json'
dest.write_text(json.dumps({'check':check,'ram_sha256':hashlib.sha256(ram).hexdigest(),'pointer_hits':hits,'memory_written':False},indent=2)+'\n','utf8')
print(json.dumps(hits))
