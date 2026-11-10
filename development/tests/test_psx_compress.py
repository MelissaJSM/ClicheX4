from functools import lru_cache
from itertools import product
import random
import struct
import unittest

from src.psx_compress import encode_stream, replace_stream
from src.psx_player import decode_stream


def pack(words):
    return struct.pack('<'+'H'*len(words), *words)


def exhaustive_cost(words):
    """작은 입력용 독립 oracle: 거리와 길이를 전부 열거하며 word 비용을 계산한다."""
    @lru_cache(None)
    def visit(position, slot):
        overhead = int(slot == 0)
        if position == len(words):
            return overhead+2
        next_slot = (slot+1) % 16
        best = 1+visit(position+1, next_slot)
        for distance in range(min(position, 2047)+1):
            length = 0
            while position+length < len(words):
                value = words[position+length-distance] if distance else 0
                if words[position+length] != value:
                    break
                length += 1
                best = min(best, (1 if length <= 31 else 2)+visit(position+length, next_slot))
        return overhead+best
    return visit(0, 0)


class CompressTests(unittest.TestCase):
    def test_exhaustive_small_inputs_have_minimum_size(self):
        for size in range(1, 7):
            for words in product(range(3), repeat=size):
                raw = pack(words)
                encoded = encode_stream(raw)
                self.assertEqual(len(encoded)//2, exhaustive_cost(words))
                self.assertEqual(decode_stream(encoded, 0, len(encoded), len(raw)).data, raw)

    def test_control_boundaries_overlap_and_extended_runs(self):
        rng = random.Random(4)
        cases = [list(range(1, 35)), [7]*96, [0]*96,
                 list(range(1, 18))+[0]*32+[5, 6]*40,
                 [rng.randrange(4) for _ in range(26)]]
        for words in cases:
            raw = pack(words)
            encoded = encode_stream(raw)
            self.assertEqual(encode_stream(raw), encoded)
            self.assertEqual(decode_stream(encoded, 0, len(encoded), len(raw)).data, raw)
            self.assertEqual(len(encoded)//2, exhaustive_cost(words))

    def test_full_window_and_nonrepeating_data_roundtrip(self):
        words = list(range(1, 2100))+list(range(53, 153))
        raw = pack(words)
        encoded = encode_stream(raw)
        self.assertEqual(decode_stream(encoded, 0, len(encoded), len(raw)).data, raw)

    def test_invalid_size_budget_and_fixed_range(self):
        for raw in (b'', b'\x00', bytes(0x8002)):
            with self.assertRaises(ValueError):
                encode_stream(raw)
        with self.assertRaises(ValueError):
            encode_stream(bytes(128), max_bytes=1)
        raw = pack(list(range(64)))
        original = encode_stream(raw)
        container = b'HEAD'+original+b'KEEP'
        descriptor = {'tile_count': 1, 'offset': 4, 'limit': len(container)-4}
        edited, report = replace_stream(container, descriptor, bytes(128))
        self.assertEqual(len(edited), len(container))
        self.assertEqual(edited[:4], b'HEAD')
        self.assertEqual(edited[4+report['encoded_bytes']:], container[4+report['encoded_bytes']:])
        self.assertEqual(decode_stream(edited, 4, descriptor['limit'], 128).data, bytes(128))
        with self.assertRaises(ValueError):
            replace_stream(container, descriptor, bytes(256))


if __name__ == '__main__':
    unittest.main()
