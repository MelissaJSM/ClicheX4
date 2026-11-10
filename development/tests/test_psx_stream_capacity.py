"""명시된 고정 슬롯 안의 재압축 여유와 다음 자원 보호를 검사한다."""
import struct,unittest
from src.psx_compress import encode_stream,replace_stream
from src.psx_player import decode_stream

class AllocatedCapacityTests(unittest.TestCase):
    def setUp(self):
        self.old=encode_stream(bytes(128));self.new=struct.pack('<64H',*range(64))
        self.encoded=encode_stream(self.new)
        self.container=b'HEAD'+self.old+bytes(256)+b'NEXT'
        self.d={'tile_count':1,'offset':4,'limit':len(self.container)-4}

    def test_default_does_not_consume_capacity(self):
        with self.assertRaisesRegex(ValueError,'budget'):replace_stream(self.container,self.d,self.new)

    def test_explicit_capacity_grows_without_moving_next_resource(self):
        out,r=replace_stream(self.container,self.d,self.new,allocated_limit=self.d['limit'])
        self.assertEqual(len(out),len(self.container));self.assertEqual(out[:4],b'HEAD')
        self.assertEqual(out[4+len(self.encoded):],self.container[4+len(self.encoded):])
        self.assertEqual(decode_stream(out,4,self.d['limit'],128).data,self.new)
        self.assertEqual(r['growth_within_allocated_slot'],len(self.encoded)-len(self.old))

    def test_next_resource_boundary_cannot_be_extended(self):
        with self.assertRaisesRegex(ValueError,'boundary'):replace_stream(self.container,self.d,self.new,allocated_limit=self.d['limit']+2)

    def test_short_capacity_still_rejects_overflow(self):
        with self.assertRaisesRegex(ValueError,'budget'):replace_stream(self.container,self.d,self.new,allocated_limit=4+len(self.encoded)-2)

if __name__=='__main__':unittest.main()
