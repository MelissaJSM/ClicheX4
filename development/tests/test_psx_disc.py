import hashlib
from pathlib import Path
import tempfile
import unittest

from src.psx_disc import write_archive_copy
from src.psx_sector import rebuild_checks


class DiscWriteTests(unittest.TestCase):
    def fixtures(self,root):
        raw=b'\0'+b'\xff'*10+b'\0'+bytes([0,2,0,2])+bytes([0,0,8,0])*2+bytes(2328)
        raw=rebuild_checks(raw)
        path=root/'source.bin';path.write_bytes(raw)
        record={'lba':0,'size':2048,'sha256':hashlib.sha256(bytes(2048)).hexdigest()}
        return path,record,hashlib.sha256(raw).hexdigest(),raw

    def test_roundtrip_and_single_sector_edit_preserve_source(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source,record,digest,raw=self.fixtures(root)
            result=write_archive_copy(source,root/'same.bin',record,bytes(2048),digest)
            self.assertEqual(result['sha256'],digest)
            result=write_archive_copy(source,root/'edit.bin',record,b'X'+bytes(2047),digest)
            self.assertEqual(result['changed_sectors'][0]['data_offsets'],[0])
            self.assertEqual(source.read_bytes(),raw)
            self.assertEqual((root/'edit.bin').read_bytes()[:24],raw[:24])

    def test_invalid_inputs_rejected_before_output(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);source,record,digest,raw=self.fixtures(root)
            cases=[(source,record,bytes(2048),digest),
                   (root/'bad.bin',record,bytes(2048),'0'*64),
                   (root/'bad.bin',record,bytes(2047),digest),
                   (root/'bad.bin',{**record,'lba':1},bytes(2048),digest),
                   (root/'bad.bin',{**record,'sha256':'0'*64},bytes(2048),digest)]
            for target,r,data,h in cases:
                with self.subTest(target=target,r=r),self.assertRaises(ValueError):
                    write_archive_copy(source,target,r,data,h)
            self.assertFalse((root/'bad.bin').exists());self.assertEqual(source.read_bytes(),raw)


if __name__=='__main__':unittest.main()
