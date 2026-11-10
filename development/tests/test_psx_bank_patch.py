"""은행 번호가 겹치는 두 그래픽 묶음의 격리·무변경 왕복 검사."""
import struct
import unittest
from src.psx_compress import encode_stream
from src.psx_player import graphics_bank, decode_stream, composition_frame, compose_indices
from src.psx_bank_patch import patch_bank


def fixture(extra_tile=False):
    def bank(value):
        tiles=2 if extra_tile else 1
        raw=bytearray([value])*(128*tiles)
        if extra_tile:
            for y in range(16):
                for x in range(8,16):
                    raw[y*16+x]=((x+y)%15+1)*17
        stream = encode_stream(bytes(raw))
        return struct.pack('<2I', tiles*0x100000+8, tiles*0x100000+8)+stream
    a,b = bank(0x33),bank(0x77)
    # Directory banks are aligned, as in the game's actual data.
    a += bytes((-len(a))%4)
    gfx = struct.pack('<2I',8,8+len(a))+a+b
    pb = struct.pack('<2I',0x20001,0x30001)+struct.pack('<BBbb',0,0,-3,-7)*2
    parts = struct.pack('<6I',*[24+i*len(pb) for i in range(6)])+pb*6
    return gfx,parts


class BankPatchTests(unittest.TestCase):
    def test_no_change_keeps_original_compressed_bytes(self):
        gfx,parts=fixture();frames={n:(bytes([7])*256,(16,16)) for n in (0,1)}
        result,report=patch_bank(gfx,parts,1,5,frames,preserved_frames=(0,1))
        self.assertEqual(gfx,result)
        self.assertTrue(all(x['byte_identical'] for x in report['compression']))
        self.assertEqual(report['decoded_changed_references'],[])

    def test_second_bank_changes_without_touching_same_number_in_first(self):
        gfx,parts=fixture();frames={n:(bytes([5])*256,(16,16)) for n in (0,1)}
        result,report=patch_bank(gfx,parts,1,5,frames)
        first=graphics_bank(gfx,0)
        self.assertEqual(gfx[:first['end']],result[:first['end']])
        self.assertEqual(report['decoded_changed_references'],[[1,0],[1,1]])
        f=graphics_bank(result,1)['frames'][0]
        raw=decode_stream(result,f['offset'],f['limit'],128).data
        self.assertEqual(compose_indices(raw,1,composition_frame(parts,5,0))[:2],frames[0])

    def test_partial_shared_stream_and_effect_change_are_rejected(self):
        gfx,parts=fixture();frame=(bytes([5])*256,(16,16))
        with self.assertRaisesRegex(ValueError,'unselected'):
            patch_bank(gfx,parts,1,5,{0:frame})
        with self.assertRaisesRegex(ValueError,'effect'):
            patch_bank(gfx,parts,1,5,{0:frame,1:frame},preserved_frames=(1,))
        with self.assertRaisesRegex(ValueError,'missing'):
            patch_bank(gfx,parts,1,5,{0:frame,1:frame},preserved_frames=(2,))

    def test_invalid_mapping_dimensions_and_shared_conflict_are_rejected(self):
        gfx,parts=fixture();frame=(bytes([5])*256,(16,16))
        cases=[(2,5,{0:frame,1:frame}),(1,6,{0:frame,1:frame}),
               (1,5,{0:frame,2:frame}),(1,5,{'0':frame}),
               (1,5,{0:frame,1:(bytes([6])*256,(16,16))}),
               (1,5,{0:(bytes([5])*256,(8,32)),1:frame})]
        for bank,pb,frames in cases:
            with self.subTest(bank=bank,pb=pb),self.assertRaises(ValueError):
                patch_bank(gfx,parts,bank,pb,frames)

    def test_clear_unreferenced_requires_complete_group_and_preserves_all_views(self):
        gfx,parts=fixture(extra_tile=True)
        frames={n:(bytes([5])*256,(16,16)) for n in (0,1)}
        result,report=patch_bank(gfx,parts,1,5,frames,clear_unreferenced=True)
        self.assertEqual(report['compression'][0]['unreferenced_raster_pixels_cleared'],256)
        f=graphics_bank(result,1)['frames'][0];raw=decode_stream(result,f['offset'],f['limit'],256).data
        for n in frames:self.assertEqual(compose_indices(raw,2,composition_frame(parts,5,n))[:2],frames[n])
        first=graphics_bank(gfx,0)
        self.assertEqual(gfx[:first['end']],result[:first['end']])
        with self.assertRaisesRegex(ValueError,'unselected'):
            patch_bank(gfx,parts,1,5,{0:frames[0]},clear_unreferenced=True)
        unchanged={n:(bytes([7])*256,(16,16)) for n in (0,1)}
        same,_=patch_bank(gfx,parts,1,5,unchanged,clear_unreferenced=True)
        self.assertEqual(same,gfx)

    def test_size_growth_is_rejected(self):
        gfx,parts=fixture()
        data=bytes((i*i+13*i+(i//16)*7)%16 for i in range(256))
        with self.assertRaisesRegex(ValueError,'budget'):
            patch_bank(gfx,parts,1,5,{n:(data,(16,16)) for n in (0,1)})


if __name__=='__main__':unittest.main()
