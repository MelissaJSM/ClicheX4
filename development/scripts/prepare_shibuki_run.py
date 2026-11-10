"""수용 체형의 이동 16포즈와 공유 사격 참조를 같은 크기의 X ARC에 넣는다."""
import argparse,json,struct,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import new_run,write_json,inspect_references,load_project
from scripts.discover_inputs import psx_arc,sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas,bank_offsets
from src.psx_compress import replace_stream,encode_stream
from src.psx_tile_layout import pack_rectangles,remap_tiles,fill_redundant_pixels
from src.psx_paired_layout import pack_pair,pack_joint_pair,pack_variant_pair

def world_canvas(packed,tiles,comp,*,allowed_cluts=None):
    pixels,size,bounds,_=compose_indices(packed,tiles,comp,allowed_cluts=allowed_cluts)
    out=np.zeros((80,96),np.uint8);x,y=bounds[0]+48,bounds[1]+40
    raster=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);yy,xx=np.nonzero(raster)
    if len(xx) and (xx.min()+x<0 or yy.min()+y<0 or xx.max()+x>=96 or yy.max()+y>=80):raise ValueError('Visible composition outside proof canvas')
    out[yy+y,xx+x]=raster[yy,xx]
    return out

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project',choices=('ver_buki_riko','ver_rin_nana'),default='ver_buki_riko')
    parser.add_argument('--art',type=Path,required=True)
    parser.add_argument('--layout',type=Path,required=True)
    parser.add_argument('--parent',type=Path,default=ROOT/'out/ver_buki_riko/shibuki_idle_20261026T044150188556Z')
    parser.add_argument('--pairs',type=Path,help='Generated body and buster layer directory')
    parser.add_argument('--scope',choices=('run','air','dash','wall','fall_legs'),default='run')
    args=parser.parse_args();artdir=args.art.resolve();parent=args.parent.resolve()
    name='nana' if args.project=='ver_rin_nana' else 'shibuki'
    artroot=ROOT/'work'/args.project/(name+'_art')
    if args.scope=='fall_legs' and name!='nana':raise ValueError('Fall leg revision is Nana-only')
    base_numbers=set(range(33,55,2) if args.scope=='air' else range(1,33,2))
    if args.scope=='dash':base_numbers={67,69,71,75,77,79,81,83}
    if args.scope=='wall':base_numbers=set(range(55,67,2))
    if args.scope=='fall_legs':base_numbers={43,45,47}
    selected=base_numbers|{n+1 for n in base_numbers}
    if args.scope=='dash':selected|={73,74}
    if not artdir.is_relative_to(artroot) or not parent.is_relative_to(ROOT/'out'/args.project):
        raise ValueError('Expected isolated Shibuki inputs')
    inspect_references(ROOT,load_project(ROOT,args.project))
    manifest=json.loads((parent/'manifest.json').read_text(encoding='utf-8'))
    arc=(parent/'modified.arc').read_bytes()
    if sha256(arc)!=manifest['modified_archive_sha256'] or manifest['task']!='x_'+name:raise ValueError('Parent ARC/task changed')
    cfg=json.loads((ROOT/'config/shibuki_x_us.json').read_text(encoding='utf-8'))
    art=json.loads((artdir/'art.json').read_text(encoding='utf-8'))
    layouts=json.loads(args.layout.read_text(encoding='utf-8'))
    planpath=ROOT/('work/ver_buki_riko/shibuki_art/air_v1/plan.json' if args.scope=='air' else 'work/ver_buki_riko/shibuki_run_plan/20261026T044831801392Z/plan.json')
    if args.scope=='dash':planpath=ROOT/'work/ver_buki_riko/shibuki_art/dash_v1/plan.json'
    if args.scope=='wall':planpath=ROOT/'work/ver_buki_riko/shibuki_art/wall_v1/plan.json'
    if name=='nana':planpath=artroot/(args.scope+'_v1')/'plan.json'
    plan=json.loads(planpath.read_text())
    if {r['frame'] for r in art['frames']}!=base_numbers or {r['frame'] for r in layouts}!=base_numbers or not all(r['fits'] for r in layouts):raise ValueError('Incomplete art/layout')
    if args.scope in ('air','dash','wall','fall_legs') and not args.pairs:raise ValueError('Paired shooting art required')
    pairs=None
    if args.pairs:
        args.pairs=args.pairs.resolve()
        if not args.pairs.is_relative_to(artroot):raise ValueError('Unexpected pair directory')
        pairs=json.loads((args.pairs/'pairs.json').read_text())
        if pairs['palette_words']!=art['palette_words'] or {r['run'] for r in pairs['frames']}!=base_numbers:raise ValueError('Pair art mismatch')
        packing=json.loads((args.pairs/'packing.json').read_text())
        if {r['frame'] for r in packing}!=base_numbers or not all(r['fits'] for r in packing):raise ValueError('Incomplete pair storage solution')
    inv=json.loads((ROOT/art['source_inventory']).read_text(encoding='utf-8'))
    entries=psx_arc(arc)
    def entry(t):
        e=next(e for e in entries if int(e['type'],16)==t);return e,arc[e['offset']:e['offset']+e['size']]
    gm,gfx=entry(2);pm,parts=entry(3);palmeta,palette=entry(9)
    if list(struct.unpack('<16H',palette[:32]))!=art['palette_words']:raise ValueError('Palette differs from accepted idle')
    updated_parts=bytearray(parts);updated_gfx=gfx;reports=[];desired={};allowed_records=set()
    bank=graphics_bank(gfx,0,allow_bank_aliases=True)
    for n in sorted(base_numbers):
        pair=next(p for p in plan['paired_frames'] if p['frames'][0]==n)
        r=next(r for r in art['frames'] if r['frame']==n);pic=Image.open(artdir/r['image'])
        target=np.array(pic)
        if pic.mode!='P' or pic.size!=(96,80) or target.max()>15:raise ValueError('Invalid run raster')
        rects=next(r for r in layouts if r['frame']==n)['rects']
        desc=bank['frames'][n];decoded=decode_stream(gfx,desc['offset'],desc['limit'],desc['tile_count']*128)
        aliases={71:73,72:74} if args.scope=='dash' and n==71 else {}
        expected_aliases=[[0,n],[0,n+1]]+[[0,q] for q in aliases.values()]
        if inv['stream_sharing'][str(desc['offset'])]!=expected_aliases:raise ValueError('Unexpected stream alias')
        writable=set(pair['common_base_tiles']+pair['nonshoot_only_tiles']+pair['shoot_only_tiles'])
        armor={t for ts in pair['armor_overlay_tiles'].values() for t in ts}
        if writable&armor:raise ValueError('Base/armor tile conflict')
        if pairs:
            pair_art=next(r for r in pairs['frames'] if r['run']==n)
            layers=[np.array(Image.open(args.pairs/f'{name}_{n:03d}.png')) for name in ('run','common','shoot_body','gun')]
            if not np.array_equal(layers[0],target):raise ValueError('Pair run differs from normalized body')
            storage=next(r for r in packing if r['frame']==n)
            common_rects=storage.get('common_rects',[pair_art['common_rects'][i] for i in storage.get('common_order',range(len(pair_art['common_rects'])))])
            if storage.get('variant_run_rects'):
                shot_target=np.array(Image.open(args.pairs/f'shoot_{n:03d}.png'))
                packed,run_parts,shot_parts,blank,shot_target=pack_variant_pair(decoded.data,desc['tile_count'],target,shot_target,common_rects,storage['variant_run_rects'],storage['variant_shot_rects'],writable)
            elif storage.get('joint_unique_rects'):
                shot_target=np.array(Image.open(args.pairs/f'shoot_{n:03d}.png'))
                packed,run_parts,shot_parts,blank,shot_target=pack_joint_pair(decoded.data,desc['tile_count'],target,shot_target,common_rects,storage['joint_unique_rects'],writable)
            else:
                packed,run_parts,shot_parts,blank,shot_target=pack_pair(decoded.data,desc['tile_count'],*layers,common_rects,pair_art['run_arm_rect'],pair_art['gun_rect'],writable)
            if sha256(packed)!=storage['raw_sha256']:raise ValueError('Packing source changed')
            mapping={int(k):v for k,v in storage['mapping'].items()};flips={int(k):v for k,v in storage['flips'].items()};shifts={int(k):v for k,v in storage.get('shifts',{}).items()}
            if set(mapping)!=writable:raise ValueError('Storage permutation escaped base tiles')
            packed=remap_tiles(packed,desc['tile_count'],mapping,flips,shifts)
            def remapped(records):return [(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,x,y in records]
            run_parts,shot_parts=remapped(run_parts),remapped(shot_parts)
            blank=mapping[blank] if blank is not None else None
            assignments={n:run_parts,n+1:shot_parts};targets={n:target,n+1:shot_target};tiles=[p[0] for p in run_parts]
            if storage.get('overlap_fill'):
                packed=fill_redundant_pixels(packed,desc['tile_count'],assignments,targets,storage['overlap_fill'],writable)
            if storage.get('post_mapping'):
                postmap={int(k):v for k,v in storage['post_mapping'].items()}
                postflip={int(k):v for k,v in storage.get('post_flips',{}).items()}
                postshift={int(k):v for k,v in storage.get('post_shifts',{}).items()}
                if set(postmap)!=writable:raise ValueError('Post storage escaped body tiles')
                # Secondary storage starts from pixels already oriented by the first map.
                # Compose both flips and translate the new source padding in display space.
                packed=remap_tiles(packed,desc['tile_count'],postmap,postflip,postshift)
                def post_records(records):
                    result=[]
                    for t,x,y,flag in records:
                        dx,dy=postshift.get(t,(0,0))
                        result.append((postmap[t],x+dx if flag&64 else x-dx,y+dy if flag&128 else y-dy,flag^postflip.get(t,0)))
                    return result
                assignments={q:post_records(rows) for q,rows in assignments.items()}
                if blank is not None:blank=postmap[blank]
                tiles=[q[0] for q in assignments[n]]
        else:
            tiles=sorted(t for t in writable if t%16!=0)[:len(rects)]
            blank=next((t for t in sorted(writable) if t not in tiles),None)
            if len(tiles)!=len(rects) or blank is None:raise ValueError('No safe tile assignment')
            packed=pack_rectangles(decoded.data,desc['tile_count'],target.tobytes(),pic.size,rects,tiles,writable)
            assignments={q:[(t,*r,0) for t,r in zip(tiles,rects)] for q in (n,n+1)};targets={n:target,n+1:target}
        for number in (n,n+1):
            comp=composition_frame(parts,0,number)
            if args.scope=='fall_legs':
                before=world_canvas(decoded.data,desc['tile_count'],comp);cut={43:44,45:44,47:46}[n];yy,xx=np.indices(before.shape);mask=(yy>cut)&(yy<70)&(xx>=37)&(xx<64)
                if not np.array_equal(before[~mask],targets[number][~mask]):raise ValueError('Fall revision changed pixels outside legs')
                if not np.array_equal(targets[n][mask],targets[n+1][mask]):raise ValueError('Fall shooting legs differ')
            assignments_for_frame=assignments[number]
            final_atlas,_,_=indexed_atlas(packed,desc['tile_count'])
            for tile,_,_,flags in assignments_for_frame:
                tx,ty=tile%16*16,tile//16*16
                if tile%16==0 and (flags&64 or any(final_atlas[(ty+y)*256+tx] for y in range(16))):raise ValueError('Final GPU U edge')
                if flags&128 and (tile//16)%16==0 and any(final_atlas[ty*256+tx:ty*256+tx+16]):raise ValueError('Final GPU V edge')
            if len(assignments_for_frame)>len(comp['parts']):raise ValueError('Would need additional part records')
            for i,q in enumerate(comp['parts']):
                if q['page'] or q['clut'] or q['unknown_flags']:raise ValueError('Unsupported part flags')
                if i<len(assignments_for_frame):tile,x,y,flags=assignments_for_frame[i]
                else:
                    if blank is None:raise ValueError('No blank tile for spare record')
                    tile=blank;x,y=rects[0];flags=0
                struct.pack_into('<BBbb',updated_parts,q['record_offset'],flags,tile,x-48,y-40)
                allowed_records.update(range(q['record_offset'],q['record_offset']+4))
            desired[number]=targets[number]
        # 73/74 reuse 71/72's body and append nine immutable speed-line records.
        # Copy only the body prefix; the separate tile and its placement stay intact.
        for primary,alias in aliases.items():
            primary_parts=composition_frame(parts,0,primary)['parts']
            alias_parts=composition_frame(parts,0,alias)['parts']
            signature=lambda q:(q['flags'],q['tile'],q['x'],q['y'])
            if sorted(map(signature,primary_parts))!=sorted(map(signature,alias_parts[:len(primary_parts)])):
                raise ValueError('Dash alias body differs')
            effects=alias_parts[len(primary_parts):]
            if len(effects)!=9 or {q['tile'] for q in effects}!={6} or 6 in writable:raise ValueError('Dash effect overlap')
            for src,dst in zip(composition_frame(updated_parts,0,primary)['parts'],alias_parts):
                so,do=src['record_offset'],dst['record_offset']
                updated_parts[do:do+4]=updated_parts[so:so+4];allowed_records.update(range(do,do+4))
            for q in effects:
                pos=q['record_offset']
                if updated_parts[pos:pos+4]!=parts[pos:pos+4]:raise ValueError('Dash effect record changed')
            desired[alias]=world_canvas(packed,desc['tile_count'],composition_frame(updated_parts,0,alias))
        old_atlas,_,_=indexed_atlas(decoded.data,desc['tile_count']);new_atlas,_,_=indexed_atlas(packed,desc['tile_count'])
        for tile in range(desc['tile_count']):
            if tile in writable:continue
            x,y=(tile%16)*16,(tile//16)*16
            if any(old_atlas[(y+j)*256+x:(y+j)*256+x+16]!=new_atlas[(y+j)*256+x:(y+j)*256+x+16] for j in range(16)):
                raise ValueError('Unselected/armor tile changed')
        for number in (n,n+1):
            if not np.array_equal(world_canvas(packed,desc['tile_count'],composition_frame(updated_parts,0,number)),targets[number]):
                raise ValueError('Raster differs after composition')
        encoded=encode_stream(packed)
        report={'frames':[n,n+1],'encoded_bytes':len(encoded),'original_bytes':decoded.end-decoded.start,'rectangles':rects,'tiles':tiles,'blank_tile':blank}
        print(json.dumps(report),flush=True)
        updated_gfx,compression=replace_stream(updated_gfx,desc,packed);report.update(compression);reports.append(report)
    changed_parts=[i for i,(a,b) in enumerate(zip(parts,updated_parts)) if a!=b]
    if not set(changed_parts)<=allowed_records:raise ValueError('Unexpected composition mutation')
    for bi,base in enumerate(bank_offsets(parts)):
        count=struct.unpack_from('<I',parts,base)[0]>>16
        for n in range(count):
            if bi==0 and n in selected:continue
            if composition_frame(parts,bi,n)!=composition_frame(updated_parts,bi,n):raise ValueError('An unselected composition aliases edited records')
    changed=[];checked_references=0
    for bi in range(len(inv['graphics_banks'])):
        for f in graphics_bank(gfx,bi,allow_bank_aliases=True)['frames']:
            checked_references+=1
            a=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
            b=decode_stream(updated_gfx,f['offset'],f['limit'],f['tile_count']*128).data
            if a!=b:
                if bi!=0 or f['index'] not in selected:raise ValueError('Unexpected bitmap changed')
                changed.append([bi,f['index']])
    patched=bytearray(arc);patched[gm['offset']:gm['offset']+gm['size']]=updated_gfx;patched[pm['offset']:pm['offset']+pm['size']]=updated_parts
    allowed=[(gm['offset']+r['start'],gm['offset']+r['start']+r['encoded_bytes']) for r in reports]+[(pm['offset']+i,pm['offset']+i+1) for i in changed_parts]
    if len(patched)!=len(arc) or any(a!=b and not any(lo<=i<hi for lo,hi in allowed) for i,(a,b) in enumerate(zip(arc,patched))):raise ValueError('ARC changed outside declared ranges')
    if {n for bi,n in changed}!=selected:raise ValueError('Missing changed reference')
    out=new_run(ROOT,args.project,name+'_'+args.scope);(out/'modified.arc').write_bytes(patched)
    font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',16);sheet=Image.new('RGB',(8*224,2*256),'#222630');draw=ImageDraw.Draw(sheet)
    for i,r in enumerate(art['frames']):
        n=r['frame'];p=save_image(desired[n].tobytes(),(96,80),art['palette_words'],out/f'run_{n:03d}.png').convert('RGBA')
        x,y=(i%8)*224,(i//8)*256;draw.text((x+6,y+5),f'{name.title()} {n:03d}',font=font,fill='white');p=p.resize((288,240),Image.Resampling.NEAREST);sheet.paste(p,(x-32,y+20),p)
    sheet.save(out/'run_master_3x.png')
    pictures=[]
    preview_animation=plan['animations']['12'] if args.scope=='air' else plan['animations']['14'] if args.scope=='wall' else plan['run_animation']
    for s in preview_animation['steps']:
        n=s['frame']
        if not (out/f'run_{n:03d}.png').exists():
            f=bank['frames'][n];raw=decode_stream(updated_gfx,f['offset'],f['limit'],f['tile_count']*128).data
            canvas=world_canvas(raw,f['tile_count'],composition_frame(updated_parts,0,n))
            save_image(canvas.tobytes(),(96,80),art['palette_words'],out/f'run_{n:03d}.png')
        p=Image.open(out/f'run_{n:03d}.png').convert('RGBA').resize((384,320),Image.Resampling.NEAREST)
        bg=Image.new('RGB',p.size,'#222630');bg.paste(p,(0,0),p);pictures.append(bg)
    pictures[0].save(out/'run_preview.gif',save_all=True,append_images=pictures[1:],duration=[round(s['duration_ticks']*1000/60) for s in preview_animation['steps']],loop=0,disposal=2)
    recipe={'task':'x_shibuki','scope':'base_air_22' if args.scope=='air' else 'base_run_16_with_shared_shoot_references','parent_build':str(parent.relative_to(ROOT)),
            'parent_bin_sha256':manifest['modified_bin']['sha256'],'parent_arc_sha256':sha256(arc),
            'original_arc_sha256':cfg['archive']['sha256'],'modified_arc_sha256':sha256(patched),'arc_size':len(patched),
            'source_art':str(artdir.relative_to(ROOT)),'art_manifest_sha256':sha256((artdir/'art.json').read_bytes()),
            'layout':str(args.layout.resolve().relative_to(ROOT)),'compression':reports,'changed_composition_bytes':changed_parts,
            'changed_bitmap_references':changed,'other_compositions_preserved':True,'other_decoded_bitmaps_preserved':True,
            'armor_tiles_preserved':True,'idle_palette_preserved':True,'idle_frames_preserved':True,
            'animation':plan.get('run_animation'),'start_animation':plan.get('start_animation'),'air_animations':plan.get('animations'),'timing_changed':False,'resources_relocated':False,
            'run_frames_preserved':args.scope=='air','standing_frames_preserved':args.scope=='air',
            'shooting_body_uses_same_run_pose':pairs is None,'shooting_arm_art_pending':pairs is None,'runtime_verified':False,
            'paired_art':str(args.pairs.relative_to(ROOT)) if args.pairs else None,
            'paired_manifest_sha256':sha256((args.pairs/'pairs.json').read_bytes()) if args.pairs else None,
            'packing_manifest_sha256':sha256((args.pairs/'packing.json').read_bytes()) if args.pairs else None,
            'earlier_keypose_style_accepted':True,'current_revision_style_accepted':False,'full_loop_user_review_pending':True}
    if args.scope=='dash':recipe.update(scope='base_dash_18',run_frames_preserved=True,standing_frames_preserved=True,air_frames_preserved=True,dash_animations=plan['animations'],dash_speed_streak_tile_preserved=True)
    if args.scope=='wall':recipe.update(scope='base_wall_12',run_frames_preserved=True,standing_frames_preserved=True,air_frames_preserved=True,dash_frames_preserved=True,wall_animations=plan['animations'])
    if args.scope=='fall_legs':recipe.update(scope='fall_legs_revision_6',run_frames_preserved=True,standing_frames_preserved=True,rise_and_landing_preserved=True,dash_frames_preserved=True,wall_frames_preserved=True,hurt_frames_preserved=True,upper_body_gun_and_registration_preserved=True,only_legs_changed=True)
    if name=='nana':
        approval=load_project(ROOT,args.project)['nana_style_approval']
        if art['master_sha256']!=approval['master_sha256'] or art['palette_sha256']!=approval['palette_sha256']:raise ValueError('Nana master mismatch')
        recipe.update(task='x_nana',scope={'air':'base_air_22','dash':'base_dash_18','wall':'base_wall_12','run':'base_run_and_shoot_32','fall_legs':'fall_legs_revision_6'}[args.scope],standing_frames_preserved=True,checked_bitmap_references=checked_references,master_sha256=art['master_sha256'],palette_sha256=art['palette_sha256'])
        for n,v in desired.items():save_image(v.tobytes(),(96,80),art['palette_words'],out/f'frame_{n:03d}.png')
        recipe['frame_sha256']={str(n):sha256((out/f'frame_{n:03d}.png').read_bytes()) for n in sorted(desired)}
    write_json(out/'recipe.json',recipe);print(json.dumps({'output':str(out),'arc_sha256':sha256(patched)}))

if __name__=='__main__':main()
