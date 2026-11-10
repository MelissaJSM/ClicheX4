"""그래픽 은행 하나의 경계를 보존하며 참조된 압축 스트림을 연속 배치한다."""
import struct

from src.psx_player import bank_offsets, graphics_bank, decode_stream


def repack_graphics_bank(source, bank_index, replacements):
    """replacements: frame index -> complete encoded stream; input is never mutated.

    Shared stream references must all be explicitly selected with identical data.
    Bank aliases are rejected because this operation promises a single-bank edit.
    Unselected streams retain their exact encoded bytes; only their addresses move.
    """
    offsets = bank_offsets(source, allow_aliases=True)
    bank = graphics_bank(source, bank_index, allow_bank_aliases=True)
    if offsets.count(bank['base']) != 1:
        raise ValueError('Cannot independently repack an aliased bank')
    frames = bank['frames']
    if not replacements or any(type(n) is not int or not 0 <= n < len(frames) for n in replacements):
        raise ValueError('Invalid replacement selection')
    groups = {}
    for frame in frames:
        groups.setdefault(frame['offset'], []).append(frame)
    codes, originals, expected = {}, {}, {}
    for start, refs in groups.items():
        f = refs[0]
        if any(r['tile_count'] != f['tile_count'] for r in refs):
            raise ValueError('Aliased stream has inconsistent tile counts')
        old = decode_stream(source, start, f['limit'], f['tile_count'] * 128)
        originals[start] = bytes(source[start:old.end])
        selected = [r['index'] for r in refs if r['index'] in replacements]
        if selected and len(selected) != len(refs):
            raise ValueError('All shared references must be selected')
        code = bytes(replacements[selected[0]]) if selected else originals[start]
        if any(bytes(replacements[n]) != code for n in selected):
            raise ValueError('Shared references have conflicting replacements')
        decoded = decode_stream(code, 0, len(code), f['tile_count'] * 128)
        if decoded.end != len(code):
            raise ValueError('Replacement has trailing bytes')
        codes[start] = code
        for r in refs:
            expected[r['index']] = decoded.data
    cursor = bank['base'] + len(frames) * 4
    locations = {}
    for start, code in sorted(codes.items()):
        locations[start] = cursor
        cursor += len(code)
    if cursor > bank['end']:
        raise ValueError('Repacked data exceeds bank capacity')
    if any(pos - bank['base'] > 0xfffff for pos in locations.values()):
        raise ValueError('Relative offset overflow')
    if locations[frames[0]['offset']] != bank['base'] + len(frames) * 4:
        raise ValueError('First stream must preserve the table-length sentinel')
    result = bytearray(source)
    for start, code in codes.items():
        pos = locations[start]
        result[pos:pos + len(code)] = code
    for f in frames:
        struct.pack_into('<I', result, bank['base'] + f['index'] * 4,
                         f['tile_count'] << 20 | locations[f['offset']] - bank['base'])
    if len(result) != len(source) or result[:bank['base']] != source[:bank['base']] or result[bank['end']:] != source[bank['end']:]:
        raise ValueError('Bank boundary changed')
    rebuilt = graphics_bank(result, bank_index, allow_bank_aliases=True)
    if len(rebuilt['frames']) != len(frames):
        raise ValueError('Frame table changed')
    for f in rebuilt['frames']:
        if f['tile_count'] != frames[f['index']]['tile_count'] or decode_stream(result, f['offset'], f['limit'], f['tile_count'] * 128).data != expected[f['index']]:
            raise ValueError('Repacked readback differs')
    report = {'bank': bank_index, 'base': bank['base'], 'end': bank['end'],
              'unique_streams': len(groups), 'checked_references': len(frames),
              'original_slack': bank['end'] - bank['base'] - len(frames)*4 - sum(map(len, originals.values())),
              'remaining_slack': bank['end'] - cursor,
              'streams_with_new_locations': sum(locations[s] != s for s in groups),
              'locations': [{'before': s, 'after': locations[s], 'encoded_bytes': len(codes[s])} for s in sorted(groups)],
              'unselected_encoded_bytes_preserved': True, 'bank_boundaries_preserved': True}
    return bytes(result), report
