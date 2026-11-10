import unittest
from scripts.overhaul_integrate import merge_bytes


class OverhaulMergeTests(unittest.TestCase):
    def test_independent_and_identical_edits_merge(self):
        baseline=b'abcdef';merged=bytearray(baseline);owners={}
        self.assertEqual(merge_bytes(baseline,merged,b'aBcdef','PL01',owners,'dialogue'),[1])
        self.assertEqual(merge_bytes(baseline,merged,b'aBcdeF','PL01',owners,'graphics'),[1,5])
        self.assertEqual(merged,b'aBcdeF')
        self.assertEqual(baseline,b'abcdef')

    def test_conflicting_shared_resource_is_rejected(self):
        baseline=b'abcdef';merged=bytearray(baseline);owners={}
        merge_bytes(baseline,merged,b'aBcdef','PL01',owners,'first')
        with self.assertRaisesRegex(ValueError,'Conflicting patches'):
            merge_bytes(baseline,merged,b'aZcdef','PL01',owners,'second')
        self.assertEqual(merged,b'aBcdef')

    def test_relocation_or_length_change_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'length changed'):
            merge_bytes(b'abc',bytearray(b'abc'),b'abcd','PL01',{},'growth')


if __name__=='__main__':unittest.main()
