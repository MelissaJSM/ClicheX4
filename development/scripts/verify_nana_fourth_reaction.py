"""피격·저체력 패킹의 공유 효과/입·접지/수용 모션/재현을 검사한다."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_reaction_reference import PARENT,PARENT_SHA,FRAMES,PRESERVED_FLASH
from scripts.prepare_nana_fourth_reaction_art import effect_parts
from scripts.prepare_nana_fourth_pilot import require,entry,render,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art
from src.psx_player import composition_frame,indexed_atlas

def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'reaction_art_v4';prepared=root/'reaction_packed_v1';same=0
    for src,dst in ((art,root/'reaction_art_repro'),(prepared,root/'reaction_packed_repro')):
        require({p.name for p in src.iterdir()}=={p.name for p in dst.iterdir()},'Reproduction file list differs')
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Independent reproduction differs: '+p.name);same+=1
    r=json.loads((prepared/'recipe.json').read_text('utf8'));rr=json.loads((root/'reaction_packed_repro/recipe.json').read_text('utf8'))
    require({k:v for k,v in r.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(prepared/'modified.arc').read_bytes();_,_,check=validate_art(prepared,old,new,PARENT_SHA,FRAMES)
    meta=json.loads((art/'layers.json').read_text('utf8'));c,nc=entry(old,3),entry(new,3)
    for n in FRAMES:
        require(render(new,n,True)[0].tobytes()==Image.open(art/f'full_{n:03}.png').convert('RGBA').tobytes(),'Full armor differs')
        require(render(old,n)[1].tobytes()==render(new,n)[1].tobytes(),'Base changed')
    for q in meta['registration']:
        n=q['frame'];v=np.array(Image.open(art/f'full_{n:03}.png'));base=render(old,n)[1];x,y,x2,y2=q['face_box']
        require(np.array_equal(v[y:y2,x:x2],base[y:y2,x:x2]),'Face changed')
        lower=q['native_lower_from_y'];require(np.array_equal(v[lower:]>0,base[lower:]>0),'Leg silhouette moved')
    foot=np.array(Image.open(art/'full_122.png'))[98:]
    for n in range(120,126):require(np.array_equal(np.array(Image.open(art/f'full_{n:03}.png'))[98:],foot),'Low-health feet move')
    for n in (120,122,124):
        a=np.array(Image.open(art/f'full_{n:03}.png'));b=np.array(Image.open(art/f'full_{n+1:03}.png'))
        ba,bb=render(old,n)[1],render(old,n+1)[1]
        require(np.array_equal(a!=b,ba!=bb),'Mouth animation difference changed')
        require(np.array_equal(a[a!=b],ba[ba!=bb]) and np.array_equal(b[a!=b],bb[ba!=bb]),'Mouth colors changed')
    frozen_parts=0;frozen_tiles=set()
    for n in (107,108):
        _,_,d,raw=render(old,n);nr=render(new,n)[3];count=d['tile_count']
        a=np.frombuffer(indexed_atlas(raw,count)[0],np.uint8).reshape(-1,256);b=np.frombuffer(indexed_atlas(nr,count)[0],np.uint8).reshape(-1,256)
        for bank in (5,6,7,8):
            expected=effect_parts(c,bank,n)['parts'];actual=composition_frame(nc,bank,n)['parts']
            for q in expected:
                require(q in actual,'Effect composition changed');frozen_parts+=1;t=q['tile'];frozen_tiles.add(t)
                sl=np.s_[t//16*16:t//16*16+16,t%16*16:t%16*16+16];require(np.array_equal(a[sl],b[sl]),'Effect tile changed')
    for n in PRESERVED_FLASH:
        require(render(old,n)[3]==render(new,n)[3] and render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Flash changed')
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Accepted armor changed')
    require(entry(old,9)==entry(new,9),'Palette changed')
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='reaction_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**r,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**check,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'accepted_armor_refs_preserved':len(inherited),'frozen_effect_parts':frozen_parts,'frozen_effect_tiles':sorted(frozen_tiles),'flash_refs_preserved':PRESERVED_FLASH,'mouth_pairs_preserved':3,'low_health_foot_refs_preserved':6,'base_rasters_unchanged':len(FRAMES),'checked_bitmap_references':r['checked_bitmap_references'],'other_compositions_preserved':r['other_compositions_preserved'],'arc_sha256':digest(prepared/'modified.arc'),'runtime_verified':False}
    write(root/'reaction_verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
