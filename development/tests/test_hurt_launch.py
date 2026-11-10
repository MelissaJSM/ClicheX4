import unittest,tempfile
from pathlib import Path
from copy import deepcopy
from src.psx_player import compose_indices
from src.psx_hurt_launch import shared_body,place_world
from src.psx_frame_edit import frame_coverage,read_indexed_png
from src.sprite_sheet import pack_frames,unpack_frames
from scripts.extract_zero import save_image
from tests.test_hurt import fixture

class LaunchTests(unittest.TestCase):
    def test_palette_selector_survives_overlapping_spark(self):
        raw,comps,base=fixture();c=comps[136];c['parts'][-1].update(clut=2,flags=8)
        with self.assertRaises(ValueError):compose_indices(raw,12,c)
        image,size,_,provenance=compose_indices(raw,12,c,allowed_cluts={0,2})
        self.assertEqual(image[21],40);self.assertEqual(sum(bool(v) for v in image),1)
        self.assertEqual(provenance[21]['part'],10)
        c['parts'][-1]['clut']=1
        with self.assertRaises(ValueError):compose_indices(raw,12,c,allowed_cluts={0,2})

    def test_body_and_nonwhite_effect_remain_independent(self):
        raw,c,base=fixture();comps={139:c[135],140:c[136],141:c[137]}
        for n in (140,141):comps[n]['parts'][-1].update(clut=2,flags=8)
        after=shared_body(raw,12,comps,139,base)
        self.assertEqual(compose_indices(after,12,comps[139])[:2],base)
        for n in (140,141):
            overlay={'parts':[dict(comps[n]['parts'][-1],clut=0)]}
            for sources in frame_coverage(raw,12,overlay)[0]:
                for offset,shift in sources:self.assertEqual((after[offset]>>shift)&15,(raw[offset]>>shift)&15)

    def test_aliasing_or_wrong_clut_rejected(self):
        raw,c,base=fixture();comps={139:c[135],140:c[136]};comps[140]['parts'][-1].update(clut=2,flags=8,tile=0)
        with self.assertRaisesRegex(ValueError,'aliases'):shared_body(raw,12,comps,139,base)
        comps[140]['parts'][-1]['clut']=0
        with self.assertRaisesRegex(ValueError,'verified body'):shared_body(raw,12,comps,139,base)

    def test_palette_aware_sheet_roundtrip_is_opt_in(self):
        frames={'body':(bytes([1,0,37,47]),(2,2),(0,0,2,2))}
        with self.assertRaises(ValueError):pack_frames(frames)
        data,layout=pack_frames(frames,max_index=63)
        self.assertEqual(unpack_frames(data,layout['size'],layout)['body'],frames['body'][:2])
        layout['max_index']=255
        with self.assertRaises(ValueError):unpack_frames(data,layout['size'],layout)

    def test_png_palette_hash_equivalent_and_transparent_alias_guard(self):
        words=tuple(range(64))
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'test.png';save_image(bytes([0,37,47]),(3,1),words,p)
            self.assertEqual(read_indexed_png(p,words,palette_banks=4)[0],bytes([0,37,47]))
            with self.assertRaises(ValueError):read_indexed_png(p,words)
            save_image(bytes([32]),(1,1),words,p)
            with self.assertRaises(ValueError):read_indexed_png(p,words,palette_banks=4)

    def test_world_registration_and_boundary_rejection(self):
        base=(bytes([0,3,0,4]),(2,2))
        data,size=place_world(base,(-1,-1,1,1),(4,4),(-2,-2,2,2))
        self.assertEqual(data[6],3);self.assertEqual(data[10],4)
        with self.assertRaises(ValueError):place_world(base,(-1,-1,1,1),(1,1),(0,0,1,1))

if __name__=='__main__':unittest.main()
