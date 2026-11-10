import unittest
from src.psx_beam_in import materialize, BEAM_BODY_FRAMES, BEAM_DERIVED_FRAMES, validate_contacts
from scripts.build_riko_idle import validate_motion_scope,BEAM_IN_SCOPE,SHIPPUUGA_SCOPE,SHIPPUUGA_NEW,SHIPPUUGA_EFFECTS,LAUNCH_FRAMES,HURT_FRAMES,LOW_HP_FRAMES,JUMP_FRAMES,RUN_FRAMES,DASH_FRAMES,WALL_FRAMES

class BeamInTests(unittest.TestCase):
    def test_sideways_body_shift_and_changed_floor_are_rejected(self):
        image=bytearray(20*8)
        for y in range(5,8):
            for x in [2,3,4,13,14,15]:image[y*20+x]=15
        frame=(bytes(image),(20,8));b=(-10,-8,10,0)
        validate_contacts({251:frame},{251:b},frame,b)
        with self.assertRaisesRegex(ValueError,'slides'):
            validate_contacts({251:frame},{251:(-7,-8,13,0)},frame,b)
        with self.assertRaisesRegex(ValueError,'baseline'):
            validate_contacts({251:frame},{251:(-10,-7,10,1)},frame,b)

    def test_glow_is_derived_from_replacement_and_contains_no_old_silhouette(self):
        body=(bytes([0,0,0,0,4,0,0,0,0]),(3,3))
        data,size=materialize(body,(-1,-1,2,2),(7,7),(-3,-3,4,4),247)
        nonzero={(i%7-3,i//7-3) for i,v in enumerate(data) if v}
        self.assertEqual(nonzero,{(x,y) for x in range(-2,3) for y in range(-2,3) if abs(x)+abs(y)<=2})
        self.assertEqual(data[3*7+3],15)
        self.assertEqual(materialize(body,(-1,-1,2,2),(3,3),(-1,-1,2,2),248)[0],bytes([0,0,0,0,15,0,0,0,0]))

    def test_glow_rejects_crop_instead_of_silently_cutting_cape(self):
        with self.assertRaisesRegex(ValueError,'escaped'):
            materialize((bytes([4]),(1,1)),(0,0,1,1),(1,1),(0,0,1,1),247)
        with self.assertRaisesRegex(ValueError,'Unsupported'):
            materialize((bytes([4]),(1,1)),(0,0,1,1),(1,1),(0,0,1,1),251)

    def test_arrival_scope_requires_flash_and_shared_recovery_but_excludes_pure_beam(self):
        old=JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|set(range(61,135))|set(range(174,247))|LOW_HP_FRAMES|HURT_FRAMES|LAUNCH_FRAMES|SHIPPUUGA_NEW|SHIPPUUGA_EFFECTS
        full={str(n):{} for n in old|BEAM_BODY_FRAMES}
        validate_motion_scope({'scope':BEAM_IN_SCOPE,'frames':full})
        from scripts.build_riko_idle import BEAM_IN_V2_SCOPE
        validate_motion_scope({'scope':BEAM_IN_V2_SCOPE,'frames':full})
        for n in BEAM_BODY_FRAMES:
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':BEAM_IN_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})
        for scope,frames in [(SHIPPUUGA_SCOPE,full),(BEAM_IN_SCOPE,{**full,'53':{}})]:
            with self.assertRaisesRegex(ValueError,'scope'):validate_motion_scope({'scope':scope,'frames':frames})

if __name__=='__main__':unittest.main()
