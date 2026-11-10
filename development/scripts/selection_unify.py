"""두 모드의 선택 그림을 공통 패널 규격으로 재조립한다."""
import argparse
from collections import deque
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.project import digest, working_cue
from scripts.prepare_rin_common import read_disc
from scripts.prepare_riko_ui import entry, replace_entry
from scripts.prepare_nana_selection_portrait import compact_bank
from scripts import prepare_shibuki_ui as shibuki_art
from scripts import prepare_riko_illustrations as riko_art
from scripts.selection_common_cursor import patch as patch_cursor, verify_palette
from scripts.hud_frame_fix import require
from scripts.discover_inputs import sha256
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition, repack_frames, tile_pixels
from src.psx_disc import write_archive_copies
from src.psx_sector import validate_checks

WORK = ROOT/'work/selection_unify_20261105'
SOURCES = {
    'ver_buki_riko': ('hud_reference_details_20261105_v8', 'shibuki_riko', '92ab09adf0284c0581a6993c88f64b2348f4e2bdc886e4ca9df1e1bc8c2bdb50'),
    'ver_rin_nana': ('hud_rin_optical_20261105_v9', 'rin_nana', '8b70dbca936c2ad4d72eade207cf44f9095fb9ae05beb4e2e4943a7ba6e19768'),
}
CHARACTERS = {'ver_buki_riko': ('shibuki', 'riko'), 'ver_rin_nana': ('nana', 'rin')}
POLYGONS = [[(1,1),(124,1),(190,158),(1,158)], [(1,1),(190,1),(190,158),(52,158)]]
BORDER = {'shibuki': (2,3,4,2), 'riko': (6,7,8,6), 'nana': (7,8,10,7), 'rin': (2,7,8,2)}


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf8')


