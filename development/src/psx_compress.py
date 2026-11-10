"""검증된 16bit LZ 형식의 결정적 인코더. 원래 스트림 범위를 넘는 삽입은 거부한다."""
from array import array
from bisect import bisect_left
import struct

from src.psx_player import decode_stream


def longest_matches(words):
    """각 위치에서 유효한 가장 긴 zero run 또는 2047-word 역참조를 찾는다."""
    count = len(words)
    zero_runs = [0]*(count+1)
    for i in range(count-1, -1, -1):
        if words[i] == 0:
            zero_runs[i] = zero_runs[i+1]+1
    history = {}
    matches = []
    for i in range(count):
        longest, distance = zero_runs[i], 0
        key = tuple(words[i:i+2])
        previous = history.setdefault(key, [])
        if len(key) == 2 and longest < count-i:
            lower = bisect_left(previous, i-2047)
            for j in reversed(previous[lower:]):
                if longest >= 2 and words[j+longest] != words[i+longest]:
                    continue
                length = 2
                while i+length < count and words[j+length] == words[i+length]:
                    length += 1
                if length > longest:
                    longest, distance = length, i-j
                    if longest == count-i:
                        break
        matches.append((longest, distance))
        previous.append(i)
    return matches


def encode_stream(packed, max_bytes=None):
    """control word 비용까지 포함한 최소 길이 경로. 동일 입력은 동일 바이트를 만든다.

    각 위치의 최장 참조의 모든 접두 길이가 유효하므로 하나의 거리만 보관한다.
    DP 상태는 (word 위치, 16-token control 내 슬롯)이다. 범위 최솟값 표로
    긴 참조를 포함한 모든 길이를 비교한다. 특정 아트/게임 주소는 사용하지 않는다.
    """
    if not packed or len(packed) % 2 or len(packed) > 0x8000:
        raise ValueError('Invalid decompressed size')
    if max_bytes is not None and (not isinstance(max_bytes, int) or max_bytes < 0):
        raise ValueError('Invalid compressed budget')
    words = struct.unpack('<'+'H'*(len(packed)//2), packed)
    count = len(words)
    matches = longest_matches(words)
    stride = count+1
    levels = stride.bit_length()
    # key = word cost * stride + reverse position; ties prefer a longer token.
    tables = [[array('I', [0])*stride for _ in range(levels)] for _ in range(16)]
    choices = [array('I', [0])*count for _ in range(16)]
    for slot in range(16):
        tables[slot][0][count] = (2+(slot == 0))*stride  # end token

    def minimum(slot, first, last):
        level = (last-first+1).bit_length()-1
        row = tables[slot][level]
        return min(row[first], row[last-(1 << level)+1])

    for i in range(count-1, -1, -1):
        longest, distance = matches[i]
        for slot in range(16):
            next_slot = (slot+1) % 16
            cost = 1+tables[next_slot][0][i+1]//stride
            length = 1
            for first, last, token_cost in ((2, min(31, longest), 1), (32, longest, 2)):
                if first > last:
                    continue
                key = minimum(next_slot, i+first, i+last)
                candidate_cost = token_cost+key//stride
                candidate_length = count-(key % stride)-i
                if (candidate_cost, -candidate_length) < (cost, -length):
                    cost, length = candidate_cost, candidate_length
            choices[slot][i] = (length << 11)|distance if length > 1 else 0
            tables[slot][0][i] = (cost+(slot == 0))*stride+count-i
        for slot in range(16):
            rows = tables[slot]
            for level in range(1, (count-i+1).bit_length()):
                rows[level][i] = min(rows[level-1][i], rows[level-1][i+(1 << (level-1))])

    tokens = []
    i, slot = 0, 0
    while i < count:
        choice = choices[slot][i]
        if not choice:
            tokens.append((False, (words[i],)))
            i += 1
        else:
            length, distance = choice >> 11, choice & 2047
            payload = ((length << 11)|distance,) if length <= 31 else (distance, length)
            tokens.append((True, payload))
            i += length
        slot = (slot+1) % 16
    tokens.append((True, (0, 0)))
    output = []
    for first in range(0, len(tokens), 16):
        group = tokens[first:first+16]
        output.append(sum(int(reference) << (15-i) for i, (reference, _) in enumerate(group)))
        for _, payload in group:
            output.extend(payload)
    result = struct.pack('<'+'H'*len(output), *output)
    if len(result)//2 != tables[0][0][0]//stride:
        raise AssertionError('Compressed cost mismatch')
    if max_bytes is not None and len(result) > max_bytes:
        raise ValueError(f'Compressed stream exceeds original budget: {len(result)} > {max_bytes}')
    return result


def replace_stream(graphics, descriptor, packed, *, allocated_limit=None):
    """위치/길이/테이블/남은 원본 바이트를 보존하며 원래 스트림 안에서만 쓴다."""
    expected = descriptor['tile_count']*128
    if len(packed) != expected:
        raise ValueError('Tile count or decompressed length change refused')
    start, limit = descriptor['offset'], descriptor['limit']
    original = decode_stream(graphics, start, limit, expected)
    capacity_end=original.end
    if allocated_limit is not None:
        if type(allocated_limit) is not int or not original.end<=allocated_limit<=limit:
            raise ValueError('Allocated stream capacity escapes descriptor boundary')
        capacity_end=allocated_limit
    encoded = encode_stream(packed, max_bytes=capacity_end-start)
    result = bytearray(graphics)
    result[start:start+len(encoded)] = encoded
    check = decode_stream(result, start, limit, expected)
    if check.data != packed or check.end != start+len(encoded) or len(result) != len(graphics):
        raise AssertionError('Compressed insertion readback mismatch')
    return bytes(result), {'start': start, 'original_end': original.end,
                           'original_bytes': original.end-start, 'encoded_bytes': len(encoded),
                           'untouched_tail_bytes': capacity_end-start-len(encoded),
                           'capacity_end':capacity_end,
                           'growth_within_allocated_slot':max(0,start+len(encoded)-original.end)}
