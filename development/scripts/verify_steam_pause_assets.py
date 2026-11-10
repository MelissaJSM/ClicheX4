"""Compare independently reconstructed PS1/Steam pause and save artwork."""
import json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_pause import W,find,sha,digest,variants
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.prepare_ui_revision import pause_background
from scripts.build_steam_selection import render_frame
from src.psx_ui_atlas import aliased_composition
from src.psx_ui_render import render_static_rgba
from src.steam_arc import SteamArc
from src.steam_ui import pat_frames

def main():
    builds=json.loads((W/'pause_builds.json').read_text('utf8'));parents=json.loads((W/'dialogue_builds.json').read_text('utf8'));reports=[]
    for mode in ('ver_rin_nana','ver_buki_riko'):
        allrows=[r for r in builds if r['mode']==mode];rows=[r for r in allrows if r['target_arc'].startswith('pl')];ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'))
        source=(ROOT/ptr['cue']).with_suffix('.bin');assert digest(source)==ptr['sha256']
        ps,_=read_disc(source,['PL00_U.ARC','PL01_U.ARC','PL02_U.ARC','LOAD_U.ARC','MOJIPAT.ARC'])
        output=(ROOT/rows[0]['output']).parents[3]/'review';output.mkdir(parents=True,exist_ok=True)
        shared=[SteamArc((ROOT/r['output']).read_bytes(),r['output_sha256']) for r in allrows if r.get('shared_x_pause_cache')]
        if shared:
            assert len(shared)==3
            for magic in (b'TEX\0',b'COF\0',b'CTEX'):
                assert len({find(a,'\\wsel\\',magic).payload for a in shared})==1,('Shared cache mismatch',magic)
            assert find(shared[1],'\\wsel\\',b'PAT\0').payload==find(shared[2],'\\wsel\\',b'PAT\0').payload
        board=Image.new('RGB',(4*320,2*265),'#202837');draw=ImageDraw.Draw(board);unique=0;checks=0
        for row in rows:
            arc=SteamArc((ROOT/row['output']).read_bytes(),row['output_sha256']);n=int(row['target_arc'][2:4]);psarc=ps[f'PL{n:02}_U.ARC']
            tex=find(arc,'\\wsel\\',b'TEX\0').payload;pal=find(arc,'\\wsel\\',b'COL\0').payload[12:];parts=pat_frames(find(arc,'\\wsel\\',b'PAT\0').payload)[0]
            cof=find(arc,'\\wsel\\',b'COF\0').payload;cp=17+cof[16]
            assert pal[:1024]==entry(psarc,17)[:1024]
            for k in range(6):
                # Native pause draw adds tile96 to its PAT tile index.
                q=bytearray(parts[38+k])
                for at in range(0,len(q),4):
                    index=((q[at]&3)*256+q[at+1])+96
                    q[at]=(q[at]&~3)|(index//256);q[at+1]=index%256
                ypos=struct.unpack_from('<I',cof,cp+4+(38+k)*4)[0]
                actual=render_frame(tex[:20]+tex[20+ypos*256:],bytes(q),pal,10)
                sourcearc=psarc
                if row.get('shared_x_pause_cache'):sourcearc=ps['PL00_U.ARC' if k<4 else 'PL02_U.ARC']
                comp=aliased_composition(struct.pack('<I',4)+entry(sourcearc,17)[1024:1536],0,k)
                expected,bounds=render_static_rgba(entry(sourcearc,0x10007)[12288:],comp,{i:struct.unpack_from('<16H',pal,(10+i)*32) for i in range(2)})
                assert actual.size==(64,80) and actual.tobytes()==expected.tobytes()
                assert bounds==(-32,-48,32,32) or list(bounds)==[-32,-48,32,32],bounds
                assert sum(v>0 for v in actual.getchannel('A').getdata())==3388
                checks+=1
                if k not in ({0,1,2,3} if n==0 else {0,1} if n==1 else {4,5}):continue
                preview=pause_background(psarc);preview.alpha_composite(actual,(32,144));preview.save(output/f'pause_pl{n:02}_{k}.png')
                x=unique%4*320;y=unique//4*265;board.paste(preview,(x,y+25));draw.text((x+8,y+5),f'PL{n:02} state{k}',fill='white');unique+=1
        board.save(output/'pause_comparison.png')
        loadrow=next(r for r in allrows+parents if r['mode']==mode and r['target_arc'].startswith('load'))
        load=SteamArc((ROOT/loadrow['output']).read_bytes(),loadrow['output_sha256'])
        textures=[e.payload for e in load.entries if '\\loading\\'in e.name and e.payload[:4]==b'TEX\0']
        bank=pat_frames(find(load,'\\loading\\',b'PAT\0').payload)[0];col=next(e.payload[12:]for e in load.entries if e.payload[:4]==b'COL\0')
        moji=ps['MOJIPAT.ARC'];off=struct.unpack_from('<4I',moji);expected_pal=moji[off[1]:off[2]];save_checks=0
        saveboard=Image.new('RGB',(6*180,220),'#202837');sd=ImageDraw.Draw(saveboard)
        for f,p in [(43,8),(43,27),(44,8),(45,8),(46,8),(47,8),(47,10),(48,8),(52,30),(53,31)]:
            comp=aliased_composition(moji,2,f)
            expected,_=render_static_rgba(entry(ps['LOAD_U.ARC'],0x10008),comp,{i:struct.unpack_from('<16H',expected_pal,(p+i)*32) for i in range(4) if p+i<32})
            for tex in textures:
                actual=render_frame(tex,bank[f],col,p)
                assert actual.size==expected.size and actual.tobytes()==expected.tobytes(),(mode,f,p)
                save_checks+=1
            if (f,p) in [(43,8),(43,27),(44,8),(52,30),(53,31)]:
                index=[(43,8),(43,27),(44,8),(52,30),(53,31)].index((f,p))
                im=actual.resize((actual.width*3,actual.height*3),Image.Resampling.NEAREST)
                saveboard.paste(im,(index*180+(180-im.width)//2,30),im);sd.text((index*180+6,8),f'Frame {f} / palette {p}',fill='white')
        saveboard.save(output/'save_comparison.png')
        reports.append({'mode':mode,'pause_rendered_frames':checks,'save_rendered_frames':save_checks,'pause_mask_pixels_each':3388,'original_widget_geometry_preserved':True,'pixels_and_palette_match_ps1':True,'shared_load_pl00_pl02_textures_cof_ctex_identical':bool(shared),'review':output.relative_to(ROOT).as_posix(),'runtime_scene_verified':False})
    (W/'menu_outfits_static_verification.json').write_text(json.dumps(reports,indent=2)+'\n');print(reports)
if __name__=='__main__':main()
