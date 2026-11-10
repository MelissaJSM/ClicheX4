import json
from pathlib import Path
import tempfile
import unittest
import zipfile

from src.steam_distribution import Package, SCHEMA, decode_delta, digest, encode_delta, json_bytes, safe_path


class DistributionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)/'게임 복제'
        self.root.mkdir()
        (self.root/'RXC1.exe').write_bytes(b'owned executable')
        self.original = b'original resource data' * 40
        self.target = 'nativeDX10/X4/romPC/load.arc'
        p = self.root/self.target;p.parent.mkdir(parents=True);p.write_bytes(self.original)
        self.private = 'nativeDX10/X4/romPC/cliche_test.arc'
        self.rows = []
        self.deltas = []
        for target, after, original in [(self.target,b'changed display'*95,digest(self.original)),
                                        (self.private,b'new private resource'*23,None)]:
            delta=encode_delta(self.original,after)
            self.rows.append({'target':target,'source':self.target,'source_sha256':digest(self.original),
                              'source_size':len(self.original),'original_sha256':original,'size':len(after),
                              'sha256':digest(after),'patch':f'delta/{len(self.rows)}.xor.z','patch_sha256':digest(delta)})
            self.deltas.append(delta)
        self.manifest={'schema':SCHEMA,'appid':743890,'release':'test',
                       'exe_sha256':digest(b'owned executable'),'files':self.rows}
        self.archive=Path(self.temp.name)/'patches.zip'
        self.write_package()
        (self.root/'savedata.dat').write_bytes(b'keep saved progress')
        (self.root/'config.ini').write_bytes(b'keep settings')

    def tearDown(self):self.temp.cleanup()

    def write_package(self):
        with zipfile.ZipFile(self.archive,'w') as z:
            z.writestr('manifest.json',json_bytes(self.manifest))
            for r,d in zip(self.rows,self.deltas):z.writestr(r['patch'],d)

    def preserved(self):
        self.assertEqual((self.root/'RXC1.exe').read_bytes(),b'owned executable')
        self.assertEqual((self.root/'savedata.dat').read_bytes(),b'keep saved progress')
        self.assertEqual((self.root/'config.ini').read_bytes(),b'keep settings')

    def test_install_repeat_restore_and_backup(self):
        p=Package(self.archive)
        self.assertEqual(p.apply(self.root)['verified'],2)
        self.assertEqual(p.apply(self.root)['changed'],0)
        self.assertEqual((self.root/'.clichex4/original'/self.target).read_bytes(),self.original)
        self.assertEqual(p.apply(self.root,restore=True)['verified'],2)
        self.assertFalse((self.root/self.private).exists())
        self.assertEqual((self.root/self.target).read_bytes(),self.original)
        self.assertEqual(p.apply(self.root,restore=True)['changed'],0)
        self.preserved()

    def prepare_upgrade(self):
        Package(self.archive).apply(self.root)
        self.manifest['release']='test-next'
        self.manifest['upgrade_from']=['test']
        for i,row in enumerate(self.rows):
            row['previous_sha256']={'test':row['sha256']}
            new=b'new iris colors and preserved art'+bytes([i])*100
            delta=encode_delta(self.original,new)
            row.update(sha256=digest(new),size=len(new),patch_sha256=digest(delta))
            self.deltas[i]=delta
        self.write_package()
        return Package(self.archive)

    def test_known_previous_upgrade_and_original_restore(self):
        p=self.prepare_upgrade()
        self.assertEqual(p.inspect(self.root)['upgradable'],2)
        self.assertEqual(p.apply(self.root)['verified'],2)
        self.assertEqual((self.root/'.clichex4/original'/self.target).read_bytes(),self.original)
        self.assertEqual(p.apply(self.root,restore=True)['verified'],2)
        self.preserved()

    def test_upgrade_failure_rolls_back_old_release_then_retries(self):
        p=self.prepare_upgrade();before=(self.root/self.target).read_bytes()
        def fail(i,path):
            if i==1:raise RuntimeError('simulated upgrade failure')
        with self.assertRaises(RuntimeError):p.apply(self.root,before_commit=fail)
        self.assertEqual((self.root/self.target).read_bytes(),before)
        self.assertEqual(json.loads((self.root/'.clichex4/state.json').read_text())['release'],'test')
        self.assertEqual(p.apply(self.root)['verified'],2)
        self.preserved()

    def test_upgrade_refuses_modified_previous_resource(self):
        p=self.prepare_upgrade();(self.root/self.target).write_bytes(b'unknown third party changes')
        with self.assertRaises(ValueError):p.apply(self.root)
        self.assertEqual((self.root/self.target).read_bytes(),b'unknown third party changes')
        self.preserved()

    def test_interrupted_upgrade_accepts_only_known_old_and_new_hashes(self):
        p=self.prepare_upgrade()
        row=self.rows[0]
        (self.root/self.target).write_bytes(decode_delta(self.original,self.deltas[0],row))
        (self.root/'.clichex4/state.json').write_bytes(json_bytes({'schema':SCHEMA,'release':'test-next','phase':'installing','upgrade_source_release':'test'}))
        self.assertEqual(p.inspect(self.root)['upgradable'],1)
        self.assertEqual(p.apply(self.root)['verified'],2)
        self.preserved()

    def test_failure_rolls_back_then_can_retry(self):
        def fail(i,path):
            if i==1:raise RuntimeError('injected write failure')
        p=Package(self.archive)
        with self.assertRaises(RuntimeError):p.apply(self.root,before_commit=fail)
        self.assertEqual((self.root/self.target).read_bytes(),self.original)
        self.assertFalse((self.root/self.private).exists())
        self.assertEqual(p.apply(self.root)['verified'],2)
        self.preserved()

    def test_interrupted_mixed_install_resumes(self):
        p=Package(self.archive);p.apply(self.root)
        (self.root/self.private).unlink()
        state=self.root/'.clichex4/state.json';data=json.loads(state.read_text('utf8'));data['phase']='installing';state.write_bytes(json_bytes(data))
        self.assertEqual(p.apply(self.root)['changed'],1)
        self.assertEqual(p.apply(self.root,restore=True)['verified'],2)
        self.preserved()

    def test_unknown_resource_and_existing_private_refused(self):
        (self.root/self.private).write_bytes(b'someone elses file')
        with self.assertRaises(ValueError):Package(self.archive).apply(self.root)
        self.assertEqual((self.root/self.private).read_bytes(),b'someone elses file')
        self.assertEqual((self.root/self.target).read_bytes(),self.original)
        self.preserved()

    def test_modified_exe_refused(self):
        (self.root/'RXC1.exe').write_bytes(b'unsupported version')
        with self.assertRaises(ValueError):Package(self.archive).apply(self.root)
        self.assertFalse((self.root/'.clichex4').exists())

    def test_running_game_and_game_start_during_preparation(self):
        p=Package(self.archive)
        with self.assertRaises(ValueError):p.apply(self.root,running=lambda:True)
        states=iter([False,True])
        with self.assertRaises(ValueError):p.apply(self.root,running=lambda:next(states))
        self.assertEqual((self.root/self.target).read_bytes(),self.original)
        self.preserved()

    def test_corrupted_delta_and_result_are_refused(self):
        d=self.deltas[0]
        with self.assertRaises(ValueError):decode_delta(self.original,d+b'bad',self.rows[0])
        row={**self.rows[0],'sha256':'0'*64}
        with self.assertRaises(ValueError):decode_delta(self.original,d,row)
        with self.assertRaises(ValueError):Package(self.archive,'0'*64)
        self.deltas[1]=b'broken patch';self.write_package()
        with self.assertRaises(ValueError):Package(self.archive).apply(self.root)
        self.assertEqual((self.root/self.target).read_bytes(),self.original)
        self.preserved()

    def test_missing_or_corrupt_backup_refused_on_restore(self):
        p=Package(self.archive);p.apply(self.root)
        (self.root/'.clichex4/original'/self.target).write_bytes(b'corrupt backup')
        before=(self.root/self.target).read_bytes()
        with self.assertRaises(ValueError):p.apply(self.root,restore=True)
        self.assertEqual((self.root/self.target).read_bytes(),before)
        self.preserved()

    def test_path_escape_and_target_allowlist(self):
        for rel in ('../outside','/absolute','C:/outside','safe/../../bad','safe\\bad','safe//bad'):
            with self.subTest(rel=rel),self.assertRaises(ValueError):safe_path(self.root,rel)
        self.rows[0]['target']='nativeDX10/X4/romPC/../../../../savedata.dat';self.write_package()
        with self.assertRaises(ValueError):Package(self.archive)

    def test_duplicate_and_extra_members_refused(self):
        with zipfile.ZipFile(self.archive,'a') as z:z.writestr('unexpected.bin',b'no')
        with self.assertRaises(ValueError):Package(self.archive)

    def test_shorter_and_longer_deltas(self):
        for a,b in ((b'abc',b'abcdef'),(b'abcdef',b'x'),(bytes(range(256)),bytes(reversed(range(256))))):
            delta=encode_delta(a,b)
            row={**self.rows[0],'source_size':len(a),'source_sha256':digest(a),'size':len(b),'sha256':digest(b),'patch_sha256':digest(delta)}
            self.assertEqual(decode_delta(a,delta,row),b)

    def test_unchanged_required_resource_counts_as_valid_both_ways(self):
        self.deltas[0]=encode_delta(self.original,self.original)
        self.rows[0].update(sha256=digest(self.original),size=len(self.original),patch_sha256=digest(self.deltas[0]))
        self.write_package();p=Package(self.archive)
        self.assertEqual(p.inspect(self.root)['unchanged'],1)
        self.assertEqual(p.apply(self.root)['verified'],2)
        self.assertEqual(p.apply(self.root,restore=True)['verified'],2)


if __name__=='__main__':unittest.main()