def render(indices, palette):
    words = struct.unpack('<16H', palette)
    colors = np.array([[(w>>s&31)*255//31 for s in (0,5,10)]+[255 if i else 0] for i,w in enumerate(words)], np.uint8)
    return Image.fromarray(colors[indices])


def components(mask):
    todo = mask.copy()
    result = []
    for y,x in zip(*np.where(mask)):
        if not todo[y,x]: continue
        q = deque([(int(x),int(y))]); todo[y,x] = False; points = []
        while q:
            xx,yy = q.popleft(); points.append((xx,yy))
            for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
                if 0<=nx<192 and 0<=ny<160 and todo[ny,nx]:
                    todo[ny,nx] = False; q.append((nx,ny))
        result.append(points)
    return result


def portrait(before, character, side):
    panel = Image.new('L',(192,160)); ImageDraw.Draw(panel).polygon(POLYGONS[side],fill=1)
    inside = np.array(panel).astype(bool)
    if character in ('shibuki','riko'):
        art = shibuki_art.native(shibuki_art.D/'selection_generated.png',(192,160),(190,158),(0,2)) if character=='shibuki' else riko_art.native(riko_art.D/'selection_generated.png',(192,160),(190,158),(1,1))
        keep = (art!=0)&(before==art)
        # Match the already accepted game's clipping, including empty windows.
        keep &= before!=0
    else:
        # Source backgrounds are a single flat index3; retain small enclosed
        # index3 details in the figure and inspect the explicit masks in review.
        bg = np.zeros((160,192),bool)
        for points in components(before==3):
            if len(points)>=24:
                box=(min(x for x,y in points),min(y for x,y in points),max(x for x,y in points)+1,max(y for x,y in points)+1)
                if character=='rin' and box in ((86,79,95,90),(51,80,66,94),(87,90,95,100)):
                    continue
                for x,y in points: bg[y,x] = True
        yy,xx = np.indices((160,192))
        if character=='nana':
            ring = (xx<=5)|(yy<=5)|(yy>=154)|(np.abs(xx-(125+yy*0.414))<=4.5)
            # The accepted pistol crosses in front of the slanted frame.
            ring[(yy>=64)&(yy<=83)&(xx>=134)&(xx<=173)] = False
        else:
            ring = (xx>=187)|(yy<=5)|(yy>=154)|(np.abs(xx-yy*0.329)<=4.5)
            # The upper hand and mop shaft also cross the left frame.
            ring[(yy>=19)&(yy<=37)&(xx>=9)&(xx<=33)] = False
        keep = (before!=0)&~bg&~ring
    result = np.zeros((160,192),np.uint8)
    # Four exact native-pixel bands, identical geometry rules in both mods.
    edge = Image.new('L',(192,160)); draw = ImageDraw.Draw(edge)
    for width,color in zip((4,3,2,1),reversed(BORDER[character])):
        draw.polygon(POLYGONS[side],outline=color,width=width)
    edge = np.array(edge); result[edge!=0]=edge[edge!=0]
    result[keep] = before[keep]
    return result, keep, {'preserved_figure_pixels':int(keep.sum()), 'changed_pixels':int(np.count_nonzero(result!=before)), 'panel_polygon':POLYGONS[side], 'border_width':4, 'background_index':0, 'palette_unchanged':True}


def regrid(parts, targets, texture, trim_name=False):
    blocks=[]
    for bank in range(3):
        records=[]
        for n in range(composition_frame(parts,bank,0)['bank_frame_count']):
            c=composition_frame(parts,bank,n)
            if bank==1 and n in targets:
                clut=c['parts'][0]['clut']
                a=targets[n]
                positions=[]
                for y in range(0,160,16):
                    xs=np.where(a[y:y+16].any(axis=0))[0]
                    if not len(xs): continue
                    left,right=int(xs[0]),int(xs[-1])+1
                    if left<=1: left=0
                    if right>=190: right=192
                    count=(right-left+15)//16
                    start=min(left,192-count*16)
                    positions.extend((start+16*i,y)for i in range(count))
                raw=b''.join(struct.pack('<BBbb',clut<<2,0,x-96,y-80) for x,y in positions)
            else:
                kept=c['parts']
                if trim_name and (bank,n)==(1,5):
                    require(len(kept)==47,'Unexpected name composition')
                    for q in kept[25:37]:
                        require((q['x'],q['y'])==(112,8) and not any(tile_pixels(texture,q['page']*256+q['tile'])),'Expected duplicate empty name windows')
                    kept=kept[:25]+kept[37:]
                raw=b''.join(parts[q['record_offset']:q['record_offset']+4] for q in kept)
            records.append(raw)
        blocks.append(compact_bank(records))
    result=bytearray(12)
    for bank,block in enumerate(blocks):
        struct.pack_into('<I',result,bank*4,len(result)); result+=block
    require(len(result)<=len(parts),f'Composition capacity exceeded: {len(result)} > {len(parts)}')
    used=len(result);result+=bytes(len(parts)-used)
    return bytes(result), {'used_bytes':used,'capacity_bytes':len(parts),'bank_bytes':[len(b)for b in blocks],'duplicate_empty_name_windows_removed':12 if trim_name else 0}


def prepare(project, destination):
    folder,stem,expected=SOURCES[project]; source=ROOT/'out'/project/folder/(stem+'.bin')
    require(digest(source)==expected,'Unsupported source BIN')
    destination=destination.resolve();require(destination.is_relative_to(WORK) and not destination.exists(),'Fresh task output required')
    destination.mkdir(parents=True)
    assets,records=read_disc(source,['ST0E_U1.ARC','COL0E_U1.ARC'])
    original=assets['ST0E_U1.ARC']; pal=entry(assets['COL0E_U1.ARC'],5)
    palette_proof=verify_palette(assets['COL0E_U1.ARC'])
    arc=original
    cursor_proof={'changed':False,'native_selection_highlight_preserved':True}
    texture=entry(arc,0x10102);parts=entry(arc,10)
    targets={};checks={};before_views=[];after_views=[]
    for n,character in enumerate(CHARACTERS[project]):
        comp=composition_frame(parts,1,n)
        px,size,bounds,_=compose_static(texture[40960:90112],local_composition(comp))
        require(size==(192,160) and bounds==(-96,-80,96,80),'Unexpected portrait dimensions')
        before=np.frombuffer(px,np.uint8).reshape(160,192)
        after,mask,proof=portrait(before,character,n); targets[n]=after;checks[character]=proof
        row=4+comp['parts'][0]['clut']; cp=pal[row*32:(row+1)*32]
        b=render(before,cp);a=render(after,cp);b.save(destination/(character+'_before.png'));a.save(destination/(character+'_after.png'))
        Image.fromarray(mask.astype(np.uint8)*255).save(destination/(character+'_figure_mask.png'))
        (destination/(character+'_indices.bin')).write_bytes(after.tobytes())
        before_views.append(b);after_views.append(a)
    try:
        new_parts,layout=regrid(parts,targets,texture[40960:90112])
    except ValueError as error:
        if project!='ver_buki_riko' or 'Composition capacity exceeded' not in str(error):raise
        new_parts,layout=regrid(parts,targets,texture[40960:90112],True)
    bank,new_parts,packing=repack_frames(texture[40960:90112],new_parts,1,{n:(a.tobytes(),(192,160))for n,a in targets.items()})
    new=replace_entry(replace_entry(arc,0x10102,texture[:40960]+bank+texture[90112:]),10,new_parts)
    # Every other rendered sprite, including all native highlight states, stays exact.
    original_parts=entry(original,10);checked=0
    for bank_id,lo,hi in ((0,0,40960),(1,40960,90112),(2,90112,len(texture))):
        oldtex=entry(original,0x10102)[lo:hi];newtex=entry(new,0x10102)[lo:hi]
        for n in range(composition_frame(original_parts,bank_id,0)['bank_frame_count']):
            if bank_id==1 and n in (0,1):continue
            oldc=composition_frame(original_parts,bank_id,n);newc=composition_frame(new_parts,bank_id,n)
            require(compose_static(oldtex,local_composition(oldc))[:3]==compose_static(newtex,local_composition(newc))[:3],f'Protected display changed {bank_id}:{n}')
            if layout['duplicate_empty_name_windows_removed'] and (bank_id,n)==(1,5):oldc={**oldc,'parts':oldc['parts'][:25]+oldc['parts'][37:]}
            normalized=lambda c:[{k:v for k,v in p.items()if k not in ('index','record_offset','tile','page','flags','clut')}for p in c['parts']]
            require(normalized(oldc)==normalized(newc),'Protected geometry changed')
            require([p['clut']for p in oldc['parts']]==[p['clut']for p in newc['parts']],'Protected palette reference changed')
            checked+=1
    require(len(new)==len(original),'ARC length changed')
    path=destination/'ST0E_U1.ARC';path.write_bytes(new)
    board=Image.new('RGB',(768,680),'#394554');draw=ImageDraw.Draw(board)
    for col,views in enumerate((before_views,after_views)):
        for n,im in enumerate(views):
            x,y=col*384,n*340;draw.text((x+4,y+3),CHARACTERS[project][n]+(' BEFORE'if col==0 else' AFTER'),fill='white');im=im.resize((384,320),Image.Resampling.NEAREST);board.paste(im,(x,y+20),im)
    board.save(destination/'comparison.png')
    proposal={'project':project,'source':source.relative_to(ROOT).as_posix(),'source_sha256':expected,'resource':path.relative_to(ROOT).as_posix(),'resource_sha256':sha256(new),'record':records['ST0E_U1.ARC'],'original_resource_sha256':sha256(original),'palette':palette_proof,'cursor':cursor_proof,'portraits':checks,'layout':layout,'packing':packing,'protected_display_frames':checked,'palette_arc_unchanged':True}
    write_json(destination/'proposal.json',proposal)
    print(json.dumps({'prepared':str(destination),'layout':layout,'packing':packing,'checks':checks}))


def build(project, proposal_path, output):
    proposal_path=proposal_path.resolve()
    proposal=json.loads(proposal_path.read_text('utf8'));folder,stem,expected=SOURCES[project]
    source=ROOT/'out'/project/folder/(stem+'.bin');require(digest(source)==expected and proposal['source_sha256']==expected,'Source mismatch')
    resource=(ROOT/proposal['resource']).resolve();require(resource.is_relative_to(WORK),'Unexpected resource')
    data=resource.read_bytes();require(sha256(data)==proposal['resource_sha256'],'Prepared resource changed')
    output=output.resolve();require(output.is_relative_to(ROOT/'out'/project) and not output.exists(),'Fresh separate BIN required')
    assets,records=read_disc(source,['ST0E_U1.ARC']);require(sha256(assets['ST0E_U1.ARC'])==proposal['original_resource_sha256'],'Original resource mismatch')
    output.mkdir(parents=True);target=output/(stem+'.bin')
    result=write_archive_copies(source,target,[({**records['ST0E_U1.ARC'],'sha256':sha256(assets['ST0E_U1.ARC'])},data)],expected)
    changed={r['lba']for r in result['changed_sectors']};count=0
    with source.open('rb')as a,target.open('rb')as b:
        while before:=a.read(2352):
            after=b.read(2352);require((before!=after)==(count in changed),'Undeclared sector change')
            if count in changed:validate_checks(after)
            count+=1
        require(not b.read(1),'Output length changed')
    readback,_=read_disc(target,['ST0E_U1.ARC']);require(readback['ST0E_U1.ARC']==data,'Resource readback differs')
    require(digest(source)==expected,'Source modified')
    (output/(stem+'.cue')).write_text(working_cue(source.with_suffix('.cue').read_text('ascii'),stem+'.bin'),'ascii')
    report={'project':project,'task':'selection_screen_unification','parent_sha256':expected,'modified_bin':result,'all_disc_sectors_compared':count,'all_unrelated_sectors_identical':True,'edc_ecc_checked':True,'resource_readback_verified':True,'proposal':proposal_path.relative_to(ROOT).as_posix(),'runtime_verified':False,'user_accepted':False}
    write_json(output/'manifest.json',report);print(json.dumps({'project':project,'output':str(output),'sha256':result['sha256'],'changed_sectors':len(changed)}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('action',choices=['prepare','build']);parser.add_argument('--project',choices=SOURCES,required=True);parser.add_argument('--output',type=Path,required=True);parser.add_argument('--proposal',type=Path);args=parser.parse_args()
    if args.action=='prepare':prepare(args.project,args.output)
    else:build(args.project,args.proposal,args.output)
