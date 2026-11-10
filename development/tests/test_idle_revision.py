import json
from pathlib import Path
import struct
import tempfile
import unittest
from unittest.mock import patch

from scripts.build_riko_idle import read_idle_revision
from scripts.discover_inputs import sha256
from scripts.extract_zero import save_image


class IdleRevisionTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name);self.folder=self.root/'work/ver_buki_riko/revision';self.folder.mkdir(parents=True)
        (self.root/'config').mkdir();(self.root/'config/riko_body_standard.json').write_text(json.dumps({'reference_roi':[12,0,35,19]}))
        self.words=[0]+[0x8000+i for i in range(1,16)];self.palette=struct.pack('<16H',*self.words)
        self.reference=bytearray(56*48)
        for y in range(19):self.reference[y*56+12:y*56+35]=bytes([1])*23
        self.base=self.root/'base.png';save_image(bytes(self.reference),(56,48),self.words,self.base)
        self.candidate=self.reference.copy();self.candidate[25*56+20]=3
        self.png=self.folder/'idle.png';self.manifest=self.folder/'revision.json';self.write_candidate()
        self.override=patch('scripts.build_riko_idle.ROOT',self.root);self.override.start();self.addCleanup(self.override.stop)

    def write_candidate(self):
        save_image(bytes(self.candidate),(56,48),self.words,self.png)
        self.record={'base_reference_sha256':sha256(self.base.read_bytes()),'palette_sha256':sha256(self.palette),
            'file':self.png.name,'sha256':sha256(self.png.read_bytes()),'head_native_position':[12,0]}
        self.manifest.write_text(json.dumps(self.record))

    def read(self):
        return read_idle_revision(self.manifest,self.base,self.palette,(bytes(self.reference),(56,48)))

    def test_body_revision_preserves_reference_and_is_review_pending(self):
        before=self.base.read_bytes();_,candidate,record=self.read()
        self.assertEqual(candidate[0],bytes(self.candidate));self.assertEqual(self.base.read_bytes(),before)
        self.assertFalse(record['final_style_user_approved'])

    def test_head_change_rejected_even_with_updated_png_hash(self):
        self.candidate[12]=2;self.write_candidate()
        with self.assertRaisesRegex(ValueError,'head/neck'):self.read()

    def test_stale_base_or_palette_rejected(self):
        for key in ['base_reference_sha256','palette_sha256']:
            with self.subTest(key=key):
                self.write_candidate();self.record[key]='0'*64;self.manifest.write_text(json.dumps(self.record))
                with self.assertRaisesRegex(ValueError,'base or palette'):self.read()

    def test_escaped_or_changed_png_rejected(self):
        self.record['file']='../../../base.png';self.manifest.write_text(json.dumps(self.record))
        with self.assertRaisesRegex(ValueError,'escaped'):self.read()
        self.write_candidate();self.png.write_bytes(self.png.read_bytes()+b'changed')
        with self.assertRaisesRegex(ValueError,'hash mismatch'):self.read()
