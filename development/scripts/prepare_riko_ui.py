"""Register accepted Riko sprites in select/save atlases; fit the new portrait."""
import argparse
import json
from pathlib import Path
import struct
import sys
import numpy as np
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.riko_master_sheet import load_model
from scripts.project import digest,write_json
from scripts.discover_inputs import sha256,psx_arc
from scripts.extract_zero import save_image
from src.psx_player import composition_frame,graphics_bank,decode_stream,compose_indices
from src.psx_static_effect import compose_static,patch_static
from src.psx_ui_atlas import local_composition,place_frame,repack_frames

SELECTION_MAPPING={0:(0,147),**{n:(0,n+60) for n in (1,2,3,5,7,9,11,13,15,17,19,21)},
    22:(0,82),23:(0,131),24:(0,132),25:(0,133),26:(0,134),
    **{n:(1,n-27) for n in range(27,41)}}


def entry(raw,kind):
    e=next(e for e in psx_arc(raw) if e['type']==hex(kind))
    return raw[e['offset']:e['offset']+e['size']]


def replace_entry(raw,kind,data):
    e=next(e for e in psx_arc(raw) if e['type']==hex(kind))
    if len(data)!=e['size']:raise ValueError('UI resource length change refused')
    return raw[:e['offset']]+data+raw[e['offset']+e['size']:]


def actual_frame(model,bank,n):
    # Read the built archive, including recolored pure warp effects.
    g=entry(model['built_arc'],2);p=entry(model['built_arc'],3)
    f=graphics_bank(g,bank)['frames'][n]
    raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
    return compose_indices(raw,f['tile_count'],composition_frame(p,0 if bank==0 else 5,n))[:3]


def portrait(image_path,texture,parts,out):
    c=local_composition(composition_frame(parts,1,1))
    original,size,bounds,coverage=compose_static(texture,c)
    im=Image.open(image_path).convert('RGBA')
    im=im.crop(im.getchannel('A').getbbox())
    im.thumbnail((178,154),Image.Resampling.NEAREST)
    rgba=Image.new('RGBA',size,(0,0,0,0))
    # Native-size production conversion; preserve alpha and reject uncovered tiles.
    rgba.alpha_composite(im,(size[0]-im.width, size[1]-im.height-2))
    a=np.array(rgba);mask=a[:,:,3]>=128
    cov=np.array([bool(v) for v in coverage]).reshape(size[1],size[0]);clipped=int(np.sum(mask&~cov));mask &= cov
    # The original slanted frame remains inside the allocated portrait grid.
    # Recreate only its edge, never any original character pixels.
    edge=Image.new('RGBA',size,(0,0,0,0));dr=ImageDraw.Draw(edge)
    dr.polygon([(1,2),(189,2),(189,157),(52,157)],outline=(28,126,134,255),width=6)
    edge.alpha_composite(rgba)
    a=np.array(edge);mask=(a[:,:,3]>=128)&cov
    colors=Image.fromarray(a[:,:,:3][mask].reshape(1,-1,3),'RGB').quantize(colors=15,method=Image.Quantize.MEDIANCUT,dither=Image.Dither.NONE)
    pal=colors.getpalette()[:45]
    rgb=np.array(pal,dtype=np.int32).reshape(15,3)
    distance=((a[:,:,:3].astype(np.int32)[:,:,None,:]-rgb)**2).sum(axis=3)
    indices=np.where(mask,np.argmin(distance,axis=2)+1,0).astype(np.uint8)
    words=[0]+[(pal[i]>>3)|((pal[i+1]>>3)<<5)|((pal[i+2]>>3)<<10)|0x8000 for i in range(0,45,3)]
    save_image(indices.tobytes(),size,words,out/'portrait_indexed.png')
    (out/'portrait_palette.bin').write_bytes(struct.pack('<16H',*words))
    return (indices.tobytes(),size),struct.pack('<16H',*words),{'native_size':size,'source_sha256':digest(image_path),
        'resampling':'nearest','opaque_colors':len(set(indices[mask].tolist())),
        'pixels_outside_original_slanted_frame_clipped':clipped,'transparent_index':0}


