"""프로젝트 혼합, 변경된 입력, CUE 추측을 거부하는 검사."""
import json
from pathlib import Path
import tempfile
import unittest

from scripts.project import checked_path, inspect_references, load_project, validate_bin, working_cue


class ProjectTests(unittest.TestCase):
    def test_both_projects_have_four_verified_references(self):
        root = Path(__file__).resolve().parents[1]
        # 실제 사용자 그림 유무에 의존하지 않도록 구성과 경로만 검사한다.
        for name in ('ver_buki_riko','ver_rin_nana'):
            project = load_project(root, name)
            self.assertEqual(len(project['references']), 4)
            self.assertEqual(next(r['character'] for r in project['references'] if r['slot']=='zero'),
                             'riko' if name == 'ver_buki_riko' else 'rin')

    def test_cross_project_reference_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                checked_path(root, 'character/ver_rin_nana/rin.webp', root/'character/ver_buki_riko')

    def test_parent_traversal_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            with self.assertRaises(ValueError):
                checked_path(root, '../source.bin', root)

    def test_wrong_bin_hash_rejected_without_modifying_input(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'source.bin'
            path.write_bytes(b'original test input')
            with self.assertRaises(ValueError):
                validate_bin(path, '0'*64)
            self.assertEqual(path.read_bytes(), b'original test input')

    def test_reference_hash_mismatch_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root/'character/ver_buki_riko/riko.webp'
            path.parent.mkdir(parents=True)
            path.write_bytes(b'changed input')
            project = {'project_id':'ver_buki_riko','references':[{'path':'character/ver_buki_riko/riko.webp','sha256':'0'*64}]}
            with self.assertRaises(ValueError):
                inspect_references(root, project)

    def test_cue_changes_only_filename(self):
        text = 'FILE "Mega Man X4.bin" BINARY\r\n  TRACK 01 MODE2/2352\r\n    INDEX 01 00:00:00\r\n'
        self.assertEqual(working_cue(text,'baseline.bin'),text.replace('Mega Man X4.bin','baseline.bin'))
        with self.assertRaises(ValueError):
            working_cue(text+'  TRACK 02 AUDIO\r\n','baseline.bin')


if __name__ == '__main__':
    unittest.main()
