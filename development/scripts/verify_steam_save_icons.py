"""Audit all saved weapon/item icons against the native shared atlas addresses."""
import argparse,json,struct,sys
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.build_steam_pause import W,find,digest
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.build_steam_selection import render_frame
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import unpack_indices
from src.steam_ui import pat_frames

ICON_ROWS=list(range(12,20))+[20,20,21,22,23,22,23,21]+[24,24,25,26]
def shifted(frame,tiles):
    result=bytearray()
    for flags,t,x,y in struct.iter_unpack('<BBbb',frame):
        index=(flags&3)*256+t+tiles
        result.extend(struct.pack('<BBbb',(flags&~3)|(index//256),index%256,x,y))
    return bytes(result)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--expect-corruption',action='store_true');a=p.parse_args()
    rows=json.loads((W/'pause_builds.json').read_text('utf8'));reports=[];failures=[]
    for mode in ('ver_rin_nana','ver_buki_riko'):
        mine=[r for r in rows if r['mode']==mode]
        lr=next(r for r in mine if r['target_arc'].startswith('load'))
        arc=SteamArc((ROOT/lr['output']).read_bytes(),lr['output_sha256'])
        ptr=json.loads((ROOT/'projects'/mode/'current_build.json').read_text('utf8'));source=(ROOT/ptr['cue']).with_suffix('.bin');assert digest(source)==ptr['sha256']
        ps,_=read_disc(source,['LOAD_U.ARC','MOJIPAT.ARC']);moji=ps['MOJIPAT.ARC'];off=struct.unpack_from('<4I',moji)
        pat=find(arc,'\\icon\\',b'PAT\0').payload
        assert pat==pat_from_ps1(struct.pack('<I',4)+moji[off[3]:])
        bank=pat_frames(pat)[0];assert len(bank)==20
        tex=find(arc,'\\wsel\\',b'TEX\0').payload;cof=find(arc,'\\wsel\\',b'COF\0').payload;cp=17+cof[16]
        pal=next(e.payload[12:]for e in arc.entries if e.payload[:4]==b'COL\0')
        ps_tex=tex[:20]+unpack_indices(entry(ps['LOAD_U.ARC'],0x10007));ps_pal=moji[off[1]:off[2]]
        board=Image.new('RGB',(800,480),'#202837');draw=ImageDraw.Draw(board);bad=[]
        for n,frame in enumerate(bank):
            # Native initializer A66027 sets virtual tile1DE0. The WSX page
            # resolver removes1D00, leaving physical tile224 for icon frame0.
            q=shifted(frame,224);yoff=struct.unpack_from('<I',cof,cp+4+n*4)[0]
            actual=render_frame(tex[:20]+tex[20+yoff*256:],q,pal,ICON_ROWS[n])
            expected=render_frame(ps_tex,q,ps_pal,ICON_ROWS[n])
            same=actual.size==expected.size and actual.tobytes()==expected.tobytes()
            if not same:bad.append(n);failures.append([mode,n])
            x=n%5*160;y=n//5*120;draw.text((x+4,y+3),f'{n}: PS1 / Steam',fill='white')
            for j,im in enumerate((expected,actual)):
                im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);board.paste(im,(x+4+j*76,y+30),im)
        folder=(ROOT/lr['output']).parents[3]/'review';folder.mkdir(exist_ok=True);board.save(folder/'save_icons_comparison.png')
        # All copies that can become the cached WSX texture must reproduce it.
        for r in mine:
            if not r.get('shared_x_pause_cache'):continue
            other=SteamArc((ROOT/r['output']).read_bytes(),r['output_sha256'])
            assert find(other,'\\wsel\\',b'TEX\0').payload==tex
            assert find(other,'\\wsel\\',b'COF\0').payload==cof
        reports.append({'mode':mode,'icons':20,'mismatched_frames':bad,'cof_icon_offsets_zero':not any(struct.unpack_from('<20I',cof,cp+4)),'native_icon_pat_preserved':True,'review':(folder/'save_icons_comparison.png').relative_to(ROOT).as_posix()})
    out=W/'save_issue_20261109'/('v2_icon_reproduction.json' if a.expect_corruption else 'icon_verification.json');out.parent.mkdir(exist_ok=True)
    report={'expected_corruption':a.expect_corruption,'native_icon_base':'0x1de0','atlas_tiles':[224,246],'results':reports,'mismatch_count':len(failures),'runtime_scene_verified':False}
    out.write_text(json.dumps(report,indent=2)+'\n');print(report)
    if a.expect_corruption:assert failures,'Reported corruption was not reproduced'
    else:assert not failures,failures
if __name__=='__main__':main()
