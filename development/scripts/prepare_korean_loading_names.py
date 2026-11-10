"""Expand Korean loading names in a fresh integrated proposal, never a BIN.

The existing direct-draw rectangles and MOJIPAT bank 2 must agree. Allocate
two isolated horizontal strips, remove only proven invisible interior parts
to preserve the fixed bank capacity, and edit a bounded EXE display table.
"""
import argparse,copy,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.inventory_korean import D,PARENT_HASH,SOURCE_HASH
from scripts.prepare_riko_ui import entry,replace_entry
from scripts.prepare_korean_ui import label,align_loading_label,loading_ink_bounds
from scripts.prepare_cliche_logo_v4 import pack_bank,old_records,loading_palettes
from scripts.discover_inputs import psx_arc,sha256
from src.psx_ui_atlas import aliased_composition,local_composition,tile_pixels,write_tile
from src.psx_static_effect import compose_static
from src.psx_korean_font import font_cache_proposal
from src.psx_korean_typography import profile_metadata

FULL_NAMES={5:'텐코 시부키',6:'유즈하 리코'}
DISPLAY_TARGETS={5,6,7}
TABLE=0xDED04


def atlas_pixels(texture):
    raw=np.frombuffer(texture,np.uint8);out=np.empty(raw.size*2,np.uint8)
    out[::2]=raw&15;out[1::2]=raw>>4
    return out.reshape(-1,256)


