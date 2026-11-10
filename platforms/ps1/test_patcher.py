import hashlib,json,tempfile,unittest,zipfile
from pathlib import Path
from patcher import create,apply,digest

class PatcherTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        self.source=self.root/'source.bin';self.source.write_bytes(bytes(range(256))*147)
        self.target=self.root/'target.bin';b=bytearray(self.source.read_bytes());b[15:21]=b'Cliche';self.target.write_bytes(b)
        self.patch=self.root/'mod.cxp';create(self.source,self.target,self.patch,'ver_buki_riko',digest(self.source),digest(self.target))
    def tearDown(self):self.temp.cleanup()
    def test_roundtrip_new_output_and_original_unchanged(self):
        before=digest(self.source);out=self.root/'new';r=apply(self.source,self.patch,out)
        self.assertTrue(r['verified']);self.assertEqual((out/'shibuki_riko.bin').read_bytes(),self.target.read_bytes());self.assertEqual(digest(self.source),before)
        self.assertIn('TRACK 01 MODE2/2352',(out/'shibuki_riko.cue').read_text())
    def test_verify_does_not_write(self):
        before=set(self.root.iterdir());self.assertTrue(apply(self.source,self.patch)['verified']);self.assertEqual(set(self.root.iterdir()),before)
    def test_wrong_source_rejected(self):
        self.source.write_bytes(bytes(self.source.stat().st_size));out=self.root/'bad'
        with self.assertRaises(ValueError):apply(self.source,self.patch,out)
        self.assertFalse(out.exists())
    def test_existing_output_rejected(self):
        out=self.root/'existing';out.mkdir();(out/'keep').write_text('keep')
        with self.assertRaises(FileExistsError):apply(self.source,self.patch,out)
        self.assertEqual((out/'keep').read_text(),'keep')
    def test_source_as_output_rejected(self):
        before=digest(self.source)
        with self.assertRaises(FileExistsError):apply(self.source,self.patch,self.source)
        self.assertEqual(digest(self.source),before)
    def test_corrupt_delta_no_final_output(self):
        with zipfile.ZipFile(self.patch) as z:m=z.read('manifest.json');d=bytearray(z.read('delta.xor'))
        d[10]^=3;p=self.root/'bad.cxp'
        with zipfile.ZipFile(p,'w') as z:z.writestr('manifest.json',m);z.writestr('delta.xor',d)
        with self.assertRaises(ValueError):apply(self.source,p,self.root/'failed')
        self.assertFalse((self.root/'failed').exists());self.assertFalse(list(self.root.glob('.clichex4-*')))
    def test_unsafe_manifest_rejected(self):
        with zipfile.ZipFile(self.patch) as z:m=json.loads(z.read('manifest.json'));d=z.read('delta.xor')
        m['output_stem']='../escape';p=self.root/'bad.cxp'
        with zipfile.ZipFile(p,'w') as z:z.writestr('manifest.json',json.dumps(m));z.writestr('delta.xor',d)
        with self.assertRaises(ValueError):apply(self.source,p)
    def test_duplicate_entry_rejected(self):
        with zipfile.ZipFile(self.patch,'a') as z:z.writestr('extra','x')
        with self.assertRaises(ValueError):apply(self.source,self.patch)
if __name__=='__main__':unittest.main()