def prepare(parent,extracted,source_dir,out):
    out.mkdir(exist_ok=False)
    model=load_model(parent,extracted)
    if not model['manifest'].get('jump_alignment'):raise ValueError('Expected accepted jump-alignment build')
    records=json.loads((source_dir/'source_inventory.json').read_text('utf8'))
    records.append(json.loads((source_dir/'mojipat_record.json').read_text('utf8')))
    records={r['path']:r for r in records}
    def original(name):
        record=records[f'/ARC/{name};1'];raw=(source_dir/name/'original.arc').read_bytes()
        if len(raw)!=record['size'] or sha256(raw)!=record['sha256']:raise ValueError('UI original changed')
        return raw
    select=original('ST0E_U1.ARC');texture=entry(select,0x10102);parts=entry(select,0xa)
    if struct.unpack('<3I',entry(select,0xc))!=(0,40960,90112):raise ValueError('Unsupported UI texture banks')
    targets={}
    for n,(b,k) in SELECTION_MAPPING.items():
        targets[n]=place_frame(actual_frame(model,b,k),composition_frame(parts,0,n),texture[:40960])
        save_image(*targets[n],model['words'],out/f'select_{n:03d}.png')
    bank0,new_parts,small_report=repack_frames(texture[:40960],parts,0,targets,{38:0})
    port,portrait_pal,portrait_report=portrait(source_dir/'portrait_generated.png',texture[40960:90112],parts,out)
    bank1,new_parts,large_report=repack_frames(texture[40960:90112],new_parts,1,{1:port})
    select=replace_entry(select,0x10102,bank0+bank1+texture[90112:])
    select=replace_entry(select,0xa,new_parts)
    col=original('COL0E_U1.ARC');pal=bytearray(entry(col,5));pal[:32]=model['palette'];pal[5*32:6*32]=portrait_pal;col=replace_entry(col,5,bytes(pal))
    menu=original('MOJIPAT.ARC');load=original('LOAD_U.ARC');g=entry(load,0x10008);c=local_composition(composition_frame(menu,2,43))
    saved=place_frame(actual_frame(model,0,147),c,g);save_image(*saved,model['words'],out/'save_zero.png')
    edited=patch_static(g,{43:c},{43:saved})
    # Other menu-bank frames must remain byte-identical when composed.
    for n in range(c['bank_frame_count']):
        co=local_composition(composition_frame(menu,2,n))
        if n!=43 and compose_static(g,co)[:2]!=compose_static(edited,co)[:2]:raise ValueError('Save icon aliases another menu image')
    load=replace_entry(load,0x10008,edited)
    palette_start=struct.unpack_from('<I',menu,4)[0]
    if palette_start!=6788 or menu[palette_start+320:palette_start+352]!=(extracted/'palette_bank.bin').read_bytes()[:32]:raise ValueError('Unexpected save Zero palette')
    menu=menu[:palette_start+320]+model['palette']+menu[palette_start+352:]
    changes=[]
    for name,data in [('ST0E_U1.ARC',select),('COL0E_U1.ARC',col),('LOAD_U.ARC',load),('MOJIPAT.ARC',menu)]:
        source=original(name);assert len(source)==len(data)
        (out/name).write_bytes(data)
        changes.append({'source':records[f'/ARC/{name};1'],'file':name,'sha256':sha256(data),
            'changed_bytes':sum(a!=b for a,b in zip(source,data))})
    report={'kind':'riko_selection_save_ui_v1','parent_build':str(parent.resolve()),'parent_manifest_sha256':digest(parent/'manifest.json'),
        'source_sha256':model['manifest']['source_sha256'],'mapping':{str(n):list(v) for n,v in SELECTION_MAPPING.items()},
        'small_sprite_atlas':small_report,'portrait_atlas':large_report,'portrait_conversion':portrait_report,
        'files':changes,'normal_save_icon_frame':43,'normal_save_palette_row':10,'runtime_verified':False,
        'black_zero_save_palette_changed':False,'exe_changed':False,'gameplay_archive_changed':False}
    write_json(out/'recipe.json',report)
    board=Image.new('RGB',(1260,7*190),(58,69,81));dr=ImageDraw.Draw(board)
    for n in range(41):
        c=composition_frame(new_parts,0,n);pic=compose_static(bank0,local_composition(c))
        words=model['words'] if not c['parts'][0]['clut'] else struct.unpack_from('<16H',pal,32)
        im=Image.open(out/f'select_{n:03d}.png').convert('RGBA') if n in targets else save_image(pic[0],pic[1],words,out/f'select_{n:03d}.png').convert('RGBA')
        im=im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST);x=n%6*210;y=n//6*190;board.paste(im,(x,y+20),im);dr.text((x,y),str(n),fill='white')
    board.save(out/'selection_motion_review.png')
    print(json.dumps({'output':str(out),'files':[(r['file'],r['changed_bytes']) for r in changes],
        'small':small_report,'portrait':large_report}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('parent','extract','source-dir','output'):p.add_argument('--'+name,type=Path,required=True)
    a=p.parse_args();prepare(a.parent,a.extract,a.source_dir,a.output)
