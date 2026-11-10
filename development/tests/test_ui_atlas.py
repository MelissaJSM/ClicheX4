import struct
import unittest
from src.psx_player import composition_frame
from src.psx_static_effect import compose_static
from src.psx_ui_atlas import repack_frames,place_frame,tile_pixels


def parts(frames):
    count=len(frames);cursor=count;headers=[];body=bytearray()
    for frame in frames:
        headers.append(len(frame)|(cursor<<16));cursor+=len(frame)
        for tile,x,y in frame:body.extend(struct.pack('<BBbb',tile//256,tile%256,x,y))
    return struct.pack('<I',4)+struct.pack('<'+'I'*count,*headers)+body


class UIAtlasTests(unittest.TestCase):
    def test_mirrored_texture_edge_is_avoided_without_clipping_art(self):
        texture=bytes(4096);p=parts([[(0,0,0)]])
        target=(bytes([3]*256),(16,16))
        g,q,_=repack_frames(texture,p,0,{0:target},guard_uv_zero=True)
        self.assertEqual(composition_frame(q,0,0)['parts'][0]['tile'],17)
        self.assertEqual(compose_static(g,composition_frame(q,0,0))[:2],target)
        with self.assertRaisesRegex(ValueError,'capacity exceeded'):
            repack_frames(bytes(2048),p,0,{0:target},guard_uv_zero=True)

    def test_unsafe_reserved_pattern_is_not_reused(self):
        from src.psx_ui_atlas import write_tile
        texture=bytearray(4096);write_tile(texture,0,bytes([3]*256))
        p=parts([[(0,0,0)],[(1,0,0)]])
        g,q,_=repack_frames(bytes(texture),p,0,{1:(bytes([3]*256),(16,16))},guard_uv_zero=True)
        self.assertEqual(composition_frame(q,0,1)['parts'][0]['tile'],17)
        self.assertEqual(tile_pixels(g,0),tile_pixels(texture,0))

    def test_non_sprite_menu_tiles_are_reserved(self):
        # A background tile is absent from the sprite-bank records but still
        # belongs to the load menu. Only the original icon slot is writable.
        texture=bytes([0x77]*2048);p=parts([[(15,0,0)]])
        g,q,report=repack_frames(texture,p,0,{0:(bytes([3]*256),(16,16))},reserved_tiles=range(15))
        for t in range(15):self.assertEqual(tile_pixels(g,t),tile_pixels(texture,t))
        self.assertEqual(composition_frame(q,0,0)['parts'][0]['tile'],15)
        self.assertEqual(report['protected_tiles'],15)
        with self.assertRaisesRegex(ValueError,'capacity exceeded'):
            repack_frames(texture,p,0,{0:(bytes([3]*256),(16,16))},reserved_tiles=range(16))
        with self.assertRaisesRegex(ValueError,'Invalid external'):
            repack_frames(texture,p,0,{0:(bytes([3]*256),(16,16))},reserved_tiles=[16])

    def test_repack_preserves_other_frame_and_geometry(self):
        texture=bytes(2048);p=parts([[(0,0,0)],[(1,0,0)]])
        target=(bytes([3]*256),(16,16))
        g,q,report=repack_frames(texture,p,0,{0:target})
        self.assertEqual(compose_static(g,composition_frame(q,0,0))[:2],target)
        self.assertEqual(tile_pixels(g,1),tile_pixels(texture,1))
        self.assertEqual(q[:12],p[:12])
        self.assertTrue(report['untouched_frames_preserved'])

    def test_capacity_failure_does_not_modify_inputs(self):
        p=parts([[(0,0,0),(1,16,0)]]+[[(i,0,0)] for i in range(1,16)])
        texture=bytes(2048);target=(bytes([1]*16+[2]*16)*16,(32,16))
        with self.assertRaisesRegex(ValueError,'capacity exceeded'):
            repack_frames(texture,p,0,{0:target})
        self.assertEqual(texture,bytes(2048))

    def test_untouched_shared_record_is_protected(self):
        p=struct.pack('<III',4,1|(2<<16),1|(2<<16))+bytes(4)
        with self.assertRaisesRegex(ValueError,'protected-frame mismatch'):
            repack_frames(bytes(2048),p,0,{0:(bytes([2]*256),(16,16))})

    def test_registration_refuses_clipping(self):
        p=parts([[(0,0,0)]])
        with self.assertRaisesRegex(ValueError,'clips an opaque pixel'):
            place_frame((b'\x01',(1,1),(16,0,17,1)),composition_frame(p,0,0),bytes(2048))


if __name__=='__main__':unittest.main()
