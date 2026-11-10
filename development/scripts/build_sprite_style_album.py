"""네 캐릭터의 현재 BIN을 다시 복원하는 대기 기준 미술 검토판."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
import sys
import struct

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_sprite_album as album
from scripts.prepare_sprite_style_unification import SOURCES as EXPECTED, WORK, write as write_json
from scripts.c01_audio_build import read_disc, require
from scripts.export_x_consistency import Archive
from scripts.prepare_riko_ui import entry
from src.psx_disc import file_hash
from scripts.overhaul_sprites_audit import render, rgba
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import local_composition


def selection_image(assets, frame):
    texture = entry(assets['ST0E_U1.ARC'], 0x10102)
    parts = entry(assets['ST0E_U1.ARC'], 10)
    palette = entry(assets['COL0E_U1.ARC'], 5)
    bank = frame['bank']
    require(bank in (0, 2), 'Unexpected player selection bank')
    lo, hi, row = (0, 40960, 0) if bank == 0 else (90112, len(texture), 16)
    comp = composition_frame(parts, bank, frame['ref'])
    result = Image.new('RGBA', (384, 384))
    for part in comp['parts']:
        px, size, bounds, _ = compose_static(texture[lo:hi], local_composition({**comp, 'parts': [part]}))
        words = struct.unpack_from('<16H', palette, (row + part['clut']) * 32)
        image = rgba(np.frombuffer(px, np.uint8).reshape(size[1], size[0]), words)
        result.alpha_composite(image, (160 + bounds[0], 160 + bounds[1]))
    return result


def zero_palettes(arc):
    palette=entry(arc,9)
    normal=list(struct.unpack_from('<64H',palette))
    launch=(ROOT/'work/ver_buki_riko/art_pilot/hurt_launch_v1/preview_palette.bin').read_bytes()
    require(hashlib.sha256(launch).hexdigest()=='ac8308a990ad8e8f60f90ab3581ec2271e0bebfd700a4cd227b66407fbe8ca2c','Historical effect CLUT changed')
    normal[16:]=struct.unpack_from('<48H',launch,32)
    black=normal.copy();black[:16]=struct.unpack_from('<16H',palette,13*32)
    return {'normal':normal,'black':black}


def zero_image(arc, character, frame, palettes):
    key=frame['id'].split(':')[-1]
    if key.startswith('static6_'):
        recipe=ROOT/('work/ver_buki_riko/art_pilot/rakuhouha_v2/static_effects.json' if character=='riko'
                    else 'work/ver_rin_nana/style_revision/v4_special/static_burst/static_effects.json')
        bound=json.loads(recipe.read_text('utf8'));pal=(recipe.parent/bound['palette_file']).read_bytes()
        require(hashlib.sha256(pal).hexdigest()==bound['palette_sha256'],'Static effect palette changed')
        ref=int(key.split('_')[-1]);cp=composition_frame(entry(arc,3),6,ref)
        pix,size,bb,_=compose_static(entry(arc,0x10206),cp)
        a=np.zeros((384,384),np.uint8)
        a[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
        return rgba(a,struct.unpack('<16H',pal))
    bank,ref=frame['bank'],frame['ref']
    return rgba(render(arc,bank,bank*5,ref)[0],palettes[frame['form']])


def extracted(text, marker):
    return json.JSONDecoder().raw_decode(text[text.index(marker) + len(marker):])[0]


def main(plan_paths, output_directory=None):
    proof = json.loads((WORK / 'protection_before.json').read_text('utf8'))
    plans = {}
    for path in plan_paths:
        require(path.resolve().is_relative_to(WORK.resolve()), 'Unexpected plan path')
        plan = json.loads(path.read_text('utf8'))
        require(plan['project'] not in plans, 'Duplicate project plan')
        plans[plan['project']] = plan
    old_html = ROOT / 'out/sprite_reaudit_20261106/ALL_SPRITES_CURRENT.html'
    require(file_hash(old_html) == '9be1fe2389cd91d512eb1691be7fcfe4d76259bc5bd866579c93cf6869b96000',
            'Original album changed')
    text = old_html.read_text('utf8')
    data = extracted(text, 'const DATA=')
    album.POOL.update(extracted(text, 'const ASSETS='))
    empty = extracted(text, 'const EMPTY=')
    playback = extracted(text, 'PLAYBACK=')
    sources, current = {}, {}
    for mode, (stem, expected) in EXPECTED.items():
        source = ROOT / proof['sources'][mode]['bin']
        require(file_hash(source) == expected, 'Reaudit parent changed')
        names = ('PL00_U.ARC', 'PL01_U.ARC', 'PL02_U.ARC', 'MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61', 'ST0E_U1.ARC', 'COL0E_U1.ARC')
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
        for name in ('MOJIPAT.ARC', 'LOAD_U.ARC', 'SLUS_005.61', 'COL0E_U1.ARC'):
            require(after[name] == before[name], 'This album wrapper requires unchanged UI/timing')
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
        for frame in char['frames']:
            if frame['form'] != 'selection':
                continue
            image = selection_image(current[mode], frame)
            before = Image.open(io.BytesIO(base64.b64decode(album.POOL[frame['path']].split(',', 1)[1]))).convert('RGBA')
            if before.tobytes() != image.tobytes():
                frame['revised_path'] = album.pooled_image(image)
                frame['revised_bbox'] = album.bounds(image)
                char['revised_count'] += 1
                delta.append({'character': name, 'form': 'selection', 'ref': frame['ref'],
                              'changed_pixels': int(np.any(np.asarray(before) != np.asarray(image), axis=2).sum())})
        if name in ('riko','rin'):
            arc=current[mode]['PL01_U.ARC'];palettes=zero_palettes(arc)
            for frame in char['frames']:
                if frame['form'] not in ('normal','black'):
                    continue
                try:
                    image=zero_image(arc,name,frame,palettes)
                except (ValueError,IndexError):
                    require(frame.get('bank')==1 and 42<=frame.get('ref',-1)<=49,'Unexpected Zero decode failure')
                    continue
                before=Image.open(io.BytesIO(base64.b64decode(album.POOL[frame['path']].split(',',1)[1]))).convert('RGBA')
                if before.tobytes()!=image.tobytes():
                    frame['revised_path']=album.pooled_image(image);frame['revised_bbox']=album.bounds(image)
                    char['revised_count']+=1
                    delta.append({'character':name,'form':frame['form'],'ref':frame['id'],
                                  'changed_pixels':int(np.any(np.asarray(before)!=np.asarray(image),axis=2).sum())})
                if frame.get('bank')==0 and frame.get('ref')==147:
                    f=next(f for f in char['forms'] if f['id']==frame['form'])
                    f['idle'],f['idle_bbox']=album.pooled_image(image),album.bounds(image)
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
            parent = read_disc(ROOT / proof['sources'][mode]['bin'], ('PL02_U.ARC',))[0]['PL02_U.ARC']
            for kind, bank in ((2, 10), (3, 18)):
                a, b = entry(parent, kind), entry(current[mode]['PL02_U.ARC'], kind)
                starts = bank_offsets(a, allow_aliases=True)
                require(starts == bank_offsets(b, allow_aliases=True) and a[starts[bank]:] == b[starts[bank]:],
                        'Capsule imagery requires fresh export')
        counts[name] = {'forms': len(char['forms']), 'references': len(char['frames']) - len(char['partial']),
                        'new_changed_references': char['revised_count']}
    html = album.page_html(data, sources, playback, empty)
    html = html.replace('전체 스프라이트 모음집', '2026-11-07 대기 기준 세부 묘사 검토판')
    html = html.replace('이번 수정77이미지 참조입니다.', f'이번 수정{len(delta)}이미지 참조입니다.')
    html = html.replace('최신 적용 BIN의 도트를', '아래 출처 해시로 확인한 현재 BIN의 도트를')
    out = output_directory.resolve() if output_directory else ROOT / 'out/sprite_style_unification_20261107'
    require(out.is_relative_to((ROOT/'out').resolve()), 'Album outside project output')
    out.mkdir(parents=True,exist_ok=True)
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
    p.add_argument('--output-directory', type=Path)
    args=p.parse_args()
    main(args.plan,args.output_directory)
