"""Riko 제작분 전체를 편집용 시트로 내보내고, 좌표·공유 관계를 검사해 분리한다."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,digest
from scripts.discover_inputs import psx_arc,sha256
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from scripts.build_riko_idle import patch_frames,validate_sword_effect,IDLE_FRAMES,check_motion_scale,GROUND_SLASH_SCOPE,AIR_SLASH_SCOPE,SUPPORTED_SABER_EFFECTS as SABER_EFFECT_FRAMES,LADDER_SCOPE,LADDER_BODY_FRAMES,LADDER_BASE_COUNTS
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
from src.psx_frame_edit import read_indexed_png
from src.sprite_sheet import pack_frames,unpack_frames
from scripts.build_riko_idle import LOW_HP_SCOPE,HURT_SCOPE,HURT_FRAMES
from scripts.build_riko_idle import LAUNCH_SCOPE,SHIPPUUGA_SCOPE,SHIPPUUGA_NEW,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE,BEAM_BODY_FRAMES,read_launch_palette
from src.psx_hurt_launch import LAUNCH_FRAMES,MULTI_FRAMES,compose_launch as compose_indices


def local(path,root):
    path=path.resolve()
    if not path.is_relative_to(root.resolve()):raise ValueError('Path escaped the project area')
    return path


def load_model(build,extracted):
    import numpy as np
    build=local(build,ROOT/'out/ver_buki_riko');extracted=local(extracted,ROOT/'work/ver_buki_riko')
    manifest=json.loads((build/'manifest.json').read_text('utf8'))
    if manifest.get('illustrations'):
        from scripts.build_riko_illustrations import validate_layer
        parent=local(Path(manifest['illustrations']['parent_build']),ROOT/'out/ver_buki_riko')
        if parent==build or json.loads((parent/'manifest.json').read_text('utf8')).get('illustrations'):
            raise ValueError('Recursive illustration parent refused')
        return validate_layer(build,manifest,load_model(parent,extracted))
    if manifest.get('ui_overlay'):
        from scripts.build_riko_ui import validate_layer
        parent=local(Path(manifest['ui_overlay']['parent_build']),ROOT/'out/ver_buki_riko')
        if parent==build or json.loads((parent/'manifest.json').read_text('utf8')).get('ui_overlay'):
            raise ValueError('Recursive UI parent refused')
        return validate_layer(build,manifest,load_model(parent,extracted))
    if manifest.get('jump_alignment'):
        from scripts.build_riko_jump_alignment import validate_layer
        parent=local(Path(manifest['jump_alignment']['parent_build']),ROOT/'out/ver_buki_riko')
        if parent==build or json.loads((parent/'manifest.json').read_text('utf8')).get('jump_alignment'):
            raise ValueError('Recursive alignment parent refused')
        return validate_layer(build,manifest,load_model(parent,extracted))
    if manifest.get('personal_effects'):
        from scripts.build_riko_personal_effects import validate_layer
        parent=local(Path(manifest['personal_effects']['parent_build']),ROOT/'out/ver_buki_riko')
        if parent==build or json.loads((parent/'manifest.json').read_text('utf8')).get('personal_effects'):
            raise ValueError('Recursive effect parent refused')
        return validate_layer(build,manifest,load_model(parent,extracted))
    profile,_,arc,gmeta,gfx,parts,_=read_inputs(extracted)
    if manifest['source_sha256']!=profile['source_sha256']:raise ValueError('Unsupported source hash')
    changed=(build/'modified.arc').read_bytes()
    if sha256(changed)!=manifest['modified_archive_sha256']:raise ValueError('Build archive hash mismatch')
    entries=psx_arc(changed)
    def entry(kind):
        e=next(e for e in entries if e['type']==hex(kind));return changed[e['offset']:e['offset']+e['size']]
    changed_gfx=entry(2);palette=entry(9)[:32];words=struct.unpack('<16H',palette)
    if entry(3)!=parts:raise ValueError('Build changes composition data')
    bank=graphics_bank(changed_gfx,0);frames={};records={};heads={};effects={}
    standard=json.loads((ROOT/'config/riko_body_standard.json').read_text('utf8'))
    selected=json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text('utf8'))
    master=local(ROOT/selected['indexed_png'],ROOT/'out/ver_buki_riko')
    if digest(master)!=selected['indexed_png_sha256']:raise ValueError('Selected identity reference changed')
    ref,rs=read_indexed_png(master,words);x0,y0,x1,y1=standard['reference_roi']
    head=np.frombuffer(ref,dtype=np.uint8).reshape(rs[1],rs[0])[y0:y1,x0:x1]
    hair=np.isin(head,[4,8,14]);hy,hx=np.nonzero(hair);anchor_y,anchor_x=int(hy[0]),int(hx[0])
    motion=None;sheet_words=words
    if any(35<=int(n)<=43 for n in manifest['frame_inputs']):
        motion_path=local(Path(manifest['motion_set']),ROOT/'work/ver_buki_riko')
        if digest(motion_path)!=manifest['motion_set_sha256']:raise ValueError('Motion metadata changed')
        motion=json.loads(motion_path.read_text('utf8'))
        if motion.get('scope') not in ('jump_run_dash_wall_v1',GROUND_SLASH_SCOPE,AIR_SLASH_SCOPE,LADDER_SCOPE,LOW_HP_SCOPE,HURT_SCOPE,LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):raise ValueError('Wall frames need explicit wall scope')
        if motion['scope'] in (LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):sheet_words=read_launch_palette(motion,motion_path,palette)
    for n in sorted(map(int,manifest['frame_inputs'])):
        name=f'{"idle" if n in IDLE_FRAMES else "frame"}_{n:03d}.png';path=build/name
        if digest(path)!=manifest['frame_inputs'][str(n)]['sha256']:raise ValueError('Build PNG hash mismatch')
        data,size=read_indexed_png(path,sheet_words if n in MULTI_FRAMES else words,palette_banks=4 if n in MULTI_FRAMES else 1);f=bank['frames'][n];comp=composition_frame(parts,0,n)
        raw=decode_stream(changed_gfx,f['offset'],f['limit'],f['tile_count']*128).data
        actual,actual_size,bounds,_=compose_indices(raw,f['tile_count'],comp)
        if (data,size)!=(actual,actual_size):raise ValueError('PNG differs from built frame')
        if n in SABER_EFFECT_FRAMES:
            original=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
            expected,expected_size=compose_indices(original,f['tile_count'],comp)[:2]
            if size!=expected_size:raise ValueError('Saber effect canvas changed')
            validate_sword_effect(expected,data,manifest.get('sword_effect_edits',{}).get(str(n)))
            effects[n]=(data,size)
            continue
        key=f'bank0_{n:03d}';frames[key]=(data,size,bounds)
        if motion and (35<=n<=43 or n in LADDER_BODY_FRAMES or n in HURT_FRAMES or n in LAUNCH_FRAMES or n in SHIPPUUGA_NEW or n in BEAM_BODY_FRAMES):
            wx,wy=motion['body_standard']['head_world_positions'][str(n)]
            heads[key]=[wx-bounds[0],wy-bounds[1],23,19]
            records[key]={'number':n,'filename':name,'png_sha256':digest(path),'indices_sha256':sha256(data),
                          'size':list(size),'bounds':list(bounds),'stream_offset':f['offset'],'tile_count':f['tile_count']}
            continue
        image=np.frombuffer(data,dtype=np.uint8).reshape(size[1],size[0]);matches=[]
        for ay,ax in np.argwhere(image==head[anchor_y,anchor_x]):
            x,y=int(ax)-anchor_x,int(ay)-anchor_y
            if x<0 or y<0 or x+head.shape[1]>size[0] or y+head.shape[0]>size[1]:continue
            candidate=image[y:y+head.shape[0],x:x+head.shape[1]]
            if np.array_equal(candidate[hair],head[hair]):matches.append([x,y])
        if len(matches)!=1:raise ValueError(f'Ambiguous head registration: {key}')
        heads[key]=[*matches[0],head.shape[1],head.shape[0]]
        records[key]={'number':n,'filename':name,'png_sha256':digest(path),'indices_sha256':sha256(data),
                      'size':list(size),'bounds':list(bounds),'stream_offset':f['offset'],'tile_count':f['tile_count']}
    if motion:
        selected_frames={int(n):(effects[int(n)] if int(n) in effects else frames[f'bank0_{int(n):03d}'][:2]) for n in motion['frames']}
        check_motion_scale(motion,selected_frames,gfx,parts,(ref,rs))
    bank1_effects={}
    if manifest.get('bank1_frame_inputs'):
        from scripts.build_riko_bank1 import read_set
        recipe=local(Path(manifest['bank1_set']),ROOT/'work/ver_buki_riko')
        if digest(recipe)!=manifest['bank1_set_sha256']:raise ValueError('Bank1 metadata changed')
        record,expected,_,_=read_set(recipe,profile['source_sha256'],palette,gfx,parts,(ref,rs))
        bank1=graphics_bank(changed_gfx,1)
        for n,(data,size) in expected.items():
            name=f'bank1_{n:03d}.png';path=build/name
            if digest(path)!=manifest['bank1_frame_inputs'][str(n)]['sha256'] or read_indexed_png(path,words)!=(data,size):
                raise ValueError('Bank1 build PNG mismatch')
            f=bank1['frames'][n];comp=composition_frame(parts,5,n)
            raw=decode_stream(changed_gfx,f['offset'],f['limit'],f['tile_count']*128).data
            actual,actual_size,bounds,_=compose_indices(raw,f['tile_count'],comp)
            if (data,size)!=(actual,actual_size):raise ValueError('Bank1 archive does not match PNG')
            if n in record['preserved_effect_frames']:
                original=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
                if compose_indices(original,f['tile_count'],comp)[:2]!=(data,size):raise ValueError('Bank1 effect changed')
                bank1_effects[n]=(data,size);continue
            key=f'bank1_{n:03d}';frames[key]=(data,size,bounds)
            wx,wy=record['body_standard']['head_world_positions'][str(n)]
            heads[key]=[wx-bounds[0],wy-bounds[1],*record['body_standard'].get('head_sizes',{}).get(str(n),[23,19])]
            records[key]={'number':n,'bank':1,'parts_bank':5,'filename':name,'png_sha256':digest(path),
                'indices_sha256':sha256(data),'size':list(size),'bounds':list(bounds),
                'stream_offset':f['offset'],'tile_count':f['tile_count']}
    if manifest.get('static_effect_edits'):
        from scripts.rakuhouha_static import apply_static_set
        static=manifest['static_effect_edits'];recipe=local(Path(static['recipe']),ROOT/'work/ver_buki_riko')
        if digest(recipe)!=static['recipe_sha256']:raise ValueError('Static recipe binding changed')
        rebuilt,checks=apply_static_set(arc,recipe)
        em=next(e for e in psx_arc(arc) if e['type']=='0x10206');lo=em['offset'];hi=lo+em['size']
        if changed[lo:hi]!=rebuilt[lo:hi] or checks!=static:raise ValueError('Static effect build differs from bound recipe')
    return {'build':build,'extract':extracted,'manifest':manifest,'arc':arc,'gmeta':gmeta,'gfx':gfx,'parts':parts,
            'built_arc':changed,'palette':palette,'words':words,'sheet_words':sheet_words,'frames':frames,'records':records,'heads':heads,
            'preserved_effects':effects,'preserved_bank1_effects':bank1_effects}


def preview(png,layout,target):
    from PIL import Image,ImageDraw
    image=Image.open(png).convert('RGBA')
    cw,ch=layout['cell'];columns=layout['columns'];rows=(len(layout['frames'])+columns-1)//columns
    board=Image.new('RGBA',(columns*cw*2,rows*(ch*2+20)),(40,43,55,255));draw=ImageDraw.Draw(board)
    for i,r in enumerate(layout['frames']):
        x,y,w,h=r['cell'];cell=image.crop((x,y,x+w,y+h)).resize((w*2,h*2),Image.Resampling.NEAREST)
        px,py=i%columns*cw*2,i//columns*(ch*2+20);board.alpha_composite(cell,(px,py+20));draw.text((px+4,py+4),r['key'],fill='white')
    board.save(target)


def pack_current_frames(m):
    # Wider workspace cells accommodate Raijingeki's original x=-49 part.
    # This is sheet padding only; game frame sizes and origins are unchanged.
    wide=any(b[0]<-48 or b[2]>48 for _,_,b in m['frames'].values())
    return pack_frames(m['frames'],cell=(112 if wide else 96,112),origin=(56 if wide else 48,56),max_index=len(m['sheet_words'])-1)


def export(build,extracted,inventory):
    m=load_model(build,extracted);inventory=local(inventory,ROOT/'work/ver_buki_riko')
    inv=json.loads((inventory/'inventory.json').read_text('utf8'))
    if inv['source_sha256']!=m['manifest']['source_sha256'] or inv['archive_sha256']!=sha256(m['arc']):raise ValueError('Inventory source mismatch')
    pixels,layout=pack_current_frames(m)
    out=new_run(ROOT,'ver_buki_riko','production_master')
    save_image(pixels,layout['size'],m['sheet_words'],out/'riko_master_indexed.png')
    layout_record={'schema_version':1,'kind':'editable_current_riko_frames_not_complete_character',
        'build':str(m['build']),'extract':str(m['extract']),'source_sha256':m['manifest']['source_sha256'],
        'build_manifest_sha256':digest(m['build']/'manifest.json'),'build_arc_sha256':sha256(m['built_arc']),
        'build_bin_sha256':m['manifest']['modified_bin']['sha256'],'palette_sha256':sha256(m['palette']),
        'layout':layout,'source_frames':m['records'],'protected_head_rectangles':m['heads'],
        'master_sha256_at_export':digest(out/'riko_master_indexed.png'),'blank_cells_are_not_new_frame_slots':True,
        'palette_encoding':'clut*16+index; index0 transparent; CLUT2 preview is a captured palette snapshot' if len(m['sheet_words'])>16 else 'single CLUT0',
        'preserved_saber_effect_frames_outside_editable_sheet':m['manifest'].get('preserved_saber_effect_frames',sorted(m['preserved_effects'])),
        'preserved_bank1_effect_frames_outside_editable_sheet':sorted(n for n in m['preserved_bank1_effects'] if n!=133),
        'preserved_bank1_body_frames_outside_editable_sheet':[133] if 133 in m['preserved_bank1_effects'] else [],
        'sword_effect_frames_outside_editable_sheet':sorted(map(int,m['manifest'].get('sword_effect_edits',{})))}
    if m['manifest'].get('static_effect_edits'):
        static=m['manifest']['static_effect_edits']
        layout_record['static_effects_outside_body_sheet']=static
        import shutil
        recipe=Path(static['recipe']);record=json.loads(recipe.read_text('utf8'))
        for item in record['frames'].values():
            shutil.copyfile(recipe.parent/item['file'],out/item['file'])
        write_json(out/'static_effects.local.json',static)
    if m['manifest'].get('personal_effects'):
        layout_record['personal_effects_outside_body_sheet']=m['manifest']['personal_effects']
        layout_record['preserved_bank1_effect_frames_outside_editable_sheet']=[n for n in layout_record['preserved_bank1_effect_frames_outside_editable_sheet'] if n not in range(9,14)]
    if m['manifest'].get('jump_alignment'):
        layout_record['jump_alignment']=m['manifest']['jump_alignment']
    if m['manifest'].get('ui_overlay'):
        layout_record['ui_overlay_outside_body_sheet']=m['manifest']['ui_overlay']
    if m['manifest'].get('illustrations'):
        layout_record['illustrations_outside_body_sheet']=m['manifest']['illustrations']
    write_json(out/'master.local.json',layout_record)
    preview(out/'riko_master_indexed.png',layout,out/'riko_master_preview_2x.png')
    original_words=struct.unpack_from('<16H',(m['extract']/'palette_bank.bin').read_bytes())
    source_layouts={}
    for bank in (0,1):
        frames={}
        for key,r in inv['frames'].items():
            if r['bank']!=bank or not r['image']:continue
            data,size=read_indexed_png(inventory/r['image'],original_words)
            if sha256(data)!=r['indices_sha256']:raise ValueError('Original reference image changed')
            frames[key]=(data,size,r['bounds'])
        data,atlas=pack_frames(frames,columns=8,cell=(208,152),origin=(136,88))
        save_image(data,atlas['size'],original_words,out/f'zero_bank{bank}_reference_indexed.png')
        source_layouts[str(bank)]=atlas
    write_json(out/'zero_reference_layout.json',{'original_source_only':True,'banks':source_layouts,'uninterpreted':inv['unverified_frames']})
    applied=set(m['records']);coverage=[]
    for key,r in inv['frames'].items():
        aids=[a['id'] for a in inv['animations'] if a['graphics_bank']==r['bank'] and any(s['frame']==r['frame'] for s in a['sequence'])]
        coverage.append({'key':key,'riko_production':('existing_applied' if key in applied else
                         'custom_sword_added_original_trail_preserved' if r['bank']==0 and str(r['frame']) in m['manifest'].get('sword_effect_edits',{}) else
                         'original_body_preserved' if r['bank']==1 and r['frame']==133 and 133 in m['preserved_bank1_effects'] else
                         'original_effect_preserved' if (r['bank']==0 and r['frame'] in m['preserved_effects'] or r['bank']==1 and r['frame'] in m['preserved_bank1_effects']) else 'not_produced'),
                         'original_render':r['render_status'],'animations':aids,'shared_stream':inv['stream_sharing'][str(r['stream_offset'])]})
    write_json(out/'coverage.json',{'entries':coverage,'made_riko_references':len(applied),
        'original_decoded_references':len(inv['frames']),'original_composed_references':inv['rendered_frames'],
        'counts_are_references_not_unique_poses':True,
        'preserved_saber_effect_references':len(m['preserved_effects'])+len(m['preserved_bank1_effects'])-int(133 in m['preserved_bank1_effects'])-len(m['manifest'].get('sword_effect_edits',{})),
        'preserved_unedited_body_references':[{'bank':1,'frame':133}] if 133 in m['preserved_bank1_effects'] else [],
        'custom_sword_effect_references':len(m['manifest'].get('sword_effect_edits',{}))})
    made_wall=all(f'bank0_{n:03d}' in applied for n in range(35,44))
    wall={'source':'Original animation inventory and the explicitly bound current build',
          'animations':[inv['animations'][n] for n in (13,14,15)],'target_frames':list(range(35,44)),
          'new_frames':[] if made_wall else list(range(35,44)),'art_present_in_bound_build':made_wall,
          'reused_existing_jump_frames':[22,23],'shared_groups':[[39,40],[41,42,43]],
          'runtime_verified':False,'new_head_views_need_art_review':True}
    write_json(out/'wall_group_plan.json',wall)
    print(json.dumps({'output':str(out),'riko_references':len(applied),'original_rendered':inv['rendered_frames'],'uninterpreted':len(inv['unverified_frames'])}))


def split(master,sheet):
    import numpy as np
    master=local(master,ROOT/'work/ver_buki_riko');sheet=local(sheet,ROOT/'work/ver_buki_riko')
    record=json.loads(master.read_text('utf8'))
    m=load_model(Path(record['build']),Path(record['extract']))
    if digest(m['build']/'manifest.json')!=record['build_manifest_sha256'] or sha256(m['built_arc'])!=record['build_arc_sha256']:
        raise ValueError('Master source binding changed')
    _,expected_layout=pack_current_frames(m)
    if record['layout']!=expected_layout or record['source_frames']!=m['records'] or record['protected_head_rectangles']!=m['heads']:
        raise ValueError('Master coordinate or source metadata changed')
    if record['source_sha256']!=m['manifest']['source_sha256'] or record['palette_sha256']!=sha256(m['palette']):raise ValueError('Master source/palette mismatch')
    data,size=read_indexed_png(sheet,m['sheet_words'],palette_banks=len(m['sheet_words'])//16);frames=unpack_frames(data,size,expected_layout);changes=[];numbered={};numbered_bank1={}
    for key,(pixels,native_size) in frames.items():
        source,_,bounds=m['frames'][key];x,y,w,h=m['heads'][key]
        before=np.frombuffer(source,dtype=np.uint8).reshape(native_size[1],native_size[0]);after=np.frombuffer(pixels,dtype=np.uint8).reshape(before.shape)
        mask=before[y:y+h,x:x+w]!=0
        if not np.array_equal(before[y:y+h,x:x+w][mask],after[y:y+h,x:x+w][mask]):raise ValueError(f'Protected head changed: {key}')
        r=m['records'][key];n=r['number'];bank=r.get('bank',0);comp=composition_frame(m.get('display_parts',m['parts']),r.get('parts_bank',0),n)
        for part in (comp['parts'][:LADDER_BASE_COUNTS[n]] if bank==0 and n in LADDER_BASE_COUNTS else comp['parts']):
            # Launch layers overlap: a visible spark at this coordinate is not
            # a body U=0 texel. validate_launch checks actual source atlas edges.
            if bank==0 and n in LAUNCH_FRAMES:continue
            if part['tile']%16==0:
                px,py=part['x']-bounds[0]+(15 if part['flip_x'] else 0),part['y']-bounds[1]
                if np.any(after[py:py+16,px]):raise ValueError(f'Opaque reflected U=0 edge: {key} part {part["index"]}')
        if pixels!=source:changes.append(key if bank else n)
        (numbered_bank1 if bank else numbered)[n]=(pixels,native_size)
    candidate,checks=patch_frames(m['arc'],m['gmeta'],m['gfx'],m['parts'],{**numbered,**m['preserved_effects']},m['palette'],m['manifest'].get('sword_effect_edits'))
    bank1_checks=None
    if numbered_bank1:
        from src.psx_bank_patch import patch_bank
        gm=m['gmeta'];base=candidate[gm['offset']:gm['offset']+gm['size']]
        changed,bank1_checks=patch_bank(base,m['parts'],1,5,{**numbered_bank1,**m['preserved_bank1_effects']},m['preserved_bank1_effects'],clear_unreferenced=True)
        candidate=candidate[:gm['offset']]+changed+candidate[gm['offset']+gm['size']:]
    if m['manifest'].get('static_effect_edits'):
        from scripts.rakuhouha_static import apply_static_set
        static=m['manifest']['static_effect_edits']
        if record.get('static_effects_outside_body_sheet')!=static:raise ValueError('Master static binding changed')
        candidate,_=apply_static_set(candidate,Path(static['recipe']))
    if m['manifest'].get('personal_effects'):
        from src.psx_personal_effects import apply_warp
        if record.get('personal_effects_outside_body_sheet')!=m['manifest']['personal_effects']:
            raise ValueError('Master personal effects binding changed')
        candidate,_=apply_warp(candidate)
    if m['manifest'].get('jump_alignment'):
        from scripts.build_riko_jump_alignment import apply_alignment
        if record.get('jump_alignment')!=m['manifest']['jump_alignment']:
            raise ValueError('Master jump alignment binding changed')
        candidate,_=apply_alignment(candidate)
    if m['manifest'].get('illustrations'):
        from scripts.build_riko_illustrations import apply_player_ui
        if record.get('illustrations_outside_body_sheet')!=m['manifest']['illustrations']:
            raise ValueError('Master illustration binding changed')
        candidate=apply_player_ui(candidate,Path(m['manifest']['illustrations']['recipe']))
    exact=candidate==m['built_arc']
    if m['manifest'].get('ui_overlay') and record.get('ui_overlay_outside_body_sheet')!=m['manifest']['ui_overlay']:
        raise ValueError('Master UI overlay binding changed')
    if not changes and not exact:raise ValueError('Unchanged master did not reconstruct identical archive')
    # All validation precedes creation. Never overwrite the source sheet or build.
    out=new_run(ROOT,'ver_buki_riko','master_split')
    png_exact=[]
    for key,(pixels,native_size) in frames.items():
        target=out/m['records'][key]['filename'];r=m['records'][key]
        save_image(pixels,native_size,m['sheet_words'] if r.get('bank',0)==0 and r['number'] in MULTI_FRAMES else m['words'],target)
        if digest(target)==m['records'][key]['png_sha256']:png_exact.append(key)
    with (out/'candidate.arc').open('xb') as stream:stream.write(candidate)
    report={'master':str(master),'sheet':str(sheet),'sheet_sha256':digest(sheet),'source_build':str(m['build']),
            'changed_frames':changes,'png_byte_identical_frames':sorted(png_exact),'archive_byte_identical':exact,
            'candidate_archive_sha256':sha256(candidate),'source_archive_sha256':sha256(m['built_arc']),
            'checks':checks,'bank1_checks':bank1_checks,'game_bin_written':False,'current_build_changed':False,'new_art_approved':False}
    write_json(out/'validation.local.json',report)
    print(json.dumps({'output':str(out),'changed_frames':changes,'png_byte_identical':len(png_exact),'archive_byte_identical':exact,'game_bin_written':False}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='action',required=True)
    e=sub.add_parser('export');e.add_argument('--build',type=Path,required=True);e.add_argument('--extract',type=Path,required=True);e.add_argument('--inventory',type=Path,required=True)
    s=sub.add_parser('split');s.add_argument('--master',type=Path,required=True);s.add_argument('--sheet',type=Path,required=True)
    a=p.parse_args()
    if a.action=='export':export(a.build,a.extract,a.inventory)
    else:split(a.master,a.sheet)
