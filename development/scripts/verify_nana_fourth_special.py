"""차지/사이클론 재현·접점·공유·기존133아머를 검사한다."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_special_reference import PARENT,PARENT_SHA,FRAMES
from scripts.prepare_nana_fourth_special_art import shift,TRANSLATIONS,LAYERS
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art

def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'special_art_v5';packed=root/'special_packed_v5';same=0
    for src,dst in ((art,root/'special_art_repro'),(packed,root/'special_packed_repro')):
        require({p.name for p in src.iterdir()}=={p.name for p in dst.iterdir()},'Reproduction file list differs')
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Reproduction differs: '+p.name);same+=1
    recipe=json.loads((packed/'recipe.json').read_text('utf8'));rr=json.loads((root/'special_packed_repro/recipe.json').read_text('utf8'))
    require({k:v for k,v in recipe.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(packed/'modified.arc').read_bytes();_,_,checks=validate_art(packed,old,new,PARENT_SHA,FRAMES)
    meta=json.loads((art/'layers.json').read_text('utf8'));contacts=0
    for n in FRAMES:
        require(np.array_equal(render(old,n)[1],render(new,n)[1]),'Basic form/trail changed')
        require(render(new,n,True)[0].tobytes()==Image.open(art/f'full_{n:03}.png').convert('RGBA').tobytes(),'Full armor readback differs')
    for q in meta['registration']:
        if 'source_cell' not in q:continue
        n=q['frame'];base=render(old,n)[1];target=np.array(Image.open(art/f'full_{n:03}.png'));lower=q['lower_y']
        require(np.array_equal(target[lower:]>0,base[lower:]>0),'Native lower silhouette changed')
        x,y,x2,y2=q['face_box'];require(np.array_equal(target[y:y2,x:x2],base[y:y2,x:x2]),'Face landmark changed')
        for x,y,x2,y2 in q['contacts']:
            require(np.array_equal(target[y:y2,x:x2],base[y:y2,x:x2]),'Pistol/hand contact changed');contacts+=1
    for n,(source,dx) in TRANSLATIONS.items():
        for name in LAYERS:
            a=np.array(Image.open(art/f'{name}_{source:03}.png'));b=np.array(Image.open(art/f'{name}_{n:03}.png'));require(np.array_equal(shift(a,dx),b),'Translated costume drift')
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Accepted armor changed')
    require(entry(old,9)==entry(new,9),'Palette changed');rejected=[]
    with tempfile.TemporaryDirectory(prefix='special_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**recipe,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**checks,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'translated_costume_pairs':2,'contact_rectangles_preserved':contacts,'prior_armor_refs_preserved':len(inherited),'checked_bitmap_references':recipe['checked_bitmap_references'],'other_compositions_preserved':recipe['other_compositions_preserved'],'all_base_special_rasters_and_trail_preserved':True,'palette_identical':True,'arc_sha256':digest(packed/'modified.arc'),'runtime_verified':False}
    write(root/'special_verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
