"""Shared hurt body and spark ownership without copyrighted input fixtures."""
import unittest
from copy import deepcopy
from src.psx_hurt import edit_hurt_stream,flash_from_body
from src.psx_player import compose_indices
from src.psx_frame_edit import frame_coverage

def fixture():
    def part(i,t,x,y):
        return dict(index=i,record_offset=i*4,flags=0,page=0,clut=0,unknown_flags=0,tile=t,x=x,y=y,flip_x=False,flip_y=False)
    parts=[part(i,i,(i%5)*16,(i//5)*16) for i in range(10)]
    comps={135:{'parts':parts},136:{'parts':deepcopy(parts)+[part(10,10,16,0)]},137:{'parts':deepcopy(parts)+[part(10,11,16,16)]}}
    raw=bytearray(12*128)
    for n in (136,137):
        overlay={'parts':comps[n]['parts'][10:]};source=frame_coverage(raw,12,overlay)[0][5][0];o,s=source;raw[o]|=8<<s
    base=(bytes([2]*(80*32)),(80,32))
    return bytes(raw),comps,base

class HurtTests(unittest.TestCase):
    def test_rin_white_is_index11_and_flash_does_not_use_eye_cyan(self):
        raw,comps,base=fixture();result=edit_hurt_stream(raw,12,comps,base,spark_index=11)
        for n in (136,137):
            overlay={'parts':comps[n]['parts'][10:]}
            before=compose_indices(raw,12,overlay)[0];after=compose_indices(result,12,overlay)[0]
            self.assertEqual(after,bytes(11 if v else 0 for v in before))
        flash,_=flash_from_body((bytes([2]),(1,1)),(0,0,1,1),(3,3),(-1,-1,2,2),fill_index=10,outline_index=11)
        self.assertEqual(flash,bytes([11,11,11,11,10,11,11,11,11]))

    def test_custom_effect_colors_reject_transparency_and_out_of_range(self):
        raw,comps,base=fixture()
        for v in (0,16,-1,True):
            with self.assertRaises(ValueError):edit_hurt_stream(raw,12,comps,base,spark_index=v)
            with self.assertRaises(ValueError):flash_from_body((bytes([2]),(1,1)),(0,0,1,1),(3,3),(-1,-1,2,2),outline_index=v)

    def test_body_replaces_shared_base_and_spark_positions_survive(self):
        raw,comps,base=fixture();result=edit_hurt_stream(raw,12,comps,base)
        self.assertEqual(compose_indices(result,12,comps[135])[:2],base)
        for n in (136,137):
            overlay={'parts':comps[n]['parts'][10:]}
            before=compose_indices(raw,12,overlay)[0];after=compose_indices(result,12,overlay)[0]
            self.assertEqual(after,bytes(15 if v else 0 for v in before))
        referenced={s for c in comps.values() for v in frame_coverage(raw,12,c)[0] for s in v}
        for o in range(len(raw)):
            for shift in (0,4):
                if (o,shift) not in referenced:self.assertEqual((raw[o]>>shift)&15,(result[o]>>shift)&15)

    def test_aliasing_body_as_overlay_is_rejected(self):
        raw,c,b=fixture();c[136]['parts'][10]['tile']=0
        with self.assertRaisesRegex(ValueError,'aliases'):edit_hurt_stream(raw,12,c,b)

    def test_unknown_overlay_color_is_rejected(self):
        raw,c,b=fixture();raw=bytearray(raw);o,s=frame_coverage(raw,12,{'parts':c[136]['parts'][10:]})[0][5][0];raw[o]^=9<<s
        with self.assertRaisesRegex(ValueError,'indices'):edit_hurt_stream(bytes(raw),12,c,b)

    def test_changed_base_geometry_is_rejected(self):
        raw,c,b=fixture();c[137]['parts'][0]['x']+=1
        with self.assertRaisesRegex(ValueError,'verified base'):edit_hurt_stream(raw,12,c,b)

    def test_flash_follows_body_and_checks_native_bounds(self):
        base=(bytes([0,0,0,0,2,0,0,0,0]),(3,3))
        flash,size=flash_from_body(base,(0,0,3,3),(5,5),(-1,-1,4,4))
        self.assertEqual(size,(5,5));self.assertEqual(flash[12],12)
        self.assertEqual(sum(v==15 for v in flash),8)
        with self.assertRaisesRegex(ValueError,'escaped'):flash_from_body((bytes([2]),(1,1)),(0,0,1,1),(1,1),(0,0,1,1))

if __name__=='__main__':unittest.main()
