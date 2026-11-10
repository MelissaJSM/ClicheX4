"""로컬 Rin 체크포인트가 있을 때만 수행하는 자산 갱신 보존/거부 검사."""
import gzip,json,unittest
from pathlib import Path
from scripts.prepare_rin_checkpoint import refresh
from scripts.build_rin_idle import entry

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'work/ver_rin_nana/checkpoints/dash_fresh_boot/SLUS_005.61.000'

@unittest.skipUnless(FIXTURE.exists(),'Local game checkpoint is not distributed')
class RinCheckpointTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.state=gzip.decompress(FIXTURE.read_bytes())
        cls.old=(ROOT/'out/ver_rin_nana/rin_dash_20261028T102644640190Z/modified.arc').read_bytes()
        cls.new=(ROOT/'out/ver_rin_nana/rin_wall_20261028T104140560792Z/modified.arc').read_bytes()
        cls.ram=442

    def test_only_identified_assets_change(self):
        result,report=refresh(self.state,self.old,self.new,self.ram)
        allowed=set()
        for r in report['asset_ranges']:allowed.update(range(r['offset'],r['offset']+r['size']))
        changed={i for i,(a,b) in enumerate(zip(self.state,result)) if a!=b}
        self.assertTrue(changed);self.assertLessEqual(changed,allowed)
        self.assertEqual(len(result),len(self.state))
        self.assertEqual(result,gzip.decompress((ROOT/'work/ver_rin_nana/checkpoints/wall_186ad99f/SLUS_005.61.000').read_bytes()))

    def test_other_character_rejected(self):
        s=bytearray(self.state);s[self.ram+0x1418c8+2]=0
        with self.assertRaisesRegex(ValueError,'Rin idle'):refresh(s,self.old,self.new,self.ram)

    def test_active_action_rejected(self):
        s=bytearray(self.state);s[self.ram+0x1418c8+0x17]=10
        with self.assertRaisesRegex(ValueError,'Rin idle'):refresh(s,self.old,self.new,self.ram)

    def test_wrong_parent_asset_rejected(self):
        s=bytearray(self.state);s[1543002+100]^=1
        with self.assertRaisesRegex(ValueError,'uniquely identified'):refresh(s,self.old,self.new,self.ram)

    def test_palette_change_rejected(self):
        m,_=entry(self.new,9);arc=bytearray(self.new);arc[m['offset']+2]^=1
        with self.assertRaisesRegex(ValueError,'Palette changed'):refresh(self.state,self.old,arc,self.ram)

    def test_active_composition_change_rejected(self):
        from src.psx_player import composition_frame
        m,parts=entry(self.new,3);q=composition_frame(parts,0,0)['parts'][0]
        arc=bytearray(self.new);arc[m['offset']+q['record_offset']+2]^=1
        with self.assertRaisesRegex(ValueError,'Active pose changed'):refresh(self.state,self.old,arc,self.ram)

if __name__=='__main__':unittest.main()
