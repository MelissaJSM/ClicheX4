import unittest
from scripts.build_riko_idle import validate_sword_effect
from scripts.discover_inputs import sha256

class SwordEffectTests(unittest.TestCase):
    def record(self,old,new):
        return {'original_indices_sha256':sha256(old),'replacement_indices_sha256':sha256(new),
                'added_pixels':sum(a!=b for a,b in zip(old,new))}
    def test_default_remains_immutable(self):
        validate_sword_effect(b'\x00\x02',b'\x00\x02')
        with self.assertRaises(ValueError):validate_sword_effect(b'\x00\x02',b'\x01\x02')
    def test_hash_bound_addition(self):
        old=b'\x00\x02\x00';new=b'\x03\x02\x0f'
        validate_sword_effect(old,new,self.record(old,new))
        with self.assertRaises(ValueError):validate_sword_effect(old,b'\x04\x02\x0f',self.record(old,new))
    def test_cannot_change_original_trail_even_with_new_hash(self):
        old=b'\x00\x02';new=b'\x03\x01'
        with self.assertRaises(ValueError):validate_sword_effect(old,new,self.record(old,new))
    def test_wrong_count_and_index_rejected(self):
        old=b'\x00\x02';new=b'\x03\x02';r=self.record(old,new);r['added_pixels']=2
        with self.assertRaises(ValueError):validate_sword_effect(old,new,r)
        new=b'\x10\x02'
        with self.assertRaises(ValueError):validate_sword_effect(old,new,self.record(old,new))
