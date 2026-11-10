"""Append Ultimate portrait frames while preserving accepted normal/Force art."""
import importlib.util,json,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_portraits import digest,sha,write,W
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.inspect_steam_portraits import frames
from scripts.build_steam_selection import render_frame
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames
from src.steam_portraits import pack,encode_banks
from src.steam_player import unpack_indices
from src.psx_ui_render import render_static_rgba
from src.psx_player import composition_frame
from src.psx_ui_atlas import aliased_composition

def main():
    parents_file=W/'portrait_v1_builds.json'
    if not parents_file.exists():parents_file.write_bytes((W/'portrait_builds.json').read_bytes())
    parents=json.loads(parents_file.read_text('utf8'));output=[];palettes={};checks=0
    old,_=read_disc(ROOT/'MegaMan X4.bin',['ST00_00.ARC']);oldp=frames(entry(old['ST00_00.ARC'],10))[11];oldpx=unpack_indices(entry(old['ST00_00.ARC'],0x10102)[204800:217088])
    spec=importlib.util.spec_from_file_location('black_source',ROOT/'work/illustration_variants_20261108/black_ui.py');black=importlib.util.module_from_spec(spec);spec.loader.exec_module(black)
    for mode,short in [('ver_rin_nana','rn'),('ver_buki_riko','br')]:
        ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));game=(ROOT/ptr['cue']).with_suffix('.bin')
        if digest(game)!=ptr['sha256']:raise ValueError('PS1 input differs')
        raw,_=read_disc(game,['ST00_00.ARC','COL00_0X.ARC','COL00_0Z.ARC','SLUS_005.61']);r=raw['ST00_00.ARC'];p=entry(r,10);start=struct.unpack_from('<I',entry(r,12),44)[0];g=entry(r,0x10102)[start:]
        private=struct.unpack_from('<I',p,44)[0]+1376;up=struct.pack('<I',4)+p[private:];uf=frames(up)[0];fr=frames(p)[11]+[uf[i] for i in [0,1,4,5]]
        xpal=entry(raw['COL00_0X.ARC'],5)[62*32:63*32];zpal=entry(raw['COL00_0Z.ARC'],5)[63*32:64*32];other=bytearray(zpal)
        helper=black.palette_helper(mode)
        if raw['SLUS_005.61'][black.off(0x800ca048):black.off(0x800ca048)+len(helper)]!=helper:raise ValueError('Black palette source helper changed')
        for idx,(red,green,blue) in black.CHANGES[mode].items():
            word=struct.unpack_from('<H',other,idx*2)[0];struct.pack_into('<H',other,idx*2,(word&0x8000)|red|green<<5|blue<<10)
        palettes[short]={'normal_hex':zpal.hex(),'black_hex':other.hex()}
        outdir=ROOT/'out'/mode/'steam_dialogue_variants_20261109_v1';review=outdir/'review';review.mkdir(parents=True,exist_ok=True)
        for parent in [q for q in parents if q['mode']==mode]:
            if 'st0d_0' in parent['original_target_arc']:output.append(parent);continue
            src=(ROOT/parent['output']).read_bytes()
            if sha(src)!=parent['output_sha256']:raise ValueError('Portrait parent changed')
            arc=SteamArc(src);orig=SteamArc((W/'original/nativeDX10/X4/romPC'/parent['original_target_arc']).read_bytes());updates={}
            tx=next(e.payload for e in orig.entries if e.payload[:4]==b'TEX\0' and e.payload[20:20+len(oldpx)]==oldpx) if any(e.payload[:4]==b'TEX\0' and e.payload[20:20+len(oldpx)]==oldpx for e in orig.entries) else None
            if tx is None:
                template=SteamArc((W/'original/nativeDX10/X4/romPC/st00_00.arc').read_bytes());tx=next(e.payload for e in template.entries if e.payload[:4]==b'TEX\0' and e.payload[20:20+len(oldpx)]==oldpx)
            tex,packed=pack(tx,fr,unpack_indices(g))
            for e in orig.entries:
                if e.payload[:4]==b'TEX\0' and e.payload[20:20+len(oldpx)]==oldpx:updates[e.key]=e.payload[:8]+tex[8:]
                elif e.payload[:4]==b'PAT\0':
                    originalbanks=pat_frames(e.payload);banks=pat_frames(arc.by_key[e.key].payload);changed=False
                    for n,b in enumerate(originalbanks):
                        if b==oldp:banks[n]=packed;changed=True
                    if changed:updates[e.key]=encode_banks(banks)
            result=arc.rebuild(updates);SteamArc(result).validate_stream_order();dest=outdir/'nativeDX10/X4/romPC'/parent['target_arc'];dest.parent.mkdir(parents=True,exist_ok=True)
            if dest.exists() and dest.read_bytes()!=result:raise ValueError('Output collision')
            dest.write_bytes(result);output.append({**parent,'output':dest.relative_to(ROOT).as_posix(),'output_sha256':sha(result),'parent_sha256':sha(src),'dialogue_ultimate_frames':4,'runtime_verified':False})
            if parent['original_target_arc'].startswith('st00_00'):
                for f,rec in enumerate(packed):
                    c=aliased_composition(p,11,f) if f<8 else composition_frame(up,0,[0,1,4,5][f-8]);expected,bb=render_static_rgba(g,c,{0:struct.unpack('<16H',xpal)});im=render_frame(tex,rec,xpal,0)
                    if im.size!=expected.size or im.tobytes()!=expected.tobytes():raise ValueError('Dialogue rendered art differs')
                    im.save(review/f'x_{f:02}.png');checks+=1
    write(W/'portrait_builds.json',output)
    routes=json.loads((W/'portrait_routes.json').read_text('utf8'))
    if not (W/'portrait_v1_routes.json').exists():write(W/'portrait_v1_routes.json',routes)
    routes['requirements']={'nativeDX10/X4/romPC/'+r['target_arc']:r['output_sha256'] for r in output}
    for r in routes['routes']:r['sha256']=next(q['output_sha256'] for q in output if q['target_arc']==r['private_arc'])
    write(W/'portrait_routes.json',routes);write(W/'dialogue_variant_runtime.json',{'installed_requirements':routes['requirements'],'zero_palettes':palettes,'native_animation_table':0x1adb108,'extra_frames':{'before_closed':8,'after_closed':9,'before_open':10,'after_open':11},'independent_frame_checks':checks})
    print({'updated_archives':len(output)-4,'extra_unique_frames':8,'independent_frame_checks':checks})
if __name__=='__main__':main()
