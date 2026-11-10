"""Independent PS1 renderer versus decoded Steam static frames and scope checks."""
import json,struct,sys,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.build_steam_selection import render_frame
from src.psx_player import composition_frame,decode_stream
from src.psx_ui_atlas import aliased_composition,write_tile
from src.psx_ui_render import render_static_rgba
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices
W=ROOT/'work/steam_port_20261109'
def sha(b):return hashlib.sha256(b).hexdigest()
def main():
    reports=json.loads((W/'portrait_builds.json').read_text('utf8'));checks=[]
    for r in reports:
        old=SteamArc((W/'original/nativeDX10/X4/romPC'/r['original_target_arc']).read_bytes());new=SteamArc((ROOT/r['output']).read_bytes());new.validate_stream_order()
        assert sha(new.raw)==r['output_sha256'] and list(old.by_key)==list(new.by_key)
        for e in old.entries:
            if e.name not in r['changed_entries']:assert e.payload==new.by_key[e.key].payload
        checks.append({'target':r['target_arc'],'unchanged_resources_exact':True,'entry_names_order_preserved':True})
    count=0
    for mode in ['ver_rin_nana','ver_buki_riko']:
        rr=[r for r in reports if r['mode']==mode];ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
        names=['ST00_00.ARC','COL00_0X.ARC','COL00_0Z.ARC','ST0D_0X.ARC','ST0D_0Z.ARC','COL0D_0X.ARC','COL0D_0Z.ARC'];raw,_=read_disc((ROOT/ptr['cue']).with_suffix('.bin'),names)
        for name,bank,kind,n,texture_suffix,row in [('ST00_00.ARC',11,'x',8,'_012',62),('ST00_00.ARC',13,'z',3,'_013',63),('ST0D_0X.ARC',2,'x',12,'_002',35),('ST0D_0Z.ARC',2,'z',14,'_002',35)]:
            stem=name.lower().replace('.arc','');r=next(q for q in rr if q['original_target_arc'].split('_eng')[0].replace('.arc','')==stem)
            a=SteamArc((ROOT/r['output']).read_bytes());tex=next(e.payload for e in a.entries if e.payload[:4]==b'TEX\0' and e.name.endswith(texture_suffix));pat=pat_frames(next(e.payload for e in a.entries if e.payload[:4]==b'PAT\0'))
            ps=raw[name];pp=entry(ps,10)
            if name=='ST0D_0X.ARC':
                blob=entry(ps,13)[96:];chunks=[]
                for c in range(struct.unpack_from('<I',blob,4)[0]):
                    k,start,off,size=struct.unpack_from('<4I',blob,16+c*16);chunks.append((k,start,decode_stream(blob,off,len(blob),size).data))
                state=next(b for k,s,b in chunks if k==0)[:1412];dictionary=b''.join(b for k,s,b in chunks if k==1);g=bytearray(176*128)
                for t,j in enumerate(struct.unpack('<176H',state[:352])):
                    if j!=65535:write_tile(g,t,unpack_indices(dictionary[j*128:j*128+128]))
                pp=struct.pack('<I',4)+state[352:];psbank=0
            else:
                offset=struct.unpack_from('<I',entry(ps,12),bank*4)[0];g=entry(ps,0x10102)[offset:];psbank=bank
            palname='COL00_0'+kind.upper()+'.ARC' if name=='ST00_00.ARC' else name.replace('ST','COL',1)
            palette=entry(raw[palname],5)[row*32:(row+1)*32];words=struct.unpack('<16H',palette)
            for f in range(n):
                c=aliased_composition(pp,psbank,f);expected,bounds=render_static_rgba(g,c,{0:words});actual=render_frame(tex,pat[bank][f],palette,0)
                assert actual.size==expected.size and actual.tobytes()==expected.tobytes(),(mode,name,f)
                qs=list(struct.iter_unpack('<BBbb',pat[bank][f]));got=(min(q[2] for q in qs),min(q[3] for q in qs),max(q[2]+16 for q in qs),max(q[3]+16 for q in qs));assert got==bounds
                count+=1
    result={'independent_rendered_frames':count,'pixels_geometry_palettes_exact':True,'archives':checks,'live_play_not_covered':True}
    (W/'portrait_static_verification.json').write_text(json.dumps(result,indent=2)+'\n');print({'frames':count,'archives':len(checks)})
if __name__=='__main__':main()
