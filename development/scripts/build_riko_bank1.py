"""검증된 bank0 빌드에 bank1 벽 베기를 추가하는 미국판 전용 그래픽 사본 빌드."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import struct
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from scripts.riko_master_sheet import load_model, local
from scripts.project import new_run, write_json, working_cue
from scripts.discover_inputs import sha256
from scripts.build_riko_idle import patch_frames
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_bank_patch import patch_bank
from src.psx_frame_edit import read_indexed_png
from src.psx_player import graphics_bank, composition_frame, compose_indices, decode_stream
from src.psx_disc import write_archive_copy
from src.sprite_scale import validate_fixed_reference,validate_reference_views
from src.psx_air_spin import BODY as SPIN_BODY,EFFECTS as SPIN_EFFECTS,SCOPE as SPIN_SCOPE,SIZED_SCOPE,JUMP_SIZED_SCOPE,validate_heads,validate_body_mass,head_views
from src.psx_ice import BODY as ICE_BODY,SCOPE as ICE_SCOPE,PRESERVED_EFFECTS as ICE_EFFECTS,PRESERVED_BODY as ICE_UNEDITED,FLASH_BODY as ICE_FLASH,validate_flash
from src.psx_ryuenjin import SCOPE as RISE_SCOPE,TURN_SCOPE,BODY as RISE_BODY,NEW_BODY as RISE_NEW,EFFECTS as RISE_EFFECTS,RISE_LOOP,TURN_VIEWS
from src.psx_rakuhouha import SCOPE as BURST_SCOPE,BODY as BURST_BODY,CHARGE as BURST_CHARGE,validate_charge

from src.psx_raijingeki import SCOPE as THRUST_SCOPE,BODY as THRUST_BODY,NEW_BODY as THRUST_NEW,EFFECTS as THRUST_EFFECTS

from src.psx_victory import SCOPE as VICTORY_SCOPE, BODY as VICTORY_BODY, KEYS as VICTORY_KEYS, EFFECTS as VICTORY_EFFECTS, HEAD_VIEWS as VICTORY_HEAD_VIEWS, validate_victory

WALL_BODY=frozenset((50,51,53,54,56,57,59,61,63,65))
WALL_EFFECTS=frozenset((52,55,58,60,62,64))


def read_set(path, source_sha, palette, original_gfx, parts, reference):
    path=local(path,ROOT/'work/ver_buki_riko');record=json.loads(path.read_text('utf8'))
    victory=record.get('scope')==VICTORY_SCOPE
    thrust=record.get('scope') in (THRUST_SCOPE,VICTORY_SCOPE)
    burst=record.get('scope') in (BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE)
    turning=record.get('scope') in (TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE)
    rise=record.get('scope') in (RISE_SCOPE,TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE)
    ice=record.get('scope') in (ICE_SCOPE,RISE_SCOPE,TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE)
    spin=record.get('scope') in (SPIN_SCOPE,SIZED_SCOPE,JUMP_SIZED_SCOPE,ICE_SCOPE,RISE_SCOPE,TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE)
    body=WALL_BODY|SPIN_BODY if spin else WALL_BODY
    effects=WALL_EFFECTS|SPIN_EFFECTS if spin else WALL_EFFECTS
    if ice:body|=ICE_BODY;effects=(effects-ICE_BODY)|ICE_EFFECTS|ICE_UNEDITED
    if rise:body|=RISE_BODY;effects|=RISE_EFFECTS
    if burst:body|=BURST_BODY
    if thrust:body|=THRUST_BODY;effects|=THRUST_EFFECTS
    if victory:body|=VICTORY_BODY;effects|=VICTORY_EFFECTS
    if (record.get('scope') not in ('wall_saber_bank1_v1','wall_saber_bank1_v2',SPIN_SCOPE,SIZED_SCOPE,JUMP_SIZED_SCOPE,ICE_SCOPE,RISE_SCOPE,TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE) or record.get('graphics_bank')!=1 or record.get('parts_bank')!=5
            or set(record['frames'])!={str(n) for n in body|effects}):
        raise ValueError('Unsupported or incomplete bank1 scope/mapping')
    if (record['source_sha256']!=source_sha or record['original_graphics_sha256']!=sha256(original_gfx)
            or record['palette_sha256']!=sha256(palette)):
        raise ValueError('Bank1 source/palette hash mismatch')
    if record.get('preserved_effect_frames')!=sorted(effects):
        raise ValueError('Original wall effects must be preserved')
    if ice and record.get('preserved_non_effect_frames')!=sorted(ICE_UNEDITED):
        raise ValueError('Shared ice flash body must be identified separately')
    standard_path=ROOT/'config/riko_body_standard.json'
    standard=json.loads(standard_path.read_text('utf8'));scale=record['body_standard']
    if (scale['config_sha256']!=sha256(standard_path.read_bytes()) or scale.get('per_pose_bbox_resize') is not False
            or scale.get('anisotropic_scale') is not False or not 0<scale['uniform_scale']<=1):
        raise ValueError('Bank1 body scale metadata mismatch')
    words=struct.unpack('<16H',palette);frames={};paths={};bounds={};original_charge={}
    for key,r in record['frames'].items():
        p=local(path.parent/r['file'],path.parent)
        if sha256(p.read_bytes())!=r['sha256']:raise ValueError('Bank1 PNG hash mismatch')
        n=int(key);frames[n]=read_indexed_png(p,words);paths[n]=p
        f=graphics_bank(original_gfx,1)['frames'][n]
        raw=decode_stream(original_gfx,f['offset'],f['limit'],f['tile_count']*128)
        bounds[n]=compose_indices(raw.data,f['tile_count'],composition_frame(parts,5,n))[2]
        if burst and n in BURST_CHARGE:original_charge[n]=compose_indices(raw.data,f['tile_count'],composition_frame(parts,5,n))[:2]
    roi=standard['reference_roi'];front_reference=reference;front_roi=roi
    if record['scope']=='wall_saber_bank1_v2' or spin:
        view_path=ROOT/'config/riko_wall_head_view.json'
        if scale.get('wall_view_config_sha256')!=sha256(view_path.read_bytes()):
            raise ValueError('Bank1 wall view standard changed')
        view=json.loads(view_path.read_text('utf8'))
        png=local(ROOT/view['reference_png'],ROOT/'work/ver_buki_riko')
        if view['base_standard_sha256']!=sha256(standard_path.read_bytes()) or sha256(png.read_bytes())!=view['reference_png_sha256']:
            raise ValueError('Bank1 wall reference changed')
        reference=read_indexed_png(png,words)
        if sha256(reference[0])!=view['reference_indices_sha256'] or list(reference[1])!=[23,19]:
            raise ValueError('Bank1 wall head indices changed')
        roi=(0,0,23,19)
    checks=validate_fixed_reference({n:frames[n] for n in WALL_BODY},{n:bounds[n] for n in WALL_BODY},
                                    *reference,roi,{str(n):scale['head_world_positions'][str(n)] for n in WALL_BODY})
    if set(scale['head_world_positions'])!={str(n) for n in body}:raise ValueError('Unexpected head placement set')
    if spin:
        spin_checks=validate_heads({n:frames[n] for n in SPIN_BODY},bounds,*front_reference,front_roi,record['spin_registration'])
        if any(scale['head_world_positions'][n]!=r[:2] or scale['head_sizes'][n]!=r[2:] for n,r in spin_checks['head_rectangles'].items()):
            raise ValueError('Spin master head rectangles differ from native rotations')
        checks={'wall':checks,'spin':spin_checks}
        if record['scope'] in (SIZED_SCOPE,JUMP_SIZED_SCOPE,ICE_SCOPE,RISE_SCOPE,TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE):
            body_path=ROOT/'config'/('riko_spin_jump_body_standard.json' if record['scope'] in (JUMP_SIZED_SCOPE,ICE_SCOPE,RISE_SCOPE,TURN_SCOPE,BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE) else 'riko_spin_body_standard.json')
            if record.get('spin_body_standard_sha256')!=sha256(body_path.read_bytes()):raise ValueError('Spin body reference changed')
            body_standard=json.loads(body_path.read_text('utf8'))
            p=local(ROOT/body_standard['reference_png'],ROOT/'out/ver_buki_riko')
            if sha256(p.read_bytes())!=body_standard['reference_png_sha256']:raise ValueError('Spin body pose reference changed')
            ref_body=read_indexed_png(p,words)[0]
            x0,y0,x1,y1=front_roi;rw,rh=front_reference[1]
            head_count=sum(front_reference[0][y*rw+x]!=0 for y in range(y0,y1) for x in range(x0,x1))
            area=sum(v!=0 for v in ref_body)-head_count
            if area!=body_standard['reference_body_pixels']:raise ValueError('Body reference area mismatch')
            views=head_views(*front_reference,front_roi,record['spin_registration'])
            checks['body_mass']=validate_body_mass(frames,views,area,body_standard['ratio_bounds'])
    if ice:
        checks['ice']=validate_fixed_reference({n:frames[n] for n in ICE_BODY-SPIN_BODY-ICE_FLASH},bounds,
            *front_reference,front_roi,{str(n):scale['head_world_positions'][str(n)] for n in ICE_BODY-SPIN_BODY-ICE_FLASH})
        checks['ice_flash']=validate_flash(frames,bounds)
        if record.get('external_ice_effect')!={'animation':121,'parts_bank':6,'modified':False}:
            raise ValueError('Ice weapon must remain a separate unmodified resource')
    if rise:
        rise_heads={str(n):scale['head_world_positions'][str(n)] for n in RISE_NEW}
        loop_head_count=head_count
        if turning:
            view_path=ROOT/'config/riko_ladder_head_views.json'
            if record.get('rise_rear_view_config_sha256')!=sha256(view_path.read_bytes()) or record.get('rise_head_views')!=TURN_VIEWS:
                raise ValueError('Rising saber must turn to the registered rear view')
            view=json.loads(view_path.read_text('utf8'))['views']['ladder_rear']
            png=local(ROOT/view['reference_png'],ROOT/'work/ver_buki_riko')
            if sha256(png.read_bytes())!=view['reference_png_sha256']:raise ValueError('Rising rear view changed')
            rear=read_indexed_png(png,words)
            if list(rear[1])!=[23,19] or sha256(rear[0])!=view['reference_indices_sha256']:
                raise ValueError('Rising rear head size/indices changed')
            views={'front':(*front_reference,front_roi),'rear':(*rear,(0,0,23,19))}
            checks['rise']=validate_reference_views({n:frames[n] for n in RISE_NEW},bounds,views,TURN_VIEWS,rise_heads)
            loop_head_count=sum(v!=0 for v in rear[0])
        else:
            checks['rise']=validate_fixed_reference({n:frames[n] for n in RISE_NEW},bounds,*front_reference,front_roi,rise_heads)
        mass={n:sum(v!=0 for v in frames[n][0])-loop_head_count for n in RISE_LOOP}
        if any(not .9<=v/area<=1.2 for v in mass.values()):
            raise ValueError('Rising pose body mass differs from approved native jump')
        checks['rise_body_mass']={'reference_pixels':area,'body_pixels':mass,'ratio_bounds':[.9,1.2],
            'full_anatomical_quality_automatically_proven':False}
    if burst:
        checks['burst']=validate_fixed_reference({n:frames[n] for n in BURST_BODY},bounds,*front_reference,front_roi,{str(n):scale['head_world_positions'][str(n)] for n in BURST_BODY})
        checks['embedded_charge']=validate_charge(frames,original_charge,bounds)
        if record.get('external_burst_effect')!={'weapon_id':36,'parts_bank':6,'modified':False}:
            raise ValueError('Burst projectiles must remain separate unchanged resources')
    if thrust:
        checks['thrust']=validate_fixed_reference({n:frames[n] for n in THRUST_NEW},bounds,*front_reference,front_roi,{str(n):scale['head_world_positions'][str(n)] for n in THRUST_NEW})
        if record.get('external_thrust_effect')!={'weapon_id':32,'parts_bank':5,'modified':False}:
            raise ValueError('Thrust lightning must retain original source texels')
    if victory:
        if record.get('victory_head_views')!=VICTORY_HEAD_VIEWS:
            raise ValueError('Victory head turn mapping changed')
        data,(width,height)=front_reference
        x0,y0,x1,y1=front_roi
        mirror=bytes(data[y*width+x] for y in range(y0,y1) for x in range(x1-1,x0-1,-1))
        views={'front':(*front_reference,front_roi),'front_mirrored':(mirror,(x1-x0,y1-y0),(0,0,x1-x0,y1-y0))}
        checks['victory_heads']=validate_reference_views({n:frames[n] for n in VICTORY_KEYS},bounds,views,VICTORY_HEAD_VIEWS,{str(n):scale['head_world_positions'][str(n)] for n in VICTORY_KEYS})
        checks['departure']=validate_victory(original_gfx,parts,frames)
    return record,frames,paths,checks


def build(parent,extracted,bank1_set):
    m=load_model(parent,extracted)
    if m['manifest'].get('bank1_frame_inputs'):raise ValueError('Expected a bank0 baseline')
    profile,project,_,_,_,_,_=read_inputs(extracted)
    bank0={r['number']:m['frames'][key][:2] for key,r in m['records'].items()}
    baseline,_=patch_frames(m['arc'],m['gmeta'],m['gfx'],m['parts'],{**bank0,**m['preserved_effects']},m['palette'],m['manifest'].get('sword_effect_edits'))
    if baseline!=m['built_arc']:raise ValueError('Parent archive cannot be reproduced')
    selected=m['manifest']['art_selection'];reference=read_indexed_png(ROOT/selected['indexed_png'],m['words'])
    record,frames,paths,head_checks=read_set(bank1_set,profile['source_sha256'],m['palette'],m['gfx'],m['parts'],reference)
    gm=m['gmeta'];parent_gfx=baseline[gm['offset']:gm['offset']+gm['size']]
    bank=graphics_bank(parent_gfx,1)
    if parent_gfx[bank['base']:bank['end']]!=m['gfx'][bank['base']:bank['end']]:
        raise ValueError('Parent bank1 is not original')
    preserved=set(record['preserved_effect_frames'])
    patched_gfx,checks=patch_bank(parent_gfx,m['parts'],1,5,frames,preserved,clear_unreferenced=True)
    candidate=bytearray(baseline);candidate[gm['offset']:gm['offset']+gm['size']]=patched_gfx
    candidate=bytes(candidate)
    allowed_ranges=m['manifest']['allowed_archive_ranges']+[
        [gm['offset']+r['start'],gm['offset']+r['start']+r['encoded_bytes']] for r in checks['compression'] if r['encoded_bytes']]
    static_checks=None
    if record.get('static_effect_set'):
        if record.get('scope') not in (BURST_SCOPE,THRUST_SCOPE,VICTORY_SCOPE):raise ValueError('Static effect edits require Rakuhouha scope')
        from scripts.rakuhouha_static import apply_static_set
        static_path=local(bank1_set.parent/record['static_effect_set'],bank1_set.parent)
        candidate,static_checks=apply_static_set(candidate,static_path)
        allowed_ranges+=static_checks['allowed_archive_ranges']
    if any(a!=b and not any(lo<=i<hi for lo,hi in allowed_ranges) for i,(a,b) in enumerate(zip(m['arc'],candidate))):
        raise ValueError('Combined archive changes escaped declared ranges')
    out=ROOT/'out/ver_buki_riko'/('riko_bank1_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True,exist_ok=False)
    result=write_archive_copy(ROOT/project['source_bin'],out/'riko_motion.bin',profile['zero_archive'],candidate,profile['source_sha256'])
    (out/'riko_motion.cue').write_text(working_cue((ROOT/project['source_cue']).read_text('utf-8-sig'),'riko_motion.bin'),'ascii',newline='')
    (out/'modified.arc').write_bytes(candidate)
    for r in m['records'].values():shutil.copyfile(parent/r['filename'],out/r['filename'])
    for n in m['preserved_effects']:shutil.copyfile(parent/f'frame_{n:03d}.png',out/f'frame_{n:03d}.png')
    for n,(data,size) in frames.items():save_image(data,size,m['words'],out/f'bank1_{n:03d}.png')
    manifest={**m['manifest'],'kind':'riko_bank0_and_bank1_special_candidate','modified_bin':result,
        'modified_archive_sha256':sha256(candidate),'parent_build':str(parent),'parent_manifest_sha256':sha256((parent/'manifest.json').read_bytes()),
        'bank1_set':str(bank1_set.resolve()),'bank1_set_sha256':sha256(bank1_set.read_bytes()),'bank1_checks':checks,
        'bank1_head_checks':head_checks,'bank1_frame_inputs':{str(n):{'path':str(p),'sha256':sha256(p.read_bytes())} for n,p in paths.items()},
        'preserved_bank1_effect_frames':sorted(preserved),'bank1_runtime_verified':False,
        'runtime_modified_verified':False,'bank1_art_user_review_pending':True}
    manifest['compression']=[{'bank':0,**r} for r in m['manifest']['compression']]+checks['compression']
    manifest['allowed_archive_ranges']=allowed_ranges
    if static_checks:manifest['static_effect_edits']=static_checks
    manifest['decoded_changed_references']=m['manifest']['decoded_changed_references']+checks['decoded_changed_references']
    manifest['archive_changed_bytes']=sum(a!=b for a,b in zip(m['arc'],candidate))
    write_json(out/'manifest.json',manifest)
    print(json.dumps({'output':str(out),'sha256':result['sha256'],'bank1_body_references':len(frames)-len(preserved),'preserved_effects':len(preserved)}))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',type=Path,required=True)
    p.add_argument('--extract',type=Path,required=True);p.add_argument('--bank1-set',type=Path,required=True)
    a=p.parse_args();build(a.parent.resolve(),a.extract.resolve(),a.bank1_set.resolve())
