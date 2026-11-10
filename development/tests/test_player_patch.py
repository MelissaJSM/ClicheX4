"""가짜 ARC로 공동 편집의 공유 범위와 바이트 보존을 검사한다. 게임 파일 불필요."""
import struct
import unittest

from scripts.build_riko_idle import (patch_frames,validate_motion_scope,JUMP_FRAMES,RUN_FRAMES,DASH_FRAMES,WALL_FRAMES,
                                     GROUND_SLASH_BODY_FRAMES,GROUND_SLASH_EFFECT_FRAMES,GROUND_SLASH_SCOPE,
                                     AIR_SLASH_BODY_FRAMES,AIR_SLASH_EFFECT_FRAMES,AIR_SLASH_SCOPE,
                                     LADDER_SCOPE,LADDER_BODY_FRAMES,LADDER_EFFECT_FRAMES)
from scripts.discover_inputs import psx_arc
from src.psx_compress import encode_stream
from src.psx_player import graphics_bank, decode_stream
from scripts.build_riko_idle import LOW_HP_SCOPE,LOW_HP_FRAMES,HURT_SCOPE,HURT_FRAMES


def fixture():
    palette = struct.pack('<16H',0,*range(0x8001,0x8010))
    first = encode_stream(bytes(range(128)))
    second = encode_stream(bytes(reversed(range(128))))
    graphics = struct.pack('<4I',4,0x10000c,0x10000c,0x100000+12+len(first))+first+second
    parts = struct.pack('<4I',4,0x30001,0x40001,0x50001)+struct.pack('<BBbb',0,0,0,0)*3
    arc = bytearray(8192)
    struct.pack_into('<8I',arc,0,3,len(arc),9,64,2,len(graphics),3,len(parts))
    arc[2048:2112] = palette*2
    arc[4096:4096+len(graphics)] = graphics
    arc[6144:6144+len(parts)] = parts
    return bytes(arc),psx_arc(arc)[1],graphics,parts,palette


