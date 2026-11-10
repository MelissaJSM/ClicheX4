"""린의 승인된 기본 이동 동작군을 같은 원작 압축 슬롯에 추가한다."""
import argparse,json,struct,sys
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.project import digest,load_project,inspect_references,working_cue
from scripts.build_rin_idle import entry,sha
from scripts.discover_inputs import psx_arc
from src.psx_player import bank_offsets,graphics_bank,decode_stream,composition_frame,compose_indices,indexed_atlas
from src.psx_frame_edit import edit_frame_set,edit_base_layer_set,read_indexed_png
from src.psx_compress import replace_stream
from src.psx_bank_patch import patch_bank
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from src.psx_hurt_launch import compose_launch, MULTI_FRAMES
from src.rin_hurt import validate as validate_rin_hurt
from src.rin_effects import validate_arrival,validate_departure,validate_ice_flash
from src.psx_air_spin import BODY as SPIN_BODY
from src.rin_spin import validate_spin
from src.psx_ice import BODY as ICE_BODY,PRESERVED_EFFECTS as ICE_EFFECTS
from scripts.build_riko_idle import GROUND_SLASH_BODY_FRAMES,GROUND_SLASH_EFFECT_FRAMES,AIR_SLASH_BODY_FRAMES,AIR_SLASH_EFFECT_FRAMES
from scripts.build_riko_idle import LADDER_BODY_FRAMES,LADDER_EFFECT_FRAMES,LADDER_BASE_COUNTS
SCOPES={'idle_style':set((0,1,2,5,6,146,147,148)),'air':set(range(21,35)),'dash':set(range(44,53)),'wall':set(range(35,44)),
        'hurt':set(range(135,146))|set(range(149,155)),'ground':GROUND_SLASH_BODY_FRAMES,'air_slash':AIR_SLASH_BODY_FRAMES,
        'wall_saber':set((50,51,53,54,56,57,59,61,63,65)),'ladder':LADDER_BODY_FRAMES,'arrival':set(range(247,254)),'victory':set(range(9)),'spin':SPIN_BODY,'ice':ICE_BODY}
SCOPE_BANKS={'wall_saber':(1,5),'victory':(1,5),'spin':(1,5),'ice':(1,5)}
WALL_SABER_EFFECTS=set((52,55,58,60,62,64))

