"""독립 재현·손상 거부·캡슐 UV 경계와 기존 플레이어를 검사한다."""
import json,struct,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_nana_fourth_ui import *
from scripts.build_nana_fourth_ui import validate
from src.psx_player import indexed_atlas

def main():
    folder=ROOT/'work/ver_rin_nana/nana_fourth_ui';art=folder/'v2';repro=folder/'repro_v2';recipe,records,edited,proof,names=validate(art,repro);original,_=read_sources();rejected=[]
    def bad(label,name,data):
        candidate={**edited,name:data}
        try:verify(original,candidate)
        except ValueError:rejected.append(label)
        else:raise AssertionError('Accepted '+label)
    menu=edited['MOJIPAT.ARC'];po=struct.unpack_from('<I',menu,4)[0]
    for label,offset in [('rin_palette',po+10*32),('armor_palette',po+9*32),('base_sprite',composition_frame(menu,2,44)['parts'][0]['record_offset']+2)]:
        v=bytearray(menu);v[offset]^=1;bad(label,'MOJIPAT.ARC',bytes(v))
    load=edited['LOAD_U.ARC'];tex=bytearray(entry(load,0x10008));tex[0]^=1;bad('unowned_atlas_tile','LOAD_U.ARC',replace_entry(load,0x10008,bytes(tex)))
    arc=edited['PL00_U.ARC'];pal=bytearray(entry(arc,9));pal[0]^=1;bad('gameplay_palette','PL00_U.ARC',replace_entry(arc,9,bytes(pal)))
    c=bytearray(entry(arc,3));c[composition_frame(c,0,0)['parts'][0]['record_offset']+2]^=1;bad('playable_pose','PL00_U.ARC',replace_entry(arc,3,bytes(c)))
    c=bytearray(entry(arc,3));c[composition_frame(c,18,0)['parts'][0]['record_offset']+2]^=1;bad('capsule_anchor','PL00_U.ARC',replace_entry(arc,3,bytes(c)))
    g,c=entry(arc,2),entry(arc,3);checked=0
    for gb in range(10,14):
        f=graphics_bank(g,gb,allow_bank_aliases=True)['frames'][0];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data;atlas=indexed_atlas(raw,f['tile_count'])[0]
        for n in range(11):
            for q in composition_frame(c,gb+8,n)['parts']:
                t=q['tile'];col=t%16*16;row=t//16*16;require(t%16!=0 or not any(atlas[(row+y)*256+col] for y in range(16)),'Unsafe capsule U0 column');require(not(q['flip_y'] and row==0) or not any(atlas[col:col+16]),'Unsafe vertical UV0');checked+=1
    suite=unittest.TestSuite()
    for pattern in ('test_ui_atlas.py','test_static_effect.py','test_psx_disc.py','test_psx_sector.py','test_psx_compress.py','test_psx_tile_layout.py','test_psx_armor_palette.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**proof,'independent_files_identical':len(names),'rejected_mutations':rejected,'unit_tests_passed':result.testsRun,'capsule_gpu_parts_checked':checked,'resource_sha256':recipe['files']};write(folder/'verification.json',report);print(json.dumps(report))
if __name__=='__main__':main()
