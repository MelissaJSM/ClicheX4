"""탑승32의상·빈198·파츠528조합·이전161참조와 재현성을 검사한다."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_vehicle_reference import PARENT,PARENT_SHA,FRAMES,ORDER,EDITED_FRAMES
from scripts.prepare_nana_fourth_vehicle_art import LAYERS
from scripts.prepare_nana_fourth_pilot import entry,render,require,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art
from src.psx_player import composition_frame,graphics_bank,decode_stream
from src.psx_sprite_batch import canvas_from_parts

def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'vehicle_art_v4';packed=root/'vehicle_packed_v1';same=0
    for src,dst in ((art,root/'vehicle_art_repro'),(packed,root/'vehicle_packed_repro')):
        require({p.name for p in src.iterdir()}=={p.name for p in dst.iterdir()},'Reproduction file list differs')
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Reproduction differs: '+p.name);same+=1
    recipe=json.loads((packed/'recipe.json').read_text('utf8'));rr=json.loads((root/'vehicle_packed_repro/recipe.json').read_text('utf8'))
    require({k:v for k,v in recipe.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(packed/'modified.arc').read_bytes();_,_,checks=validate_art(packed,old,new,PARENT_SHA,FRAMES);oc,nc=entry(old,3),entry(new,3)
    for n in FRAMES:
        require(np.array_equal(render(old,n)[1],render(new,n)[1]),'Base changed')
        require(render(new,n,True)[0].tobytes()==Image.open(art/f'full_{n:03}.png').convert('RGBA').tobytes(),'Armor readback differs')
        if n>=184:
            for b in ((0,5,6,7,8) if n==198 else (0,6,7,8)):
                require(composition_frame(oc,b,n)==composition_frame(nc,b,n),'Blank/body composition changed')
                _,_,f,raw=render(new,n);v=canvas_from_parts(raw,f['tile_count'],composition_frame(nc,b,n))
                if b!=0 or n==198:require(not np.any(v),'Head-only frame gained extra body pixels')
    meta=json.loads((art/'layers.json').read_text('utf8'))
    for q in meta['registration']:
        n=q['frame'];a=np.array(Image.open(art/f'full_{n:03}.png'));b=render(old,n)[1]
        if n in ORDER:
            for x,y,x2,y2 in [q['face_box']]+q['contacts']:require(np.array_equal(a[y:y2,x:x2],b[y:y2,x:x2]),'Face/grip contact changed')
            lower=q['lower_y'];require(np.array_equal(a[lower:]>0,b[lower:]>0),'Native leg silhouette moved')
        if q.get('head_only'):
            x,y=q['eye'];require(a[y,x]==b[y,x]==14,'Head eye moved')
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Accepted armor changed')
    require(entry(old,9)==entry(new,9),'Palette changed');rejected=[]
    with tempfile.TemporaryDirectory(prefix='vehicle_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**recipe,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    coverage={'fourth_costume':sorted(set(inherited)|set(EDITED_FRAMES)),'shared_hurt_flash':[109,112,113,114],'shared_light':list(range(126,138))+[140]+list(range(158,162)),'shared_clones':list(range(208,213)),'reserved_unrenderable':[105]+list(range(175,183)),'blank':[198],'ultimate_separate':list(range(213,221))}
    flat=[n for group in coverage.values() for n in group];require(len(flat)==len(set(flat))==237 and set(flat)==set(range(237)),'Coverage partition incomplete')
    og,ng=entry(old,2),entry(new,2);ob=graphics_bank(og,0,allow_bank_aliases=True);nb=graphics_bank(ng,0,allow_bank_aliases=True)
    for key in ('shared_hurt_flash','shared_light','shared_clones','blank','ultimate_separate','reserved_unrenderable'):
        for n in coverage[key]:
            f,of=nb['frames'][n],ob['frames'][n];raw=decode_stream(ng,f['offset'],f['limit'],f['tile_count']*128).data;before=decode_stream(og,of['offset'],of['limit'],of['tile_count']*128).data
            if n!=198:require(raw==before,'Shared/Ultimate texture changed')
            for b in (0,5,6,7,8):require(composition_frame(oc,b,n)==composition_frame(nc,b,n),'Shared/Ultimate composition changed')
            if key not in ('ultimate_separate','reserved_unrenderable'):
                for b in LAYERS.values():require(not np.any(canvas_from_parts(raw,f['tile_count'],composition_frame(nc,b,n))),f'Unreplaced armor pixels {n}/{b}')
    report={**checks,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'new_costume_refs':len(EDITED_FRAMES),'blank_198_preserved':True,'head_other_parts_blank':True,'vehicle_contacts_preserved':True,'prior_armor_refs_preserved':len(inherited),'checked_bitmap_references':recipe['checked_bitmap_references'],'other_compositions_preserved':recipe['other_compositions_preserved'],'palette_identical':True,'coverage':coverage,'allocated_slot_growth':[q for q in recipe['compression'] if q['growth_within_allocated_slot']],'arc_sha256':digest(packed/'modified.arc'),'runtime_verified':False}
    write(root/'vehicle_verification.json',report);print(json.dumps(report))
if __name__=='__main__':main()
