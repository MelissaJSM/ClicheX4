"""공중 의상 재현, 무기/눈/하체 등록, 이전 수용42참조 보존을 검사한다."""
import argparse,json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_air_reference import PARENT,PARENT_SHA,FRAMES
from scripts.prepare_nana_fourth_pilot import require,entry,render,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art

def main():
    p=argparse.ArgumentParser();p.add_argument('--profile',choices=('air','wall'),default='air');args=p.parse_args()
    profile=args.profile;parent,parent_sha,frames=PARENT,PARENT_SHA,FRAMES
    if profile=='wall':
        from scripts.prepare_nana_fourth_wall_reference import PARENT as wp,PARENT_SHA as wh,FRAMES as wf
        parent,parent_sha,frames=wp,wh,wf
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor'
    art=root/('wall_art_v10' if profile=='wall' else 'air_art_v4');prepared=root/('wall_packed_v3' if profile=='wall' else 'air_packed_v1');same=0
    suffix='_repro_v3' if profile=='wall' else '_repro'
    for src,dst in ((art,root/f'{profile}_art{suffix}'),(prepared,root/f'{profile}_packed{suffix}')):
        for p in src.iterdir():
            if p.name=='recipe.json':continue
            require(digest(p)==digest(dst/p.name),'Independent reproduction differs: '+p.name);same+=1
    r=json.loads((prepared/'recipe.json').read_text('utf8'));rr=json.loads((root/f'{profile}_packed{suffix}/recipe.json').read_text('utf8'))
    require({k:v for k,v in r.items() if k!='art'}=={k:v for k,v in rr.items() if k!='art'},'Packing recipe differs')
    old=(parent/'modified.arc').read_bytes();new=(prepared/'modified.arc').read_bytes();_,_,check=validate_art(prepared,old,new,parent_sha,frames)
    meta=json.loads((art/'layers.json').read_text('utf8'));joint_count=0
    for q in meta['registration']:
        n=q['frame'];base=render(old,n)[1];shot=render(old,n+1)[1]
        a=np.array(Image.open(art/f'full_{n:03}.png'));b=np.array(Image.open(art/f'full_{n+1:03}.png'));start=q['native_lower_silhouette_preserved_from_y']
        require(np.array_equal(a[start:]>0,base[start:]>0),'Lower silhouette changed')
        require(np.array_equal(a[start:],b[start:]),'Shooting changes lower pose')
        x,y,x2,y2=q['pistol_box']
        if profile!='wall':require(np.array_equal(b[y:y2,x:x2],shot[y:y2,x:x2]),'Pistol/hand moved')
        else:
            fix=q['wall_pistol_adjustment'];gx,gy,gx2,gy2=fix['registered_box']
            require(np.array_equal(b[:,gx],shot[:,gx]),'Muzzle column moved')
            prior=np.array(Image.open(root/f'wall_art_v5/full_{n+1:03}.png'));mask=np.zeros(prior.shape,bool);mask[gy:gy2,gx:gx2]=True
            require(np.array_equal(b[~mask],prior[~mask]),'Armor body changed outside pistol')
            require(np.array_equal(a,np.array(Image.open(root/f'wall_art_v5/full_{n:03}.png'))),'Nonfiring wall pose changed')
            base_new=render(new,n+1)[1]
            require(np.array_equal(base_new[~mask],shot[~mask]),'Base changed outside pistol')
            require(np.array_equal(base_new,np.array(Image.open(art/f'base_{n+1:03}.png'))),'Base pistol readback differs')
            require(fix['grip_shift_toward_shoulder_pixels']>=3,'Pistol correction did not shorten arm')
        require(np.array_equal(a==14,base==14),'Native eye registration changed')
        if profile=='wall':
            x,y,x2,y2=q['wall_contact_box']
            require(np.array_equal(a[y:y2,x:x2],base[y:y2,x:x2]),'Wall palm contact changed')
            require(np.array_equal(b[y:y2,x:x2],shot[y:y2,x:x2]),'Shooting wall palm contact changed')
        for x,y in q['shoulder_bridge_pixels']:require(b[y,x]>0 if profile=='wall' else b[y,x] in (1,2),'Missing shooting shoulder bridge')
        joint_count+=len(q['shoulder_bridge_pixels'])
    inherited=json.loads((parent/'manifest.json').read_text('utf8'))['fourth_armor_frames']
    for n in inherited:require(render(old,n,True)[0].tobytes()==render(new,n,True)[0].tobytes(),'Accepted armor appearance changed')
    require(entry(old,9)==entry(new,9),'Palette changed')
    base_rejected=[]
    if profile=='wall':
        from scripts.prepare_nana_fourth_wall_gun import patch_base
        from src.psx_player import composition_frame
        im,values,descriptor,raw=render(old,55);c=entry(old,3)
        regular,shoot=composition_frame(c,0,55),composition_frame(c,0,56)
        target=np.array(Image.open(art/'base_056.png'));box=meta['registration'][0]['wall_pistol_adjustment']['registered_box']
        outside=target.copy();outside[0,0]=1
        erased=target.copy();erased[box[1],box[0]]=0
        for name,value,reg,bounds in (('outside_pistol',outside,regular,box),('erase_base',erased,regular,box),('shared_regular_tile',target,shoot,box),('uncovered_pixel',outside,regular,[0,0,160,160])):
            try:patch_base(raw,descriptor['tile_count'],reg,shoot,value,bounds)
            except ValueError:base_rejected.append(name)
            else:raise AssertionError('Unsafe base correction accepted: '+name)
    rejected=[]
    with tempfile.TemporaryDirectory(prefix=profile+'_negative_',dir=root) as name:
        temp=Path(name)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            write(temp/'recipe.json',{**r,field:value})
            try:validate_art(temp,old,new,parent_sha,frames)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted')
    suite=unittest.TestSuite()
    for pattern in ('test_psx_armor_palette.py','test_armor_remaining_layout.py','test_armor_motion_layout.py','test_psx_tile_layout.py','test_psx_compress.py','test_psx_disc.py','test_psx_sector.py'):suite.addTests(unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=pattern))
    result=unittest.TextTestRunner().run(suite);require(result.wasSuccessful(),'Unit suite failed')
    pairs=len(meta['registration'])
    report={**check,'profile':profile,'independent_identical_files':same,'rejected_cases':rejected,'unit_tests_passed':result.testsRun,'native_pistol_pairs':pairs,'native_eye_pairs':pairs,'native_lower_silhouette_pairs':pairs,'native_wall_contact_pairs':pairs if profile=='wall' else None,'shoulder_bridge_pixels':joint_count,'accepted_armor_refs_preserved':len(inherited),'arc_sha256':digest(prepared/'modified.arc'),'runtime_verified':False}
    if profile=='wall':
        report['native_pistol_pairs']=0
        report['native_muzzle_pairs']=pairs
        report['base_and_armor_wall_pistols_refitted']=pairs
        report['hand_shift_pixels']=[q['wall_pistol_adjustment']['grip_shift_toward_shoulder_pixels'] for q in meta['registration']]
        report['base_edit_rejected_cases']=base_rejected
    write(root/f'{profile}_verification.json',report);print(json.dumps(report))

if __name__=='__main__':main()
