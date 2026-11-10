"""최신 적용 BIN에서 리코·린을 전수 추출한다. 게임/원화/저장자료는 읽기 전용."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import struct
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.c01_audio_build import read_disc
from scripts.overhaul_sprites_audit import render, rgba, metrics
from scripts.prepare_riko_ui import entry
from scripts.inventory_zero_animations import LABELS
from scripts.prepare_zero_specials import GROUPS
from src.psx_player import graphics_bank, composition_frame, decode_stream
from src.psx_static_effect import compose_static
from src.psx_disc import file_hash

OUT = ROOT / 'out/sprite_consistency_20261105'
WORK = ROOT / 'work/sprite_consistency_20261105/zero'
SOURCES = {
    'riko': ('ver_buki_riko', 'shibuki_riko', 'bedba81a4c1263388835e10f57a8e30f6b7e9d9ac6f3f3d3dbf77821f4fb7c08'),
    'rin': ('ver_rin_nana', 'rin_nana', 'b15be8bf18921f06c8e6713c0bdc51a22374764c7d59ec7fca29df97f2e742c1'),
}
GROUND_BODY = {61,62,63,65,67,69,71,73,75,77,79,81,82,83,85,87,89,91,93,95,97,99,101,
               105,107,109,111,113,115,117,119,121,123,125,127,130,131,132,133,134}
AIR_BODY = {*range(213,230,2), *range(230,247,2)}
LADDER_EFFECT = {198,200,203,205,207,209,211}
SPECIAL_BODY = {86,87,88,91,93,95,96,98,99,101,103,105,107,108,110,112,114,116,119,122,125,128,129,130,131,
                *range(132,144), *range(144,161,2), 161,163,165,167,169,171,173,175, *range(177,190)}
LABELS = {**LABELS, 1:'등장 빛', 2:'등장 착지', 3:'귀환', 4:'전송 빛 이동',
          18:'공중 대시', 19:'공중 대시 종료', 34:'강한 피격', 39:'승리', 40:'퇴장',
          **{i:'라이드 아머 탑승' for i in range(41,65)},
          **{i:'라이드 체이서' for i in range(65,77)},
          **{i:'부분 업로드: 사용 경로 미확정' for i in range(77,81)}}
for name, bodies, effects in GROUPS:
    for aid in bodies:
        LABELS[aid] = name
    for aid in effects:
        LABELS[aid] = name + ' 효과/별도 호출'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(ok, why):
    if not ok:
        raise ValueError(why)


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')


def classify(bank, number):
    if bank == 0:
        if number in {0,1,2,146,147,148}:
            return 'idle', 'body'
        for low, high, label in ((3,20,'run'),(21,34,'jump'),(35,43,'wall'),(44,52,'dash'),
                                 (53,60,'arrival_light'),(61,134,'ground_saber'),(135,145,'hurt'),
                                 (149,154,'low_hp'),(155,173,'shippuuga'),(174,212,'ladder'),
                                 (213,246,'air_saber'),(247,253,'arrival_body')):
            if low <= number <= high:
                effect = (label == 'arrival_light' or label == 'ground_saber' and number not in GROUND_BODY or
                          label == 'shippuuga' and number >= 157 and number % 2 == 1 or
                          label == 'ladder' and number in LADDER_EFFECT or
                          label == 'air_saber' and number not in AIR_BODY)
                return label, 'effect' if effect else 'body_with_effect' if number in {140,141,143,145,247,248} else 'body'
    else:
        if number < 9:
            return 'victory_return_body', 'body_with_effect' if number >= 7 else 'body'
        if number < 14:
            return 'return_light', 'effect'
        if number < 42:
            return 'ride_chaser', 'body'
        if number < 50:
            return 'ride_partial_unknown', 'partial_vram_update'
        if number < 66:
            return 'wall_saber', 'body' if number in {50,51,53,54,56,57,59,61,63,65} else 'effect'
        if number < 86:
            return 'ride_armor_head', 'blank' if number == 80 else 'head_only'
        for low, high, label in ((86,131,'raijingeki_shared'),(132,143,'hyouretsuzan'),
                                 (144,159,'ryuenjin'),(160,176,'air_spin'),(177,189,'rakuhouha')):
            if low <= number <= high:
                return label, 'body_with_effect' if number in {88,*range(177,182)} else 'body' if number in SPECIAL_BODY else 'effect'
    return 'unclassified', 'unknown'


def animations(exe):
    cfg = json.loads((ROOT / 'config/ps1_us_slus00561.json').read_text('utf8'))
    def get(address, length):
        start = address - 0x80010000 + 2048
        need(start >= 2048 and start + length <= len(exe), 'Sequence outside EXE')
        return exe[start:start + length]
    result, refs = [], defaultdict(list)
    for aid in range(144):
        pointer = struct.unpack('<I', get(cfg['zero_animation_table_address'] + 4 * aid, 4))[0]
        selector = get(cfg['zero_animation_bank_table_address'] + aid, 1)[0]
        need(selector in (0,1), 'Unexpected player bank selector')
        seen, seq, pos = set(), [], 0
        while pos not in seen:
            need(0 <= pos and len(seen) < 512, 'Invalid sequence traversal')
            seen.add(pos)
            duration, event, step, number = struct.unpack('<bbbB', get(pointer + pos * 4, 4))
            item = {'position':pos, 'duration_ticks':duration, 'event':event,
                    'relative_step':step, 'frame':number}
            seq.append(item)
            refs[selector,number].append({'id':aid, **item})
            pos += step
        result.append({'id':aid,'label':LABELS.get(aid),'graphics_bank':selector,
                       'parts_bank':0 if selector == 0 else 5,'table_address':hex(pointer),
                       'sequence':seq,'loop_to_position':pos,'timing_known':True,
                       'timing_unit':'animation_update_tick','wall_time_rate_known':False,
                       'event_behavior_verified':False,'label_evidence':
                       'scripts/inventory_zero_animations.py; scripts/prepare_zero_specials.py; '
                       'docs/RIKO_SPECIAL_TECHNIQUES.md; docs/RIKO_VICTORY_BEAM_OUT.md; docs/RIN_RIDE_PRODUCTION.md'})
    return result, refs, {key: {'address':hex(cfg[key]),'sha256':sha(get(cfg[key],size))}
                          for key,size in [('zero_animation_table_address',576),('zero_animation_bank_table_address',144)]}


def sheets(output, variant, records, images, idle):
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 13)
    groups = defaultdict(list)
    for record in records:
        if record['render_status'] == 'decoded':
            groups[record['group']].append(record)
    results = []
    for group, rows in groups.items():
        for start in range(0, len(rows), 24):
            batch = rows[start:start + 24]
            bounds = [im.getbbox() for im in [idle] + [images[r['id']] for r in batch]]
            bounds = [b for b in bounds if b]
            viewport = (min(b[0] for b in bounds)-5, min(b[1] for b in bounds)-5,
                        max(b[2] for b in bounds)+5, max(b[3] for b in bounds)+5)
            width, height = viewport[2]-viewport[0], viewport[3]-viewport[1]
            scale = 2
            cw, ch = max(width*4+24, 220), height*2+46
            columns = min(4,len(batch)); count_rows = (len(batch)+columns-1)//columns
            board = Image.new('RGB', (cw*columns,ch*count_rows+34), '#222b35')
            draw = ImageDraw.Draw(board)
            draw.text((8,5),f'{output.name} / {variant} / {group} | idle147 + frame | 2x nearest | world origin unchanged',font=font,fill='white')
            for i, record in enumerate(batch):
                x,y = i%columns*cw, i//columns*ch+34
                for column,im in enumerate((idle,images[record['id']])):
                    shown=im.crop(viewport).resize((width*scale,height*scale),Image.Resampling.NEAREST)
                    board.paste(shown,(x+6+column*(width*2+8),y+31),shown)
                draw.text((x+6,y+3),f"147    {record['id']} / {record['classification']}",font=font,fill='#dce8f2')
            relative = Path(variant)/'sheets'/f'{group}_{start//24:02}.png'
            board.save(output/relative)
            results.append({'group':group,'variant':variant,'path':relative.as_posix(),
                            'frames':[r['id'] for r in batch],'world_viewport':[q-160 for q in viewport],
                            'scale':2,'contains_complete_opaque_bounds':True})
    return results


def export(character, source=None, expected=None):
    mode, stem, historical_hash = SOURCES[character]
    need((source is None) == (expected is None), 'Explicit source requires its expected hash')
    if source is None:
        source = ROOT/'out'/mode/'ultimate_costumes_swapped_20261105_v1'/f'{stem}.bin'
        expected = historical_hash
    else:
        source = source.resolve()
        need(source.is_relative_to((ROOT/'out'/mode).resolve()), 'Source outside character project output')
    need(file_hash(source) == expected, 'Source BIN changed')
    out, work = OUT/character, WORK/character
    need(not work.exists() and all(not (out/name).exists() for name in
         ('manifest.json','indices','diagnostics','normal','black')), 'Export artifacts already exist')
    data, disc_records = read_disc(source, ('PL01_U.ARC','SLUS_005.61'))
    arc, exe = data['PL01_U.ARC'], data['SLUS_005.61']
    gfx, parts, palette = (entry(arc,kind) for kind in (2,3,9))
    out.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True)
    (out/'indices').mkdir();(out/'diagnostics').mkdir()
    for variant in ('normal','black'):
        (out/variant/'native').mkdir(parents=True);(out/variant/'sheets').mkdir()
    for name, value in data.items():
        (work/name).write_bytes(value)
    seqs, refs, tables = animations(exe)
    normal = list(struct.unpack_from('<64H',palette))
    # CLUT2 is a runtime effect palette, not PL01 row2. Preserve the bound
    # historical snapshot only for preview; it is not fresh runtime proof.
    launch_path = ROOT/'work/ver_buki_riko/art_pilot/hurt_launch_v1/preview_palette.bin'
    launch = launch_path.read_bytes()
    need(sha(launch)=='ac8308a990ad8e8f60f90ab3581ec2271e0bebfd700a4cd227b66407fbe8ca2c','Historical CLUT snapshot changed')
    normal[16:] = struct.unpack_from('<48H',launch,32)
    black = normal.copy();black[:16] = struct.unpack_from('<16H',palette,13*32)
    palettes = {'normal':normal,'black':black}
    for variant, words in palettes.items():
        (out/variant/'preview_palettes.bin').write_bytes(struct.pack('<64H',*words))
    rows, all_images, groups = [], {'normal':{},'black':{}}, defaultdict(list)
    for gb in (0,1):
        bank = graphics_bank(gfx,gb)
        for descriptor in bank['frames']:
            n = descriptor['index']; pb = 0 if gb == 0 else 5
            ident = f'b{gb}_{n:03}'; group, kind = classify(gb,n)
            decoded = decode_stream(gfx,descriptor['offset'],descriptor['limit'],descriptor['tile_count']*128)
            comp = composition_frame(parts,pb,n)
            row = {'id':ident,'form':'zero_shared_bitmap','graphics_bank':gb,'parts_bank':pb,
                   'frame':n,'group':group,'classification':kind,'stream_offset':descriptor['offset'],
                   'compressed_bytes':decoded.end-decoded.start,'tile_count':descriptor['tile_count'],
                   'raw_sha256':sha(decoded.data),'parts':comp['parts'],
                   'animation_refs':refs.get((gb,n),[]),'timing_known':bool(refs.get((gb,n))),
                   'timing_unit':'animation_update_tick','runtime_verified_this_export':False,
                   'palette_status':'normal body row0 / black body row13; nonzero CLUT historical preview only',
                   'images':{},'render_status':'unverified'}
            try:
                indices, meta = render(arc,gb,pb,n)
                row.update(render_status='decoded',metrics=metrics(indices),indices_sha256=sha(indices.tobytes()),
                           indices_path=f'indices/{ident}.png',composition_bounds=meta['bounds'])
                im=Image.fromarray(indices,'P')
                table=[int(v) for word in normal for v in (((word&31)*255//31),((word>>5&31)*255//31),((word>>10&31)*255//31))]
                im.putpalette(table+[0]*(768-len(table)));im.save(out/row['indices_path'],transparency=0)
                for variant, words in palettes.items():
                    image=rgba(indices,words);relative=f'{variant}/native/{ident}.png'
                    image.save(out/relative);all_images[variant][ident]=image;row['images'][variant]=relative
            except (ValueError,IndexError) as error:
                need(gb==1 and 42<=n<=49,'Unexpected decode failure: '+ident+' / '+str(error))
                row.update(render_status='partial_vram_requires_previous_texture',reason=str(error),
                           reconstruction_limitation='1 tile update; parts reference prior VRAM beyond uploaded tile. '
                           'Do not label as missing body. Normal PS1 callers observed in historical audit use65..76; '
                           '77..80 reachability is not globally proved.',
                           evidence='docs/RIN_RIDE_PRODUCTION.md#남은8참조-조사')
                raw=np.frombuffer(decoded.data,np.uint8);pixels=np.empty(raw.size*2,np.uint8)
                pixels[0::2]=raw&15;pixels[1::2]=raw>>4
                tiny=rgba(pixels.reshape(16,16),normal[:16]);tiny.save(out/'diagnostics'/f'{ident}_single_tile.png')
                (work/f'{ident}_raw.bin').write_bytes(decoded.data)
                row['diagnostic_only']=f'diagnostics/{ident}_single_tile.png'
            rows.append(row)
    # A shockwave has embedded body pixels outside the compressed player banks.
    static_recipe = ROOT/('work/ver_buki_riko/art_pilot/rakuhouha_v2/static_effects.json' if character=='riko'
                         else 'work/ver_rin_nana/style_revision/v4_special/static_burst/static_effects.json')
    bound=json.loads(static_recipe.read_text('utf8'));static_palette=(static_recipe.parent/bound['palette_file']).read_bytes()
    need(sha(static_palette)==bound['palette_sha256'],'Static effect palette changed')
    for n in (23,24):
        cp=composition_frame(parts,6,n);pix,size,bb,_=compose_static(entry(arc,0x10206),cp)
        a=np.zeros((384,384),np.uint8);small=np.frombuffer(pix,np.uint8).reshape(size[1],size[0])
        a[160+bb[1]:160+bb[3],160+bb[0]:160+bb[2]]=small
        ident=f'static6_{n:03}';im=rgba(a,struct.unpack('<16H',static_palette))
        row={'id':ident,'form':'shared_static_effect','graphics_bank':None,'parts_bank':6,'frame':n,
             'group':'rakuhouha_static_body','classification':'body_with_effect','render_status':'decoded',
             'metrics':metrics(a),'indices_path':f'indices/{ident}.png','indices_sha256':sha(a.tobytes()),
             'images':{},'parts':cp['parts'],'texture_entry':'0x10206','timing_known':False,'animation_refs':[],
             'palette_status':'hash-bound historical CLUT0x7803, common to normal/black; fresh runtime unverified',
             'palette_source':static_recipe.relative_to(ROOT).as_posix(),'palette_sha256':sha(static_palette)}
        Image.fromarray(a,'L').save(out/row['indices_path'])
        for variant in palettes:
            relative=f'{variant}/native/{ident}.png';im.save(out/relative)
            all_images[variant][ident]=im;row['images'][variant]=relative
        rows.append(row)
    sheet_rows=[]
    for variant in palettes:
        sheet_rows.extend(sheets(out,variant,rows,all_images[variant],all_images[variant]['b0_147']))
    manifest={'character':character,'project':mode,'source':{'bin':source.relative_to(ROOT).as_posix(),
              'sha256':expected,'arc_sha256':sha(arc),'exe_sha256':sha(exe),'disc_records':disc_records},
              'canvas':{'width':384,'height':384,'origin':[160,160],'per_frame_scaling':False},
              'variants':{v:{'idle':f'{v}/native/b0_147.png','palette_row':0 if v=='normal' else 13,
                            'bitmap_shared':True} for v in palettes},
              'frames':rows,'animations':seqs,'animation_tables':tables,'sheets':sheet_rows,
              'coverage':{'compressed_refs':444,'standalone_decoded':436,'partial_updates':8,
                          'embedded_static_bodies':2,'all_compressed_streams_decoded':True,
                          'other_static_banks':'UI, projectiles and effects excluded from body consistency verdict'},
              'limitations':['Static PNGs are not in-game captures.',
                             'Do not infer body scale from whole bbox height during crouching, attack effects or riding.',
                             'Sequence traversal follows relative_step; event handlers and separate effect calls may alter playback.',
                             'No 60fps claim: animation ticks are known; observed wall-clock rate remains unknown.',
                             'CLUT2 and static body shockwaves use historical captured palettes, not current runtime color proof.',
                             'Normal/Black share every bitmap; changed row13 does not recolor shared external effects.']}
    need(len(rows)==446 and sum(r['render_status']=='decoded' for r in rows)==438,'Coverage mismatch')
    need(file_hash(source)==expected,'Input changed during export')
    write(out/'manifest.json',manifest)
    write(work/'extraction.json',{'source_preserved':True,'source_sha256':expected,'frames':len(rows),'sheets':len(sheet_rows),
                                 'output':out.relative_to(ROOT).as_posix(),'runtime_opened':False,'game_modified':False})
    print(json.dumps({'character':character,'frames':len(rows),'decoded':438,'partial':8,'sheets':len(sheet_rows),
                      'manifest':(out/'manifest.json').relative_to(ROOT).as_posix()},ensure_ascii=False))


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--character',choices=SOURCES,required=True)
    p.add_argument('--source',type=Path);p.add_argument('--expected-sha256')
    p.add_argument('--output-root',type=Path);p.add_argument('--work-root',type=Path)
    a=p.parse_args()
    if a.output_root is not None:
        OUT=a.output_root.resolve()
        need(OUT.is_relative_to((ROOT/'out').resolve()), 'Export outside output directory')
    if a.work_root is not None:
        WORK=a.work_root.resolve()
        need(WORK.is_relative_to((ROOT/'work').resolve()), 'Export outside work directory')
    export(a.character,a.source,a.expected_sha256)
