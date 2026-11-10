"""피격 외곽 수정의 재현·기본형/부분 아머 보존·잘못된 입력 거부 검사."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from scripts.prepare_nana_hurt_aura_reference import PARENT,PARENT_SHA,FRAMES,bodies
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.build_nana_fourth_idle import validate_art
from scripts.project import digest
from src.psx_player import graphics_bank,decode_stream,composition_frame
from src.psx_sprite_batch import canvas_from_parts

def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'hurt_aura_packed_v1';repro=root/'hurt_aura_packed_repro'
    files=sorted(p.name for p in art.iterdir());require(files==sorted(p.name for p in repro.iterdir()),'Reproduction list differs')
    for name in files:require(digest(art/name)==digest(repro/name),'Reproduction differs: '+name)
    old=(PARENT/'modified.arc').read_bytes();new=(art/'modified.arc').read_bytes();recipe,_,checks=validate_art(art,old,new,PARENT_SHA,FRAMES)
    require(entry(old,9)==entry(new,9),'Palette changed')
    variants=bodies(old);union=np.logical_or.reduce([v>0 for v in variants]);counts=[]
    for n in FRAMES:
        body=render(new,n)[1];fx=(body>0)&~(variants[0]>0)
        require(not np.any(fx&union),'Effect intersects an outfit')
        require(np.array_equal(body[union],variants[0][union]),'Accepted basic body changed')
        layers=[]
        for arc in (old,new):
            g,c=entry(arc,2),entry(arc,3);f=graphics_bank(g,0,allow_bank_aliases=True)['frames'][n];raw=decode_stream(g,f['offset'],f['limit'],f['tile_count']*128).data
            layers.append({b:canvas_from_parts(raw,f['tile_count'],composition_frame(c,b,n)) for b in (5,6,7,8)})
        for b in layers[0]:require(np.array_equal(layers[0][b],layers[1][b]),'Armor layer changed')
        for mask in range(16):
            merged=body.copy()
            for bit,b in ((8,8),(1,5),(4,7),(2,6)):
                if mask&bit:merged=np.where(layers[1][b],layers[1][b],merged)
            visible=variants[mask]>0;require(np.array_equal(merged[visible],variants[mask][visible]),'Partial body changed')
        counts.append({'frame':n,'new_effect_pixels':int(fx.sum()),'old_effect_pixels':int(((render(old,n)[1]>0)&(variants[0]==0)).sum())})
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames'];preserved=[n for n in inherited if n not in FRAMES]
    for n in preserved:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Prior armor raster changed')
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='hurt_aura_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**recipe,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**checks,'independent_identical_files':len(files),'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'other_armor_refs_preserved':len(preserved),'checked_bitmap_references':recipe['checked_bitmap_references'],'other_compositions_preserved':recipe['other_compositions_preserved'],'all_16_body_silhouettes_preserved':True,'palette_identical':True,'effects':counts,'arc_sha256':digest(art/'modified.arc'),'runtime_verified':False}
    write(root/'hurt_aura_verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
