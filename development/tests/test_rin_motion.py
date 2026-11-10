"""로컬 승인 자산으로 bank0/1의 동번호 충돌과 매핑 거부를 검사한다."""
import json,tempfile,unittest
from pathlib import Path
from scripts.build_rin_motion import prepare
from scripts.build_rin_idle import entry
from src.psx_player import graphics_bank,decode_stream,composition_frame,compose_indices
ROOT=Path(__file__).resolve().parents[1]
RECIPE=ROOT/'work/ver_rin_nana/wall_saber_production/v1/wall_saber_recipe.json'

@unittest.skipUnless(RECIPE.exists(),'Local proprietary artwork is not distributed')
class RinBankIsolationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _,cls.arc,cls.report,cls.recipe,_,parent=prepare(RECIPE,'wall_saber');cls.before=(parent/'modified.arc').read_bytes()

    def test_same_number_other_bank_is_unchanged(self):
        _,old=entry(self.before,2);_,new=entry(self.arc,2)
        f=graphics_bank(old,0)['frames'][50]
        self.assertEqual(decode_stream(old,f['offset'],f['limit'],f['tile_count']*128).data,decode_stream(new,f['offset'],f['limit'],f['tile_count']*128).data)
        f=graphics_bank(old,1)['frames'][50]
        self.assertNotEqual(decode_stream(old,f['offset'],f['limit'],f['tile_count']*128).data,decode_stream(new,f['offset'],f['limit'],f['tile_count']*128).data)

    def test_original_wall_effects_survive(self):
        _,old=entry(self.before,2);_,new=entry(self.arc,2);_,parts=entry(self.arc,3)
        for n in (52,55,58,60,62,64):
            f=graphics_bank(old,1)['frames'][n];c=composition_frame(parts,5,n)
            a=decode_stream(old,f['offset'],f['limit'],f['tile_count']*128).data;b=decode_stream(new,f['offset'],f['limit'],f['tile_count']*128).data
            self.assertEqual(compose_indices(a,f['tile_count'],c)[:3],compose_indices(b,f['tile_count'],c)[:3])

    def test_ambiguous_bank_mapping_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work/ver_rin_nana') as d:
            path=Path(d)/'bad_recipe.json';r=dict(self.recipe);r['graphics_bank']=0;path.write_text(json.dumps(r),'utf-8')
            with self.assertRaisesRegex(ValueError,'bank mapping'):prepare(path,'wall_saber')

    def test_incomplete_shared_selection_refused(self):
        with tempfile.TemporaryDirectory(dir=ROOT/'work/ver_rin_nana') as d:
            path=Path(d)/'bad_recipe.json';r=dict(self.recipe);r['frames']={n:q for n,q in r['frames'].items() if n!='53'};path.write_text(json.dumps(r),'utf-8')
            with self.assertRaisesRegex(ValueError,'Incomplete'):prepare(path,'wall_saber')

if __name__=='__main__':unittest.main()
