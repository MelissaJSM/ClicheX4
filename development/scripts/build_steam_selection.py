"""Port accepted selection sprites/portraits/names/background to both regions."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from src.psx_player import composition_frame
from src.psx_ui_atlas import tile_pixels,write_tile
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_player import static_texture
from src.steam_ui import stage_texture,pat_frames

WORK=ROOT/'work/steam_port_20261109'


def sha(b):return hashlib.sha256(b).hexdigest()


def digest(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()


def render_frame(tex,records,palette,base_row):
    parts=[struct.unpack_from('<BBbb',records,i) for i in range(0,len(records),4)]
    if not parts:return Image.new('RGBA',(1,1))
    left,top=min(p[2] for p in parts),min(p[3] for p in parts)
    right,bottom=max(p[2]+16 for p in parts),max(p[3]+16 for p in parts)
    result=Image.new('RGBA',(right-left,bottom-top))
    atlas=np.frombuffer(tex[20:],np.uint8).reshape(-1,256)
    for flags,tile,x,y in parts:
        if flags&0x30:raise ValueError('Unsupported PAT flags')
        index=(flags&3)*256+tile
        a=atlas[index//16*16:index//16*16+16,index%16*16:index%16*16+16]
        if flags&64:a=np.fliplr(a)
        if flags&128:a=np.flipud(a)
        words=struct.unpack_from('<16H',palette,(base_row+(flags>>2&3))*32)
        colors=np.array([[(w>>s&31)*255//31 for s in (0,5,10)]+[255 if i else 0] for i,w in enumerate(words)],np.uint8)
        im=Image.fromarray(colors[a]);result.paste(im,(x-left,y-top),im)
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--version',choices=['v1','v2','v3'],default='v1')
    args=parser.parse_args()
    inv=json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf8'))
    us_path=ROOT/'MegaMan X4.bin'
    if digest(us_path)!=inv['ps1_original']['sha256']:raise ValueError('Unsupported US source')
    us,_=read_disc(us_path,['ST0E_U1.ARC','COL0E_U1.ARC'])
    jp_path=ROOT/'Rockman X4.bin';jp_hash=digest(jp_path)
    jp,_=read_disc(jp_path,['ST0E_01.ARC','COL0E_01.ARC'])
    original=us['ST0E_U1.ARC'];pal_original=entry(us['COL0E_U1.ARC'],5)
    reports=[]
    for mode,suffix,native,native_col in [('ver_rin_nana','',jp['ST0E_01.ARC'],jp['COL0E_01.ARC']),
                                        ('ver_buki_riko','_eng',original,us['COL0E_U1.ARC'])]:
        pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text(encoding='utf8'))
        source_bin=(ROOT/pointer['cue']).with_suffix('.bin')
        if digest(source_bin)!=pointer['sha256']:raise ValueError('Current PS1 source mismatch')
        assets,_=read_disc(source_bin,['ST0E_U1.ARC','COL0E_U1.ARC'])
        source=assets['ST0E_U1.ARC'];pal_source=entry(assets['COL0E_U1.ARC'],5)
        target='st0e_01'+suffix+'.arc'
        arc=SteamArc((WORK/'original/nativeDX10/X4/romPC'/target).read_bytes(),inv['archives'][target]['sha256'])
        textures=sorted([e for e in arc.entries if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name],key=lambda e:e.name)
        pat=next(e for e in arc.entries if e.payload[:4]==b'PAT\0')
        col=next(e for e in arc.entries if e.payload[:4]==b'COL\0')
        bg=next(e for e in arc.entries if e.payload[:4]==b'TEX\0' and '\\dds\\' in e.name)
        if len(textures)!=3 or pat.payload!=pat_from_ps1(entry(native,10)) or col.payload[12:]!=entry(native_col,5):
            raise ValueError('Original native UI correspondence differs')
        if entry(native,10)!=entry(original,10):raise ValueError('Regional PAT layout differs')
        for kind,magic in [(0,b'OMP\0'),(1,b'OCL\0')]:
            e=next(e for e in arc.entries if e.payload[:4]==magic)
            if e.payload[12:]!=entry(native,kind) or entry(native,kind)[:len(entry(original,kind))]!=entry(original,kind):
                raise ValueError('Regional background map prefix differs')
            if entry(source,kind)!=entry(original,kind):raise ValueError('Source map changed')
        offsets=list(struct.unpack('<3I',entry(original,12)))+[len(entry(original,0x10102))]
        if entry(native,12)!=entry(source,12) or entry(source,12)!=entry(original,12):
            raise ValueError('Static atlas offsets changed')
        updates={};checks=[]
        for b,e in enumerate(textures):
            lo,hi=offsets[b:b+2]
            updates[e.key]=static_texture(e.payload,entry(native,0x10102)[lo:hi],entry(source,0x10102)[lo:hi])
        updates[pat.key]=pat_from_ps1(entry(source,10))
        converted=pat_frames(updates[pat.key])
        for b,frames in enumerate(converted):
            for f,record in enumerate(frames):
                comp=composition_frame(entry(source,10),b,f)
                expected=b''.join(entry(source,10)[q['record_offset']:q['record_offset']+4] for q in comp['parts'])
                if record!=expected:raise ValueError('Converted UI frame differs')
                checks.append({'bank':b,'frame':f,'parts':len(comp['parts'])})
        # Region-exclusive JP artwork uses rows69..95 and tiles301 onward.
        # Preserve it while replacing only the shared backgrounds actually used by US.
        pal=bytearray(col.payload[12:]);rows=[]
        for row in range(len(pal_original)//32):
            lo,hi=row*32,(row+1)*32
            if pal_source[lo:hi]!=pal_original[lo:hi]:
                if pal[lo:hi]!=pal_original[lo:hi]:raise ValueError('Modified palette row has regional conflict')
                pal[lo:hi]=pal_source[lo:hi];rows.append(row)
        updates[col.key]=col.payload[:12]+bytes(pal)
        old_bg=entry(native,0x10000);new_bg=bytearray(old_bg)
        mp=struct.unpack('<'+'H'*(len(entry(original,0))//2),entry(original,0))
        descriptors=struct.unpack('<'+'I'*(len(entry(original,1))//4),entry(original,1))
        tiles=sorted({descriptors[v&16383]>>16&4095 for v in mp if v})
        for tid in tiles:write_tile(new_bg,tid,tile_pixels(entry(source,0x10000),tid))
        updates[bg.key]=stage_texture(bg.payload,old_bg,bytes(new_bg))
        result=arc.rebuild(updates);readback=SteamArc(result);readback.validate_stream_order()
        if any(readback.by_key[e.key].payload!=updates.get(e.key,e.payload) for e in arc.entries):
            raise ValueError('Selection output read-back differs')
        outdir=ROOT/'out'/mode/f'steam_selection_20261109_{args.version}'
        out=outdir/'nativeDX10/X4/romPC'/target;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=result:raise ValueError('Existing output differs')
        out.write_bytes(result)
        # Preview decoded output assets (not a real gameplay screenshot).
        review=outdir/'review';review.mkdir(exist_ok=True)
        board=Image.new('RGB',(800,430),'#252d40');draw=ImageDraw.Draw(board)
        for side in (0,1):
            im=render_frame(updates[textures[1].key],converted[1][side],bytes(pal),4)
            im.save(review/f'portrait_{side}.png');im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST)
            board.paste(im,(8+side*400,35),im)
        draw.text((8,10),'Steam output decode / '+mode+' / NOT gameplay capture',fill='white')
        board.save(review/'portraits.png')
        changed=[{'name':e.name,'type':hex(e.kind),'before':sha(e.payload),'after':sha(updates[e.key])}
                 for e in arc.entries if e.key in updates and e.payload!=updates[e.key]]
        report={'mode':mode,'target_arc':target,'source_bin':str(source_bin.relative_to(ROOT)),
                'source_bin_sha256':pointer['sha256'],'original_sha256':sha(arc.raw),
                'jp_reference_sha256':jp_hash if not suffix else None,'output':str(out.relative_to(ROOT)),
                'output_sha256':sha(result),'changed_entries':changed,'verified_frames':checks,
                'palette_rows':rows,'background_tiles':tiles,'native_maps_unchanged':True,
                'jp_extra_background_art_preserved':not bool(suffix),'runtime_verified':False,
                'install_eligible':True}
        (outdir/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        reports.append(report)
        print({'mode':mode,'changed':len(changed),'verified_frames':len(checks),'palette_rows':rows,'output':str(out)})
    (WORK/'selection_builds.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':main()
