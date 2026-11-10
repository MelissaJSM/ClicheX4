"""수용한 포스 나나 대기·사격10참조를 보호된 부모 BIN의 별도 사본에 넣는다."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import shutil
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_pilot import PARENT, PARENT_SHA, entry, require, write
from scripts.prepare_nana_fourth_idle import FRAMES, LAYERS
from scripts.project import digest
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from src.psx_disc import write_archive_copy
from src.psx_sector import validate_checks
from src.psx_player import graphics_bank, decode_stream, composition_frame
from src.psx_sprite_batch import canvas_from_parts


def validate_art(prepared, old, new, parent_sha256=PARENT_SHA, frames=FRAMES):
    recipe = json.loads((prepared / 'recipe.json').read_text('utf8'))
    require(recipe['parent_sha256'] == parent_sha256, 'Unexpected parent')
    require(recipe['parent_arc_sha256'] == sha256(old), 'ARC parent differs')
    require(recipe['modified_arc_sha256'] == sha256(new), 'Prepared ARC differs')
    require(recipe['frames'] == frames and recipe['partial_outfit_assignment'], 'Unapproved scope')
    require(len(old) == len(new), 'ARC length changed')
    entries = psx_arc(old)
    require(old[:2048] == new[:2048], 'ARC table changed')
    allowed = set()
    changed_kinds = []
    for e in entries:
        start, size = e['offset'], e['size']
        a, b = old[start:start+size], new[start:start+size]
        if a != b:
            require(int(e['type'], 16) in (2, 3, 9), 'Non-graphics ARC entry changed')
            allowed.update(range(start, start+size)); changed_kinds.append(e['type'])
    offsets = {i for i, (a, b) in enumerate(zip(old, new)) if a != b}
    require(offsets and offsets <= allowed, 'ARC padding/header changed')
    pal = entry(new, 9)
    # Both arm variants use adjacent armor CLUTs. Their visible colors agree.
    require(all((int.from_bytes(pal[i:i+2], 'little') & 0x7fff) ==
                (int.from_bytes(pal[i+32:i+34], 'little') & 0x7fff)
                for i in range(32, 64, 2)), 'Arm palette variant mismatch')
    g, c = entry(new, 2), entry(new, 3)
    bank = graphics_bank(g, 0, allow_bank_aliases=True)
    combinations = 0
    for n in frames:
        f = bank['frames'][n]
        raw = decode_stream(g, f['offset'], f['limit'], f['tile_count']*128).data
        body = canvas_from_parts(raw, f['tile_count'], composition_frame(c, 0, n))
        layers = {b: canvas_from_parts(raw, f['tile_count'], composition_frame(c, b, n)) for b in LAYERS.values()}
        for mask in range(16):
            merged = body.copy()
            for bit, b in ((8, 8), (1, 5), (4, 7), (2, 6)):
                if mask & bit:
                    merged = np.where(layers[b], layers[b], merged)
            require(np.array_equal(merged, np.array(Image.open(prepared / f'frame_{n:03}_mask{mask:02}.png'))),
                    'Readback armor combination differs')
            combinations += 1
    return recipe, offsets, {'arc_entries_changed': changed_kinds, 'readback_armor_combinations': combinations,
                             'arm_palette_variants_equal': True, 'only_graphics_entries_changed': True}


def build(prepared, activate, expected_active_sha256=None, scope='idle'):
    require(scope in ('idle', 'run', 'run_fix', 'air', 'wall', 'dash', 'reaction', 'hurt_extra', 'hurt_aura', 'ladder', 'ceremony', 'special', 'elemental', 'hover', 'vehicle'), 'Unsupported scope')
    parent, parent_sha, frames = PARENT, PARENT_SHA, FRAMES
    if scope in ('run', 'run_fix'):
        from scripts.prepare_nana_fourth_run_art import PARENT as run_parent, PARENT_SHA as run_sha
        parent, parent_sha, frames = run_parent, run_sha, list(range(1, 33))
        if scope == 'run_fix':
            from scripts.finish_nana_fourth_run import FRAMES as fixed_frames
            frames = fixed_frames
    if scope == 'air':
        from scripts.prepare_nana_fourth_air_reference import PARENT as ap,PARENT_SHA as ah,FRAMES as af
        parent, parent_sha, frames = ap, ah, af
    if scope == 'wall':
        from scripts.prepare_nana_fourth_wall_reference import PARENT as wp,PARENT_SHA as wh,FRAMES as wf
        parent, parent_sha, frames = wp, wh, wf
    if scope == 'dash':
        from scripts.prepare_nana_fourth_dash_reference import PARENT as dp,PARENT_SHA as dh,FRAMES as df
        parent, parent_sha, frames = dp, dh, df
    if scope == 'reaction':
        from scripts.prepare_nana_fourth_reaction_reference import PARENT as rp,PARENT_SHA as rh,FRAMES as rf
        parent, parent_sha, frames = rp, rh, rf
    if scope == 'hurt_extra':
        from scripts.prepare_nana_fourth_hurt_extra_reference import PARENT as hp,PARENT_SHA as hh,FRAMES as hf
        parent, parent_sha, frames = hp, hh, hf
    if scope == 'hurt_aura':
        from scripts.prepare_nana_hurt_aura_reference import PARENT as hp,PARENT_SHA as hh,FRAMES as hf
        parent, parent_sha, frames = hp, hh, hf
    if scope == 'ladder':
        from scripts.prepare_nana_fourth_ladder_reference import PARENT as lp,PARENT_SHA as lh,FRAMES as lf
        parent, parent_sha, frames = lp, lh, lf
    if scope == 'ceremony':
        from scripts.prepare_nana_fourth_ceremony_reference import PARENT as cp,PARENT_SHA as ch,FRAMES as cf
        parent, parent_sha, frames = cp, ch, cf
    if scope == 'special':
        from scripts.prepare_nana_fourth_special_reference import PARENT as sp,PARENT_SHA as sh,FRAMES as sf
        parent, parent_sha, frames = sp, sh, sf
    if scope == 'elemental':
        from scripts.prepare_nana_fourth_elemental_reference import PARENT as ep,PARENT_SHA as eh,FRAMES as ef
        parent, parent_sha, frames = ep, eh, ef
    if scope == 'hover':
        from scripts.prepare_nana_fourth_hover_reference import PARENT as hp,PARENT_SHA as hh,FRAMES as hf
        parent, parent_sha, frames = hp, hh, hf
    if scope == 'vehicle':
        from scripts.prepare_nana_fourth_vehicle_reference import PARENT as vp,PARENT_SHA as vh,FRAMES as vf
        parent, parent_sha, frames = vp, vh, vf
    expected_active_sha256 = expected_active_sha256 or parent_sha
    prepared = prepared.resolve()
    require(prepared.is_relative_to(ROOT / 'work/ver_rin_nana/nana_fourth_armor'), 'Unexpected prepared path')
    pointer_path = ROOT / 'projects/ver_rin_nana/current_build.json'
    previous = pointer_path.read_bytes(); pointer = json.loads(previous)
    if activate:
        require(pointer['sha256'] == expected_active_sha256, 'Active parent differs')
        require(digest(ROOT / pointer['build'] / 'rin_nana.bin') == expected_active_sha256, 'Active BIN changed')
    game = parent / 'rin_nana.bin'
    require(digest(game) == parent_sha, 'Unsupported BIN')
    protection = json.loads((parent / 'preservation.json').read_text('utf8'))
    def protect():
        for q in protection['files']:
            require(digest(ROOT / q['path']) == q['expected_sha256'], 'Protected file changed: ' + q['path'])
    protect()
    with game.open('rb') as f:
        reader = DiscReader(f, game.stat().st_size)
        records = [r for r in reader.inspect()['files'] if r['name'] == 'PL00_U.ARC;1']
        require(len(records) == 1, 'Ambiguous PL00')
        record = records[0]
        require((record['lba'], record['size']) == (1135, 796672), 'Unsupported PL00')
        old = reader.read(record['lba'], record['size'])
    require(old == (parent / 'modified.arc').read_bytes(), 'Parent extraction differs')
    new = (prepared / 'modified.arc').read_bytes()
    recipe, offsets, validation = validate_art(prepared, old, new, parent_sha, frames)
    if scope != 'idle':
        require(entry(old, 9) == entry(new, 9), 'Movement palette changed')
    record['sha256'] = sha256(old)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    out = ROOT / 'out/ver_rin_nana' / ('nana_fourth_' + scope + '_' + stamp)
    out.mkdir(exist_ok=False)
    result = write_archive_copy(game, out / 'rin_nana.bin', record, new, parent_sha)
    changed, found = [], set()
    with game.open('rb') as a, (out / 'rin_nana.bin').open('rb') as b:
        for lba in range(game.stat().st_size // 2352):
            x, y = a.read(2352), b.read(2352)
            require(len(x) == len(y) == 2352, 'Truncated BIN')
            if x == y:
                continue
            require(x[:24] == y[:24], 'Sector header changed')
            validate_checks(y)
            differences = {(lba-record['lba'])*2048+i for i in range(2048) if x[24+i] != y[24+i]}
            require(differences and differences <= offsets, 'Unexpected sector payload change')
            found.update(differences); changed.append(lba)
        require(not b.read(1), 'Disc grew')
    require(found == offsets and set(changed) == {q['lba'] for q in result['changed_sectors']}, 'Change coverage differs')
    with (out / 'rin_nana.bin').open('rb') as f:
        require(DiscReader(f, result['size']).read(record['lba'], record['size']) == new, 'BIN readback differs')
    protect(); require(digest(game) == parent_sha, 'Parent BIN changed')
    for name in ('rin_nana.cue', 'PL01_U.ARC', 'PL02_U.ARC'):
        shutil.copyfile(parent / name, out / name)
    for folder in parent.iterdir():
        if folder.is_dir():
            shutil.copytree(folder, out / folder.name)
    (out / 'modified.arc').write_bytes(new)
    shutil.copytree(prepared, out / ('fourth_' + scope if scope != 'idle' else 'fourth_armor'))
    verification = {**validation, 'all_disc_sectors_compared': game.stat().st_size // 2352,
                    'changed_sectors': changed, 'changed_resource_bytes': len(offsets),
                    'readback_arc_identical': True, 'edc_ecc_checked': True, 'all_other_disc_payload_exact': True,
                    'protected_files': len(protection['files']), 'runtime_verified': False,
                    'checked_bitmap_references': recipe['checked_bitmap_references'],
                    'other_compositions_preserved': recipe['other_compositions_preserved'],
                    'limitation': ('이동·이동 사격32참조 추가. 대기 포함42참조 적용; 공중·대시 등 나머지 아머 후속 제작.' if scope != 'idle' else '대기·정지 사격10참조만 새 아머. 이동·공중 등 나머지 아머는 후속 제작.')}
    if scope == 'air':
        verification['limitation'] = '공중·공중 사격22참조 추가, 누적64참조. 벽·대시 등 나머지 아머 후속 제작.'
    if scope == 'wall':
        verification['limitation'] = '벽타기·벽 점프·벽 사격12참조 추가, 누적76참조. 대시 등 나머지 아머는 후속 제작.'
    if scope == 'dash':
        verification['limitation'] = '대시·대시 사격18참조 추가, 누적94아머 참조. 기본형9대시 사격에도 같은 권총 비율 적용. 나머지 아머는 후속 제작.'
    if scope == 'reaction':
        verification['limitation'] = '피격5·저체력6참조 추가, 누적105아머 참조. 별도 섬광109/112..114는 수용 기본형 그대로. 사다리·등장·승리 등 후속 제작.'
    if scope == 'hurt_extra':
        verification['limitation'] = '다른 피격233..236의 남아 있던 원작 아머4참조 수정, 누적109아머 참조. 실제 수정본 재생은 별도 확인. 사다리 등 후속 제작.'
    if scope == 'hurt_aura':
        verification['limitation'] = '공통 피격235/236의 외곽 효과만 수정, 아머 누적109참조 유지. 기본형·부분 아머 몸 보존. 실제 효과 재생은 별도 확인.'
    if scope == 'ladder':
        verification['limitation'] = '사다리 진입·이동·사격·상단 이탈14아머 참조 추가, 누적123참조. 사다리 실기는 별도 확인; 등장·승리·특수 등 후속 제작.'
    if scope == 'ceremony':
        verification['limitation'] = '준비·승리·귀환10아머 참조 추가, 누적133참조. 공통 빛/변신17참조 보존. 실제 장면 재생은 별도 확인; 특수·탑승 등 후속 제작.'
    if scope == 'special':
        verification['limitation'] = '차지 연계·더블 사이클론7아머 참조 추가, 누적140참조. 기본 몸·궤적·효과 보존. 라이징/프로스트·추가 공중·탑승 등 후속 제작.'
    if scope == 'elemental':
        verification['limitation'] = '라이징 파이어·프로스트 계열9아머 참조 추가, 누적149참조. 기본 몸·권총 접점·효과 보존. 추가 공중·탑승 등 후속 제작.'
    if scope == 'hover':
        verification['limitation'] = '공중 대시·호버12아머 참조 추가, 누적161참조. 호버10참조 하체는 다리 파츠로 통합하며 비트8 없는 호버는 게임에서 진입하지 못한다. 탑승 등 후속 제작.'
    if scope == 'vehicle':
        verification['limitation'] = '체이서13·라이드 아머 머리19의32의상 참조 추가, 누적193참조. 공유 빈198은 보존하며 새 의상 수에 포함하지 않는다. 탑승 실기·부분 아머 전수는 별도 확인. Ultimate는 별도 미제작.'
    manifest = json.loads((parent / 'manifest.json').read_text('utf8'))
    added_frames = [n for n in frames if not(scope=='vehicle' and n==198)]
    cumulative = sorted(set(manifest.get('fourth_armor_frames', [])) | set(added_frames))
    manifest.update(kind='nana_fourth_armor_' + scope, task='fourth_armor_nana',
                    parent=parent.relative_to(ROOT).as_posix(), parent_sha256=parent_sha,
                    modified_bin=result, modified_archive_sha256=sha256(new),
                    inherited_manifest=(parent / 'manifest.json').relative_to(ROOT).as_posix(),
                    inherited_verification=manifest['verification'], verification=verification,
                    runtime_verified=False, fourth_armor_frames=cumulative, added_fourth_armor_frames=added_frames,
                    source_script_sha256=digest(Path(__file__)))
    write(out / 'manifest.json', manifest); write(out / 'verification.json', verification)
    write(out / 'preservation.json', protection)
    shutil.copyfile(ROOT / 'projects/ver_rin_nana/nana_fourth_candidate.json', out / 'authorization.json')
    if activate:
        require(pointer_path.read_bytes() == previous, 'Pointer changed during build')
        (out / 'previous_current_build.json').write_bytes(previous)
        pointer.update(task='fourth_armor_nana', build=out.relative_to(ROOT).as_posix(),
                       cue=(out / 'rin_nana.cue').relative_to(ROOT).as_posix(), sha256=result['sha256'],
                       current_session=None, runtime_verified=False, fourth_armor_frames=cumulative,
                       fourth_armor_user_accepted=False, fourth_armor_style_accepted=True,
                       next_scope=('Fourth armor movement runtime review, then dash/air production' if scope != 'idle' else 'Fourth armor idle/standing shot runtime check; movement production next'))
        if scope != 'idle':
            pointer.update(fourth_armor_idle_user_accepted=True, fourth_armor_movement_user_accepted=False,
                           fourth_armor_acceptance_scope='대기·정지 사격10참조 수용 유지. 새 이동·이동 사격32참조는 검토 대기.')
        if scope == 'air':
            pointer.update(fourth_armor_movement_user_accepted=True, fourth_armor_air_user_accepted=False,
                           fourth_armor_acceptance_scope='대기·이동 및 이동 사격 어깨/모자 수정 수용 유지. 공중22참조는 검토 대기.',
                           next_scope='Fourth armor air/jump/landing runtime review, then wall/dash production')
        if scope == 'wall':
            pointer.update(fourth_armor_movement_user_accepted=True, fourth_armor_air_user_accepted=True,
                           fourth_armor_wall_user_accepted=False,
                           fourth_armor_acceptance_scope='대기·이동·공중64참조 수용 유지. 벽타기·벽 점프·벽 사격12참조는 검토 대기.',
                           next_scope='Fourth armor wall/wall jump/wall shot runtime review, then dash production')
        if scope == 'dash':
            pointer.update(fourth_armor_movement_user_accepted=True, fourth_armor_air_user_accepted=True,
                           fourth_armor_wall_user_accepted=True, fourth_armor_dash_user_accepted=False,
                           fourth_armor_acceptance_scope='대기·이동·공중·벽76참조 수용 유지. 대시18참조 검토 대기.',
                           next_scope='Fourth armor dash review, then hurt/ladder/low-health production')
        if scope in ('reaction','hurt_extra','hurt_aura'):
            pointer.update(fourth_armor_movement_user_accepted=True, fourth_armor_air_user_accepted=True,
                           fourth_armor_wall_user_accepted=True, fourth_armor_dash_user_accepted=True,
                           fourth_armor_reaction_user_accepted=False,
                           fourth_armor_acceptance_scope='대기·이동·공중·벽·대시94참조 수용 유지. 피격·저체력11참조 검토 대기.',
                           next_scope='Fourth armor hurt/low-health review, then ladder production')
            if scope=='hurt_extra':pointer.update(fourth_armor_acceptance_scope='대시까지94참조 수용 유지. 피격·저체력 및 추가 피격15참조 검토 대기.')
            if scope=='hurt_aura':
                pointer.update(fourth_armor_acceptance_scope='대시까지94참조 수용 유지. 피격·저체력15참조 및 공통 피격 테두리2참조 검토 대기.',
                               fourth_armor_hurt_aura_user_accepted=False,
                               next_scope='Review corrected Nana hurt aura, then Fourth Armor ladder production')
        if scope=='ladder':
            for key in ('movement','air','wall','dash'):
                pointer['fourth_armor_'+key+'_user_accepted']=True
            pointer.update(fourth_armor_hurt_aura_user_accepted=True,fourth_armor_ladder_user_accepted=False,
                           fourth_armor_acceptance_scope='대시까지94참조 및 직전 피격 외곽 수정 수용 유지. 사다리14참조는 검토 대기.',
                           next_scope='Fourth Armor ladder review, then arrival/victory production')
        if scope=='ceremony':
            for key in ('movement','air','wall','dash','hurt_aura','ladder'):
                pointer['fourth_armor_'+key+'_user_accepted']=True
            pointer.update(fourth_armor_ceremony_user_accepted=False,
                           fourth_armor_acceptance_scope='직전 사다리 작업까지 수용 유지. 준비·승리·귀환10아머 참조는 검토 대기.',
                           next_scope='Fourth Armor arrival/victory/return review, then special weapon and vehicle production')
        if scope=='special':
            for key in ('movement','air','wall','dash','hurt_aura','ladder','ceremony'):
                pointer['fourth_armor_'+key+'_user_accepted']=True
            pointer.update(fourth_armor_special_user_accepted=False,
                           fourth_armor_acceptance_scope='직전 준비·승리·귀환 작업 수용 유지. 차지 연계·더블 사이클론7참조는 검토 대기.',
                           next_scope='Fourth Armor charge/Cyclone review, then remaining special weapon and air costumes')
        if scope=='elemental':
            for key in ('movement','air','wall','dash','hurt_aura','ladder','ceremony','special'):
                pointer['fourth_armor_'+key+'_user_accepted']=True
            pointer.update(fourth_armor_elemental_user_accepted=False,
                           fourth_armor_acceptance_scope='직전 차지·사이클론까지 수용 유지. 라이징 파이어·프로스트 계열9참조 검토 대기.',
                           next_scope='Fourth Armor elemental review, then remaining air and vehicle costumes')
        if scope=='hover':
            for key in ('movement','air','wall','dash','hurt_aura','ladder','ceremony','special','elemental'):
                pointer['fourth_armor_'+key+'_user_accepted']=True
            pointer.update(fourth_armor_hover_user_accepted=False,
                           fourth_armor_acceptance_scope='직전 프로스트·라이징 파이어 작업 수용 유지. 공중 대시·호버12참조 검토 대기.',
                           next_scope='Fourth Armor air dash/hover review, then vehicle costumes')
        if scope=='vehicle':
            for key in ('movement','air','wall','dash','hurt_aura','ladder','ceremony','special','elemental','hover'):
                pointer['fourth_armor_'+key+'_user_accepted']=True
            pointer.update(fourth_armor_vehicle_user_accepted=False,
                           fourth_armor_acceptance_scope='직전 공중 대시·호버 작업 수용 유지. 체이서13·탑승 머리19의32참조 검토 대기.',
                           next_scope='Fourth Armor vehicle review and coverage audit; Ultimate remains separate')
        write(pointer_path, pointer)
    print(json.dumps({'build': out.relative_to(ROOT).as_posix(), 'sha256': result['sha256'],
                      'changed_sectors': len(changed), 'changed_bytes': len(offsets), 'activated': activate}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepared', type=Path, required=True)
    p.add_argument('--activate', action='store_true')
    p.add_argument('--expected-active-sha256')
    p.add_argument('--scope', choices=('idle', 'run', 'run_fix', 'air', 'wall', 'dash', 'reaction', 'hurt_extra', 'hurt_aura', 'ladder', 'ceremony', 'special', 'elemental', 'hover', 'vehicle'), default='idle')
    args = p.parse_args(); build(args.prepared, args.activate, args.expected_active_sha256, args.scope)
