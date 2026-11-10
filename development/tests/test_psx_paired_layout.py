import unittest
import numpy as np
from src.psx_paired_layout import pack_pair,pack_joint_pair,pack_variant_pair
from src.psx_tile_layout import remap_tiles
from src.psx_player import compose_indices,indexed_atlas


class PairedLayoutTests(unittest.TestCase):
    def fixture(self):
        common=np.zeros((80,96),np.uint8);common[16:30,32:44]=3
        run=common.copy();run[32:40,32:40]=5
        shot=np.zeros_like(run);shot[32:36,32:44]=6
        gun=np.zeros_like(run);gun[32:36,18:32]=7
        return run,common,shot,gun

    def world(self,raw,parts):
        comp={'parts':[dict(index=i,tile=t,x=x,y=y,page=0,clut=0,unknown_flags=0,flip_x=bool(f&64),flip_y=bool(f&128)) for i,(t,x,y,f) in enumerate(parts)]}
        pix,size,bounds,_=compose_indices(raw,6,comp);out=np.zeros((80,96),np.uint8)
        out[bounds[1]:bounds[3],bounds[0]:bounds[2]]=np.frombuffer(pix,np.uint8).reshape(size[1],size[0]);return out

    def test_two_distinct_arms_share_body_and_preserve_armor(self):
        run,common,shot,gun=self.fixture();raw=bytes([0x98])*768
        packed,rp,sp,blank,target=pack_pair(raw,6,run,common,shot,gun,[(32,16)],(32,32),(16,28),{0,1,2,3,4})
        self.assertTrue(np.array_equal(self.world(packed,[(*p,0) for p in rp]),run))
        self.assertTrue(np.array_equal(self.world(packed,[(*p,0) for p in sp]),target))
        self.assertFalse(np.array_equal(run,target));self.assertEqual(blank,4)
        a,_,_=indexed_atlas(raw,6);b,_,_=indexed_atlas(packed,6)
        for y in range(16):self.assertEqual(a[y*256+80:y*256+96],b[y*256+80:y*256+96])
        mapping={0:0,1:3,2:2,3:1,4:4};flips={1:64,2:128};shifts={2:(1,2)}
        shifted=remap_tiles(packed,6,mapping,flips,shifts)
        def changed(parts):return [(mapping[t],x-shifts.get(t,(0,0))[0],y-shifts.get(t,(0,0))[1],flips.get(t,0)) for t,x,y in parts]
        self.assertTrue(np.array_equal(self.world(shifted,changed(rp)),run))
        self.assertTrue(np.array_equal(self.world(shifted,changed(sp)),target))

    def test_invalid_inputs_and_clipping_rejected(self):
        run,common,shot,gun=self.fixture()
        with self.assertRaises(ValueError):pack_pair(bytes(768),6,run.astype(np.int64)+256,common,shot,gun,[(32,16)],(32,32),(16,28),{0,1,2,3,4})
        with self.assertRaises(ValueError):remap_tiles(bytes([0x11])*768,6,{1:1},shifts={1:(1,0)})
        with self.assertRaises(ValueError):remap_tiles(bytes(768),6,{1:2})
        with self.assertRaises(ValueError):remap_tiles(bytes(768),6,{0:0},flips={0:64})
        with self.assertRaisesRegex(ValueError,'source row'):
            remap_tiles(bytes([0x11])*768,6,{1:1},flips={1:128})

    def test_joint_pair_preserves_both_targets_without_extra_parts(self):
        run,common,arm,gun=self.fixture();run[24:28,30:32]=4
        shot=common.copy();shot[arm!=0]=arm[arm!=0];shot[gun!=0]=gun[gun!=0];shot[24:28,30:32]=4
        packed,rp,sp,blank,target=pack_joint_pair(bytes(768),6,run,shot,[(32,16)],[(16,24),(32,32)],{0,1,2,3,4})
        self.assertEqual(len(rp),3);self.assertEqual(len(sp),3)
        self.assertTrue(np.array_equal(self.world(packed,[(*p,0) for p in rp]),run))
        self.assertTrue(np.array_equal(self.world(packed,[(*p,0) for p in sp]),shot))
        broken=shot.copy();broken[0,0]=3
        with self.assertRaisesRegex(ValueError,'outside unique'):
            pack_joint_pair(bytes(768),6,run,broken,[(32,16)],[(16,24),(32,32)],{0,1,2,3,4})

    def test_variant_pair_shares_only_equal_pixels_and_preserves_other_tiles(self):
        run=np.zeros((80,96),np.uint8);run[16:30,32:44]=3;run[32:40,32:40]=5
        shot=run.copy();shot[20:23,34:38]=9;shot[32:40,32:40]=0;shot[24:28,18:32]=7
        raw=bytes([0x98])*768
        packed,rp,sp,blank,target=pack_variant_pair(raw,6,run,shot,[(32,16)],[(32,24),(32,16)],[(17,16),(32,16)],{0,1,2,3,4})
        self.assertTrue(np.array_equal(self.world(packed,[(*p,0) for p in rp]),run))
        self.assertTrue(np.array_equal(self.world(packed,[(*p,0) for p in sp]),shot))
        a,_,_=indexed_atlas(raw,6);b,_,_=indexed_atlas(packed,6)
        for y in range(16):self.assertEqual(a[y*256+80:y*256+96],b[y*256+80:y*256+96])
        self.assertIsNone(blank)
        with self.assertRaisesRegex(ValueError,'Uncovered'):
            pack_variant_pair(raw,6,run,shot,[(32,16)],[],[(17,16),(32,16)],{0,1,2,3,4})

if __name__=='__main__':unittest.main()
