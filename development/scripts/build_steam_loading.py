"""Port loading names/logo and shared menu pictures; leave text renderer separate."""
import argparse
import hashlib
import json
from pathlib import Path
import struct
import sys

from PIL import Image

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.prepare_riko_ui import entry
from scripts.build_steam_selection import digest
from scripts.prepare_cliche_logo_v4 import loading_palettes
from scripts.prepare_korean_loading_names import loading_preview
from src.steam_arc import SteamArc,pat_from_ps1
from src.steam_ui import pat_frames
from src.steam_player import unpack_indices,tex_geometry

WORK=ROOT/'work/steam_port_20261109'
TABLE_OFFSET=0xDED04


def sha(b):return hashlib.sha256(b).hexdigest()


def loading_pat(moji):
    offsets=struct.unpack_from('<4I',moji)
    return pat_from_ps1(struct.pack('<I',4)+moji[offsets[2]:offsets[3]])


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--version',choices=['v1','v2','v3'],default='v1');args=p.parse_args()
    inv=json.loads((ROOT/'work/steam_port_research_20261109/inventory.json').read_text(encoding='utf8'))
    original_path=ROOT/'MegaMan X4.bin'
    if digest(original_path)!=inv['ps1_original']['sha256']:raise ValueError('Original PS1 mismatch')
    names=['LOAD_U.ARC','MOJIPAT.ARC','SLUS_005.61'];originals,_=read_disc(original_path,names)
    original_pat=loading_pat(originals['MOJIPAT.ARC'])
    native_exe=(WORK/'original/RXC1.exe').read_bytes();reports=[];data_patches=[];installed_requirements={}
    for mode,suffix,va,file_offset in [('ver_rin_nana','',0x1ae0f10,0x16dfd10),('ver_buki_riko','_eng',0x1ae0f58,0x16dfd58)]:
        pointer=json.loads((ROOT/'projects'/mode/'current_build.json').read_text(encoding='utf8'))
        source=(ROOT/pointer['cue']).with_suffix('.bin')
        if digest(source)!=pointer['sha256']:raise ValueError('Current source mismatch')
        assets,_=read_disc(source,names);moji=assets['MOJIPAT.ARC'];offsets=struct.unpack_from('<4I',moji)
        old_offsets=struct.unpack_from('<4I',originals['MOJIPAT.ARC'])
        if offsets!=old_offsets:raise ValueError('MOJIPAT segment boundaries changed')
        target='load'+suffix+'.arc';arc=SteamArc((WORK/'original/nativeDX10/X4/romPC'/target).read_bytes(),inv['archives'][target]['sha256'])
        textures=[e for e in arc.entries if e.payload[:4]==b'TEX\0' and '\\loading\\'in e.name]
        pat=next(e for e in arc.entries if e.payload[:4]==b'PAT\0' and '\\loading\\'in e.name)
        col=next(e for e in arc.entries if e.payload[:4]==b'COL\0')
        if len(textures)!=2 or pat.payload!=original_pat:raise ValueError('Native loading correspondence differs')
        pixels=unpack_indices(entry(assets['LOAD_U.ARC'],0x10008))
        updates={}
        for tex in textures:
            if tex_geometry(tex.payload)!=(256,256,20) or len(pixels)!=65536:raise ValueError('Unexpected loading atlas')
            updates[tex.key]=tex.payload[:20]+pixels
        updates[pat.key]=loading_pat(moji)
        before_frames,after_frames=pat_frames(pat.payload)[0],pat_frames(updates[pat.key])[0]
        if len(before_frames)!=53 or len(after_frames) not in (53,54):raise ValueError('Unexpected loading frame count')
        # The untouched READY consumes only the first 128x32 region and frame0.
        if after_frames[0]!=before_frames[0]:raise ValueError('READY parts changed')
        old_pixels=unpack_indices(entry(originals['LOAD_U.ARC'],0x10008))
        for flag,tile,x,y in struct.iter_unpack('<BBbb',before_frames[0]):
            index=(flag&3)*256+tile;tx=index%16*16;ty=index//16*16
            for dy in range(16):
                lo=(ty+dy)*256+tx
                if pixels[lo:lo+16]!=old_pixels[lo:lo+16]:raise ValueError('READY pixels changed')
        native_pal=bytearray(col.payload[12:]);source_pal=moji[offsets[1]:offsets[2]];old_pal=originals['MOJIPAT.ARC'][offsets[1]:offsets[2]];changed_rows=[]
        for row in range(32):
            lo,hi=row*32,(row+1)*32
            if source_pal[lo:hi]!=old_pal[lo:hi]:
                if native_pal[lo:hi]!=old_pal[lo:hi]:raise ValueError('Menu palette regional conflict')
                native_pal[lo:hi]=source_pal[lo:hi];changed_rows.append(row)
        updates[col.key]=col.payload[:12]+bytes(native_pal)
        result=arc.rebuild(updates);readback=SteamArc(result);readback.validate_stream_order()
        for e in arc.entries:
            if readback.by_key[e.key].payload!=updates.get(e.key,e.payload):raise ValueError('Loading output read-back failed')
        outdir=ROOT/'out'/mode/f'steam_loading_20261109_{args.version}';out=outdir/'nativeDX10/X4/romPC'/target;out.parent.mkdir(parents=True,exist_ok=True)
        if out.exists() and out.read_bytes()!=result:raise ValueError('Existing loading output differs')
        out.write_bytes(result);review=outdir/'review';review.mkdir(exist_ok=True)
        for char in (5,6):loading_preview(assets,char).resize((960,720),Image.Resampling.NEAREST).save(review/f'loading_{char}.png')
        table=assets['SLUS_005.61'][TABLE_OFFSET:TABLE_OFFSET+72];native=native_exe[file_offset:file_offset+72]
        rows=[struct.unpack_from('<hhBBBB',table,i*8)for i in range(9)]
        if rows[0]!=(96,96,0,8,1,1) or rows[3]!=(16,192,8,5,1,0) or rows[4]!=(16,192,203,5,1,0):raise ValueError('Unrecognized full-name display table')
        if any(not(0<=x<320 and 0<=y<240 and 1<=width<=16 and 1<=height<=16 and tile%16+width<=16 and tile//16+height<=16)for x,y,tile,width,height,pal in rows):raise ValueError('Loading rectangle out of bounds')
        data_patches.append({'name':mode+'_loading_rectangles','address':va,'file_offset':file_offset,
                             'before_hex':native.hex(),'after_hex':table.hex(),'kind':'game_data'})
        if not suffix:
            palette=loading_palettes(assets['SLUS_005.61']);expected=loading_palettes(originals['SLUS_005.61'])
            if palette!=expected or native_exe[0xb5e368:0xb5e568]!=expected:raise ValueError('Loading color table differs')
            data_patches.append({'name':'jp_loading_logo_colors','address':0xf5eda8,'file_offset':0xb5e1a8,
                                 'before_hex':native_exe[0xb5e1a8:0xb5e1e8].hex(),'after_hex':palette[64:128].hex(),'kind':'game_data'})
        installed_requirements['nativeDX10/X4/romPC/'+target]=sha(result)
        report={'mode':mode,'target_arc':target,'output':str(out.relative_to(ROOT)),'output_sha256':sha(result),
                'source_bin':str(source.relative_to(ROOT)),'source_bin_sha256':pointer['sha256'],
                'original_sha256':sha(arc.raw),'changed_entries':[e.name for e in arc.entries if e.payload!=updates.get(e.key,e.payload)],
                'loading_frames':len(after_frames),'palette_rows':changed_rows,'ready_pixels_and_parts_unchanged':True,
                'korean_menu_text_renderer_ported':False,'ultimate_save_selector_ported':False,
                'native_font_atlas_and_controller_option_resources_preserved':True,'requires_runtime_data_patch':True,
                'runtime_verified':False,'install_eligible':True}
        (outdir/'manifest.json').write_text(json.dumps(report,indent=2)+'\n');reports.append(report)
        print({'mode':mode,'frames':len(after_frames),'ready_preserved':True,'palette_rows':changed_rows})
    (WORK/'loading_builds.json').write_text(json.dumps(reports,indent=2)+'\n')
    (WORK/'loading_runtime_patch.json').write_text(json.dumps({'installed_requirements':installed_requirements,'patches':data_patches},indent=2)+'\n')


if __name__=='__main__':main()
