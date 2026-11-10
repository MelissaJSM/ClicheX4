"""원작 금속 HUD 몸체를 가로로 연장하고 기존 심볼을 그 위에 합성한다."""
import argparse,json,sys,struct
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts import hud_frame_fix as base
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_hud_emblems import all_compositions,composed
from scripts.discover_inputs import sha256,psx_arc
from scripts.project import digest
from src.psx_ui_atlas import tile_pixels

SOURCES={'ver_buki_riko':('shibuki_riko','d426ac48b7e8efa7e3e5b879d391efab89fe19993d22b7cb98ae2c08eaff85fd'),
         'ver_rin_nana':('rin_nana','2c3cf873615cab8c84fd7a5dc8a6260d95e6bea26b84de5c87d08651e6ce53dc')}
SYMBOL_SOURCES={'ver_buki_riko':'bcdc219a1fa90ed277eecdf7b28ac196489d3297f49914470bf45e0844db2171',
                'ver_rin_nana':'1a2d97272bb0dde2395aa7f1daa9136dd247125456090ff519fe3c484e3be2e2'}
CONTEXT={}
WHITE_ONLY=False
require=base.require

def load_context():
    original=ROOT/'MegaMan X4.bin';require(digest(original)=='3ceab06ac99add4035f912188bcbf5b16c02056f46a33d38ff0c8dbce6cb613b','Original BIN differs')
    native,_=read_disc(original,base.NAMES)
    for project,(stem,expected)in SOURCES.items():
        current=ROOT/'out'/project/'hud_frame_fix_20261105_v1'/(stem+'.bin')
        symbols=ROOT/'out'/project/'overhaul_20261105_candidate04'/(stem+'.bin')
        require(digest(current)==expected and digest(symbols)==SYMBOL_SOURCES[project],'Source identity changed')
        current_assets,_=read_disc(current,base.NAMES);symbol_assets,_=read_disc(symbols,base.NAMES)
        for name in base.NAMES:
            CONTEXT[sha256(current_assets[name])]=(native[name],symbol_assets[name],project,name)

def desired(before,native,symbol,bounds):
    out=before.copy();left,top,_,_=bounds
    out[24-top:41-top,-24-left:5-left]=0
    for y in range(25,39):
        # Repeat the native flat middle; mirror the native curved right end.
        fill=int(native[y-top,5-left])
        out[y-top,-14-left:5-left]=10 if WHITE_ONLY and fill==14 else fill
        for x in range(-22,-14):
            value=int(native[y-top,(-7-x)-left])
            out[y-top,x-left]=10 if WHITE_ONLY and value==14 else value
    if WHITE_ONLY:
        # Keep the original numeric aperture and its left rim exactly in place.
        out[25-top:39-top,2-left:5-left]=native[25-top:39-top,2-left:5-left]
    # Native upper shoulder joins the vertical gauge to the horizontal body.
    out[24-top,-18-left:3-left]=native[24-top,-18-left:3-left]
    if WHITE_ONLY:
        require(np.array_equal(out[24-top:41-top]==14,native[24-top:41-top]==14),'Native dark life-number aperture changed')
    region=symbol[24-top:41-top,-24-left:2-left]
    dst=out[24-top:41-top,-24-left:2-left];dst[region>0]=region[region>0]
    require(np.array_equal(out[:24-top],before[:24-top]),'Vertical health bar changed')
    require(np.array_equal(out[:,5-left:],before[:,5-left:]),'Life digits/right frame changed')
    require(np.array_equal(dst[region>0],region[region>0]),'Accepted symbol pixels changed')
    # Midline continuity must exist under the symbol, even through its open pixels.
    require(np.all(out[31-top,-20-left:10-left]>0),'Horizontal HUD disconnected')
    return out

def patch(arc):
    require(sha256(arc)in CONTEXT,'Unsupported source ARC')
    original,symbols,project,name=CONTEXT[sha256(arc)]
    tex,parts=entry(arc,0x10206),entry(arc,3);comps=all_compositions(parts)
    native_comps=all_compositions(entry(original,3));symbol_comps=all_compositions(entry(symbols,3))
    users={}
    for key,comp in comps.items():
        for p in comp['parts']:users.setdefault(p['page']*256+p['tile'],set()).add(key)
    demands={};wanted={};tiles=set();frames=[]
    for key in sorted(base.TARGETS):
        a,sz,bb,locations=composed(tex,comps[key]);n,ns,nb,_=composed(entry(original,0x10206),native_comps[key]);s,ss,sb,_=composed(entry(symbols,0x10206),symbol_comps[key])
        require(sz==ns==ss and bb==nb==sb,'Native/emblem geometry differs')
        b=desired(a,n,s,bb);wanted[key]=b
        for y,x in zip(*np.where(a!=b)):
            loc=locations[int(y)*sz[0]+int(x)];require(bool(loc),'Underlay leaves existing parts')
            for j,(off,shift)in enumerate(loc):
                tile=(off//128//16)*16+(off%128)//8;require(users[tile]<=base.TARGETS,'Underlay tile shared outside HUD')
                v=int(b[y,x])if j==len(loc)-1 else 0
                require((off,shift)not in demands or demands[off,shift]==v,'Shared HUD pixel conflict')
                demands[off,shift]=v;tiles.add(tile)
        frames.append(dict(frame=key[1],changed_pixels=int(np.count_nonzero(a!=b)),continuous_midline=True))
    result=bytearray(tex)
    for(off,shift),v in demands.items():result[off]=(result[off]&~(15<<shift))|(v<<shift)
    result=bytes(result);count=struct.unpack_from('<I',parts)[0]//4
    static={1,2,3,4,6}if count==7 else{1,2,3,4,*range(9,count)};checked=0
    for key,c in comps.items():
        if key[0]not in static:continue
        a,sz,bb,_=composed(tex,c);b,ns,nb,_=composed(result,c)
        require(sz==ns and bb==nb and np.array_equal(b,wanted.get(key,a)),'Unintended static frame change '+str(key));checked+=1
    for tile in range(len(tex)//128):
        if tile not in tiles:require(tile_pixels(tex,tile)==tile_pixels(result,tile),'Unrelated tile modified')
    new=replace_entry(arc,0x10206,result)
    for e in psx_arc(arc):
        kind=int(e['type'],16)
        if kind!=0x10206:require(entry(arc,kind)==entry(new,kind),'Nontexture entry modified')
    return new,dict(frames=frames,private_tiles=sorted(tiles),static_frames_checked=checked,
        native_right_cap_mirrored_to_left=True,native_middle_extended_under_symbol=True,
        white_metal_only_extended=WHITE_ONLY,native_number_aperture_preserved=WHITE_ONLY,
        symbol_pixels_preserved=True,life_digits_and_right_frame_preserved=True,
        geometry_palette_timing_audio_and_all_nontexture_entries_unchanged=True)

def configure():
    load_context();base.SOURCES=SOURCES;base.SOURCE_FOLDER='hud_frame_fix_20261105_v1';base.BUILD_KIND='white_metal_extended_under_symbol_original_numeric_aperture'if WHITE_ONLY else'continuous_native_HUD_body_under_foreground_symbol';base.patch=patch

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','build']);p.add_argument('--output',type=Path,required=True);p.add_argument('--project',choices=SOURCES);p.add_argument('--proposal',type=Path);p.add_argument('--white-only',action='store_true');a=p.parse_args();WHITE_ONLY=a.white_only;configure()
    if a.action=='prepare':base.prepare(a.output)
    else:base.build(a.project,a.proposal,a.output)
