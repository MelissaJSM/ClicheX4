"""별도 피격4참조 수정의 원본 보존·전체 아머 회귀·팔레트 증거 검사."""
import json,sys,tempfile,unittest,struct
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_hurt_extra_reference import PARENT,PARENT_SHA,FRAMES
from scripts.prepare_nana_fourth_pilot import require,entry,render,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art

def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'hurt_extra_art_v2';packed=root/'hurt_extra_packed_v1';same=0
    for src,dst in ((art,root/'hurt_extra_art_repro'),(packed,root/'hurt_extra_packed_repro')):
        require({p.name for p in src.iterdir()}=={p.name for p in dst.iterdir()},'Reproduction file list differs')
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Reproduction differs: '+p.name);same+=1
    recipe=json.loads((packed/'recipe.json').read_text('utf8'));rr=json.loads((root/'hurt_extra_packed_repro/recipe.json').read_text('utf8'))
    require({k:v for k,v in recipe.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(packed/'modified.arc').read_bytes();_,_,checks=validate_art(packed,old,new,PARENT_SHA,FRAMES)
    meta=json.loads((art/'layers.json').read_text('utf8'))
    for n in FRAMES:
        require(render(old,n)[1].tobytes()==render(new,n)[1].tobytes(),'Base/effects changed')
        require(render(new,n,True)[0].tobytes()==Image.open(art/f'full_{n:03}.png').convert('RGBA').tobytes(),'Armor readback differs')
    for q in meta['registration']:
        n=q['frame'];v=np.array(Image.open(art/f'full_{n:03}.png'));base=render(old,n)[1];x,y,x2,y2=q['face_box'];lower=q['native_lower_from_y']
        require(np.array_equal(v[y:y2,x:x2],base[y:y2,x:x2]),'Face moved')
        require(np.array_equal(v[lower:]>0,base[lower:]>0),'Lower body silhouette changed')
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Prior armor changed')
    require(entry(old,9)==entry(new,9),'Palette changed')
    # Observe whether the reported reverse colors came from a different CLUT.
    obsdir=ROOT/'work/ver_rin_nana/nana_armor_hurt_palette/20261030T093830699065Z';obs=json.loads((obsdir/'observation.json').read_text('utf8'));pal=entry(old,9);palette_rows=[]
    for s in obs['samples']:
        v=(obsdir/(s['prefix']+'_vram.bin')).read_bytes();matches={}
        for name,clut in (('body',s['body_clut']),('armor',0x7843),('arm',0x7844)):
            pos=(clut>>6)*2048+(clut&63)*32;data=v[pos:pos+32];matches[name]=[i for i in range(len(pal)//32) if pal[32*i:32*i+32]==data]
            require(bool(matches[name]),'Observed palette is not in current ARC')
        palette_rows.append({'prefix':s['prefix'],'frame':s['frame'],'rows':matches})
    for source,flash in ((0,35),(1,36),(2,37)):
        a=struct.unpack_from('<16H',pal,source*32);b=struct.unpack_from('<16H',pal,flash*32)
        for i in range(1,16):
            for shift in (0,5,10):require(((b[i]>>shift)&31)==round(((a[i]>>shift)&31)*.35+31*.65),'Flash differs from white blend')
    require({233,234,235,236}<={q[2] for q in obs['trace']},'Alternate hurt was not seen in runtime trace')
    write(obsdir/'palette_analysis.json',{'samples':palette_rows,'alternate_hurt_frames_observed':[233,234,235,236],'alternate_hurt_full_framebuffer_captured':False,'normal_and_white_flash_palettes_correct':True,'flash_white_weight':.65,'old_armor_bitmap_remaining_before_fix':[233,234,235,236],'process_memory_written':False,'input_sent':False})
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='hurt_extra_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**recipe,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**checks,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'prior_armor_refs_preserved':len(inherited),'checked_bitmap_references':recipe['checked_bitmap_references'],'other_compositions_preserved':recipe['other_compositions_preserved'],'base_effect_rasters_preserved':FRAMES,'face_lower_pose_preserved':[233,234],'palette_identical':True,'arc_sha256':digest(packed/'modified.arc'),'new_build_runtime_verified':False}
    write(root/'hurt_extra_verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
