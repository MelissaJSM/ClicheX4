"""수용한 Shibuki 기준안으로 X 대기 가족을 공동 편집하고 나머지 타일을 보존한다."""
import json
import argparse
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scripts.project import new_run,write_json,inspect_references,load_project
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import edit_frame_indices
from src.psx_compress import replace_stream

FRAMES=(0,115,116,117,118,119)


def breathe(pixels, delta):
    """머리~골반~허벅지는 같은 위상. 무릎 아래에서만 접지로 이어진다."""
    result=np.zeros_like(pixels)
    for y in range(48):
        shift=delta if y<35 else round(delta*max(0,43-y)/8)
        source=y-shift
        if 0<=source<48:result[y]=pixels[source]
    if not np.array_equal(result[43:],pixels[43:]):
        raise ValueError('Soles moved during breathing')
    return result


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--selection',type=Path,default=ROOT/'projects/ver_buki_riko/shibuki_art_selection.json')
    args=parser.parse_args()
    selection_path=args.selection.resolve()
    if not selection_path.is_relative_to((ROOT/'projects/ver_buki_riko').resolve()):
        raise ValueError('Expected a local Shibuki art selection')
    inspect_references(ROOT,load_project(ROOT,'ver_buki_riko'))
    pointer=json.loads((ROOT/'projects/ver_buki_riko/shibuki_source_inventory.json').read_text(encoding='utf-8'))
    extracted=(ROOT/pointer['inventory']).parent
    inv=json.loads((extracted/'inventory.json').read_text(encoding='utf-8'))
    arc=(extracted/'original.arc').read_bytes()
    if sha256(arc)!=inv['archive']['sha256']:raise ValueError('X extraction changed')
    entries=psx_arc(arc)
    def entry(kind):
        e=next(e for e in entries if int(e['type'],16)==kind)
        return e,arc[e['offset']:e['offset']+e['size']]
    gm,gfx=entry(2);pm,parts=entry(3);palmeta,old_palette=entry(9)
    selection=json.loads(selection_path.read_text(encoding='utf-8'))
    if selection['task']!='x_shibuki' or selection['status'] not in ('accepted_design_basis','candidate_revision_requested'):
        raise ValueError('Accepted design or explicitly requested Shibuki revision required')
    if selection['status']=='candidate_revision_requested' and not selection.get('user_request'):
        raise ValueError('Revision requires recorded user instruction')
    source=(ROOT/selection['candidate']).resolve()
    if not source.is_relative_to((ROOT/'work/ver_buki_riko/shibuki_art').resolve()):
        raise ValueError('Selected artwork escaped Shibuki work directory')
    if sha256((source/'shibuki_idle000_indexed.png').read_bytes())!=selection['indexed_sha256']:
        raise ValueError('Accepted Shibuki artwork changed')
    base_image=Image.open(source/'shibuki_idle000_indexed.png')
    base=np.array(base_image)
    words=struct.unpack('<16H',(source/'palette.bin').read_bytes())
    palette=np.array(base_image.getpalette()[:48],dtype=np.int32).reshape(16,3)
    # Only take the configured generated eyelid pixels; all other new model pixels
    # are ignored so a blink cannot change the approved face/body design.
    blink_source=(ROOT/selection.get('blink_source','work/ver_buki_riko/shibuki_art/idle_animation_v1/blink_generated.png')).resolve()
    if not blink_source.is_relative_to((ROOT/'work/ver_buki_riko/shibuki_art').resolve()):
        raise ValueError('Blink source escaped Shibuki art directory')
    eye_patch=selection.get('eye_patch',[14,13,17,15])
    if (len(eye_patch)!=4 or any(type(v)!=int for v in eye_patch)
            or not (0<=eye_patch[0]<eye_patch[2]<=48 and 0<=eye_patch[1]<eye_patch[3]<=48)):
        raise ValueError('Invalid eye patch')
    im=Image.open(blink_source).convert('RGBA');a=np.array(im);yy,xx=np.nonzero(a[:,:,3]>=128)
    crop=im.crop((int(xx.min()),int(yy.min()),int(xx.max()+1),int(yy.max()+1)))
    bbox=base_image.convert('RGBA').getbbox()
    sampled=np.array(crop.convert('RGBa').resize((bbox[2]-bbox[0],bbox[3]-bbox[1]),Image.Resampling.BOX).convert('RGBA'))
    d=sampled[:,:,:3].astype(np.int32)[:,:,None,:]-palette[None,None,1:,:]
    labels=np.argmin((d*d).sum(axis=3),axis=2)+1
    generated=base.copy();generated[bbox[1]:bbox[3],bbox[0]:bbox[2]]=labels
    x0,y0,x1,y1=eye_patch
    closed=base.copy();closed[y0:y1,x0:x1]=generated[y0:y1,x0:x1]
    if np.array_equal(closed,base):raise ValueError('Generated eyelid did not change eye')
    artwork={0:base,115:breathe(base,1),116:breathe(closed,1),117:breathe(closed,1),118:breathe(closed,1),119:breathe(base,-1)}
    modified_parts=bytearray(parts)
    for n in (115,116,117,118):
        comp=composition_frame(parts,0,n)
        # Six existing base parts become a full 32x48 rectangle, making room
        # for Shibuki's ears. Reuse the former spare leg tile as upper hair.
        for q in comp['parts']:
            if q['tile']==2:
                struct.pack_into('<bb',modified_parts,q['record_offset']+2,-19,-25)
            elif q['tile']==5:
                struct.pack_into('<bb',modified_parts,q['record_offset']+2,-3,-25)
    world_x_shift=selection.get('world_x_shift',0)
    if type(world_x_shift)!=int or not -8<=world_x_shift<=8:raise ValueError('Invalid idle alignment shift')
    shifted_records={q['record_offset'] for n in FRAMES for q in composition_frame(parts,0,n)['parts']}
    if world_x_shift:
        for off in shifted_records:
            x=struct.unpack_from('<b',modified_parts,off+2)[0]
            struct.pack_into('<b',modified_parts,off+2,x+world_x_shift)
    flipped_records=set()
    for number_text,flips in selection.get('tile_flips_by_frame',{}).items():
        number=int(number_text)
        if number not in FRAMES:raise ValueError('Unselected packing frame')
        for tile_text,flags in flips.items():
            tile=int(tile_text)
            if flags not in (0,64,128,192) or (tile%16==0 and flags&64):raise ValueError('Unsafe packing flip')
            matching=[q for q in composition_frame(parts,0,number)['parts'] if q['tile']==tile]
            if len(matching)!=1 or tile>=(6 if number in (115,116,117,118) else 7):raise ValueError('Packing flip escaped base tiles')
            off=matching[0]['record_offset'];modified_parts[off]=matching[0]['flags']^flags;flipped_records.add(off)
    modified_parts=bytes(modified_parts)
    changed_part_bytes=[i for i,(a,b) in enumerate(zip(parts,modified_parts)) if a!=b]
    allowed_parts={q['record_offset']+j for n in (115,116,117,118)
                   for q in composition_frame(parts,0,n)['parts'] if q['tile'] in (2,5) for j in (2,3)}
    if world_x_shift:allowed_parts.update(off+2 for off in shifted_records)
    allowed_parts.update(flipped_records)
    if not set(changed_part_bytes)<=allowed_parts:raise ValueError('Unapproved composition edit')
    for bi in range(len(bank_offsets(parts))):
        count=struct.unpack_from('<I',parts,bank_offsets(parts)[bi])[0]>>16
        for n in range(count):
            if bi==0 and n in (FRAMES if world_x_shift or flipped_records else (115,116,117,118)):continue
            if composition_frame(parts,bi,n)!=composition_frame(modified_parts,bi,n):
                raise ValueError('Another composition was changed through shared records')
    bank=graphics_bank(gfx,0,allow_bank_aliases=True)
    desired={}
    for n in FRAMES:
        comp=composition_frame(modified_parts,0,n)
        desc=bank['frames'][n];raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
        _,size,bounds,_=compose_indices(raw.data,desc['tile_count'],comp)
        if bounds[:2]!=(-19+world_x_shift,-25) or size[1]!=48:raise ValueError('Unexpected idle origin')
        if np.any(artwork[n][:,size[0]:]):raise ValueError('New art clipped at composition edge')
        desired[n]=(artwork[n][:,:size[0]].astype(np.uint8).tobytes(),size)
    result=gfx;compression=[]
    for n,numbers in ((0,[0]),(115,[115,116,117,118]),(119,[119])):
        desc=bank['frames'][n]
        shared=inv['stream_sharing'][str(desc['offset'])]
        if shared!=[[0,q] for q in numbers]:raise ValueError('Unexpected shared idle stream')
        raw=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
        packed=edit_frame_indices(raw.data,desc['tile_count'],composition_frame(modified_parts,0,n),*desired[n])
        if n==115:
            _,mapping,_=indexed_atlas(packed,desc['tile_count'])
            edited=bytearray(packed)
            def set_pixel(tx,ty,value):
                off,shift=mapping[ty*256+tx]
                edited[off]=(edited[off]&~(15<<shift))|int(value)<<shift
            for number in (116,117,118):
                comp=composition_frame(modified_parts,0,number)
                overlay=next(q for q in comp['parts'] if q['tile'] in (6,7,8))
                tx,ty=(overlay['tile']&15)*16,(overlay['tile']>>4)*16
                for y in range(16):
                    for x in range(16):set_pixel(tx+x,ty+y,0)
                difference=np.argwhere(artwork[number]!=artwork[115])
                for y,x in difference:
                    ox=x-19+world_x_shift-overlay['x'];oy=y-25-overlay['y']
                    if not (0<=ox<16 and 0<=oy<16) or not artwork[number][y,x]:
                        raise ValueError('Eyelid requires unsupported overlay operation')
                    set_pixel(tx+ox,ty+oy,artwork[number][y,x])
            packed=bytes(edited)
        # Armor overlays use tiles 7..16 or 9..17 of these SAME streams.
        old_atlas,_,_=indexed_atlas(raw.data,desc['tile_count'])
        new_atlas,_,_=indexed_atlas(packed,desc['tile_count'])
        first_armor=9 if n==115 else 7
        for tile in range(first_armor,desc['tile_count']):
            x,y=(tile&15)*16,(tile>>4)*16
            for row in range(16):
                start=(y+row)*256+x
                if old_atlas[start:start+16]!=new_atlas[start:start+16]:raise ValueError('Armor tile changed')
        for number in numbers:
            actual=compose_indices(packed,desc['tile_count'],composition_frame(modified_parts,0,number))[:2]
            if actual!=desired[number]:raise ValueError(f'Idle {number} raster mismatch')
        result,report=replace_stream(result,desc,packed)
        compression.append({'frames':numbers,**report})
    changed=[]
    for bi in range(len(inv['graphics_banks'])):
        for f in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
            before=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
            after=decode_stream(result,f['offset'],f['limit'],f['tile_count']*128).data
            if before!=after:
                if bi!=0 or f['index'] not in FRAMES:raise ValueError('Unselected bitmap changed')
                changed.append([bi,f['index']])
    patched=bytearray(arc)
    patched[gm['offset']:gm['offset']+gm['size']]=result
    patched[pm['offset']:pm['offset']+pm['size']]=modified_parts
    patched[palmeta['offset']:palmeta['offset']+32]=struct.pack('<16H',*words)
    allowed=[(gm['offset']+r['start'],gm['offset']+r['start']+r['encoded_bytes']) for r in compression]
    allowed+=[(pm['offset']+i,pm['offset']+i+1) for i in changed_part_bytes]+[(palmeta['offset'],palmeta['offset']+32)]
    if len(patched)!=len(arc) or any(a!=b and not any(l<=i<h for l,h in allowed) for i,(a,b) in enumerate(zip(arc,patched))):
        raise ValueError('ARC mutation escaped declared ranges')
    out=new_run(ROOT,'ver_buki_riko','shibuki_idle')
    (out/'modified.arc').write_bytes(patched)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17)
    sheet=Image.new('RGB',(6*208,244),'#222630');draw=ImageDraw.Draw(sheet)
    for i,n in enumerate(FRAMES):
        pix,size=desired[n]
        pic=save_image(pix,size,words,out/f'idle_{n:03d}.png').convert('RGBA')
        draw.text((i*208+8,6),f'Shibuki {n:03d}',font=font,fill='white')
        enlarged=pic.resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST)
        sheet.paste(enlarged,(i*208+8,32),enlarged)
    sheet.save(out/'idle_family_4x.png')
    frames=[];durations=[]
    for step in inv['idle_animation']['steps']:
        im=Image.new('RGB',(240,240),'#222630')
        pic=Image.open(out/f"idle_{step['frame']:03d}.png").convert('RGBA');big=pic.resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST)
        im.paste(big,(24,24),big);frames.append(im);durations.append(round(step['duration_ticks']*1000/60))
    frames[0].save(out/'idle_preview.gif',save_all=True,append_images=frames[1:],duration=durations,loop=0,disposal=2)
    report=dict(task='x_shibuki',scope='six_frame_idle',source_inventory=pointer['inventory'],source_art=str(source.relative_to(ROOT)),
                original_arc_sha256=sha256(arc),modified_arc_sha256=sha256(patched),arc_size=len(patched),
                compression=compression,changed_composition_bytes=changed_part_bytes,changed_bitmap_references=changed,
                palette_changed_range=[palmeta['offset'],palmeta['offset']+32],normal_palette_shared_with_unedited_X_poses=True,
                untouched_armor_tiles_verified=True,other_compositions_preserved=True,other_decoded_bitmaps_preserved=True,
                eye_patch=eye_patch,blink_source_sha256=sha256(blink_source.read_bytes()),
                world_x_shift=world_x_shift,
                tile_flips_by_frame=selection.get('tile_flips_by_frame',{}),
                art_selection=str(selection_path.relative_to(ROOT)),
                user_accepted_design_basis=selection['status']=='accepted_design_basis',
                revised_design_user_review_pending=selection['status']=='candidate_revision_requested',
                breathing_offsets={'0':0,'115':1,'116':1,'117':1,'118':1,'119':-1},
                breathing_transition_rows=[35,43],soles_rows_preserved=[43,48],
                original_animation=inv['idle_animation'],timing_changed=False,executable_changed=False,
                resources_relocated=False,runtime_verified=False,game_applied=False,
                gif_timing_note='Preview assumes 60 animation updates/sec; actual elapsed-time rate not measured')
    write_json(out/'recipe.json',report)
    print(json.dumps({'output':str(out),'compression':[(r['frames'],r['encoded_bytes'],r['original_bytes']) for r in compression]}))


if __name__=='__main__':main()
