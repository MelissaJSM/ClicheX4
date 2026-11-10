"""선택된 Riko 대기 그림을 여섯 표시 프레임과 정상 팔레트에 적용하는 사본 빌드."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.discover_inputs import psx_arc, sha256
from scripts.project import working_cue, write_json, validate_bin, checked_path
from scripts.repack_zero import read_inputs
from scripts.extract_zero import save_image
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices
from src.psx_frame_edit import read_indexed_png, edit_frame_set, edit_base_layer_set
from src.psx_compress import replace_stream
from src.psx_disc import write_archive_copy
from src.psx_hurt import HURT_FRAMES, edit_hurt_stream, validate_hurt_frames
from src.psx_hurt_launch import LAUNCH_FRAMES, MULTI_FRAMES, validate_launch, compose_launch as compose_indices

IDLE_FRAMES = (0, 1, 2, 146, 147, 148)
JUMP_FRAMES = frozenset((5, 6, *range(21, 35)))
RUN_FRAMES = frozenset((3, 4, *range(7, 21)))
DASH_FRAMES = frozenset(range(44, 53))
WALL_FRAMES = frozenset(range(35, 44))
GROUND_SLASH_BODY_FRAMES = frozenset((61,62,63,65,67,69,71,73,75,77,79,81,82,83,85,87,89,91,93,95,97,99,101,
                                    105,107,109,111,113,115,117,119,121,123,125,127,130,131,132,133,134))
GROUND_SLASH_EFFECT_FRAMES = frozenset(range(61,135)) - GROUND_SLASH_BODY_FRAMES
GROUND_SLASH_SCOPE = 'jump_run_dash_wall_ground_slash_v1'
AIR_SLASH_BODY_FRAMES = frozenset((*range(213,230,2),*range(230,247,2)))
AIR_SLASH_EFFECT_FRAMES = frozenset(range(213,247)) - AIR_SLASH_BODY_FRAMES
LADDER_EFFECT_FRAMES = frozenset((198,200,203,205,207,209,211))
LADDER_BODY_FRAMES = frozenset(range(174,213)) - LADDER_EFFECT_FRAMES
LADDER_BASE_COUNTS = {**dict.fromkeys(range(174,178),8),**dict.fromkeys(range(178,182),9),
                      **dict.fromkeys(range(182,186),10),**dict.fromkeys(range(186,190),8)}
SABER_EFFECT_FRAMES = GROUND_SLASH_EFFECT_FRAMES | AIR_SLASH_EFFECT_FRAMES
KNOWN_SABER_EFFECT_FRAMES = SABER_EFFECT_FRAMES | LADDER_EFFECT_FRAMES
AIR_SLASH_SCOPE = 'jump_run_dash_wall_ground_air_slash_v1'
LADDER_SCOPE = 'jump_run_dash_wall_ground_air_ladder_v1'
LOW_HP_FRAMES = frozenset(range(149,155))
LOW_HP_SCOPE = 'jump_run_dash_wall_ground_air_ladder_low_hp_v1'
HURT_SCOPE = 'jump_run_dash_wall_ground_air_ladder_low_hp_hurt_v1'
LAUNCH_SCOPE = HURT_SCOPE + '_launch_v1'
SHIPPUUGA_SCOPE = LAUNCH_SCOPE + '_shippuuga_v1'
SHIPPUUGA_NEW = frozenset((155,156,158,160,162,164,166,168,170,172))
SHIPPUUGA_BODY = SHIPPUUGA_NEW | frozenset((131,132,133,134))
SHIPPUUGA_EFFECTS = frozenset(range(157,174,2))
SHIPPUUGA_VIEWS = {str(n):'ladder_rear' if n>=160 else 'approved_front' for n in SHIPPUUGA_NEW}
SUPPORTED_SABER_EFFECTS = KNOWN_SABER_EFFECT_FRAMES | SHIPPUUGA_EFFECTS
from src.psx_beam_in import BEAM_BODY_FRAMES, BEAM_DERIVED_FRAMES, validate_beam_frames
BEAM_IN_SCOPE = SHIPPUUGA_SCOPE + "_beam_in_v1"
BEAM_IN_V2_SCOPE = SHIPPUUGA_SCOPE + "_beam_in_v2"

def read_launch_palette(motion, path, normal):
    record=motion['launch_production']['preview_palette']
    target=(path.parent/record['file']).resolve()
    if not target.is_relative_to(path.parent.resolve()) or sha256(target.read_bytes())!=record['sha256']:
        raise ValueError('Launch preview palette path/hash mismatch')
    data=target.read_bytes()
    if len(data)!=128 or data[:32]!=normal:raise ValueError('Launch preview normal palette differs')
    return struct.unpack('<64H',data)


def validate_motion_scope(motion):
    """묶음 누락이나 이름만 바꾼 임의 동작 확대를 빌드 전에 거부한다."""
    scope = motion.get('scope', 'jump_v1')
    supported = {'jump_v1': JUMP_FRAMES, 'jump_and_run_v1': JUMP_FRAMES | RUN_FRAMES,
                 'jump_run_dash_v1': JUMP_FRAMES | RUN_FRAMES | DASH_FRAMES,
                 'jump_run_dash_wall_v1': JUMP_FRAMES | RUN_FRAMES | DASH_FRAMES | WALL_FRAMES,
                 GROUND_SLASH_SCOPE: JUMP_FRAMES | RUN_FRAMES | DASH_FRAMES | WALL_FRAMES | frozenset(range(61,135)),
                 AIR_SLASH_SCOPE: JUMP_FRAMES | RUN_FRAMES | DASH_FRAMES | WALL_FRAMES | frozenset(range(61,135)) | frozenset(range(213,247))}
    supported[LADDER_SCOPE] = supported[AIR_SLASH_SCOPE] | frozenset(range(174,213))
    supported[LOW_HP_SCOPE] = supported[LADDER_SCOPE] | LOW_HP_FRAMES
    supported[HURT_SCOPE] = supported[LOW_HP_SCOPE] | HURT_FRAMES
    supported[LAUNCH_SCOPE] = supported[HURT_SCOPE] | LAUNCH_FRAMES
    supported[SHIPPUUGA_SCOPE] = supported[LAUNCH_SCOPE] | SHIPPUUGA_NEW | SHIPPUUGA_EFFECTS
    supported[BEAM_IN_SCOPE] = supported[SHIPPUUGA_SCOPE] | BEAM_BODY_FRAMES
    supported[BEAM_IN_V2_SCOPE] = supported[BEAM_IN_SCOPE]
    if scope not in supported or set(motion['frames']) != {str(n) for n in supported[scope]}:
        raise ValueError('Incomplete or unsupported motion scope')


def patch_idle(arc, gfx_meta, gfx, parts, frame_images, palette_bytes):
    """기존 대기 전용 진입점. 범위를 넓히지 않고 공통 검사기로 전달한다."""
    if set(frame_images) != set(IDLE_FRAMES):
        raise ValueError('Exactly six supported idle frames required')
    return patch_frames(arc, gfx_meta, gfx, parts, frame_images, palette_bytes)


def validate_sword_effect(original, replacement, record=None):
    """명시한 검날 추가만 허용하고 기존 잔상의 모든 불투명 픽셀을 보존한다."""
    if record is None:
        if replacement != original:
            raise ValueError('Saber effect pixels must remain original')
        return
    if (len(original) != len(replacement) or
        record.get('original_indices_sha256') != sha256(original) or
        record.get('replacement_indices_sha256') != sha256(replacement)):
        raise ValueError('Sword effect hash/length mismatch')
    added = sum(a != b for a,b in zip(original,replacement))
    if not added or record.get('added_pixels') != added:
        raise ValueError('Sword effect addition count mismatch')
    if any(a and a != b or not 0 <= b < 16 for a,b in zip(original,replacement)):
        raise ValueError('Sword effect overwrote an original trail pixel')


def patch_frames(arc, gfx_meta, gfx, parts, frame_images, palette_bytes, sword_effect_edits=None):
    """명시한 bank 0 프레임을 공동 편집. 공유 참조 전체 포함과 나머지 바이트 보존 요구."""
    if not frame_images or any(type(n) is not int for n in frame_images):
        raise ValueError('Explicit integer frame numbers required')
    sword_effect_edits = sword_effect_edits or {}
    if any(str(int(n)) != n or int(n) not in KNOWN_SABER_EFFECT_FRAMES or int(n) not in frame_images for n in sword_effect_edits):
        raise ValueError('Sword edits outside selected saber effects')
    if len(palette_bytes) != 32:
        raise ValueError('Expected one 16-color palette')
    words = struct.unpack('<16H', palette_bytes)
    if words[0] != 0 or any(not word & 0x8000 for word in words[1:]):
        raise ValueError('Unsupported transparency/high-bit policy')
    bank = graphics_bank(gfx, 0)
    if any(n < 0 or n >= len(bank['frames']) for n in frame_images):
        raise ValueError('Frame number outside graphics bank')
    hurt_check = validate_hurt_frames(gfx, parts, frame_images) if HURT_FRAMES & frame_images.keys() else None
    launch_streams,launch_check=validate_launch(gfx,parts,frame_images) if LAUNCH_FRAMES & frame_images.keys() else ({},None)
    groups = {}
    for number in sorted(frame_images):
        frame = bank['frames'][number]
        groups.setdefault(frame['offset'], []).append(number)
    modified_gfx = gfx
    compression = []
    for offset, numbers in groups.items():
        descriptor = bank['frames'][numbers[0]]
        refs = {(bi, f['index']) for bi in range(len(bank_offsets(gfx)))
                for f in graphics_bank(gfx, bi)['frames'] if f['offset'] == offset}
        if refs != {(0, n) for n in numbers}:
            raise ValueError('Stream shared with an unselected frame')
        original = decode_stream(gfx, offset, descriptor['limit'], descriptor['tile_count']*128)
        edits = [(composition_frame(parts, 0, n), *frame_images[n]) for n in numbers]
        for n in set(numbers) & SUPPORTED_SABER_EFFECTS:
            expected = compose_indices(original.data,descriptor['tile_count'],composition_frame(parts,0,n))[:2]
            if tuple(frame_images[n][1]) != expected[1]:
                raise ValueError('Sword effect canvas changed')
            validate_sword_effect(expected[0],frame_images[n][0],sword_effect_edits.get(str(n)))
        try:
            if set(numbers) & LAUNCH_FRAMES:
                packed=launch_streams[numbers[0]]
            elif set(numbers) == {135,136,137}:
                packed = edit_hurt_stream(original.data, descriptor['tile_count'],
                                          {n:composition_frame(parts,0,n) for n in numbers}, frame_images[135])
            elif set(numbers) <= LADDER_BASE_COUNTS.keys():
                packed = edit_base_layer_set(original.data,descriptor['tile_count'],
                                             [(*edit,LADDER_BASE_COUNTS[n]) for n,edit in zip(numbers,edits)])
            else:
                packed = edit_frame_set(original.data, descriptor['tile_count'], edits,
                                        overlap_policy='equal_sources' if 81 in numbers else 'reject')
            modified_gfx, budget = replace_stream(modified_gfx, descriptor, packed)
        except ValueError as exc:
            raise ValueError(f'Frames {numbers}: {exc}') from exc
        compression.append({'frames': numbers, **budget, 'decoded_sha256': sha256(packed)})
    decoded_changes = []
    for bi in range(len(bank_offsets(gfx))):
        for frame in graphics_bank(gfx, bi)['frames']:
            before = decode_stream(gfx, frame['offset'], frame['limit'], frame['tile_count']*128)
            after = decode_stream(modified_gfx, frame['offset'], frame['limit'], frame['tile_count']*128)
            if before.data != after.data:
                if bi != 0 or frame['index'] not in frame_images:
                    raise ValueError('Unselected bitmap changed')
                decoded_changes.append([bi, frame['index']])
                pixels, size, _, _ = compose_indices(after.data, frame['tile_count'], composition_frame(parts, 0, frame['index']))
                if (pixels, size) != (frame_images[frame['index']][0], tuple(frame_images[frame['index']][1])):
                    raise ValueError('Reassembled Riko pixels differ from input')
    entries = psx_arc(arc)
    palettes = [e for e in entries if e['type'] == '0x9']
    if len(palettes) != 1:
        raise ValueError('Ambiguous player palette entry')
    pal = palettes[0]
    original_words = struct.unpack_from('<16H', arc, pal['offset'])
    if any((a ^ b) & 0x8000 for a, b in zip(original_words, words)):
        raise ValueError('Palette bit 15 changed')
    result = bytearray(arc)
    result[gfx_meta['offset']:gfx_meta['offset']+gfx_meta['size']] = modified_gfx
    result[pal['offset']:pal['offset']+32] = palette_bytes
    allowed = [(pal['offset'], pal['offset']+32)] + [
        (gfx_meta['offset']+b['start'], gfx_meta['offset']+b['start']+b['encoded_bytes']) for b in compression]
    changed = [i for i, (a, b) in enumerate(zip(arc, result)) if a != b]
    if len(result) != len(arc) or any(not any(start <= i < end for start, end in allowed) for i in changed):
        raise ValueError('Archive write escaped approved ranges')
    return bytes(result), {'compression': compression, 'decoded_changed_references': decoded_changes,
                           'archive_changed_bytes': len(changed), 'allowed_archive_ranges': allowed,
                           'palette_row': 0, 'original_palette_words': list(original_words),
                           'replacement_palette_words': list(words), 'other_palette_rows_unchanged': True,
                           'other_bitmaps_unchanged': True, 'composition_changed': False,
                           'animation_timing_changed': False, 'relocated': False,
                           'hurt_effect_check': hurt_check,
                           'launch_effect_check':launch_check,
                           'preserved_ground_effect_frames': sorted((set(frame_images) & GROUND_SLASH_EFFECT_FRAMES)-set(map(int,sword_effect_edits))),
                           'preserved_saber_effect_frames': sorted((set(frame_images) & SUPPORTED_SABER_EFFECTS)-set(map(int,sword_effect_edits))),
                           'sword_effect_edits': sword_effect_edits,
                           'original_trail_opaque_pixels_preserved': True}


def check_motion_scale(motion, frames, gfx, parts, reference):
    from src.sprite_scale import validate_fixed_reference,validate_reference_views
    config_path=ROOT/'config/riko_body_standard.json'
    standard=json.loads(config_path.read_text(encoding='utf-8'))
    if sha256(reference[0])!=standard['reference_indices_sha256']:
        raise ValueError('Body standard is bound to another approved reference')
    scale=motion.get('body_standard')
    if not scale or scale.get('config_sha256')!=sha256(config_path.read_bytes()):
        raise ValueError('Motion lacks the current body-scale standard; historical inputs require --historical-art')
    if scale.get('per_pose_bbox_resize') is not False or scale.get('anisotropic_scale') is not False:
        raise ValueError('Per-pose bbox fitting or anisotropic body scaling is prohibited')
    if motion.get('scope') in (GROUND_SLASH_SCOPE,AIR_SLASH_SCOPE,LADDER_SCOPE,LOW_HP_SCOPE,HURT_SCOPE,LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
        effects={GROUND_SLASH_SCOPE:GROUND_SLASH_EFFECT_FRAMES,
                 AIR_SLASH_SCOPE:GROUND_SLASH_EFFECT_FRAMES|AIR_SLASH_EFFECT_FRAMES,
                 LADDER_SCOPE:KNOWN_SABER_EFFECT_FRAMES,LOW_HP_SCOPE:KNOWN_SABER_EFFECT_FRAMES,HURT_SCOPE:KNOWN_SABER_EFFECT_FRAMES,LAUNCH_SCOPE:KNOWN_SABER_EFFECT_FRAMES,SHIPPUUGA_SCOPE:SUPPORTED_SABER_EFFECTS,BEAM_IN_SCOPE:SUPPORTED_SABER_EFFECTS,BEAM_IN_V2_SCOPE:SUPPORTED_SABER_EFFECTS}[motion['scope']]
        edits=motion.get('sword_effect_edits',{})
        if any(int(n) not in effects for n in edits) or motion.get('preserved_effect_frames')!=sorted(effects-set(map(int,edits))):
            raise ValueError('Saber scope needs the exact preserved effect set')
        frames={n:v for n,v in frames.items() if n not in effects}
    placements=scale['head_world_positions']
    hurt_check=None
    if motion.get('scope') in (HURT_SCOPE,LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
        hurt_check=validate_hurt_frames(gfx,parts,frames)
        if set(placements)!={str(n) for n in frames} or any(placements[str(n)]!=placements['135'] for n in HURT_FRAMES):
            raise ValueError('Hurt variants must use the common body registration')
        frames={n:v for n,v in frames.items() if n not in (136,137,138)}
        placements={str(n):placements[str(n)] for n in frames}
    launch_check=None
    if motion.get('scope') in (LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
        _,launch_check=validate_launch(gfx,parts,frames)
        if any(placements[str(n)]!=placements['139'] for n in LAUNCH_FRAMES):
            raise ValueError('Launch variants require the same body registration')
        frames={n:v for n,v in frames.items() if n not in LAUNCH_FRAMES-{139}}
        placements={str(n):placements[str(n)] for n in frames}
    beam_check=None
    if motion.get('scope') in (BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
        dynamic=motion.get('scope')==BEAM_IN_V2_SCOPE
        beam_check=validate_beam_frames(gfx,parts,frames,dynamic=dynamic)
        if dynamic:
            from src.psx_beam_in import validate_contacts
            r=motion['beam_in_production'];png=checked_path(ROOT,r['idle_source'],ROOT/'out/ver_buki_riko')
            if sha256(png.read_bytes())!=r['idle_source_sha256']:raise ValueError('Arrival stance reference changed')
            words=struct.unpack('<16H',(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
            stance=read_indexed_png(png,words);bank=graphics_bank(gfx,0);bb={}
            for n in [147,*range(249,254)]:
                f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128).data
                bb[n]=compose_indices(raw,f['tile_count'],composition_frame(parts,0,n))[2]
            beam_check['stance']=validate_contacts({n:frames[n] for n in range(249,254)},bb,stance,bb[147])
        derived=beam_check['derived_frames'];base_number=beam_check['derived_from']
        if any(placements[str(n)]!=placements[str(base_number)] for n in derived):
            raise ValueError('Arrival flashes must share body registration')
        frames={n:v for n,v in frames.items() if n not in derived}
        placements={str(n):placements[str(n)] for n in frames}
    bank=graphics_bank(gfx,0);bounds={}
    for n in frames:
        f=bank['frames'][n];raw=decode_stream(gfx,f['offset'],f['limit'],f['tile_count']*128)
        _,_,bounds[n],_=compose_indices(raw.data,f['tile_count'],composition_frame(parts,0,n))
    if motion.get('scope') in ('jump_run_dash_wall_v1',GROUND_SLASH_SCOPE,AIR_SLASH_SCOPE,LADDER_SCOPE,LOW_HP_SCOPE,HURT_SCOPE,LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
        path=ROOT/'config/riko_wall_head_view.json'
        if scale.get('wall_view_config_sha256')!=sha256(path.read_bytes()):raise ValueError('Wall view standard changed')
        view=json.loads(path.read_text(encoding='utf8'))
        if view['base_standard_sha256']!=sha256(config_path.read_bytes()) or view['frames']!=list(range(38,44)):
            raise ValueError('Wall view scope or original standard changed')
        png=checked_path(ROOT,view['reference_png'],ROOT/'work/ver_buki_riko')
        if sha256(png.read_bytes())!=view['reference_png_sha256']:raise ValueError('Wall head reference PNG changed')
        words=struct.unpack('<16H',(ROOT/'out/ver_buki_riko/riko_pilot_20261023T082720987715Z/candidate_palette.bin').read_bytes())
        data,size=read_indexed_png(png,words)
        if sha256(data)!=view['reference_indices_sha256'] or list(size)!=view['size']:raise ValueError('Wall head indices changed')
        views={'approved_front':(*reference,standard['reference_roi']),
               'provisional_wall_side':(data,size,(0,0,*size))}
        assignments={str(n):'provisional_wall_side' if n in view['frames'] else 'approved_front' for n in frames}
        if motion.get('scope') in (LADDER_SCOPE,LOW_HP_SCOPE,HURT_SCOPE,LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
            path=ROOT/'config/riko_ladder_head_views.json'
            if scale.get('ladder_view_config_sha256')!=sha256(path.read_bytes()):raise ValueError('Ladder view standard changed')
            ladder=json.loads(path.read_text(encoding='utf8'))
            if ladder['base_standard_sha256']!=sha256(config_path.read_bytes()) or set(map(int,ladder['assignments']))!=set(range(174,191)):
                raise ValueError('Ladder view scope or original standard changed')
            for name,r in ladder['views'].items():
                png=checked_path(ROOT,r['reference_png'],ROOT/'work/ver_buki_riko')
                if sha256(png.read_bytes())!=r['reference_png_sha256']:raise ValueError('Ladder head reference PNG changed')
                data,size=read_indexed_png(png,words)
                if sha256(data)!=r['reference_indices_sha256'] or list(size)!=[23,19]:raise ValueError('Ladder head indices changed')
                views[name]=(data,size,(0,0,*size))
            assignments.update(ladder['assignments'])
        if motion.get('scope') in (SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):
            if motion.get('shippuuga_head_views')!=SHIPPUUGA_VIEWS:raise ValueError('Dash slash must retain registered rear-turn views')
            assignments.update(SHIPPUUGA_VIEWS)
        result=validate_reference_views(frames,bounds,views,assignments,placements)
        if hurt_check:result['derived_hurt_variants']=hurt_check
        if launch_check:result['derived_launch_variants']=launch_check
        if beam_check:result['derived_arrival_variants']=beam_check
        return result
    return validate_fixed_reference(frames,bounds,*reference,standard['reference_roi'],scale['head_world_positions'])


def read_idle_revision(path, selected_png, palette_bytes, reference):
    """명시한 디자인 수정안만 허용하고 기존 선택/머리 기준은 보존한다."""
    from src.sprite_scale import validate_fixed_reference
    path=path.resolve()
    if not path.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
        raise ValueError('Unexpected idle revision manifest')
    record=json.loads(path.read_text(encoding='utf-8'))
    if record['base_reference_sha256']!=sha256(selected_png.read_bytes()) or record['palette_sha256']!=sha256(palette_bytes):
        raise ValueError('Idle revision base or palette mismatch')
    candidate=(path.parent/record['file']).resolve()
    if not candidate.is_relative_to(path.parent) or sha256(candidate.read_bytes())!=record['sha256']:
        raise ValueError('Idle revision PNG escaped directory or hash mismatch')
    pixels,size=read_indexed_png(candidate,struct.unpack('<16H',palette_bytes))
    if size!=reference[1]:raise ValueError('Idle revision native canvas mismatch')
    standard=json.loads((ROOT/'config/riko_body_standard.json').read_text(encoding='utf-8'))
    check=validate_fixed_reference({147:(pixels,size)},{147:(0,0,*size)},*reference,
        standard['reference_roi'],{'147':record['head_native_position']})
    return candidate,(pixels,size),{'manifest':str(path),'manifest_sha256':sha256(path.read_bytes()),
        **record,'head_check':check,'final_style_user_approved':False}


def build(extracted, frames_dir=None, motion_set=None, historical_art=False, idle_revision=None):
    profile, project, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    selected = json.loads((ROOT/'projects/ver_buki_riko/art_selection.json').read_text(encoding='utf-8'))
    if not selected['idle_style_approved'] or selected['task_id'] != 'zero_riko':
        raise ValueError('Selected Riko idle art required')
    png = checked_path(ROOT, selected['indexed_png'], ROOT/'out/ver_buki_riko')
    if sha256(png.read_bytes()) != selected['indexed_png_sha256']:
        raise ValueError('Selected Riko art hash changed')
    palette_bytes = (png.parent/'candidate_palette.bin').read_bytes()
    words = struct.unpack('<16H', palette_bytes)
    selected_pixels, selected_size = read_indexed_png(png, words)
    idle_reference=(selected_pixels,selected_size);revision_record=None;idle_png=png
    if idle_revision:
        idle_png,idle_reference,revision_record=read_idle_revision(idle_revision,png,palette_bytes,(selected_pixels,selected_size))
        if (selected.get('active_design_user_review_pending') is False
                and selected.get('active_design_acceptance')
                and (ROOT/selected.get('active_idle_revision','')).resolve()==idle_revision.resolve()
                and selected.get('active_idle_reference_sha256')==sha256(idle_png.read_bytes())):
            revision_record['final_style_user_approved']=True
            revision_record['acceptance']=selected['active_design_acceptance']
    if frames_dir:
        frames_dir = frames_dir.resolve()
        if not any(frames_dir.is_relative_to((ROOT/p).resolve()) for p in ('work/ver_buki_riko', 'out/ver_buki_riko')):
            raise ValueError('Unexpected animation input directory')
        sources = {n: frames_dir/f'idle_{n:03d}.png' for n in IDLE_FRAMES}
        frames = {n: read_indexed_png(path, words) for n, path in sources.items()}
        if frames[147] != idle_reference:
            raise ValueError('Approved reference frame 147 must remain exact')
    else:
        sources = {n: idle_png for n in IDLE_FRAMES}
        frames = {n: idle_reference for n in IDLE_FRAMES}
    motion = None;launch_words=None
    if motion_set:
        motion_set = motion_set.resolve()
        if not motion_set.is_relative_to((ROOT/'work/ver_buki_riko').resolve()):
            raise ValueError('Unexpected motion manifest path')
        motion = json.loads(motion_set.read_text(encoding='utf-8'))
        if motion['source_sha256'] != profile['source_sha256'] or motion['palette_sha256'] != sha256(palette_bytes):
            raise ValueError('Motion input or palette hash mismatch')
        validate_motion_scope(motion)
        if motion['scope'] in (LAUNCH_SCOPE,SHIPPUUGA_SCOPE,BEAM_IN_SCOPE,BEAM_IN_V2_SCOPE):launch_words=read_launch_palette(motion,motion_set,palette_bytes)
        for key, record in motion['frames'].items():
            n = int(key); path = (motion_set.parent/record['file']).resolve()
            if not path.is_relative_to(motion_set.parent) or sha256(path.read_bytes()) != record['sha256']:
                raise ValueError('Motion PNG escaped directory or hash mismatch')
            sources[n] = path
            frames[n] = read_indexed_png(path, launch_words if n in MULTI_FRAMES else words, palette_banks=4 if n in MULTI_FRAMES else 1)
    scale_check=None
    if motion and not historical_art:
        motion_frames={int(n):frames[int(n)] for n in motion['frames']}
        scale_check=check_motion_scale(motion,motion_frames,gfx,parts,(selected_pixels,selected_size))
    patched, checks = patch_frames(arc, gfx_meta, gfx, parts, frames, palette_bytes,
                                  motion.get('sword_effect_edits') if motion else None)
    parent = (ROOT/'out/ver_buki_riko').resolve()
    if not parent.is_relative_to(ROOT):
        raise ValueError('Output escaped workspace')
    stem = 'riko_motion' if motion else 'riko_idle'
    out = parent/(stem+'_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    out.mkdir(parents=True, exist_ok=False)
    result = write_archive_copy(ROOT/project['source_bin'], out/(stem+'.bin'), profile['zero_archive'], patched, profile['source_sha256'])
    cue = (ROOT/project['source_cue']).read_bytes().decode('utf-8-sig')
    (out/(stem+'.cue')).write_text(working_cue(cue, stem+'.bin'), encoding='ascii', newline='')
    (out/'modified.arc').write_bytes(patched)
    for n in sorted(frames):
        save_image(*frames[n], launch_words if n in MULTI_FRAMES else words, out/f'{"idle" if n in IDLE_FRAMES else "frame"}_{n:03d}.png')
    manifest = {'project': 'ver_buki_riko', 'task': 'zero_riko', 'kind': stem+'_graphics_and_normal_palette',
                'bin_file': stem+'.bin', 'cue_file': stem+'.cue',
                'motion_set': str(motion_set) if motion else None,
                'body_scale_check':scale_check,'historical_art_validation_bypass':historical_art,
                'motion_set_sha256': sha256(motion_set.read_bytes()) if motion else None,
                'source_sha256': profile['source_sha256'], 'source_archive_sha256': sha256(arc),
                'modified_bin': result, 'modified_archive_sha256': sha256(patched), **checks,
                'frame_inputs': {str(n): {'path': str(p), 'sha256': sha256(p.read_bytes())} for n, p in sources.items()},
                'art_selection': selected, 'idle_reference_revision':revision_record,
                'static_pose_repeated': len({v[0] for v in frames.values()}) == 1,
                'finished_idle_animation': False, 'runtime_modified_verified': False,
                'known_limitations': ['Unselected Zero bitmaps remain original and use the new normal palette.',
                                      'Black Zero and special-effect palette rows are unchanged.',
                                      'Full character replacement and final animation quality are not claimed.']}
    write_json(out/'manifest.json', manifest)
    validate_bin(ROOT/project['source_bin'], profile['source_sha256'])
    print(json.dumps({'output': str(out), 'sha256': result['sha256'], 'compression': checks['compression'],
                      'static_pose_repeated': manifest['static_pose_repeated'], 'changed_sectors': len(result['changed_sectors'])}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path, required=True)
    parser.add_argument('--frames-dir', type=Path)
    parser.add_argument('--motion-set', type=Path)
    parser.add_argument('--idle-revision',type=Path,help='Explicit hashed idle design revision; original selected reference remains preserved')
    parser.add_argument('--historical-art',action='store_true',help='Explicit reproduction of earlier art without the new scale standard')
    args = parser.parse_args()
    build(args.extract, args.frames_dir, args.motion_set,args.historical_art,args.idle_revision)
