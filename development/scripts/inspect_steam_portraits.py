"""Read-only correspondence audit for stage portrait PAT and split textures."""
import json, struct, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.discover_inputs import DiscReader,psx_arc
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_ui_atlas import aliased_composition
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
W=ROOT/'work/steam_port_20261109';D=W/'portraits_research';D.mkdir(exist_ok=True)

def frames(p):
    banks=[]
    for b in range(struct.unpack_from('<I',p)[0]//4):
        c=aliased_composition(p,b,0);bank=[]
        for f in range(c['bank_frame_count']):
            c=aliased_composition(p,b,f)
            bank.append(b''.join(p[q['record_offset']:q['record_offset']+4] for q in c['parts']))
        banks.append(bank)
    return banks

def main():
    with (ROOT/'MegaMan X4.bin').open('rb') as s:
        r=DiscReader(s,(ROOT/'MegaMan X4.bin').stat().st_size)
        names=[x['name'].split(';')[0] for x in r.inspect()['files'] if not x['directory'] and x['name'].startswith(('ST','COL')) and '.ARC' in x['name']]
    raw,_=read_disc(ROOT/'MegaMan X4.bin',names)
    pats={};slices=[]
    for name,b in raw.items():
        kinds={int(e['type'],16) for e in psx_arc(b)}
        if 10 in kinds:
            try:pats[name]=frames(entry(b,10))
            except ValueError:pass
        if 12 not in kinds:continue
        table=entry(b,12)
        for kind in kinds:
            if kind>>16!=1:continue
            g=entry(b,kind)
            offsets=list(struct.unpack('<'+'I'*(len(table)//4),table))
            if any(x>len(g) for x in offsets):continue
            for bank,lo in enumerate(offsets):
                hi=min((v for v in offsets if v>lo),default=len(g))
                if hi>lo:slices.append((name,kind,bank,lo,hi,unpack_indices(g[lo:hi])))
    results=[]
    for p in sorted((W/'original/nativeDX10/X4/romPC').glob('st*.arc')):
        a=SteamArc(p.read_bytes());record={'arc':p.name,'pat':[],'textures':[]}
        for e in a.entries:
            if e.payload[:4]==b'PAT\0':
                try:fr=pat_frames(e.payload)
                except ValueError:continue
                matches=[n for n,v in pats.items() if v==fr]
                record['pat'].append({'name':e.name,'sources':matches,'banks':len(fr)})
            if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name:
                hits=[{'arc':n,'kind':k,'bank':bi,'lo':lo,'hi':hi} for n,k,bi,lo,hi,g in slices if len(g)<=len(e.payload)-20 and e.payload[20:20+len(g)]==g and len(g)>1024]
                record['textures'].append({'name':e.name,'sources':hits})
        results.append(record)
    (D/'correspondence.json').write_text(json.dumps(results,indent=2)+'\n')
    for q in results:
        if q['pat'] and q['pat'][0]['sources'] and any(n in q['pat'][0]['sources'] for n in ['ST00_00.ARC','ST00_01.ARC','ST09_00.ARC','ST0A_00.ARC','ST0B_00.ARC','ST0B_01.ARC','ST0B_0X.ARC','ST0C_01.ARC','ST0C_U1.ARC','ST0D_0X.ARC','ST0D_0Z.ARC']):
            print(q['arc'],q['pat'],[(t['name'].split('\\')[-1],len(t['sources'])) for t in q['textures']])
if __name__=='__main__':main()
