import unittest
from scripts.prepare_shibuki_hover_alignment import replace_reserved_slot
from src.psx_compress import encode_stream

class HoverReservedSlotTests(unittest.TestCase):
    def test_expands_only_into_existing_slot_tail(self):
        old=bytes(128);new=bytes(range(128));code=encode_stream(old)
        source=b'HEAD'+code+bytes(256-len(code))+b'NEXT'
        result,report=replace_reserved_slot(source,{'offset':4,'limit':260,'tile_count':1},new)
        self.assertEqual(result[:4],b'HEAD');self.assertEqual(result[260:],b'NEXT')
        self.assertEqual(len(result),len(source));self.assertGreater(report['used_preexisting_tail_bytes'],0)

    def test_refuses_to_enter_next_stream(self):
        code=encode_stream(bytes(128));source=code+b'NEXT'
        with self.assertRaises(ValueError):
            replace_reserved_slot(source,{'offset':0,'limit':len(code),'tile_count':1},bytes(range(128)))

    def test_refuses_tile_count_change(self):
        code=encode_stream(bytes(128))
        with self.assertRaises(ValueError):
            replace_reserved_slot(code,{'offset':0,'limit':len(code),'tile_count':1},bytes(256))
