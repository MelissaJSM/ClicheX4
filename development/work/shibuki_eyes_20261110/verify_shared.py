import json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from audit import find,D,sha
from scripts.build_steam_selection import render_frame
from scripts.verify_steam_get_boss import render_background
import numpy as np
W=ROOT/'work/steam_port_20261109';rows=json.loads((W/'shibuki_eyes_builds.json').read_text('utf8'));pairs={r['target_arc']:(SteamArc((D/'before'/r['target_arc']).read_bytes()),SteamArc((ROOT/r['output']).read_bytes()))for r in rows}
results={}
a,b=pairs['st0e_01_eng.arc'];ts=sorted([e for e in a.entries if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name],key=lambda e:e.name);t=ts[1];p=find(a,b'COL\0','\\stage\\col\\').payload[12:];bs=pat_frames(find(a,b'PAT\0','').payload)
changed=[]
for n,r in enumerate(bs[1]):
    if not r:continue
    x=render_frame(t.payload,r,p,4);y=render_frame(b.by_key[t.key].payload,r,p,4)
    if x.tobytes()!=y.tobytes():changed.append(n)
assert changed==[0],changed;results['selection_changed_frames_only']=changed
results['background_screens']={}
for name in ('st0f_0x_eng.arc','st0f_0z_eng.arc','st0e_00_eng.arc'):
    a,b=pairs[name];changed=[];mp=find(a,b'OMP\0','')
    for n in range((len(mp.payload)-12)//512):
        x=render_background(a,n);y=render_background(b,n)
        if x.tobytes()!=y.tobytes():changed.append(n)
    assert changed==([6]if name.startswith('st0e')else[5]),(name,changed)
    results['background_screens'][name]=changed
results['pause_changed_frames']={}
for name in ('pl00_eng.arc','pl02_eng.arc'):
    a,b=pairs[name];t=find(a,b'TEX\0','\\wsel\\');p=find(a,b'COL\0','\\wsel\\').payload[12:];bs=pat_frames(find(a,b'PAT\0','\\wsel\\').payload)[0];c=find(a,b'COF\0','\\wsel\\').payload;at=17+c[16];changed=[]
    for n,r in enumerate(bs):
        if not r:continue
        r=bytearray(r)
        for j in range(0,len(r),4):
            tid=(r[j]&3)*256+r[j+1]+96;r[j]=(r[j]&~3)|(tid//256);r[j+1]=tid%256
        offset=struct.unpack_from('<I',c,at+4+n*4)[0]*256
        x=render_frame(t.payload[:20]+t.payload[20+offset:],r,p,10);v=b.by_key[t.key].payload;y=render_frame(v[:20]+v[20+offset:],r,p,10)
        if x.tobytes()!=y.tobytes():changed.append(n)
    assert changed==list(range(38,44)),(name,changed);results['pause_changed_frames'][name]=changed
results['passed']=True;(D/'shared_resource_verification.json').write_text(json.dumps(results,indent=2)+'\n');print(results)
