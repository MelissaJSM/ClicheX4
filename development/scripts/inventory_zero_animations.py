"""지원 미국판의 실제 제로 애니메이션 테이블·프레임·공유 스트림을 읽기 전용으로 목록화."""
import argparse
import json
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.repack_zero import read_inputs
from scripts.project import new_run, write_json
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image
from src.psx_player import graphics_bank, bank_offsets, decode_stream, composition_frame, compose_indices

# 설명/기록은 한국어. 이름은 공개 디컴파일 호출부와 아래 로컬 테이블을 함께 근거로 삼는다.
LABELS = {5: '일반 대기', 7: '이동 시작', 8: '이동', 9: '이동 종료', 10: '점프', 11: '낙하',
          12: '착지', 13: '벽 붙기', 14: '벽 차기', 15: '벽 미끄러짐', 16: '대시',
          17: '대시 종료', 27: '사다리 잡기', 88: '지상 베기 1', 89: '지상 베기 2', 90: '지상 베기 3'}


def inventory(extracted):
    profile, _, arc, gfx_meta, gfx, parts, _ = read_inputs(extracted)
    exe = (extracted/'original.exe').read_bytes()
    if sha256(exe) != profile['executable']['sha256']:
        raise ValueError('Extracted executable hash mismatch')
    def read(address, length):
        offset = address-profile['executable']['load_address']+2048
        if offset < 2048 or offset+length > len(exe):
            raise ValueError('Animation address outside executable payload')
        return exe[offset:offset+length]
    out = new_run(ROOT, 'ver_buki_riko', 'animation_inventory')
    words = struct.unpack_from('<16H', (extracted/'palette_bank.bin').read_bytes())
    banks = [graphics_bank(gfx, n) for n in range(len(bank_offsets(gfx)))]
    frames, streams = {}, {}
    for bi, bank in enumerate(banks):
        for f in bank['frames']:
            decoded = decode_stream(gfx, f['offset'], f['limit'], f['tile_count']*128)
            composition = composition_frame(parts, 0 if bi == 0 else 5, f['index'])
            name = f"bank{bi}_{f['index']:03d}"
            try:
                pixels, size, bounds, _ = compose_indices(decoded.data, f['tile_count'], composition)
                save_image(pixels, size, words, out/f'{name}.png')
                rendering = {'size': size, 'bounds': bounds, 'origin': [-bounds[0], -bounds[1]],
                             'opaque_pixels': sum(bool(x) for x in pixels), 'indices_sha256': sha256(pixels),
                             'image': f'{name}.png', 'render_status': 'supported_local_decode'}
            except ValueError as error:
                # 별도 페이지/CLUT/무기 조립을 일반 몸체처럼 그려서 검증된 것으로 오인하지 않는다.
                rendering = {'size': None, 'bounds': None, 'origin': None, 'opaque_pixels': None,
                             'indices_sha256': None, 'image': None, 'render_status': 'unverified', 'reason': str(error)}
            stream_key = str(f['offset'])
            streams.setdefault(stream_key, []).append([bi, f['index']])
            frames[name] = {'bank': bi, 'frame': f['index'], 'stream_offset': f['offset'],
                            'compressed_bytes': decoded.end-decoded.start, 'tile_count': f['tile_count'],
                            'parts': composition['parts'], **rendering}
    animations = []
    for aid in range(144):
        address = struct.unpack('<I', read(profile['zero_animation_table_address']+aid*4, 4))[0]
        selector = read(profile['zero_animation_bank_table_address']+aid, 1)[0]
        bank = 0 if selector == 0 else 1
        seen, sequence, pos = set(), [], 0
        while pos not in seen:
            if pos < 0 or len(seen) >= 512:
                raise ValueError('Invalid animation sequence traversal')
            seen.add(pos)
            duration, event, step, frame = struct.unpack('<bbbB', read(address+pos*4, 4))
            if frame >= len(banks[bank]['frames']):
                raise ValueError('Animation references nonexistent frame')
            sequence.append({'position': pos, 'duration_ticks': duration, 'event': event,
                             'relative_step': step, 'frame': frame})
            pos += step
        animations.append({'id': aid, 'id_hex': hex(aid), 'label': LABELS.get(aid),
                           'label_evidence': 'player_enter.c / player_special.c / player_common.c' if aid in LABELS else None,
                           'table_address': address, 'bank_selector': selector, 'graphics_bank': bank,
                           'parts_bank': 0 if bank == 0 else 5, 'sequence': sequence, 'loop_to_position': pos,
                           'event_behavior_verified': False, 'runtime_verified': aid == 5})
    from PIL import Image, ImageDraw, ImageFont
    font = ImageFont.truetype('C:/Windows/Fonts/malgun.ttf', 16)
    for aid in (5, 8, 10, 16, 88):
        animation = animations[aid]
        numbers = list(dict.fromkeys(s['frame'] for s in animation['sequence']))
        columns = min(8, len(numbers)); rows = (len(numbers)+columns-1)//columns
        sheet = Image.new('RGB', (columns*200, rows*220+34), (30, 33, 40))
        draw = ImageDraw.Draw(sheet)
        draw.text((8, 6), f"원본 제로 · {LABELS[aid]} · ID {aid:#x} · 2배", font=font, fill='white')
        for index, frame in enumerate(numbers):
            name = f"bank{animation['graphics_bank']}_{frame:03d}"
            if not frames[name]['image']:
                continue
            picture = Image.open(out/f'{name}.png').convert('RGBA')
            x, y = index % columns*200, index//columns*220+34
            draw.text((x+6, y+5), f'frame {frame}', font=font, fill='white')
            enlarged = picture.resize((picture.width*2, picture.height*2), Image.Resampling.NEAREST)
            sheet.paste(enlarged, (x+4, y+32), enlarged)
        sheet.save(out/f'animation_{aid:03d}_2x.png')
    report = {'source_sha256': profile['source_sha256'], 'archive_sha256': sha256(arc), 'executable_sha256': sha256(exe),
              'animation_table_entries': len(animations), 'unique_sequence_addresses': len({a['table_address'] for a in animations}),
              'frame_references': len(frames), 'unique_streams': len(streams), 'animations': animations,
              'rendered_frames': sum(bool(f['image']) for f in frames.values()),
              'unverified_frames': [k for k, f in frames.items() if not f['image']],
              'frames': frames, 'stream_sharing': streams,
              'limitations': ['Sequence traversal follows relative_step only; event handlers can select other steps/states.',
                              '144 table entries are not 144 distinct gameplay actions; aliases/placeholders exist.',
                              'Frame images are local original extracts, not Riko production or gameplay proof.']}
    write_json(out/'inventory.json', report)
    print(json.dumps({'output': str(out), **{k: report[k] for k in ('animation_table_entries','unique_sequence_addresses','frame_references','unique_streams')}}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--extract', type=Path, required=True)
    inventory(parser.parse_args().extract)
