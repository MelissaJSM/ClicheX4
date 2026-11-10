"""확인된 파츠 조립을 역으로 적용하는 인덱스 프레임 편집. 파츠/기준점 변경 없음."""
from src.psx_player import indexed_atlas, compose_indices


def frame_coverage(packed, tiles, composition):
    _, locations, _ = indexed_atlas(packed, tiles)
    _, size, bounds, _ = compose_indices(packed, tiles, composition)
    coverage = [[] for _ in range(size[0]*size[1])]
    for part in composition['parts']:
        tx, ty = (part['tile'] & 15)*16, (part['tile'] >> 4)*16
        for y in range(16):
            for x in range(16):
                source = locations[(ty+y)*256+tx+x]
                px = part['x']-bounds[0]+(15-x if part['flip_x'] else x)
                py = part['y']-bounds[1]+(15-y if part['flip_y'] else y)
                coverage[py*size[0]+px].append(source)
    return coverage, size, bounds


def _requested_writes(packed, tiles, composition, indices, size, overlap_policy):
    coverage, expected_size, _ = frame_coverage(packed, tiles, composition)
    if tuple(size) != expected_size or len(indices) != size[0]*size[1]:
        raise ValueError('Frame dimensions changed')
    if any(index > 15 for index in indices):
        raise ValueError('Pixel index exceeds 4bpp palette')
    if overlap_policy not in ('reject', 'equal_sources'):
        raise ValueError('Unknown overlap edit policy')
    # The opt-in policy is order independent: every source at an overlapping
    # position must originally be identical, including transparent pixels.
    # All of those sources receive the same requested value. It cannot flatten
    # distinct foreground/background layers or silently discard hidden data.
    for sources in coverage:
        if len(set(sources)) > 1:
            if overlap_policy != 'equal_sources':
                raise ValueError('Overlapping parts require an explicit edit policy')
            if len({(packed[o] >> s) & 15 for o,s in sources}) != 1:
                raise ValueError('Overlapping sources differ in original data')
    writes = {}
    for index, sources in zip(indices, coverage):
        if not sources:
            if index:
                raise ValueError('Opaque pixel outside existing part coverage')
            continue
        for source in sources:
            if source in writes and writes[source] != index:
                raise ValueError('Shared tile pixels request conflicting values')
            writes[source] = index
    return writes, expected_size


def _apply_writes(packed, writes):
    result = bytearray(packed)
    for (offset, shift), index in writes.items():
        result[offset] = (result[offset] & ~(15 << shift)) | (index << shift)
    return bytes(result)


def edit_frame_indices(packed, tiles, composition, indices, size, *, overlap_policy='reject'):
    writes, expected_size = _requested_writes(packed, tiles, composition, indices, size, overlap_policy)
    result = _apply_writes(packed, writes)
    actual, actual_size, _, _ = compose_indices(result, tiles, composition)
    if actual_size != expected_size or actual != indices:
        raise ValueError('Edited frame cannot be represented by existing parts')
    return bytes(result)


def read_indexed_png(path, palette_words, *, palette_banks=1):
    """초기 편집 경로는 원본 팔레트 순서/단일 투명 index 0만 허용한다."""
    from PIL import Image
    with Image.open(path) as picture:
        if picture.format != 'PNG' or picture.mode != 'P' or getattr(picture, 'n_frames', 1) != 1:
            raise ValueError('Expected a single indexed PNG')
        if picture.info.get('transparency') != 0:
            raise ValueError('Expected transparent index 0 only')
        expected = [component for word in palette_words for component in
                    ((word & 31)*255//31, ((word >> 5) & 31)*255//31, ((word >> 10) & 31)*255//31)]
        if palette_banks not in (1,4) or len(palette_words) != 16*palette_banks or picture.getpalette()[:48*palette_banks] != expected:
            raise ValueError('Palette changes require a separate palette edit')
        indices = picture.tobytes()
        if max(indices, default=0) >= 16*palette_banks or any(i and i%16==0 for i in indices):
            raise ValueError('PNG contains pixel indices above 15')
        return indices, picture.size


def edit_frame_set(packed, tiles, frames, *, overlap_policy='reject', preserved_compositions=()):
    """같은 블록의 프레임을 함께 편집하고 모든 공유 타일 요구가 양립하는지 검사한다."""
    if not frames and not preserved_compositions:
        raise ValueError('At least one frame edit required')
    writes = {}
    # Preserve every original source texel, including pixels hidden by an
    # overlapping effect part. Rewriting a flattened preview would lose them.
    for composition in preserved_compositions:
        coverage, _, _ = frame_coverage(packed, tiles, composition)
        for sources in coverage:
            for offset, shift in sources:
                writes[offset, shift] = (packed[offset] >> shift) & 15
    for composition, indices, size in frames:
        requested, _ = _requested_writes(packed, tiles, composition, indices, size, overlap_policy)
        for source, value in requested.items():
            if source in writes and writes[source] != value:
                raise ValueError('Frame set has conflicting shared tile pixels')
            writes[source] = value
    result = _apply_writes(packed, writes)
    # 뒤 프레임이 앞 프레임의 공유 타일을 덮어쓴 경우도 여기서 거부한다.
    for composition, indices, size in frames:
        actual, actual_size, _, _ = compose_indices(result, tiles, composition)
        if actual != indices or actual_size != tuple(size):
            raise ValueError('Frame set has conflicting shared tile pixels')
    return result


def edit_base_layer_set(packed, tiles, frames):
    """Explicit base-part ownership; inactive overlay tiles must be disjoint.

    frames contains (composition, indices, size, base_part_count). All old
    overlay pixels are cleared, including hidden pixels. Shared active tiles
    still require identical writes. The complete original composition is used
    for the final roundtrip, so omitted/cropped artwork cannot silently pass.
    """
    writes = {}
    inactive = set()
    for composition, indices, size, count in frames:
        if not 0 < count < len(composition['parts']):
            raise ValueError('Explicit base layer count required')
        if any(p['flags'] & ~0x40 for p in composition['parts']):
            raise ValueError('Unmodeled base layer flags')
        _, full_size, bounds, _ = compose_indices(packed, tiles, composition)
        if tuple(size) != full_size or len(indices) != size[0]*size[1]:
            raise ValueError('Frame dimensions changed')
        base = {**composition, 'parts': composition['parts'][:count]}
        _, base_size, bb, _ = compose_indices(packed, tiles, base)
        cropped = bytes(indices[(y+bb[1]-bounds[1])*size[0]+x+bb[0]-bounds[0]]
                        for y in range(base_size[1]) for x in range(base_size[0]))
        requested, _ = _requested_writes(packed, tiles, base, cropped, base_size, 'reject')
        for source, value in requested.items():
            if source in writes and writes[source] != value:
                raise ValueError('Frame set has conflicting shared tile pixels')
            writes[source] = value
        overlay = {**composition, 'parts': composition['parts'][count:]}
        coverage, _, _ = frame_coverage(packed, tiles, overlay)
        inactive.update(source for sources in coverage for source in sources)
    if not frames or inactive & writes.keys():
        raise ValueError('Active and inactive layers share source pixels')
    result = _apply_writes(packed, {**dict.fromkeys(inactive, 0), **writes})
    for composition, indices, size, _ in frames:
        actual, actual_size, _, _ = compose_indices(result, tiles, composition)
        if actual != indices or actual_size != tuple(size):
            raise ValueError('Artwork cannot be represented by the selected base layer')
    return result
