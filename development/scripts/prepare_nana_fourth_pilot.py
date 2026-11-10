"""포스아머 기준안 두 자세를 정규화하고 현재 파츠를 읽기 전용으로 조사한다."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scripts.discover_inputs import DiscReader, psx_arc, sha256
from scripts.project import digest
from scripts.extract_zero import save_image
from scripts.prepare_nana_pilot import normalize, COLORS
from src.psx_player import graphics_bank, decode_stream, composition_frame
from src.psx_sprite_batch import canvas_from_parts

PARENT = ROOT / 'out/ver_rin_nana/rin_sfx_20261030T052735067302Z'
PARENT_SHA = 'd1cae82f50bce60c91fa0a2f8a35ac61dec13eca428d24ef5f0281253c7e13eb'
ART = ROOT / 'work/ver_rin_nana/nana_fourth_armor/pilot_v1'
ORIGINAL = ROOT / 'work/ver_buki_riko/shibuki_x_extract/20261026T024200768121Z/original.arc'
REF = ROOT / 'character/ver_rin_nana/nana(4th armor).webp'
REF_SHA = '18a7ce7ea8056ff04ddc536df6536a6ce18aed93771b48a9f396d6144f599920'
GENERATED_SHA = '7f9ac0f1a8ff60f2facc83d3d18565f53a5a12b7f052800da583706b379b9b1e'
LAYERS = [('head', 1, 5), ('body', 2, 6), ('arm', 4, 7), ('leg', 8, 8)]


def require(value, message):
    if not value:
        raise ValueError(message)


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', 'utf8')


def entry(raw, kind):
    hits = [e for e in psx_arc(raw) if int(e['type'], 16) == kind]
    require(len(hits) == 1, 'Ambiguous requested graphics entry')
    e = hits[0]
    return raw[e['offset']:e['offset'] + e['size']]


def render(raw, frame, armor=False):
    g, c, p = entry(raw, 2), entry(raw, 3), entry(raw, 9)
    d = graphics_bank(g, 0, allow_bank_aliases=True)['frames'][frame]
    pixels = decode_stream(g, d['offset'], d['limit'], d['tile_count'] * 128).data
    def layer(bank):
        v = canvas_from_parts(pixels, d['tile_count'], composition_frame(c, bank, frame))
        words = struct.unpack_from('<16H', p, 0 if bank == 0 else 32)
        im = Image.fromarray(v, 'P')
        colors = [component for w in words for component in ((w & 31)*255//31, ((w >> 5)&31)*255//31, ((w >> 10)&31)*255//31)]
        im.putpalette(colors + [0]*(768-len(colors))); im.info['transparency'] = 0
        return im.convert('RGBA'), v
    im, v = layer(0)
    if armor:
        for bank in (8, 5, 7, 6):
            im.alpha_composite(layer(bank)[0])
    return im, v, d, pixels


def prepare(output):
    output = output.resolve()
    require(output.is_relative_to(ROOT/'out/ver_rin_nana') and not output.exists(), 'Fresh variant output required')
    require(digest(PARENT/'rin_nana.bin') == PARENT_SHA and digest(REF) == REF_SHA, 'Game/reference changed')
    require(digest(ART/'generated.png') == GENERATED_SHA, 'Generated art changed')
    protected = json.loads((PARENT/'preservation.json').read_text('utf8'))
    for q in protected['files']:
        require(digest(ROOT/q['path']) == q['expected_sha256'], 'Protected input differs')
    arc = (PARENT/'modified.arc').read_bytes(); original = ORIGINAL.read_bytes()
    require(sha256(original) == '92b2a3209ad6603cf519616dc580400434271f87e8e7129495430c04d0d1c35a', 'Original extraction changed')
    with (PARENT/'rin_nana.bin').open('rb') as f:
        require(DiscReader(f, (PARENT/'rin_nana.bin').stat().st_size).read(1135, 796672) == arc, 'Current ARC differs from disc')
    current_compositions = entry(arc, 3)
    rows = []
    for frame in (0, 85, 115, 116, 117, 118, 119):
        _, v, desc, raw = render(arc, frame)
        base = composition_frame(current_compositions, 0, frame)
        base_tiles = {q['tile'] for q in base['parts']}
        layers = []
        for name, bit, bank in LAYERS:
            comp = composition_frame(current_compositions, bank, frame)
            tiles = {q['tile'] for q in comp['parts']}
            layers.append({'name': name, 'bit': bit, 'composition_bank': bank, 'part_count': len(comp['parts']),
                           'tiles': sorted(tiles), 'base_shared_tiles': sorted(base_tiles & tiles),
                           'composition': comp})
        yy, xx = np.nonzero(v)
        rows.append({'frame': frame, 'stream': desc, 'base_opaque_bbox_world': [int(xx.min())-80, int(yy.min())-80, int(xx.max()+1)-80, int(yy.max()+1)-80],
                     'base_tiles': sorted(base_tiles), 'armor_layers': layers})
    image = Image.open(ART/'generated.png').convert('RGBA')
    require(image.getchannel('A').getextrema() == (0, 255), 'Transparent artwork required')
    # Match accepted skin/hair indices; substitute only the unused cyan swatch
    # with light gray so the new white dress lining can be rendered cleanly.
    colors = COLORS[:-1] + [(208, 216, 224)]
    words = [0] + [0x8000 | ((r*31+127)//255) | ((g*31+127)//255)<<5 | ((b*31+127)//255)<<10 for r,g,b in colors]
    palette = np.array([[(w&31)*255//31, ((w>>5)&31)*255//31, ((w>>10)&31)*255//31] for w in words], np.int32)
    output.mkdir(parents=True)
    frames = []
    for section, frame in enumerate((0, 85)):
        crop = image.crop((section*image.width//2, 0, (section+1)*image.width//2, image.height))
        ys, xs = np.nonzero(np.array(crop.getchannel('A')) >= 128)
        box = (int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1))
        pic = normalize(crop.crop(box), 45, palette)
        foot = np.nonzero(pic[-3:])[1]
        x = round(79 - (int(foot.min())+int(foot.max()))/2)
        y = 103 - pic.shape[0]
        require(0 <= x and x+pic.shape[1] <= 160, 'Artwork outside canvas')
        canvas = np.zeros((160,160), np.uint8); canvas[y:y+pic.shape[0], x:x+pic.shape[1]] = pic
        rendered = save_image(canvas.tobytes(), (160,160), words, output/f'fourth_{frame:03d}_indexed.png').convert('RGBA')
        rendered.save(output/f'fourth_{frame:03d}.png')
        rendered.crop((48,48,120,112)).resize((432,384), Image.Resampling.NEAREST).save(output/f'fourth_{frame:03d}_6x.png')
        current, current_v, _, _ = render(arc, frame); current.save(output/f'base_{frame:03d}.png')
        native, _, _, _ = render(original, frame, True); native.save(output/f'original_fourth_{frame:03d}.png')
        opaque = canvas != 0; by, bx = np.nonzero(current_v)
        frames.append({'frame': frame, 'source_section': section, 'source_crop': box,
                       'normalized_size': list(pic.shape[::-1]), 'origin': [80,80],
                       'opaque_bbox_world': [x-80,y-80,x+pic.shape[1]-80,y+pic.shape[0]-80],
                       'sole_world_y': 22, 'support_center_world': x-80+(int(foot.min())+int(foot.max()))/2,
                       'accepted_base_height': int(by.max()-by.min()+1), 'candidate_height': 45,
                       'opaque_pixels': int(opaque.sum()), 'used_opaque_colors': len(set(canvas.flat)-{0}),
                       'base_pixels_outside_candidate': int(np.count_nonzero((current_v>0)&~opaque)),
                       'armor_overlay_packing_verified': False})
    (output/'palette.bin').write_bytes(struct.pack('<16H', *words))
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 18)
    small = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 15)
    board = Image.new('RGB', (960, 624), '#242934'); draw = ImageDraw.Draw(board)
    labels = [('original_fourth', '원작 포스아머'), ('base', '현재 나나 기본형'), ('fourth', '나나 포스아머 기준안')]
    for col, (prefix, label) in enumerate(labels):
        draw.text((col*320+16,12), label, font=font, fill='white')
        for row, frame in enumerate((0,85)):
            pic = Image.open(output/f'{prefix}_{frame:03d}.png').convert('RGBA').crop((40,48,120,112))
            base_y = 52 + row*270
            board.paste(pic, (col*320+226,base_y), pic)
            big = pic.resize((320,256), Image.Resampling.NEAREST)
            board.paste(big, (col*320,base_y), big)
            draw.line((col*320+10,base_y+55*4,col*320+309,base_y+55*4),fill='#61717d')
            draw.text((col*320+12,base_y+230), ('대기' if row==0 else '사랑이 사격')+' · 1× / 4×',font=small,fill='#d4deed')
    draw.text((16,598),'정적 미술 기준안 · 실제 게임 적용 화면 아님 · 체형 높이45px / 발 Y22',font=small,fill='#d4deed')
    board.save(output/'review_1x_4x.png')
    background = ROOT/'work/ver_buki_riko/zero_extract/20261023T062408235550Z/runtime_framebuffer_0.png'
    scene = Image.open(background).convert('RGBA')
    # A labeled staging composite; no claim that the scene was run with this art.
    for frame, x in ((0,220), (85,280)):
        pic = Image.open(output/f'fourth_{frame:03d}.png').convert('RGBA')
        scene.alpha_composite(pic, (x-80, 195-103))
    composite = Image.new('RGB',(960,764),'#242934')
    ImageDraw.Draw(composite).text((12,8),'배경 위 합성 미리보기 · 게임 미적용',font=font,fill='white')
    composite.paste(scene.resize((960,720),Image.Resampling.NEAREST),(0,44));composite.save(output/'background_composite_3x.png')
    report = {'task': 'fourth_armor_nana', 'scope': 'two_pose_art_pilot', 'parent': PARENT.relative_to(ROOT).as_posix(),
              'parent_sha256': PARENT_SHA, 'current_arc_sha256': sha256(arc), 'reference': REF.relative_to(ROOT).as_posix(),
              'reference_sha256': REF_SHA, 'generated_sha256': GENERATED_SHA, 'prompt': (ART/'prompt.txt').relative_to(ROOT).as_posix(),
              'image_tool': 'built_in_imagegen', 'frames': frames, 'palette_words': words,
              'current_armor_structure': rows, 'part_bits': {'head':1,'body':2,'arm':4,'leg':8},
              'renderer_order_from_verified_us_analysis': ['leg','head','arm','body'],
              'partial_outfit_assignment': None, 'game_data_modified': False, 'runtime_verified': False,
              'art_user_approved': False, 'armor_packing_verified': False,
              'outstanding': ['실제 기본형을 덮는 파츠 분배 및 바깥 실루엣 잔존 해결', '부분 장착 의상 배정 사용자 확인',
                              '사격 총구 실기 정렬', '전체 동작 확대 전 미술 기준 수용'],
              'protected_files': len(protected['files'])}
    write(output/'candidate.json', report)
    for q in protected['files']:
        require(digest(ROOT/q['path']) == q['expected_sha256'], 'Protected input changed')
    require(digest(PARENT/'rin_nana.bin') == PARENT_SHA, 'Current game changed')
    write(output/'preservation.json', {'files':protected['files'], 'parent_sha256':PARENT_SHA, 'unchanged':True})
    print(json.dumps({'output':output.relative_to(ROOT).as_posix(),'frames':frames,'game_modified':False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    prepare(parser.parse_args().output)
