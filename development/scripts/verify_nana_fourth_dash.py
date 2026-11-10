"""대시18참조의 재현·총구·하체·속도선·슬롯 이동과 보호를 검증한다."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_dash_reference import PARENT,PARENT_SHA,FRAMES,ORDER
from scripts.prepare_nana_fourth_pilot import require,entry,render,write
from scripts.prepare_nana_fourth_wall_gun import patch_base,fit_pistol_coverage
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art
from src.psx_player import composition_frame,indexed_atlas


def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor';art=root/'dash_art_v4';prepared=root/'dash_packed_v1';same=0
    for src,dst in ((art,root/'dash_art_repro'),(prepared,root/'dash_packed_repro')):
        require({p.name for p in src.iterdir()}=={p.name for p in dst.iterdir()},'Reproduction file list differs')
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Independent reproduction differs: '+p.name);same+=1
    r=json.loads((prepared/'recipe.json').read_text('utf8'));rr=json.loads((root/'dash_packed_repro/recipe.json').read_text('utf8'))
    require({k:v for k,v in r.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(prepared/'modified.arc').read_bytes();_,_,check=validate_art(prepared,old,new,PARENT_SHA,FRAMES)
    meta=json.loads((art/'layers.json').read_text('utf8'));joints=0;grips=[]
    for q in meta['registration']:
        n=q['frame'];base=render(old,n)[1];shot=render(old,n+1)[1]
        a=np.array(Image.open(art/f'full_{n:03}.png'));b=np.array(Image.open(art/f'full_{n+1:03}.png'));y=q['native_lower_silhouette_preserved_from_y']
        require(np.array_equal(a[y:]>0,base[y:]>0),'Lower silhouette changed')
        require(np.array_equal(a[y:],b[y:]),'Shooting changes lower pose')
        require(np.array_equal(a==14,base==14),'Eye moved')
        gx,gy,gx2,gy2=q['wall_pistol_adjustment']['registered_box'];mask=np.zeros(base.shape,bool);mask[gy:gy2,gx:gx2]=True
        require(np.array_equal(b[:,gx],shot[:,gx]),'Muzzle moved')
        actual=render(new,n+1)[1]
        require(np.array_equal(actual,np.array(Image.open(art/f'base_{n+1:03}.png'))),'Corrected base readback differs')
        require(np.array_equal(actual[~mask],shot[~mask]),'Base changed outside pistol')
        require(np.array_equal(render(new,n)[1],base),'Nonfiring base changed')
        grips.append(q['wall_pistol_adjustment']['grip_shift_toward_shoulder_pixels']);require(grips[-1]>=1,'Hand did not shorten arm')
        for x,y in q['shoulder_bridge_pixels']:require(b[y,x]>0,'Shoulder bridge missing')
        joints+=len(q['shoulder_bridge_pixels'])
    for n in FRAMES:require(render(new,n,True)[0].tobytes()==Image.open(art/f'full_{n:03}.png').convert('RGBA').tobytes(),'Full armor differs')
    inherited=json.loads((PARENT/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Accepted armor changed')
    require(entry(old,9)==entry(new,9),'Palette changed')
    c,nc=entry(old,3),entry(new,3)
    for n in (73,74):
        a=render(old,n);b=render(new,n);count=a[2]['tile_count']
        at=np.frombuffer(indexed_atlas(a[3],count)[0],np.uint8).reshape(-1,256);bt=np.frombuffer(indexed_atlas(b[3],count)[0],np.uint8).reshape(-1,256)
        require(np.array_equal(at[:16,96:112],bt[:16,96:112]),'Speed-line tile6 changed')
        require(composition_frame(c,0,n)==composition_frame(nc,0,n),'Speed-line composition changed')
    for key,shifts in r['base_pistol_slot_shifts'].items():
        oc,ac=composition_frame(c,0,int(key)),composition_frame(nc,0,int(key));require(len(oc['parts'])==len(ac['parts']),'Base part count changed')
        for p,q in zip(oc['parts'],ac['parts']):
            s=next((s for s in shifts if s['record_offset']==p['record_offset']),None)
            expected={**p,'y':p['y']+(s['shift_y'] if s else 0)}
            require(q==expected,'Unexpected base part change')
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='dash_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**r,field:value})
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    # Guard the newly used slot adjustment with actual supported pose data.
    _,_,desc,raw=render(old,67);regular=composition_frame(c,0,67);shoot=composition_frame(c,0,68)
    target=np.array(Image.open(art/'base_068.png'));bad=target.copy();bad[105,55]=1
    try:fit_pistol_coverage(raw,desc['tile_count'],regular,shoot,bad)
    except ValueError:rejected.append('oversized_pistol_slot_shift')
    else:raise AssertionError('Oversized slot shift accepted')
    raw2,comp,_=fit_pistol_coverage(raw,desc['tile_count'],regular,shoot,target)
    box=meta['registration'][0]['wall_pistol_adjustment']['registered_box'];outside=target.copy();outside[0,0]=1
    erased=target.copy();erased[box[1],box[0]]=0
    for name,value,reg,bounds in (('outside_pistol',outside,regular,box),('erase_base',erased,regular,box),('shared_regular_tile',target,comp,box),('uncovered_pixel',outside,regular,[0,0,160,160])):
        try:patch_base(raw2,desc['tile_count'],reg,comp,value,bounds)
        except ValueError:rejected.append(name)
        else:raise AssertionError('Unsafe base correction accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    report={**check,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'native_muzzle_pairs':8,'native_eye_pairs':8,'native_lower_silhouette_pairs':8,'shoulder_bridge_pixels':joints,'hand_shift_pixels':grips,'accepted_armor_refs_preserved':len(inherited),'speed_line_tile_and_parts_preserved':True,'base_pistol_slot_shifts':r['base_pistol_slot_shifts'],'arc_sha256':digest(prepared/'modified.arc'),'runtime_verified':False}
    write(root/'dash_verification.json',report);print(json.dumps(report))


if __name__=='__main__':main()
