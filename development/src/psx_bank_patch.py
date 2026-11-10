"""명시한 그래픽/파츠 은행의 같은 위치 이미지 갱신. 게임별 역할은 호출부에서 결속한다."""
from hashlib import sha256
from src.psx_player import bank_offsets, graphics_bank, decode_stream, composition_frame, compose_indices
from src.psx_frame_edit import edit_frame_set, frame_coverage
from src.psx_compress import replace_stream


def patch_bank(graphics, parts, bank_index, parts_index, frames, preserved_frames=(), *, clear_unreferenced=False, allow_slot_growth=False):
    """공유 스트림 전체를 요구하고 선택 은행의 그래픽 바이트만 변경한다.

    무변경 입력은 압축 바이트까지 보존한다. 효과는 caller가 원본 해시에
    결속한 입력 그래픽 기준으로 보존한다. 팔레트·파츠·시간표는 쓰지 않는다.
    """
    if type(bank_index) is not int or type(parts_index) is not int:
        raise ValueError('Explicit integer bank mapping required')
    if not frames or any(type(n) is not int for n in frames):
        raise ValueError('Explicit integer frame numbers required')
    bank = graphics_bank(graphics, bank_index)
    if any(n < 0 or n >= len(bank['frames']) for n in frames):
        raise ValueError('Frame outside selected graphics bank')
    preserved = set(preserved_frames)
    if not preserved <= frames.keys():
        raise ValueError('Preserved frame missing from selection')
    groups = {}; originals = {}; refs = {}
    for bi in range(len(bank_offsets(graphics))):
        for f in graphics_bank(graphics, bi)['frames']:
            refs.setdefault(f['offset'], set()).add((bi, f['index']))
    for n in sorted(frames):
        f = bank['frames'][n]
        c = composition_frame(parts, parts_index, n)
        raw = decode_stream(graphics, f['offset'], f['limit'], f['tile_count']*128)
        original = compose_indices(raw.data, f['tile_count'], c)[:2]
        if n in preserved and (frames[n][0], tuple(frames[n][1])) != original:
            raise ValueError('Preserved effect pixels changed')
        originals[n] = original
        groups.setdefault(f['offset'], []).append(n)
    result = graphics; reports = []
    for offset, numbers in groups.items():
        if refs[offset] != {(bank_index, n) for n in numbers}:
            raise ValueError('Stream shared with an unselected frame')
        f = bank['frames'][numbers[0]]
        if len({bank['frames'][n]['tile_count'] for n in numbers}) != 1:
            raise ValueError('Shared stream has inconsistent tile counts')
        raw = decode_stream(graphics, offset, f['limit'], f['tile_count']*128)
        edits = [(composition_frame(parts, parts_index, n), *frames[n]) for n in numbers]
        packed = edit_frame_set(raw.data, f['tile_count'],
            [edit for n,edit in zip(numbers,edits) if n not in preserved],
            preserved_compositions=[edit[0] for n,edit in zip(numbers,edits) if n in preserved])
        cleared=0
        if clear_unreferenced and packed != raw.data:
            # Every stream reference was required above. These are decoded
            # raster nibbles outside ALL of their original compositions,
            # never compression padding, headers or unexplained metadata.
            used=set()
            for composition,_,_ in edits:
                coverage,_,_=frame_coverage(raw.data,f['tile_count'],composition)
                used.update(source for sources in coverage for source in sources)
            cleaned=bytearray(packed)
            for offset in range(len(cleaned)):
                for shift in (0,4):
                    if (offset,shift) not in used and cleaned[offset]>>shift&15:
                        cleaned[offset]&=~(15<<shift);cleared+=1
            packed=bytes(cleaned)
        if packed == raw.data:
            report = {'start': offset, 'original_end': raw.end, 'original_bytes':raw.end-offset,
                      'encoded_bytes': 0, 'untouched_tail_bytes': raw.end-offset, 'byte_identical':True}
        else:
            try:
                result, report = replace_stream(result, f, packed,allocated_limit=f['limit'] if allow_slot_growth else None)
            except ValueError as exc:
                raise ValueError(f'Bank {bank_index} frames {numbers}: {exc}') from exc
            report['byte_identical'] = False
        reports.append({'bank':bank_index, 'parts_bank':parts_index, 'frames':numbers,
                        'unreferenced_raster_pixels_cleared':cleared,
                        'decoded_sha256':sha256(packed).hexdigest(), **report})
    allowed = [(r['start'], r['start']+r['encoded_bytes']) for r in reports if r['encoded_bytes']]
    if len(result) != len(graphics) or any(a != b and not any(lo <= i < hi for lo,hi in allowed)
            for i,(a,b) in enumerate(zip(graphics,result))):
        raise ValueError('Graphics write escaped selected stream ranges')
    changed = []
    for bi in range(len(bank_offsets(graphics))):
        for f in graphics_bank(graphics, bi)['frames']:
            before = decode_stream(graphics, f['offset'], f['limit'], f['tile_count']*128).data
            after = decode_stream(result, f['offset'], f['limit'], f['tile_count']*128).data
            if before != after:
                if bi != bank_index or f['index'] not in frames:
                    raise ValueError('Unselected bitmap changed')
                changed.append([bi,f['index']])
            if bi == bank_index and f['index'] in frames:
                actual = compose_indices(after,f['tile_count'],composition_frame(parts,parts_index,f['index']))[:2]
                data,size = frames[f['index']]
                if actual != (data,tuple(size)):
                    raise ValueError('Reassembled frame differs from input')
    return result, {'bank':bank_index,'parts_bank':parts_index,'compression':reports,
                    'decoded_changed_references':changed,'preserved_frames':sorted(preserved),
                    'other_bitmaps_unchanged':True,'composition_changed':False,
                    'animation_timing_changed':False,'relocated':False}
