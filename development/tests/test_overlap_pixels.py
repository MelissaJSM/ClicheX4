import unittest
import numpy as np
from src.psx_tile_layout import fill_redundant_pixels
from src.psx_player import indexed_atlas
from scripts.prepare_shibuki_run import world_canvas

class OverlapPixelsTests(unittest.TestCase):
    def setUp(self):
        self.raw=bytes(256);self.targets={1:np.zeros((80,96),np.uint8),2:np.zeros((80,96),np.uint8)}
        for a in self.targets.values():a[13,12]=5
        self.parts={1:[(1,10,10,0)],2:[(1,10,10,0)]}

    def test_duplicate_color_preserves_other_nibbles(self):
        out=fill_redundant_pixels(self.raw,2,self.parts,self.targets,[[1,2,3,5]],{1})
        atlas,_,_=indexed_atlas(out,2)
        self.assertEqual(atlas[3*256+18],5)
        self.assertEqual(sum(atlas),5)
        self.assertEqual(self.raw,bytes(256))

    def test_conflicting_shooting_pose_rejected(self):
        self.targets[2][13,12]=6
        with self.assertRaisesRegex(ValueError,'visible variant'):
            fill_redundant_pixels(self.raw,2,self.parts,self.targets,[[1,2,3,5]],{1})

    def test_armor_and_duplicate_write_rejected(self):
        with self.assertRaisesRegex(ValueError,'Invalid overlap'):
            fill_redundant_pixels(self.raw,2,self.parts,self.targets,[[1,2,3,5]],{0})
        with self.assertRaisesRegex(ValueError,'Duplicate overlap'):
            fill_redundant_pixels(self.raw,2,self.parts,self.targets,[[1,2,3,5],[1,2,3,5]],{1})

    def test_gpu_edge_rejected(self):
        parts={1:[(0,12,10,0)],2:[(0,12,10,0)]}
        with self.assertRaisesRegex(ValueError,'GPU U boundary'):
            fill_redundant_pixels(self.raw,2,parts,self.targets,[[0,0,3,5]],{0})

    def test_erasing_only_owner_rejected(self):
        out=fill_redundant_pixels(self.raw,2,self.parts,self.targets,[[1,2,3,5]],{1})
        with self.assertRaisesRegex(ValueError,'visible variant'):
            fill_redundant_pixels(out,2,self.parts,self.targets,[[1,2,3,0]],{1})

    def test_empty_part_can_extend_past_proof_border(self):
        part={'index':0,'tile':0,'x':0,'y':31,'page':0,'clut':0,'unknown_flags':0,'flip_x':False,'flip_y':False}
        self.assertFalse(world_canvas(self.raw,2,{'parts':[part]}).any())

    def test_visible_part_past_proof_border_rejected(self):
        raw=bytearray(self.raw);_,positions,_=indexed_atlas(raw,2);off,shift=positions[15*256+1];raw[off]=5<<shift
        part={'index':0,'tile':0,'x':0,'y':31,'page':0,'clut':0,'unknown_flags':0,'flip_x':False,'flip_y':False}
        with self.assertRaisesRegex(ValueError,'Visible composition'):
            world_canvas(raw,2,{'parts':[part]})