def prepare(recipe,scope):
    recipe=recipe.resolve()
    if not recipe.is_relative_to(ROOT/'work/ver_rin_nana'):raise ValueError('Unexpected art path')
    art=recipe.parent;r=json.loads(recipe.read_text('utf-8'));ids=SCOPES[scope]
    graphics_index,parts_index=SCOPE_BANKS.get(scope,(0,0))
    if r.get('graphics_bank',0)!=graphics_index or r.get('parts_bank',0)!=parts_index:raise ValueError('Recipe bank mapping differs')
    if r['issues'] or set(map(int,r['frames']))!=ids:raise ValueError('Incomplete or invalid art')
    effects={'ground':GROUND_SLASH_EFFECT_FRAMES,'air_slash':AIR_SLASH_EFFECT_FRAMES,'wall_saber':WALL_SABER_EFFECTS,'ladder':LADDER_EFFECT_FRAMES,'victory':set(range(9,14)),'spin':set(range(162,177,2)),'ice':ICE_EFFECTS}.get(scope,set())
    preserved_bodies={133} if scope=='spin' else set()
    if preserved_bodies and r.get('preserved_shared_body_frames')!=sorted(preserved_bodies):raise ValueError('Explicit shared body preservation required')
    preserved=effects|preserved_bodies
    if scope=='ladder' and {int(n):v for n,v in r.get('base_part_counts',{}).items()}!=LADDER_BASE_COUNTS:raise ValueError('Explicit original ladder base ownership required')
    if effects and r.get('preserved_effect_frames')!=sorted(effects):raise ValueError('Explicit original effect preservation required')
    parent=(ROOT/r['parent']).resolve()
    if not parent.is_relative_to(ROOT/'out/ver_rin_nana'):raise ValueError('Unexpected parent')
    pm=json.loads((parent/'manifest.json').read_text('utf-8'));arc=(parent/'modified.arc').read_bytes()
    if pm['modified_bin']['sha256']!=r['parent_sha256'] or sha(arc)!=pm['modified_archive_sha256']:raise ValueError('Parent identity mismatch')
    project=load_project(ROOT,'ver_rin_nana');inspect_references(ROOT,project)
    gm,g=entry(arc,2);cm,oldparts=entry(arc,3);_,pal=entry(arc,9);words=struct.unpack_from('<16H',pal)
    parts=(art/'composition_entry.bin').read_bytes()
    if sha(parts)!=r['composition_sha256'] or len(parts)!=len(oldparts):raise ValueError('Invalid parts source')
    allowed=set()
    for bi,offset in enumerate(bank_offsets(oldparts)):
        count=struct.unpack_from('<I',oldparts,offset)[0]>>16
        for n in range(count):
            a=composition_frame(oldparts,bi,n);b=composition_frame(parts,bi,n)
            if a==b:continue
            targeted=(bi==parts_index and n in ids) or (scope=='idle_style' and bi==5 and n in (0,86))
            if not targeted or len(a['parts'])!=len(b['parts']):raise ValueError('Unrelated part change')
            for before,after in zip(a['parts'],b['parts']):
                permitted={'x'}
                if scope=='arrival' and n==252 and before['tile'] in (6,9):
                    if after['y']!=before['y']-1:raise ValueError('Arrival ribbon tile must move up exactly one pixel')
                    permitted.add('y');allowed.add(before['record_offset']+3)
                if any(before[k]!=after[k] for k in before if k not in permitted):raise ValueError('Unapproved presentation part change')
                allowed.add(before['record_offset']+2)
    if any(a!=b and i not in allowed for i,(a,b) in enumerate(zip(oldparts,parts))):raise ValueError('Unknown composition mutation')
    frames={}
    for n in ids:
        info=r['frames'][str(n)];p=art/info['file']
        if digest(p)!=info['sha256']:raise ValueError('Changed indexed art')
        multi=scope=='hurt' and n in MULTI_FRAMES
        frames[n]=read_indexed_png(p,struct.unpack_from('<64H',pal) if multi else words,palette_banks=4 if multi else 1)
    special=validate_rin_hurt(g,parts,frames) if scope=='hurt' else {}
    groups={};bank=graphics_bank(g,graphics_index)
    arrival_validation=None
    departure_validation=validate_departure(g,parts,frames) if scope=='victory' else None
    spin_validation=validate_spin(g,parts,frames) if scope=='spin' else None
    ice_validation=validate_ice_flash(g,parts,frames) if scope=='ice' else None
    if scope=='ice':
        if r.get('preserved_authored_body_frames')!=[132]:raise ValueError('Ice must preserve existing spin lead132')
        f=bank['frames'][132];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
        if composition_frame(parts,5,132)!=composition_frame(oldparts,5,132) or frames[132]!=compose_indices(raw,f['tile_count'],composition_frame(parts,5,132))[:2]:raise ValueError('Ice changed existing spin lead132')
    if scope=='arrival':
        def native(n):
            f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            return compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))
        idle=native(147)
        arrival_validation=validate_arrival(g,parts,frames,{n:native(n)[2] for n in frames},idle[:2],idle[2])
    for f in bank['frames']:
        if f['index'] in ids:groups.setdefault(f['offset'],[]).append(f)
    modified=g;budgets=[]
    if scope=='idle_style':
        modified,bank_report=patch_bank(g,parts,0,0,frames,clear_unreferenced=True,allow_slot_growth=True)
        budgets=bank_report['compression'];groups={}
    if graphics_index==1:
        allframes=dict(frames)
        for n in preserved:
            f=bank['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            allframes[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,parts_index,n))[:2]
        modified,bank_report=patch_bank(g,parts,graphics_index,parts_index,allframes,preserved,clear_unreferenced=True)
        budgets=bank_report['compression'];groups={}
    for offset,refs in groups.items():
        shared=[f['index'] for f in bank['frames'] if f['index'] not in ids and f['offset']==offset]
        if any(n not in effects for n in shared):raise ValueError('Unselected shared bitmap')
        f=refs[0];raw=decode_stream(g,offset,f['limit'],f['tile_count']*128).data
        if scope=='arrival' and any(q['index']==252 for q in refs):
            if shared:raise ValueError('Arrival ribbon bitmap has an unowned reference')
            raw=bytes(len(raw))
        edits=[(composition_frame(parts,parts_index,q['index']),*frames[q['index']]) for q in refs]
        if scope=='ladder' and {q['index'] for q in refs}<=LADDER_BASE_COUNTS.keys():
            packed=edit_base_layer_set(raw,f['tile_count'],[(*e,LADDER_BASE_COUNTS[q['index']]) for q,e in zip(refs,edits)])
        else:
            packed=special[f['index']] if f['index'] in special else edit_frame_set(raw,f['tile_count'],edits,preserved_compositions=[composition_frame(parts,parts_index,n) for n in shared],overlap_policy='equal_sources' if graphics_index==0 and any(q['index'] in (81,252) for q in refs) else 'reject')
        atlas,_,_=indexed_atlas(packed,f['tile_count'])
        for q in refs:
            for part in composition_frame(parts,parts_index,q['index'])['parts']:
                t=part['tile']
                if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Mirror U0 clipping boundary')
        modified,budget=replace_stream(modified,f,packed);budgets.append({'frames':[q['index'] for q in refs],**budget})
    checked=0
    # Source column U0 must stay transparent for both branches, including bank1.
    for n in ids:
        f=bank['frames'][n];raw=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data;atlas,_,_=indexed_atlas(raw,f['tile_count'])
        for part in composition_frame(parts,parts_index,n)['parts']:
            t=part['tile']
            if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Mirror U0 clipping boundary')
    for bi in (0,1):
        if graphics_bank(g,bi)!=graphics_bank(modified,bi):raise ValueError('Resource addresses changed')
        for f in graphics_bank(g,bi)['frames']:
            old=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;new=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data
            if bi==graphics_index and f['index'] in ids:
                expected,size=frames[f['index']];actual=compose_launch(new,f['tile_count'],composition_frame(parts,parts_index,f['index']))
                if actual[:2]!=(expected,tuple(size)):raise ValueError('Roundtrip displayed pixels differ')
            elif bi==graphics_index and f['index'] in preserved:
                c=composition_frame(parts,parts_index,f['index'])
                if compose_indices(old,f['tile_count'],c)[:3]!=compose_indices(new,f['tile_count'],c)[:3]:raise ValueError('Original saber effect changed')
            elif old!=new:raise ValueError('Existing sprite changed')
            checked+=1
    idle_aliases=None
    if scope=='idle_style':
        if set(r.get('bank1_aliases',{}))!={'0','86'}:raise ValueError('Both existing idle aliases required')
        aliases={};bank1=graphics_bank(modified,1);preserved_aliases={1,2,87,88,89,90}
        def world(pixels,size,bounds):
            return {(i%size[0]+bounds[0],i//size[0]+bounds[1]):v for i,v in enumerate(pixels) if v}
        neutral_bounds=compose_indices(decode_stream(modified,bank['frames'][147]['offset'],bank['frames'][147]['limit'],bank['frames'][147]['tile_count']*128).data,bank['frames'][147]['tile_count'],composition_frame(parts,0,147))[2]
        neutral=world(*frames[147],neutral_bounds)
        for n,info in r['bank1_aliases'].items():
            path=art/info['file']
            if digest(path)!=info['sha256']:raise ValueError('Changed alias art')
            aliases[int(n)]=read_indexed_png(path,words)
            f=bank1['frames'][int(n)];raw=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data
            bounds=compose_indices(raw,f['tile_count'],composition_frame(parts,5,int(n)))[2]
            if world(*aliases[int(n)],bounds)!=neutral:raise ValueError('Idle alias world pixels differ')
        for n in preserved_aliases:
            f=bank1['frames'][n];raw=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data
            aliases[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,5,n))[:2]
        modified,idle_aliases=patch_bank(modified,parts,1,5,aliases,preserved_aliases,clear_unreferenced=True,allow_slot_growth=True)
        for n in (0,86):
            f=bank1['frames'][n];raw=decode_stream(modified,f['offset'],f['limit'],f['tile_count']*128).data;atlas,_,_=indexed_atlas(raw,f['tile_count'])
            for part in composition_frame(parts,5,n)['parts']:
                t=part['tile']
                if t%16==0 and any(atlas[(t//16*16+y)*256] for y in range(16)):raise ValueError('Idle alias mirror boundary')
    result=bytearray(arc);result[gm['offset']:gm['offset']+gm['size']]=modified;result[cm['offset']:cm['offset']+cm['size']]=parts
    for e in psx_arc(arc):
        if e['type'] not in ('0x2','0x3') and result[e['offset']:e['offset']+e['size']]!=arc[e['offset']:e['offset']+e['size']]:raise ValueError('Other ARC data changed')
    report={'graphics_bank':graphics_index,'parts_bank':parts_index,'decoded_references_checked':checked,'new_frames':sorted(ids),'previous_unshared_bitmaps_preserved':True,'previous_displayed_frames_preserved':True,'preserved_saber_effect_frames':sorted(effects),'palette_animation_other_entries_preserved':True,'only_selected_part_x_changed':True,'graphics_addresses_preserved':True,'compression':budgets,'recipe_sha256':digest(recipe)}
    if idle_aliases:report['idle_aliases']=idle_aliases
    if arrival_validation:
        report.update({'arrival_validation':arrival_validation,'only_selected_part_x_changed':False,'selected_part_offsets_changed_only':True,'arrival_252_ribbon_column_y_change':-1})
    if departure_validation:report['departure_validation']=departure_validation
    if preserved_bodies:report['preserved_shared_body_frames']=sorted(preserved_bodies)
    if spin_validation:report['spin_validation']=spin_validation
    if ice_validation:report.update({'ice_validation':ice_validation,'preserved_authored_body_frames':[132]})
    return project,bytes(result),report,r,pm,parent

def main():
    p=argparse.ArgumentParser();p.add_argument('--recipe',type=Path,required=True);p.add_argument('--scope',choices=SCOPES,required=True);args=p.parse_args()
    project,arc,report,r,pm,parent=prepare(args.recipe,args.scope);_,again,*_=prepare(args.recipe,args.scope)
    if arc!=again:raise ValueError('Repeated ARC differs')
    if digest(parent/'rin_nana.bin')!=r['parent_sha256']:raise ValueError('Actual parent BIN differs')
    out=ROOT/'out/ver_rin_nana'/('rin_'+args.scope+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'));out.mkdir(parents=True)
    profile=json.loads((ROOT/'config/ps1_us_slus00561.json').read_text('utf-8'));source=ROOT/project['source_bin'];target=out/'rin_nana.bin'
    result=write_archive_copy(source,target,profile['zero_archive'],arc,project['source_sha256'])
    (out/'rin_nana.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'rin_nana.bin'),'ascii',newline='')
    (out/'modified.arc').write_bytes(arc)
    changed={v['lba'] for v in result['changed_sectors']};rec=profile['zero_archive'];readback=bytearray();count=0
    with source.open('rb') as a,target.open('rb') as b:
        while True:
            x=a.read(2352);y=b.read(2352)
            if not x:break
            if (x!=y)!=(count in changed):raise ValueError('Unexpected disc difference')
            if count in changed:validate_checks(y)
            if rec['lba']<=count<rec['lba']+(rec['size']+2047)//2048:readback.extend(y[24:2072])
            count+=1
    if readback[:len(arc)]!=arc:raise ValueError('BIN reextraction differs')
    report.update({'repeat_arc_identical':True,'all_disc_sectors_compared':count,'changed_sectors':len(changed),'edc_ecc_checked':True,'reextracted_arc_equal':True})
    graphics_index,_=SCOPE_BANKS.get(args.scope,(0,0))
    cumulative=sorted(set(pm.get('cumulative_frames',[0,1,2,*range(3,21),146,147,148]))|(SCOPES[args.scope] if graphics_index==0 else set()))
    cumulative_bank1=sorted(set(pm.get('cumulative_bank1_frames',[]))|(SCOPES[args.scope] if graphics_index==1 else set()))
    manifest={'project':'ver_rin_nana','task':'zero_rin','kind':args.scope,'parent':r['parent'],'parent_sha256':r['parent_sha256'],'source_sha256':project['source_sha256'],'modified_bin':result,'modified_archive_sha256':sha(arc),'art_recipe':args.recipe.as_posix(),'verification':report,'cumulative_frames':cumulative,'runtime_verified':False}
    manifest['cumulative_bank1_frames']=cumulative_bank1
    manifest['bank1_frame_inputs']=dict(pm.get('bank1_frame_inputs',{}))
    if args.scope=='idle_style':
        manifest['bank1_frame_inputs'].update({n:{'path':str(args.recipe.resolve().parent/q['file']),'sha256':q['sha256']} for n,q in r['bank1_aliases'].items()})
    if graphics_index==1:
        manifest['bank1_frame_inputs'].update({n:{'path':str(args.recipe.resolve().parent/q['file']),'sha256':q['sha256']} for n,q in r['frames'].items()})
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n','utf-8')
    pointer={'project':'ver_rin_nana','task':'zero_rin','build':out.relative_to(ROOT).as_posix(),'cue':(out/'rin_nana.cue').relative_to(ROOT).as_posix(),'sha256':result['sha256'],'frames':cumulative,'runtime_verified':False}
    pointer['bank1_frames']=cumulative_bank1
    (ROOT/'projects/ver_rin_nana/current_build.json').write_text(json.dumps(pointer,indent=2)+'\n','utf-8')
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'new_frames':len(SCOPES[args.scope]),'total_frames':len(cumulative)+len(cumulative_bank1),'changed_sectors':len(changed)}))

if __name__=='__main__':main()
