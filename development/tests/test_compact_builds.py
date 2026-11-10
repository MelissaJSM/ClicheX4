import hashlib
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from scripts.compact_builds import SOURCE, SECTOR, compact, reconstruct, restore, safe_path, protected_directories


class CompactTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = bytes(range(256)) * (SECTOR * 2048 // 256)
        (self.root / SOURCE).write_bytes(self.source)
        self.sh = hashlib.sha256(self.source).hexdigest()
        data = bytearray(self.source)
        for sector in (0, 1023, 1024, 2047):
            data[sector * SECTOR + 12] ^= 0xff
        self.data = bytes(data)
        self.rel = 'out/ver_buki_riko/old/game.bin'
        self.target = self.root / self.rel
        self.target.parent.mkdir(parents=True)
        self.target.write_bytes(self.data)
        self.th = hashlib.sha256(self.data).hexdigest()

    def archive(self):
        info = compact(self.root, self.rel, self.th, self.sh)
        return self.root / info['archive']

    def rewrite(self, archive, change):
        with zipfile.ZipFile(archive) as z:
            meta = json.loads(z.read('metadata.json'))
            payload = z.read('sectors.bin')
        meta, payload = change(meta, payload)
        with zipfile.ZipFile(archive, 'w') as z:
            z.writestr('metadata.json', json.dumps(meta))
            z.writestr('sectors.bin', payload)

    def test_roundtrip_boundaries_and_source_preservation(self):
        archive = self.archive()
        self.assertFalse(self.target.exists())
        m = reconstruct(self.root, archive, required_source_hash=self.sh)
        self.assertEqual(m['lbas'], [0, 1023, 1024, 2047])
        self.assertEqual(restore(self.root, archive, self.sh).read_bytes(), self.data)
        self.assertEqual((self.root / SOURCE).read_bytes(), self.source)

    def test_wrong_expected_target_preserves_bin(self):
        with self.assertRaises(ValueError):
            compact(self.root, self.rel, '0' * 64, self.sh)
        self.assertEqual(self.target.read_bytes(), self.data)

    def test_second_variant_roundtrip(self):
        relative = 'out/ver_rin_nana/old/rin_nana.bin'
        target = self.root / relative
        target.parent.mkdir(parents=True)
        target.write_bytes(self.data)
        info = compact(self.root, relative, self.th, self.sh)
        archive = self.root / info['archive']
        self.assertFalse(target.exists())
        self.assertEqual(restore(self.root, archive, self.sh).read_bytes(), self.data)
        self.assertEqual(self.target.read_bytes(), self.data)
        self.assertEqual((self.root / SOURCE).read_bytes(), self.source)

    def test_unrelated_output_roots_rejected(self):
        for relative in ('out/other/game.bin', 'character/ver_rin_nana/game.bin',
                         'completed/ver_buki_riko/game.bin', 'out/ver_rin_nana/../game.bin'):
            with self.assertRaises(ValueError):
                safe_path(self.root, relative, output=True)

    def test_keep_full_release_copy(self):
        info = compact(self.root, self.rel, self.th, self.sh, remove_full=False)
        self.assertFalse(info['full_bin_removed'])
        self.assertEqual(self.target.read_bytes(), self.data)
        m = reconstruct(self.root, self.root / info['archive'], required_source_hash=self.sh)
        self.assertEqual(m['target_sha256'], self.th)

    def test_final_and_latest_protected_despite_stale_feature_pointer(self):
        d = self.root / 'projects/ver_buki_riko'
        d.mkdir(parents=True)
        (d / 'current_build.json').write_text(json.dumps({'build':'out/ver_buki_riko/stale'}))
        (d / 'project.json').write_text(json.dumps({'latest_integrated_build':'out\\ver_buki_riko\\latest'}))
        (d / 'final_release.json').write_text(json.dumps({'protected_build_directories':['out/ver_buki_riko/final/game','out/ver_buki_riko/rollback']}))
        self.assertEqual(protected_directories(self.root), {'out/ver_buki_riko/stale','out/ver_buki_riko/latest','out/ver_buki_riko/final/game','out/ver_buki_riko/rollback'})

    def test_wrong_source_preserves_bin(self):
        with self.assertRaises(ValueError):
            compact(self.root, self.rel, self.th, '0' * 64)
        self.assertTrue(self.target.exists())

    def test_restore_wrong_source_does_not_publish(self):
        archive = self.archive()
        (self.root / SOURCE).write_bytes(b'X' * len(self.source))
        with self.assertRaises(ValueError):
            restore(self.root, archive, self.sh)
        self.assertFalse(self.target.exists())

    def test_corrupt_payload_does_not_publish(self):
        archive = self.archive()
        self.rewrite(archive, lambda m, p: (m, bytes([p[0] ^ 1]) + p[1:]))
        with self.assertRaises(ValueError):
            restore(self.root, archive, self.sh)
        self.assertFalse(self.target.exists())

    def test_invalid_sector_lists(self):
        archive = self.archive()
        for values in ([0, 0, 1024, 2047], [-1, 1023, 1024, 2047], [0, 1023, 1024, 2048], [1024, 1023, 0, 2047]):
            self.rewrite(archive, lambda m, p: (dict(m, lbas=values), p))
            with self.assertRaises(ValueError):
                reconstruct(self.root, archive, required_source_hash=self.sh)

    def test_path_escape_rejected(self):
        for p in ('../original.bin', 'out/ver_buki_riko/../../original.bin', 'C:/x', 'out\\ver_buki_riko\\x'):
            with self.assertRaises(ValueError):
                safe_path(self.root, p, output=True)

    def test_existing_output_and_archive_preserved(self):
        archive = self.archive()
        self.target.write_bytes(b'user data')
        with self.assertRaises(FileExistsError):
            restore(self.root, archive, self.sh)
        self.assertEqual(self.target.read_bytes(), b'user data')
        self.target.write_bytes(self.data)
        with self.assertRaises(FileExistsError):
            compact(self.root, self.rel, self.th, self.sh)
        self.assertTrue(self.target.exists())

    def test_hardlink_rejected(self):
        link = self.target.parent / 'link.bin'
        link.hardlink_to(self.target)
        with self.assertRaises(ValueError):
            compact(self.root, self.rel, self.th, self.sh)

    def test_unchanged_image_archive(self):
        self.target.write_bytes(self.source)
        info = compact(self.root, self.rel, self.sh, self.sh)
        self.assertEqual(info['changed_sectors'], 0)
        restore(self.root, self.root / info['archive'], self.sh)
        self.assertEqual(self.target.read_bytes(), self.source)


if __name__ == '__main__':
    unittest.main()