class PlayerPatchTests(unittest.TestCase):
    def test_dash_slash_requires_every_body_and_effect_reference(self):
        from scripts.build_riko_idle import SHIPPUUGA_SCOPE,LAUNCH_SCOPE,LAUNCH_FRAMES,SHIPPUUGA_NEW,SHIPPUUGA_EFFECTS
        base=JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|set(range(61,135))|set(range(174,247))|LOW_HP_FRAMES|HURT_FRAMES|LAUNCH_FRAMES
        full={str(n):{} for n in base|SHIPPUUGA_NEW|SHIPPUUGA_EFFECTS}
        validate_motion_scope({'scope':SHIPPUUGA_SCOPE,'frames':full})
        for n in SHIPPUUGA_NEW|SHIPPUUGA_EFFECTS:
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':SHIPPUUGA_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_motion_scope({'scope':LAUNCH_SCOPE,'frames':full})

    def test_hurt_scope_requires_body_sparks_and_flash(self):
        base=JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|set(range(61,135))|set(range(174,247))|LOW_HP_FRAMES
        full={str(n):{} for n in base|HURT_FRAMES}
        validate_motion_scope({'scope':HURT_SCOPE,'frames':full})
        for n in HURT_FRAMES:
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':HURT_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_motion_scope({'scope':LOW_HP_SCOPE,'frames':full})

    def test_low_hp_scope_requires_all_six_shared_idle_frames(self):
        base=JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|set(range(61,135))|set(range(174,247))
        full={str(n):{} for n in base|LOW_HP_FRAMES}
        validate_motion_scope({'scope':LOW_HP_SCOPE,'frames':full})
        for n in LOW_HP_FRAMES:
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':LOW_HP_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_motion_scope({'scope':LADDER_SCOPE,'frames':full})

    def test_ladder_scope_requires_climb_slash_recovery_and_original_effects(self):
        self.assertEqual(len(LADDER_BODY_FRAMES),32)
        self.assertEqual(len(LADDER_EFFECT_FRAMES),7)
        self.assertFalse(LADDER_BODY_FRAMES & LADDER_EFFECT_FRAMES)
        full={str(n):{} for n in JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|set(range(61,135))|set(range(174,247))}
        validate_motion_scope({'scope':LADDER_SCOPE,'frames':full})
        for n in range(174,213):
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':LADDER_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_motion_scope({'scope':AIR_SLASH_SCOPE,'frames':full})

    def test_air_slash_requires_air_and_landing_shared_body_and_effects(self):
        self.assertEqual(len(AIR_SLASH_BODY_FRAMES),18)
        self.assertEqual(len(AIR_SLASH_EFFECT_FRAMES),16)
        self.assertFalse(AIR_SLASH_BODY_FRAMES & AIR_SLASH_EFFECT_FRAMES)
        full={str(n):{} for n in JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|set(range(61,135))|set(range(213,247))}
        validate_motion_scope({'scope':AIR_SLASH_SCOPE,'frames':full})
        for n in range(213,247):
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':AIR_SLASH_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_motion_scope({'scope':GROUND_SLASH_SCOPE,'frames':full})

    def test_ground_slash_scope_includes_all_body_and_preserved_effect_aliases(self):
        self.assertEqual(len(GROUND_SLASH_BODY_FRAMES),40)
        self.assertEqual(len(GROUND_SLASH_EFFECT_FRAMES),34)
        self.assertFalse(GROUND_SLASH_BODY_FRAMES & GROUND_SLASH_EFFECT_FRAMES)
        full={str(n):{} for n in JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES|GROUND_SLASH_BODY_FRAMES|GROUND_SLASH_EFFECT_FRAMES}
        validate_motion_scope({'scope':GROUND_SLASH_SCOPE,'frames':full})
        for n in range(61,135):
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':GROUND_SLASH_SCOPE,'frames':{k:v for k,v in full.items() if k!=str(n)}})

    def test_wall_scope_requires_all_shared_and_transition_frames(self):
        full={str(n):{} for n in JUMP_FRAMES|RUN_FRAMES|DASH_FRAMES|WALL_FRAMES}
        validate_motion_scope({'scope':'jump_run_dash_wall_v1','frames':full})
        for n in WALL_FRAMES:
            with self.subTest(missing=n),self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope({'scope':'jump_run_dash_wall_v1','frames':{k:v for k,v in full.items() if k!=str(n)}})
        with self.assertRaisesRegex(ValueError,'scope'):
            validate_motion_scope({'scope':'jump_run_dash_wall_v1','frames':{**full,'53':{}}})

    def test_explicit_complete_motion_scopes_and_legacy_jump(self):
        jump = {str(n): {} for n in JUMP_FRAMES}
        combined = {str(n): {} for n in JUMP_FRAMES | RUN_FRAMES}
        validate_motion_scope({'frames': jump})
        validate_motion_scope({'scope': 'jump_v1', 'frames': jump})
        validate_motion_scope({'scope': 'jump_and_run_v1', 'frames': combined})
        validate_motion_scope({'scope': 'jump_run_dash_v1',
                               'frames': {str(n): {} for n in JUMP_FRAMES | RUN_FRAMES | DASH_FRAMES}})

    def test_dash_requires_complete_loop_and_end_without_extra_actions(self):
        complete = {str(n): {} for n in JUMP_FRAMES | RUN_FRAMES | DASH_FRAMES}
        for number in range(44, 53):
            with self.subTest(missing=number), self.assertRaisesRegex(ValueError, 'scope'):
                validate_motion_scope({'scope': 'jump_run_dash_v1',
                                       'frames': {k:v for k,v in complete.items() if k != str(number)}})
        for scope, frames in [('jump_and_run_v1', complete), ('jump_run_dash_v1', {**complete,'53':{}})]:
            with self.subTest(scope=scope), self.assertRaisesRegex(ValueError, 'scope'):
                validate_motion_scope({'scope': scope, 'frames': frames})

    def test_motion_scope_rejects_partial_extra_and_unannounced_run(self):
        jump = {str(n): {} for n in JUMP_FRAMES}
        combined = {str(n): {} for n in JUMP_FRAMES | RUN_FRAMES}
        cases = [{'frames': combined}, {'scope':'jump_and_run_v1','frames':jump},
                 {'scope':'future','frames':combined},
                 {'scope':'jump_and_run_v1','frames':{k:v for k,v in combined.items() if k!='3'}},
                 {'scope':'jump_and_run_v1','frames':{**combined,'44':{}}}]
        for motion in cases:
            with self.subTest(motion=motion), self.assertRaisesRegex(ValueError,'scope'):
                validate_motion_scope(motion)

    def test_unselected_shared_frame_is_rejected(self):
        arc,meta,gfx,parts,palette = fixture()
        with self.assertRaisesRegex(ValueError,'unselected'):
            patch_frames(arc,meta,gfx,parts,{0:(bytes([3])*256,(16,16))},palette)

    def test_complete_group_preserves_other_bitmap_parts_palette_and_padding(self):
        arc,meta,gfx,parts,palette = fixture()
        frame = (bytes([3])*256,(16,16))
        result,report = patch_frames(arc,meta,gfx,parts,{0:frame,1:frame},palette)
        self.assertEqual(report['decoded_changed_references'],[[0,0],[0,1]])
        self.assertEqual(result[:4096],arc[:4096])
        self.assertEqual(result[4096+len(gfx):],arc[4096+len(gfx):])
        changed_gfx = result[4096:4096+len(gfx)]
        descriptor = graphics_bank(gfx,0)['frames'][2]
        self.assertEqual(changed_gfx[descriptor['offset']:],gfx[descriptor['offset']:])
        first = graphics_bank(changed_gfx,0)['frames'][0]
        self.assertEqual(decode_stream(changed_gfx,first['offset'],first['limit'],128).data,bytes([0x33])*128)
        self.assertEqual(fixture()[0],arc)

    def test_conflicting_group_cannot_overwrite_prior_frame(self):
        arc,meta,gfx,parts,palette = fixture()
        with self.assertRaisesRegex(ValueError,'conflicting'):
            patch_frames(arc,meta,gfx,parts,{0:(bytes([3])*256,(16,16)),1:(bytes([4])*256,(16,16))},palette)

    def test_invalid_frame_and_palette_policy_rejected(self):
        arc,meta,gfx,parts,palette = fixture()
        for frames in ({}, {-1:(b'',(0,0))}, {3:(b'',(0,0))}, {True:(b'',(0,0))}):
            with self.subTest(frames=frames),self.assertRaises(ValueError):
                patch_frames(arc,meta,gfx,parts,frames,palette)
        for bad in (palette[:-1],bytes(32)):
            with self.assertRaises(ValueError):
                patch_frames(arc,meta,gfx,parts,{0:(bytes(256),(16,16))},bad)


if __name__ == '__main__': unittest.main()
