"""이전 최종 도트를 현재 입력에 결속하고 이번 수정만 전후 비교하는 단독 검토판."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import sys

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_sprite_album as album
from scripts.audit_sprite_reaudit_source import EXPECTED, WORK
from scripts.build_hurt_capsule_fix import require, write_json
from scripts.c01_audio_build import read_disc
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash


def extracted(text, marker):
    return json.JSONDecoder().raw_decode(text[text.index(marker) + len(marker):])[0]


def main(plan_paths):
    proof = json.loads((WORK / 'source_identity.json').read_text('utf8'))
    require(proof['passed'], 'Current source binding required')
    plans = {}
    for path in plan_paths:
        require(path.resolve().is_relative_to(WORK.resolve()), 'Unexpected plan path')
        plan = json.loads(path.read_text('utf8'))
        require(plan['project'] not in plans, 'Duplicate project plan')
        plans[plan['project']] = plan
    old_html = ROOT / 'out/sprite_consistency_20261105/ALL_SPRITES.html'
    require(file_hash(old_html) == '0997b82203efe919b859e0716ba684d160f09c3c2543024117244d0fa4a17fa3',
            'Original album changed')
    text = old_html.read_text('utf8')
    data = extracted(text, 'const DATA=')
    album.POOL.update(extracted(text, 'const ASSETS='))
    empty = extracted(text, 'const EMPTY=')
    playback = extracted(text, 'PLAYBACK=')
    sources, current = {}, {}
    for mode, (stem, expected, _) in EXPECTED.items():
        source = ROOT / proof['projects'][mode]['bin']
        require(file_hash(source) == expected, 'Reaudit parent changed')
        names = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61')
        before, _ = read_disc(source, names)
        target, target_sha = source, expected
        if mode in plans:
            plan = plans[mode]
            require(plan['source_sha256'] == expected, 'Wrong proposal parent')
            target = ROOT / plan['output'] / (stem + '.bin')
            manifest = json.loads((target.parent / 'manifest.json').read_text('utf8'))
            target_sha = file_hash(target)
            require(target_sha == manifest['modified_bin']['sha256'], 'Built candidate differs')
        after, _ = read_disc(target, names)
        for name in ('MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61'):
            require(after[name] == before[name], 'This album wrapper requires unchanged UI/timing')
        for kind in (2, 3, 9, 0x10206):
            require(entry(after['PL01_U.ARC'], kind) == entry(before['PL01_U.ARC'], kind),
                    'Zero changed: fresh Zero export is required')
        for name in names[:3]:
            require(entry(after[name], 9) == entry(before[name], 9), 'Palette changed')
        current[mode] = after
        sources[mode] = {'bin': target.relative_to(ROOT).as_posix(), 'sha256': target_sha,
                         'parent_sha256': expected, 'graphics_from_actual_BIN': True}
        playback['sources'][mode] = {'bin': sources[mode]['bin'], 'bin_sha256': target_sha,
                                     'timing_identical_to_verified_20261105_tables': True}
    counts, delta = {}, []
    for char in data:
        name = char['id']
        mode = 'ver_buki_riko' if name in ('riko', 'shibuki') else 'ver_rin_nana'
        # Fold last session's accepted/revised frames into this session's baseline.
        for frame in char['frames']:
            if frame.get('revised_path'):
                frame['path'] = frame.pop('revised_path')
                frame['bbox'] = frame.pop('revised_bbox')
        char['sheets'] = []
        for review in plans.get(mode, {}).get('review_images', []):
            if review['character'] != name:
                continue
            path = (ROOT / review['path']).resolve()
            require(path.is_relative_to(WORK.resolve()) and path.is_file(), 'Review sheet outside task workspace')
            char['sheets'].append({'label': review['label'], 'path': album.pooled_png(path.read_bytes())})
        char['revised_count'] = 0
        if name in ('shibuki', 'nana'):
            archives = {n: Archive(current[mode][n]) for n in ('PL00_U.ARC', 'PL02_U.ARC')}
            for frame in char['frames']:
                form = frame['form']
                if form not in ('base', 'fourth', 'fourth_arm1', 'ultimate_before', 'ultimate_after'):
                    continue
                ref = frame['ref']
                arc = archives['PL02_U.ARC' if form.startswith('ultimate') else 'PL00_U.ARC']
                mask = 15 if form in ('fourth', 'fourth_arm1', 'ultimate_before') or form == 'ultimate_after' and 217 <= ref <= 230 else 0
                arm = 1 if form == 'fourth_arm1' else 2
                try:
                    image = arc.composite(ref, mask, arm)[0]
                except (ValueError, IndexError):
                    require(frame['status'] == 'unreconstructed', 'Unexpected decode failure')
                    continue
                before = Image.open(io.BytesIO(base64.b64decode(album.POOL[frame['path']].split(',', 1)[1]))).convert('RGBA')
                if before.tobytes() != image.tobytes():
                    frame['revised_path'] = album.pooled_image(image)
                    frame['revised_bbox'] = album.bounds(image)
                    char['revised_count'] += 1
                    delta.append({'character': name, 'form': form, 'ref': ref,
                                  'changed_pixels': int(np.any(np.asarray(before) != np.asarray(image), axis=2).sum())})
                if ref == 0:
                    f = next(f for f in char['forms'] if f['id'] == form)
                    f['idle'], f['idle_bbox'] = album.pooled_image(image), album.bounds(image)
            # Replace partial layers directly from the current resource, including new layer ownership fixes.
            arc = archives['PL00_U.ARC']
            for frame in char['partial']:
                ref = frame['ref']
                if frame['status'] == 'unreconstructed':
                    continue
                layers, union = {}, np.zeros((384, 384), bool)
                for label, pb, start in (('base', 0, 0), ('legs', 8, 16), ('head', 5, 16),
                                         ('body', 6, 16), ('arm1', 7, 16), ('arm2', 7, 32)):
                    indices, _ = arc.layer(ref, pb)
                    image = arc.rgba(indices, start)
                    layers[label] = album.pooled_image(image)
                    union |= np.asarray(image)[:, :, 3] > 0
                frame['layers'] = layers
                ys, xs = np.nonzero(union)
                frame['bbox'] = [int(xs.min()-160), int(ys.min()-160), int(xs.max()+1-160), int(ys.max()+1-160)] if len(xs) else None
                other = next(f for f in char['frames'] if f['id'] == frame['id'])
                other['layers'], other['bbox'] = layers, frame['bbox']
            # Capsule sheets also remain current only if their banks were preserved by proposal proof.
            from src.psx_player import bank_offsets
            parent = read_disc(ROOT / proof['projects'][mode]['bin'], ('PL02_U.ARC',))[0]['PL02_U.ARC']
            for kind, bank in ((2, 10), (3, 18)):
                a, b = entry(parent, kind), entry(current[mode]['PL02_U.ARC'], kind)
                starts = bank_offsets(a, allow_aliases=True)
                require(starts == bank_offsets(b, allow_aliases=True) and a[starts[bank]:] == b[starts[bank]:],
                        'Capsule imagery requires fresh export')
        counts[name] = {'forms': len(char['forms']), 'references': len(char['frames']) - len(char['partial']),
                        'new_changed_references': char['revised_count']}
    html = album.page_html(data, sources, playback, empty)
    html = html.replace('전체 스프라이트 모음집', '2026-11-06 현재 스프라이트 재검토판')
    html = html.replace('이번 수정77이미지 참조입니다.', f'이번 수정{len(delta)}이미지 참조입니다.')
    html = html.replace('최신 적용 BIN의 도트를', '아래 출처 해시로 확인한 현재 BIN의 도트를')
    out = ROOT / 'out/sprite_reaudit_20261106'
    out.mkdir(exist_ok=True)
    target = out / 'ALL_SPRITES_CURRENT.html'
    require(not target.exists(), 'Current album already exists')
    target.write_text(html, 'utf8')
    write_json(out / 'manifest.json', {'HTML': target.relative_to(ROOT).as_posix(), 'sha256': file_hash(target),
                                     'sources': sources, 'counts': counts, 'changes': delta,
                                     'timing_unchanged': True, 'gameplay_simulated': False,
                                     'all_images_embedded': True, 'original_album_preserved': True})
    print(json.dumps({'HTML': str(target), 'changed_references': len(delta), 'counts': counts}))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--plan', type=Path, action='append', default=[])
    main(p.parse_args().plan)
