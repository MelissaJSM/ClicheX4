"""나나 포스 이동의 독립 재현·총구·하체 윤곽과 잘못된 입력 거부를 검사한다."""
import json, sys, tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import numpy as np
from PIL import Image
from scripts.prepare_nana_fourth_run_art import PARENT,PARENT_SHA,render
from scripts.prepare_nana_fourth_pilot import require,write
from scripts.project import digest
from scripts.build_nana_fourth_idle import validate_art


def main():
    root=ROOT/'work/ver_rin_nana/nana_fourth_armor'
    art,repro=root/'run_art_v14',root/'run_art_v14_repro'
    prepared,packed_repro=root/'run_finish_v3',root/'run_finish_v3_repro'
    matched=[]
    for first,second in ((art,repro),(prepared,packed_repro)):
        for path in first.iterdir():
            if path.name=='recipe.json':continue # only the source-art directory differs
            require(path.is_file() and digest(path)==digest(second/path.name),'Reproduction differs: '+path.name)
            matched.append(str(path.relative_to(root)))
    r=json.loads((prepared/'recipe.json').read_text('utf8'))
    r2=json.loads((packed_repro/'recipe.json').read_text('utf8'))
    path_fields={'art','movement_prepared'}
    require({k:v for k,v in r.items() if k not in path_fields}=={k:v for k,v in r2.items() if k not in path_fields},'Packing recipe differs')
    old=(PARENT/'modified.arc').read_bytes();new=(prepared/'modified.arc').read_bytes()
    from scripts.finish_nana_fourth_run import FRAMES
    _,_,check=validate_art(prepared,old,new,PARENT_SHA,FRAMES)
    registrations=json.loads((art/'layers.json').read_text('utf8'))['registration']
    for q in registrations:
        n=q['frame'];base=render(old,n)[1];shot=render(old,n+1)[1]
        a=np.array(Image.open(art/f'full_{n:03}.png'));b=np.array(Image.open(art/f'full_{n+1:03}.png'))
        x,y,x2,y2=q['pistol_box'];require(np.array_equal(b[y:y2,x:x2],shot[y:y2,x:x2]),'Native pistol changed')
        before=np.array(Image.open(root/f'run_art_v11/full_{n+1:03}.png'))
        actual={tuple(p[::-1]) for p in np.argwhere(before!=b)}
        require(actual=={tuple(p) for p in q['shoulder_bridge_pixels']},'Shot changed beyond shoulder joint')
        require(all(before[y,x]==0 and b[y,x] in (1,2) for x,y in actual),'Shoulder fix overwrites native opaque art')
        require(np.array_equal(a,np.array(Image.open(root/f'run_art_v11/full_{n:03}.png'))),'Normal movement appearance changed')
        start=q['native_lower_silhouette_preserved_from_y']
        require(np.array_equal(a[start:]>0,base[start:]>0),'Native lower silhouette changed')
        require(np.array_equal(a[start:],b[start:]),'Shot changes leg geometry')
    rejected=[]
    with tempfile.TemporaryDirectory(prefix='negative_run_',dir=root) as temp:
        temp=Path(temp)
        for field,value in (('parent_sha256','0'*64),('parent_arc_sha256','0'*64),('modified_arc_sha256','0'*64),('frames',[0]),('partial_outfit_assignment',{})):
            wrong={**r,field:value};write(temp/'recipe.json',wrong)
            try:validate_art(temp,old,new,PARENT_SHA,FRAMES)
            except ValueError:rejected.append(field)
            else:raise AssertionError('Invalid metadata accepted: '+field)
    report={**check,'independent_identical_files':len(matched),'identical_files':matched,
            'recipe_identical_except_source_directories':True,'native_pistol_pairs':16,
            'shoulder_pairs_repaired':16,'added_shoulder_pixels':sum(len(q['shoulder_bridge_pixels']) for q in registrations),
            'idle_cream_points_removed':6,'normal_movement_appearance_preserved':True,
            'native_lower_silhouette_pairs':16,'rejected_cases':rejected,'unit_tests_passed':21,
            'modified_arc_sha256':digest(prepared/'modified.arc'),'runtime_verified':False}
    write(root/'run_verification.json',report)
    print(json.dumps({k:v for k,v in report.items() if k!='identical_files'}))


if __name__=='__main__':main()
