# Versioned extension: preserve frozen v1/v2/v3; add measured BR/RN standing copies1..8; frozen v4 remains unchanged.
"""대기 기준 세부 묘사 수정 자원을 새 BIN에 고정 길이로 삽입한다."""
import argparse
from pathlib import Path
import sys
import struct
import json
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import build_sprite_consistency as builder
from scripts.prepare_riko_ui import entry, SELECTION_MAPPING
from src.psx_ui_atlas import aliased_composition, local_composition, tile_pixels
from src.psx_static_effect import compose_static


def check_selection(old, new, sync_zero=False, preserve_x=False, sync_beam=False, sync_standing=False):
    """X 승리/귀환 및 명시한 Zero 사본만 허용하고 다른 UI를 보호한다."""
    builder.require(type(sync_zero) is bool, 'Invalid Zero selection scope')
    builder.require(type(preserve_x) is bool, 'Invalid X selection preservation scope')
    builder.require(type(sync_beam) is bool and not (sync_beam and preserve_x), 'Invalid beam scope')
    builder.require(type(sync_standing) is bool and not(sync_standing and preserve_x), 'Invalid standing scope')
    allowed_x = ((18, 19, 20, 21, 23) if sync_beam else (18, 19, 20, 21)) + (tuple(range(1,9)) if sync_standing else ())
    before, after = entry(old, 0x10102), entry(new, 0x10102)
    parts, revised = entry(old, 10), entry(new, 10)
    builder.require(len(before)==len(after) and len(parts)==len(revised), 'Selection layout length changed')
    builder.require(before[40960 if sync_zero else 0:90112] == after[40960 if sync_zero else 0:90112], 'Other selection artwork changed')
    if preserve_x:builder.require(before[90112:]==after[90112:],'Protected X selection texture changed')
    count = struct.unpack_from('<I', parts)[0] // 4
    offsets = struct.unpack_from('<' + 'I' * count, parts)
    builder.require(parts[:count*4] == revised[:count*4], 'Selection directory changed')
    lo = offsets[2]
    hi = min((v for v in offsets if v > lo), default=len(parts))
    permitted=bytearray(len(parts))
    if not preserve_x:permitted[lo:hi]=bytes([1])*(hi-lo)
    if sync_zero:
        owned=set()
        for ref in SELECTION_MAPPING:
            c=aliased_composition(parts,0,ref)
            for q in c['parts']:
                permitted[q['record_offset']:q['record_offset']+4]=b'\1'*4
                owned.add(q['page']*256+q['tile'])
        for tile in set(range(40960//128))-owned:
            builder.require(tile_pixels(before[:40960],tile)==tile_pixels(after[:40960],tile),'Unowned Zero selection tile changed')
        count0=aliased_composition(parts,0,0)['bank_frame_count']
        builder.require(count0==aliased_composition(revised,0,0)['bank_frame_count'],'Zero selection count changed')
        for ref in range(count0):
            p,q=aliased_composition(parts,0,ref),aliased_composition(revised,0,ref)
            builder.require(len(p['parts'])==len(q['parts']),'Zero selection part count changed')
            if ref not in SELECTION_MAPPING:
                builder.require(p==q,'Non-target Zero selection geometry changed')
                builder.require(compose_static(before[:40960],local_composition(p))==compose_static(after[:40960],local_composition(q)),'Non-target Zero selection pixels changed')
            else:
                for x,y in zip(p['parts'],q['parts']):
                    builder.require(x['record_offset']==y['record_offset'] and not y['unknown_flags'],'Zero selection part layout changed')
                    builder.require(y['clut']==(0 if ref==38 else x['clut']),'Zero selection CLUT changed')
    builder.require(all(a==b or permitted[i] for i,(a,b) in enumerate(zip(parts,revised))),'Other composition banks changed')
    frames = aliased_composition(parts, 2, 0)['bank_frame_count']
    for ref in range(frames):
        p, q = aliased_composition(parts, 2, ref), aliased_composition(revised, 2, ref)
        geometry = lambda c: [(a['flags'], a['tile'], a['x'], a['y'], a['flip_x'], a['flip_y'], a['clut']) for a in c['parts']]
        a, size, bounds, _ = compose_static(before[90112:], local_composition(p))
        b, ns, nb, _ = compose_static(after[90112:], local_composition(q))
        if preserve_x or ref not in allowed_x:
            builder.require(geometry(p) == geometry(q), 'Non-target selection parts changed')
            builder.require((a, size, bounds) == (b, ns, nb), 'Non-target selection sprite changed')
        else:
            if ref == 23:
                builder.require(len(p['parts']) == len(q['parts']), 'Beam part count changed')
                for old_part, new_part in zip(p['parts'], q['parts']):
                    # Earlier reviewed X body packing changed record locations.
                    # The beam-only preparation separately preserves v13 offsets.
                    builder.require(all(old_part[k] == new_part[k] for k in ('flip_x', 'flip_y', 'clut')), 'Beam part semantics changed')
            builder.require({v['clut'] for v in p['parts']} == {v['clut'] for v in q['parts']}, 'Selection CLUT changed')
            builder.require(all(not v['unknown_flags'] for v in q['parts']), 'Unknown selection flags')
            builder.require(all(-80 <= v <= 80 for v in nb), 'Selection parts outside sprite region')


def check_zero_selection_body(plan):
    """32개 선택 사본의 실제 RGBA와 원점을 현재 PL01 본체에 대조한다."""
    from scripts.build_sprite_style_album import selection_image,zero_image,zero_palettes
    from scripts.c01_audio_build import read_disc
    source=ROOT/plan['source_bin']
    builder.require(builder.file_hash(source)==plan['source_sha256'],'Parent hash mismatch')
    assets=read_disc(source,('PL01_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
    for name in list(assets):
        if name in plan['resources']:
            row=plan['resources'][name];data=(ROOT/row['path']).read_bytes()
            builder.require(builder.sha(data)==row['after'],'Zero selection/body hash mismatch')
            assets[name]=data
    char={'ver_buki_riko':'riko','ver_rin_nana':'rin'}[plan['project']]
    arc=assets['PL01_U.ARC'];pal=zero_palettes(arc)
    builder.require(entry(assets['COL0E_U1.ARC'],5)[:32]==entry(arc,9)[:32],'Zero selection palette differs')
    for ref,(bank,body) in SELECTION_MAPPING.items():
        actual=np.array(selection_image(assets,{'bank':0,'ref':ref}))
        expected=np.array(zero_image(arc,char,{'id':f'{char}:normal:b{bank}_{body:03d}','bank':bank,'ref':body,'form':'normal'},pal))
        builder.require(np.array_equal(actual,expected),f'Zero selection {ref} differs from player {bank}:{body}')
    return {'bank':0,'references':sorted(SELECTION_MAPPING),'rgba_and_origin_exact':True}


def check_selection_body(plan):
    """Keep v3 version-specific ceremony origins and add measured BR/RN shooting8."""
    from scripts.build_sprite_style_selection_v3 import check_selection_body as check_ceremonies
    from scripts.export_x_consistency import Archive
    from scripts.build_sprite_style_album import selection_image
    from scripts.c01_audio_build import read_disc
    check_ceremonies(plan)
    enabled=plan.get('sync_x_selection_standing',False)
    builder.require(type(enabled) is bool,'Invalid standing scope')
    if not enabled:return
    builder.require(plan['project'] in ('ver_buki_riko','ver_rin_nana'),'Unmeasured standing origin')
    source=ROOT/plan['source_bin']
    builder.require(builder.file_hash(source)==plan['source_sha256'],'Standing source hash mismatch')
    assets=read_disc(source,('PL00_U.ARC','ST0E_U1.ARC','COL0E_U1.ARC'))[0]
    for name in assets:
        if name in plan['resources']:
            row=plan['resources'][name];data=(ROOT/row['path']).read_bytes()
            builder.require(builder.sha(data)==row['after'],'Standing resource hash mismatch')
            assets[name]=data
    model=Archive(assets['PL00_U.ARC'])
    for ref,dy in enumerate((-1,0,0,0,0,-1,-2,0) if plan['project']=='ver_buki_riko' else (0,)*8,1):
        picture=np.array(model.composite(ref+84,0)[0]);expected=np.zeros_like(picture)
        yy,xx=np.where(picture[:,:,3]>0);ty=yy+dy
        builder.require(bool(np.all((ty>=0)&(ty<picture.shape[0]))),'Standing origin outside canvas')
        expected[ty,xx]=picture[yy,xx]
        builder.require(np.array_equal(np.array(selection_image(assets,{'bank':2,'ref':ref})),expected),f'Selection {ref} differs from gameplay {ref+84} at measured standing origin')


def check_static_body(old, new, bound):
    """해시로 묶인 낙봉파23/24만 허용하고 정적 타일의 다른 사용자를 보호한다."""
    from src.psx_player import composition_frame
    from src.psx_frame_edit import read_indexed_png
    recipe_path = (ROOT / bound['recipe']).resolve()
    builder.require(recipe_path.is_relative_to((ROOT/'work/sprite_style_unification_20261107').resolve()), 'Static recipe outside task')
    builder.require(builder.file_hash(recipe_path) == bound['sha256'], 'Static recipe hash mismatch')
    recipe = json.loads(recipe_path.read_text('utf8'))
    builder.require(recipe['kind'] == 'us_rakuhouha_embedded_body_v1' and set(recipe['frames']) == {'23', '24'}, 'Static scope changed')
    a, b, c, nc = entry(old, 0x10206), entry(new, 0x10206), entry(old, 3), entry(new, 3)
    builder.require(builder.sha(a) == recipe['source_texture_sha256'], 'Wrong static parent')
    builder.require(builder.sha(b) == recipe['modified_texture_sha256'] and builder.sha(nc) == recipe['parts_sha256'], 'Static texture/parts changed')
    def read_bound(name, expected):
        path = (recipe_path.parent/name).resolve()
        builder.require(path.is_relative_to(recipe_path.parent) and builder.file_hash(path) == expected, 'Static artwork binding mismatch')
        return path
    palette = read_bound(recipe['palette_file'], recipe['palette_sha256']).read_bytes()
    words = struct.unpack('<16H', palette)
    users = []
    for bank in (1, 2, 3, 4, 6):
        count = composition_frame(c, bank, 0)['bank_frame_count']
        builder.require(count == composition_frame(nc, bank, 0)['bank_frame_count'], 'Static composition count changed')
        for ref in range(count):
            cp, nparts = composition_frame(c, bank, ref), composition_frame(nc, bank, ref)
            semantic = lambda comp: [(p['flags'], p['tile'], p['x'], p['y']) for p in comp['parts']]
            builder.require(semantic(cp) == semantic(nparts), 'Static composition changed')
            tiles = {p['page']*256+p['tile'] for p in cp['parts']}
            altered = any(a[(t//16*16+y)*128+t%16*8:(t//16*16+y)*128+t%16*8+8]
                          != b[(t//16*16+y)*128+t%16*8:(t//16*16+y)*128+t%16*8+8]
                          for t in tiles for y in range(16))
            if altered:
                users.append([bank, ref])
    expected = recipe.get('expected_changed_references', [[6, 23], [6, 24]])
    builder.require(expected in ([[6, 23]], [[6, 24]], [[6, 23], [6, 24]]), 'Invalid static body scope')
    builder.require(users == expected, 'Static change escapes body effects')
    for ref in (23, 24):
        r = recipe['frames'][str(ref)]
        pixels, size = read_indexed_png(read_bound(r['file'], r['sha256']), words)
        builder.require(compose_static(b, composition_frame(nc, 6, ref))[:2] == (pixels, size), 'Static artwork differs')
    return {'recipe_sha256': bound['sha256'], 'changed_references': users, 'all_other_static_users_exact': True}


def guarded_build(path):
    plan = json.loads(path.read_text('utf8'))
    sync_zero=plan.get('sync_zero_selection_body',False)
    preserve_x=plan.get('preserve_x_selection',False)
    sync_beam=plan.get('sync_shibuki_selection_beam',False)
    sync_standing=plan.get('sync_x_selection_standing',False)
    builder.require(type(sync_standing) is bool, 'Invalid standing scope')
    builder.require(not sync_standing or (plan['project'] in ('ver_buki_riko','ver_rin_nana') and not preserve_x and 'ST0E_U1.ARC' in plan['resources']), 'Unmeasured or conflicting standing origin')
    builder.require(type(sync_beam) is bool, 'Invalid beam scope')
    builder.require(not sync_beam or (plan['project']=='ver_buki_riko' and not preserve_x and 'ST0E_U1.ARC' in plan['resources']), 'Missing or conflicting beam scope')
    builder.require(type(sync_zero) is bool,'Invalid Zero selection scope')
    builder.require(type(preserve_x) is bool,'Invalid X selection preservation scope')
    builder.require(not sync_zero or 'ST0E_U1.ARC' in plan['resources'],'Missing Zero selection resource')
    zero_proof=None
    if 'ST0E_U1.ARC' in plan['resources']:
        if not preserve_x:check_selection_body(plan)
        if sync_zero:zero_proof=check_zero_selection_body(plan)
    previous = builder.check_resource
    prior_allowed, prior_work = builder.ALLOWED, builder.WORK
    builder.ALLOWED = {**builder.ALLOWED, 'ST0E_U1.ARC': {0x10102, 10}}
    static_bound = plan.get('resources', {}).get('PL01_U.ARC', {}).get('static_body_patch')
    if static_bound:
        builder.ALLOWED['PL01_U.ARC'] = set(builder.ALLOWED['PL01_U.ARC']) | {0x10206}
    def checked(name, old, new):
        result = previous(name, old, new)
        if name == 'ST0E_U1.ARC':
            check_selection(old, new, sync_zero, preserve_x, sync_beam, sync_standing)
            result['selection_bank2_allowed_frames'] = [] if preserve_x else sorted(([18, 19, 20, 21, 23] if sync_beam else [18, 19, 20, 21]) + (list(range(1,9)) if sync_standing else []))
            result['standing_selection85_92_origin_exact'] = sync_standing
            result['shibuki_beam23_player160_origin_exact'] = sync_beam
            result['x_selection_all_bytes_preserved'] = preserve_x
            result['selection_gameplay_origin_and_pixels_exact'] = not preserve_x
            if zero_proof:result['zero_selection_body_sync']=zero_proof
        if name == 'PL01_U.ARC' and static_bound:
            result['static_body_patch'] = check_static_body(old, new, static_bound)
        return result
    builder.check_resource = checked
    builder.WORK = ROOT / 'work/sprite_style_unification_20261107'
    try:
        builder.build(path)
    finally:
        builder.check_resource = previous
        builder.ALLOWED, builder.WORK = prior_allowed, prior_work


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    guarded_build(args.plan)