def transformed(files):
    old_load=files['LOAD_U.ARC'];menu=files['MOJIPAT.ARC'];exe=files['SLUS_005.61']
    texture=entry(old_load,0x10008);offsets=struct.unpack_from('<4I',menu)
    originals=old_records(menu,2);records=copy.deepcopy(originals)
    if len(records)!=53:raise ValueError('Unexpected loading composition count')
    compositions={n:aliased_composition(menu,2,n) for n in range(53)}
    rendered={n:compose_static(texture,local_composition(c))[:3] for n,c in compositions.items()}
    rows=[struct.unpack_from('<hhBBBB',exe,TABLE+i*8) for i in range(9)]
    expected=[(96,96,0,8,1,1),(200,192,112,5,2,2),(248,192,117,4,2,3),
              (16,192,8,3,1,0),(32,192,203,2,1,0),(64,192,12,4,1,0),
              (16,208,32,6,1,0),(120,208,121,3,1,0),(120,208,137,3,1,0)]
    if rows!=expected:raise ValueError('Unrecognized loading display table')
    inventory_exe=(D/'inventory/SLUS_005.61').read_bytes()
    renderer_exe,renderer_proof=font_cache_proposal(inventory_exe)
    if exe!=renderer_exe:raise ValueError('Input EXE differs from the verified Korean renderer')
    renderer_offsets=[i for i,(a,b) in enumerate(zip(inventory_exe,exe)) if a!=b]
    if len(renderer_offsets)!=54:raise ValueError('Expected 54 preserved renderer bytes')

    reserved={p['page']*256+p['tile'] for n,c in compositions.items() if n not in DISPLAY_TARGETS for p in c['parts']}
    # Direct draws include transparent cells omitted from the composition
    # lists, notably the logo. Protect their complete fixed UV rectangles.
    direct_reserved=set()
    for i,(x,y,t,w,h,clut) in enumerate(rows):
        if i in (3,4,5):continue
        starts=list(exe[TABLE+72:TABLE+84]) if i==6 else [t]
        for start in starts:
            direct_reserved.update(start+dy*16+dx for dy in range(h) for dx in range(w))
    reserved|=direct_reserved
    # Continue/save/mission menus draw the bottom 48px as repeated background
    # using direct GPU UVs, outside MOJIPAT's composed-frame inventory. Protect
    # the entire strip, including blank/dither cells, rather than only logos.
    reserved.update(range(208,256))
    available=set(range(len(texture)//128))-reserved
    free_before=sorted(available);allocated={};new_texture=bytearray(texture);targets={}
    # Reuse the existing top name/departure row and the original Riko strip.
    # Compact departure's transparent tail to three tiles, freeing one tile
    # for the full Shibuki name without touching any menu-background cells.
    placements={5:list(range(8,13)),6:list(range(203,208)),7:list(range(13,16))}
    for n,tiles in placements.items():
        if not set(tiles)<=available:raise ValueError('Verified loading strip aliases a protected consumer')
        allocated[n]=tiles;available.difference_update(tiles)
        if n in FULL_NAMES:a=align_loading_label(n,label(FULL_NAMES[n],(80,16),12,profile='loading',shaded=True))
        else:
            px,size,_=rendered[7];old=np.frombuffer(px,np.uint8).reshape(size[1],size[0])
            if size!=(64,16) or np.any(old[:,48:]):raise ValueError('Departure transparent tail no longer fits')
            a=old[:,:48].copy()
        targets[n]=a;records[n]=[]
        for x,tile in enumerate(allocated[n]):
            write_tile(new_texture,tile,a[:,x*16:x*16+16].tobytes())
            records[n].append(struct.pack('<BBbb',tile//256,tile%256,x*16,0))
    # Grow only the two target part lists. Recover space from zero-valued
    # interior text parts whose removal preserves the entire rendered frame.
    omitted={};removed=[];capacity=offsets[3]-offsets[2]
    def try_pack():
        try:return pack_bank(records,capacity)
        except ValueError as exc:
            if not str(exc).startswith('Fixed bank capacity '):raise
            return None
    packed=try_pack()
    if packed is None:
        for n in range(8,22):
            cp=compositions[n]
            for i,p in enumerate(cp['parts']):
                if any(tile_pixels(texture,p['page']*256+p['tile'])):continue
                exclusions=omitted.get(n,set())|{i}
                reduced=[q for j,q in enumerate(cp['parts']) if j not in exclusions]
                if not reduced or compose_static(texture,local_composition({**cp,'parts':reduced}))[:3]!=rendered[n]:continue
                omitted[n]=exclusions;records[n]=[r for j,r in enumerate(originals[n]) if j not in exclusions]
                removed.append({'frame':n,'original_part':i,'tile':p['page']*256+p['tile'],
                                'origin':[p['x'],p['y']],'pixel_size_bounds_unchanged':True})
                packed=try_pack()
                if packed is not None:break
            if packed is not None:break
    if packed is None:raise ValueError('Insufficient invisible interior parts to preserve bank capacity')
    bank,bank_proof=packed;new_menu=menu[:offsets[2]]+bank+menu[offsets[3]:]
    new_exe=bytearray(exe)
    for n,row in ((5,3),(6,4)):
        struct.pack_into('<hhBBBB',new_exe,TABLE+row*8,16,192,allocated[n][0],5,1,0)
    struct.pack_into('<hhBBBB',new_exe,TABLE+5*8,96,192,13,3,1,0)
    allowed=set()
    for row in (3,4):allowed.update(TABLE+row*8+j for j in (0,1,4,5))
    allowed.update(TABLE+5*8+j for j in (0,1,4,5))
    edits=[{'offset':i,'before':a,'after':b} for i,(a,b) in enumerate(zip(exe,new_exe)) if a!=b]
    if not {e['offset'] for e in edits}<=allowed:raise ValueError('EXE mutation escaped display data allowlist')
    if any(new_exe[i]!=exe[i] for i in renderer_offsets):raise ValueError('Korean renderer bytes changed')
    if new_menu[:offsets[2]]!=menu[:offsets[2]] or new_menu[offsets[3]:]!=menu[offsets[3]:]:
        raise ValueError('Menu glyph bank, palettes or other banks changed')

    new_texture=bytes(new_texture);changed_tiles={t for t in range(len(texture)//128) if tile_pixels(texture,t)!=tile_pixels(new_texture,t)}
    used_tiles=set(allocated[5]+allocated[6]+allocated[7])
    if changed_tiles-reserved!=changed_tiles or not changed_tiles<=used_tiles:raise ValueError('Name texture touches a shared tile')
    protected_frames=[];names=[];atlas=atlas_pixels(new_texture)
    for n in range(53):
        actual=compose_static(new_texture,local_composition(aliased_composition(new_menu,2,n)))[:3]
        if n in DISPLAY_TARGETS:
            width=targets[n].shape[1]
            if actual!=(targets[n].tobytes(),(width,16),(0,0,width,16)):raise ValueError('Loading label composition differs')
            t=allocated[n][0];direct=atlas[t//16*16:t//16*16+16,t%16*16:t%16*16+width]
            if direct.tobytes()!=targets[n].tobytes():raise ValueError('Full-name fixed UV differs')
            if n==7:continue
            bounds=loading_ink_bounds(targets[n]);screen=[bounds[0]+16,bounds[1]+192,bounds[2]+16,bounds[3]+192]
            departure=atlas[:16,208:256];db=loading_ink_bounds(departure);ds=[db[0]+96,db[1]+192,db[2]+96,db[3]+192]
            if screen[2]!=94 or ds[0]!=98 or ds[0]-screen[2]!=4:raise ValueError('Full-name/departure gap differs')
            names.append({'frame':n,'text':FULL_NAMES[n],'tiles':allocated[n],'canvas':[80,16],
                          'screen_ink':screen,'departure_ink':ds,'gap_pixels':4})
        elif actual!=rendered[n]:raise ValueError(f'Unrelated loading composition changed: {n}')
        else:protected_frames.append(n)
    new_load=replace_entry(old_load,0x10008,new_texture)
    if atlas_pixels(texture)[208:256].tobytes()!=atlas[208:256].tobytes():
        raise ValueError('Continue/save repeated background strip changed')
    arc_layout=lambda raw:[(e['index'],e['type'],e['offset'],e['size']) for e in psx_arc(raw)]
    if arc_layout(old_load)!=arc_layout(new_load):raise ValueError('LOAD entries changed size or offset')
    for e in psx_arc(old_load):
        if int(e['type'],16)!=0x10008 and entry(old_load,int(e['type'],16))!=entry(new_load,int(e['type'],16)):
            raise ValueError('LOAD non-loading entry changed')
    result={**files,'LOAD_U.ARC':new_load,'MOJIPAT.ARC':new_menu,'SLUS_005.61':bytes(new_exe)}
    for name in files:
        if len(result[name])!=len(files[name]):raise ValueError('Resource length changed')
    proof={'kind':'korean_loading_full_names_postprocess','runtime_verified':False,'bin_applied':False,
           'names':names,'typography':profile_metadata('loading'),'atlas_tiles':len(texture)//128,
           'available_tiles_before':free_before,'allocated_tiles':allocated,'changed_tiles':sorted(changed_tiles),
           'allocated_tiles_disjoint_from_all_other_compositions_and_direct_draws':True,
           'bank':bank_proof,'invisible_interior_parts_removed':removed,
           'protected_compositions':protected_frames,'protected_composition_count':len(protected_frames),
           'protected_pixels_sizes_bounds_equal':True,'ready_and_logos_preserved':True,
           'other_mojipat_banks_and_palettes_byte_identical':True,'font_and_runtime_cache_texture_byte_identical':True,
           'load_non_loading_entries_byte_identical':True,'exe_allowed_file_offsets':sorted(allowed),'exe_edits':edits,
           'continue_save_background_uv_rect_preserved':[0,208,256,48],
           'continue_save_background_pixels_byte_identical':True,
           'exe_outside_allowlist_byte_identical':True,'renderer_modified_bytes_preserved':len(renderer_offsets),
           'renderer_file_offsets':renderer_offsets,'renderer_verifier':renderer_proof,
           'logo_display_rows_unchanged':rows[1:3],'resource_lengths_offsets_lbas_preserved':True,
           'game_bin_written':False,'process_memory_written':False}
    return result,proof


def loading_preview(files,character,stage=8,area=20):
    atlas=atlas_pixels(entry(files['LOAD_U.ARC'],0x10008));exe=files['SLUS_005.61']
    pal=loading_palettes(exe);canvas=np.zeros((240,320,3),np.uint8)
    for row in (0,1,2,3 if character==5 else 4,5,6,7 if area==20 else 8):
        x,y,t,w,h,clut=struct.unpack_from('<hhBBBB',exe,TABLE+row*8)
        if row==6:t=exe[TABLE+72+stage-8]
        pixels=atlas[t//16*16:t//16*16+h*16,t%16*16:t%16*16+w*16]
        words=struct.unpack_from('<16H',pal,clut*32)
        colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in words],np.uint8)
        region=canvas[y:y+h*16,x:x+w*16];region[pixels!=0]=colors[pixels[pixels!=0]]
    return Image.fromarray(canvas)


def main(candidate,output):
    candidate=candidate.resolve();output=output.resolve()
    if not candidate.is_relative_to(D.resolve()) or not output.is_relative_to(D.resolve()):raise ValueError('Use isolated Korean work proposals')
    if output==candidate or output.exists():raise ValueError('Fresh distinct output required')
    report_raw=(candidate/'proposal.json').read_bytes();report=json.loads(report_raw)
    if report['kind']!='korean_localization_integrated_proposal' or report['source_sha256']!=SOURCE_HASH or report['parent_sha256']!=PARENT_HASH:
        raise ValueError('Unsupported integrated proposal provenance')
    files={}
    for name,meta in report['files'].items():
        if Path(name).name!=name:raise ValueError('Unsafe resource path')
        raw=(candidate/name).read_bytes()
        if sha256(raw)!=meta['after'] or len(raw)!=meta['size']:raise ValueError(f'Input candidate hash/size differs: {name}')
        files[name]=raw
    result,proof=transformed(files);modified=[name for name in files if result[name]!=files[name]]
    if set(modified)!={'LOAD_U.ARC','MOJIPAT.ARC','SLUS_005.61'}:raise ValueError('Unexpected full-name resource set')
    proof['input_candidate']=str(candidate.relative_to(ROOT));proof['input_proposal_sha256']=sha256(report_raw)
    proof['input_file_sha256']={n:sha256(b) for n,b in files.items()}
    new_report=copy.deepcopy(report);new_report['runtime_verified']=False;new_report['bin_applied']=False
    for name in modified:
        new_report['files'][name]['after']=sha256(result[name])
        new_report['files'][name].setdefault('components',[]).append('loading_full_names_v1')
    new_report.setdefault('postprocessors',[]).append({'script':'scripts/prepare_korean_loading_names.py',
        'script_sha256':sha256(Path(__file__).read_bytes()),'input_proposal_sha256':sha256(report_raw),
        'input_candidate':str(candidate.relative_to(ROOT)),'changed_files':modified})
    new_report['loading_full_names']=proof
    new_report['coverage']['loading_full_names']=list(FULL_NAMES.values())
    # Verify source identities again before publishing the new proposal.
    if (candidate/'proposal.json').read_bytes()!=report_raw or any((candidate/n).read_bytes()!=b for n,b in files.items()):
        raise ValueError('Source candidate changed during processing')
    output.mkdir()
    for name,raw in result.items():(output/name).write_bytes(raw)
    for n in FULL_NAMES:
        loading_preview(result,n).save(output/f'loading_full_name_{n}.png')
        loading_preview(result,n).resize((960,720),Image.Resampling.NEAREST).save(output/f'loading_full_name_{n}_3x.png')
    (output/'proposal.json').write_text(json.dumps(new_report,ensure_ascii=False,indent=2),encoding='utf-8')
    (output/'loading_names_verification.json').write_text(json.dumps(proof,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({'output':str(output),'files':len(result),'modified':modified,'protected_frames':len(proof['protected_compositions']),
                      'exe_changed_bytes':len(proof['exe_edits']),'removed_parts':len(proof['invisible_interior_parts_removed']),
                      'bank':proof['bank'],'game_bin_written':False}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--candidate',type=Path,required=True);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();main(args.candidate,args.output)
