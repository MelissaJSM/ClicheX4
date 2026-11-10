"""Prepare native title artwork, preserving regional effects and copyright."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from PIL import Image,ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.build_steam_selection import render_frame,digest
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_ui import pat_frames,stage_texture
from src.steam_player import unpack_indices

WORK=ROOT/'work/steam_port_20261109'
TARGETS={0,1,2,4,5,6,*range(10,18),26,27,28,29,30,32,33,34}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def tile8(pixels,index):
    x=index%16*16;y=index//16*16
    rows=[pixels[(y+r)*256+x:(y+r)*256+x+16] for r in range(16)]
    if any(len(r)!=16 for r in rows):raise ValueError('Title tile exceeds atlas')
    return b''.join(rows)


def pack(native_textures,native_frames,source_pixels,source_frames):
    patterns={};tiles=[];frames=[]
    for f,original in enumerate(native_frames):
        records=source_frames[f] if f in TARGETS else original
        revised=bytearray()
        for flags,tile,x,y in struct.iter_unpack('<BBbb',records):
            index=(flags&3)*256+tile
            pair=(tile8(source_pixels,index),)*len(native_textures) if f in TARGETS else tuple(tile8(t[20:],index) for t in native_textures)
            if pair not in patterns:patterns[pair]=len(tiles);tiles.append(pair)
            index=patterns[pair]
            if index>=1024:raise ValueError('Title PAT page capacity exceeded')
            revised.extend(struct.pack('<BBbb',(flags&~3)|(index//256),index%256,x,y))
        frames.append(bytes(revised))
    height=256
    while height<((len(tiles)+15)//16)*16:height*=2
    textures=[]
    for variant,base in enumerate(native_textures):
        texture=bytearray(base[:20])+bytearray(256*height)
        struct.pack_into('<I',texture,8,1|(256<<6)|(height<<19))
        for index,pair in enumerate(tiles):
            x=index%16*16;y=index//16*16
            for row in range(16):texture[20+(y+row)*256+x:20+(y+row)*256+x+16]=pair[variant][row*16:row*16+16]
        textures.append(bytes(texture))
    headers=bytearray();quads=bytearray();location=len(frames)
    for records in frames:
        n=len(records)//4;headers.extend(struct.pack('<HH',n,location));quads.extend(records);location+=n
    pat=pat_from_ps1(struct.pack('<I',4)+headers+quads)
    # Every quad keeps its exact pixels, position, relative palette and flips.
    decoded=pat_frames(pat)[0]
    for f,records in enumerate(decoded):
        expected=source_frames[f] if f in TARGETS else native_frames[f]
        if len(records)!=len(expected):raise ValueError('Title quad count changed')
        for new,old in zip(struct.iter_unpack('<BBbb',records),struct.iter_unpack('<BBbb',expected)):
            if (new[0]&~3,new[2:])!=(old[0]&~3,old[2:]):raise ValueError('Title geometry/flags changed')
            oldindex=(old[0]&3)*256+old[1];newindex=(new[0]&3)*256+new[1]
            for variant,tex in enumerate(textures):
                pixels=source_pixels if f in TARGETS else native_textures[variant][20:]
                if tile8(tex[20:],newindex)!=tile8(pixels,oldindex):raise ValueError('Title pixels changed')
    return textures,pat,{'unique_tiles':len(tiles),'height':height,'frame_count':len(decoded),
                        'changed_frame_ids':sorted(TARGETS&set(range(len(decoded)))),
                        'all_quad_pixels_coordinates_palettes_flips_verified':True}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',choices=['v1','v2','v3'],default='v1');args=p.parse_args()
    inventory=json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf8'))
    original_path=ROOT/'MegaMan X4.bin'
    if digest(original_path)!=inventory['ps1_original']['sha256']:raise ValueError('Unsupported original PS1')
    originals,_=read_disc(original_path,['ST0E_U0.ARC','COL0E_U0.ARC'])
    original_stage=originals['ST0E_U0.ARC'];original_palette=entry(originals['COL0E_U0.ARC'],5)
    reports=[]
    for mode,suffix in [('ver_rin_nana',''),('ver_buki_riko','_eng')]:
        pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text(encoding='utf8'))
        source=(ROOT/pointer['cue']).with_suffix('.bin')
        if digest(source)!=pointer['sha256']:raise ValueError('Current source hash mismatch')
        files,_=read_disc(source,['ST0E_U0.ARC','COL0E_U0.ARC'])
        ps1=files['ST0E_U0.ARC'];palette=entry(files['COL0E_U0.ARC'],5)
        source_frames=pat_frames(pat_from_ps1(struct.pack('<I',4)+entry(ps1,18)))[0]
        target='st0e_00'+suffix+'.arc'
        arc=SteamArc((WORK/'original/nativeDX10/X4/romPC'/target).read_bytes(),inventory['archives'][target]['sha256'])
        tex=sorted([e for e in arc.entries if e.payload[:4]==b'TEX\0' and '\\chr\\' in e.name],key=lambda e:e.name)
        native_pat=next(e for e in arc.entries if e.payload[:4]==b'PAT\0')
        stage_col=next(e for e in arc.entries if e.payload[:4]==b'COL\0' and len(e.payload)==4108)
        fade_col=next(e for e in arc.entries if e.payload[:4]==b'COL\0' and len(e.payload)!=4108)
        native_frames=pat_frames(native_pat.payload)[0]
        if len(tex)!=2 or len(native_frames)!=(35 if suffix else 31):raise ValueError('Unrecognized title resources')
        textures,pat,proof=pack([e.payload for e in tex],native_frames,unpack_indices(entry(ps1,0x10002)),source_frames)
        updates={e.key:t for e,t in zip(tex,textures)};updates[native_pat.key]=pat
        # Main art uses only relative row0. Preserve menu/copyright/effect rows.
        col=bytearray(stage_col.payload[:12]+palette[:32]+stage_col.payload[44:])
        background_rows=[]
        for row in range(64,128):
            lo,hi=row*32,(row+1)*32
            if palette[lo:hi]!=original_palette[lo:hi]:
                if stage_col.payload[12+lo:12+hi]!=original_palette[lo:hi]:raise ValueError('Background palette regional conflict')
                col[12+lo:12+hi]=palette[lo:hi];background_rows.append(row)
        col=bytes(col);updates[stage_col.key]=col
        background=next(e for e in arc.entries if e.payload[:4]==b'TEX\0' and '\\dds\\' in e.name)
        updates[background.key]=stage_texture(background.payload,entry(original_stage,0x10000),entry(ps1,0x10000))
        for kind,magic in [(0,b'OMP\0'),(1,b'OCL\0')]:
            native_map=next(e for e in arc.entries if e.payload[:4]==magic)
            if native_map.payload[12:]!=entry(original_stage,kind) or len(entry(original_stage,kind))!=len(entry(ps1,kind)):
                raise ValueError('Title background map correspondence differs')
            updates[native_map.key]=native_map.payload[:12]+entry(ps1,kind)
        fade=bytearray(fade_col.payload);rows=2 if suffix else 3
        if len(fade)!=12+15*rows*32:raise ValueError('Unrecognized regional fade table')
        src_fade=entry(ps1,13)
        if len(src_fade)!=15*2*32:raise ValueError('Unrecognized source fade table')
        for phase in range(15):fade[12+phase*rows*32:12+phase*rows*32+32]=src_fade[phase*64:phase*64+32]
        updates[fade_col.key]=bytes(fade)
        result=arc.rebuild(updates);SteamArc(result).validate_stream_order()
        outdir=ROOT/'out'/mode/f'steam_title_20261109_{args.version}'
        out=outdir/'nativeDX10/X4/romPC'/target;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=result:raise ValueError('Existing title output differs')
        out.write_bytes(result)
        review=outdir/'review';review.mkdir(exist_ok=True)
        frames=pat_frames(pat)[0]
        view=Image.new('RGBA',(320,240),'black')
        for frame,anchor,row in [(0,(144,72),0),(2,(160,128),6),(29,(160,144),7),(30,(160,160),7),(4,(160,184),10),(7,(160,216),10)]:
            records=frames[frame];records_list=list(struct.iter_unpack('<BBbb',records))
            left,top=min(r[2]for r in records_list),min(r[3]for r in records_list)
            im=render_frame(textures[0],records,col[12:],row);view.alpha_composite(im,(anchor[0]+left,anchor[1]+top))
        view.resize((960,720),Image.Resampling.NEAREST).save(review/'layout_simulation.png')
        report={'mode':mode,'target_arc':target,'source_bin':str(source.relative_to(ROOT)),
                'source_bin_sha256':pointer['sha256'],'original_sha256':sha(arc.raw),
                'output':str(out.relative_to(ROOT)),'output_sha256':sha(result),'proof':proof,
                'changed_entries':[e.name for e in arc.entries if updates.get(e.key,e.payload)!=e.payload],
                'native_copyright_preserved':True,'background_art_reused_from_latest_ps1':True,
                'background_palette_rows':background_rows,'runtime_verified':False,
                'requires_jp_title_runtime_alignment':not bool(suffix),'install_eligible':True}
        (outdir/'manifest.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
        reports.append(report);print({'mode':mode,**proof})
    (WORK/'title_builds.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n',encoding='utf8')


if __name__=='__main__':main()
