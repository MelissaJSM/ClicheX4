"""공중12참조의 재현·허리/권총 접점·파츠 배분과 기존149아머를 검사한다."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_hover_reference import PARENT,PARENT_SHA,FRAMES,REUSE,CUTS
from scripts.prepare_nana_fourth_hover_art import LAYERS
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art

def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'hover_art_v2';packed=root/'hover_packed_v2';same=0
    for src,dst in ((art,root/'hover_art_repro'),(packed,root/'hover_packed_repro')):
        require({p.name for p in src.iterdir()}=={p.name for p in dst.iterdir()},'Reproduction file list differs')
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Reproduction differs: '+p.name);same+=1
    recipe=json.loads((packed/'recipe.json').read_text('utf8'));rr=json.loads((root/'hover_packed_repro/recipe.json').read_text('utf8'))
    require({k:v for k,v in recipe.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(packed/'modified.arc').read_bytes();_,_,checks=validate_art(packed,old,new,PARENT_SHA,FRAMES)
    for n in FRAMES:
        before=render(old,n)[1];after=render(new,n)[1];cut=CUTS.get(n,160)
        require(np.array_equal(before[:cut],after[:cut]),'Base upper/air-dash changed')
        if n in CUTS:require(not np.any(after[cut:]),'Duplicate hover legs remain')
        require(render(new,n,True)[0].tobytes()==Image.open(art/f'full_{n:03}.png').convert('RGBA').tobytes(),'Armor readback differs')
        if n in REUSE:
            source=render(old,REUSE[n],True)[0];target=render(new,n,True)[0]
            require(np.array_equal(np.array(source)[:cut],np.array(target)[:cut]),'Accepted upper body/pistol changed')
    for n in (221,223,225,227,229):
        # 수용 사격 상체에는 팔 접속부를 비운 몸통 차이가 이미 있다.
        # 그 영역은 위의 원본 상체 비교로 보호하고 새 하체·머리 공유를 검사한다.
        for name in ('head','leg'):
            require(Image.open(art/f'{name}_{n:03}.png').tobytes()==Image.open(art/f'{name}_{n+1:03}.png').tobytes(),'Shooting body differs')
    meta=json.loads((art/'layers.json').read_text('utf8'));q=next(q for q in meta['registration'] if q['frame']==94);a=np.array(Image.open(art/'full_094.png'));b=render(old,94)[1]
    for x,y,x2,y2 in [q['face_box']]+q['contacts']:require(np.array_equal(a[y:y2,x:x2],b[y:y2,x:x2]),'Dash face/gun contact changed')
    require(np.array_equal(a[82:]>0,b[82:]>0),'Dash native legs moved')
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Accepted armor changed')
    require(entry(old,9)==entry(new,9),'Palette changed');rejected=[]
    with tempfile.TemporaryDirectory(prefix='hover_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**recipe,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**checks,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'accepted_upper_reused':REUSE,'base_lower_cut':CUTS,'hover_without_leg_armor_not_reachable':True,'valid_partial_combinations':112,'prior_armor_refs_preserved':len(inherited),'checked_bitmap_references':recipe['checked_bitmap_references'],'other_compositions_preserved':recipe['other_compositions_preserved'],'palette_identical':True,'arc_sha256':digest(packed/'modified.arc'),'runtime_verified':False}
    write(root/'hover_verification.json',report);print(json.dumps(report))
if __name__=='__main__':main()
