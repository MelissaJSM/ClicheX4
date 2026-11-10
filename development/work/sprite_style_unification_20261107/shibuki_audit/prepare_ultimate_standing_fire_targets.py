"""Ultimate85..92 새40층 및88 원효과 전체타일을 결속한다."""
from pathlib import Path
import sys,json,copy
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from src.psx_player import composition_frame,compose_indices,indexed_atlas
from pack_shibuki_hurt import raw
from prepare_lowhp_final import compose
from scripts.c01_audio_build import read_disc
P=H/'prepared_standing_special_ultimate01/PL02_U.ARC'
PARENT='26fd4c46813775ae7a2210b463725952abbabc5f3c172eafb7b5533f994168ce'
PBS=(0,5,6,7,8);REFS=tuple(range(85,93));TD=H/'ultimate_standing_fire_targets01'
SOURCES={85:'ultimate_standing_fire_common01',89:'ultimate_standing_fire_common01',90:'ultimate_standing_followthrough_common03',91:'ultimate_standing_followthrough_common03',86:'ultimate_standing_recovery_common02',87:'ultimate_standing_recovery_common02',92:'ultimate_standing_recovery_common02'}

def main():
    need(not TD.exists(),'새 목표 폴더 필요');need(sha(P.read_bytes())==PARENT,'부모 변경');a=Archive(P.read_bytes())
    targets={n:{b:np.array(Image.open(H/f'{folder}/{n:03}_bank{b}_indices.png'))for b in PBS}for n,folder in SOURCES.items()}
    original_data=read_disc(ROOT/'MegaMan X4.bin',('PL02_U.ARC',))[0]['PL02_U.ARC']
    need(sha(original_data)=='fa8accf20e35634120fd4fc59bac1f31b0fdadaf639b06a783e92189e93c8042','원US PL02 변경')
    original=Archive(original_data)
    cp=composition_frame(original.c,0,88);fc=copy.deepcopy(cp);fc['parts']=[p for p in cp['parts']if p['tile']in(7,8)]
    need(len(fc['parts'])==2,'88 효과 두 기록');rr=raw(original,0,88);count=original.banks[0]['frames'][88]['tile_count']
    pixels,size,box,_=compose_indices(rr,count,fc,allowed_cluts={0});small=np.frombuffer(pixels,np.uint8).reshape(size[1],size[0]);fx=np.zeros((384,384),np.uint8)
    yy,xx=np.nonzero(small);fx[yy+box[1]+160,xx+box[0]+160]=small[yy,xx]
    need((fx>0).sum()==83 and set(np.unique(fx))=={0,12},'원US 효과83/색12');fx[fx==12]=6
    need(np.array_equal(a.layer(88,0)[0][fx>0],fx[fx>0]),'부모 효과의 가시83셀/색6')
    clean={b:np.roll(targets[89][b],-1,axis=1)for b in PBS}
    targets[88]={b:v.copy()for b,v in clean.items()};overlaps={str(b):int(((v>0)&(fx>0)).sum())for b,v in clean.items()}
    targets[88][0][fx>0]=fx[fx>0]
    for b in PBS[1:]: targets[88][b][fx>0]=0
    TD.mkdir();(TD/'original_PL02_U.ARC').write_bytes(original_data);source_files={}
    for folder in sorted(set(SOURCES.values())):
        for p in sorted((H/folder).iterdir()):
            if p.is_file():source_files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    source_dirs=['ultimate_standing_fire_inputs01','ultimate_standing_fire_native01','ultimate_standing_fire_sleeves01','ultimate_standing_fire_sleeves_inspection01','ultimate_standing89_arm02','ultimate_standing_fire_native02','ultimate_standing_followthrough_inputs01','ultimate_standing_followthrough_native01','ultimate_standing90_arm01','ultimate_standing90_arm_inspection01','ultimate_standing_followthrough_native02','ultimate_standing_recovery_inputs01','ultimate_standing_recovery_native01']
    for folder in source_dirs:
        for p in sorted((H/folder).iterdir()):
            if p.is_file():source_files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for p in H.glob('*ultimate_standing*.py'):source_files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for p in (H/'ultimate_dash_barrel_guard01').glob('master*.png'):source_files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    for n in SOURCES:
        p=H/f'standing_fire_modules_probe02/{n:03}_gun_guard.png';source_files[p.relative_to(ROOT).as_posix()]=sha(p.read_bytes())
    rel=H.parent/'zero_audit/shibuki_standing_special_relations01/report.json';source_files[rel.relative_to(ROOT).as_posix()]=sha(rel.read_bytes())
    for n,ll in targets.items():
        for b,v in ll.items():Image.fromarray(v).save(TD/f'{n:03}_bank{b}_indices.png')
        for form,mask in [('before',15),('after',0)]:
            im=compose(a,ll,mask);im.save(TD/f'{form}_{n:03}.png')
            if n!=88:need(im.tobytes()==Image.open(H/f'{SOURCES[n]}/{form}_{n:03}.png').convert('RGBA').tobytes(),'개별 등록판과 불일치')
    for b,v in clean.items():Image.fromarray(v).save(TD/f'088_clean_bank{b}_indices.png')
    Image.fromarray(fx).save(TD/'088_effect_indices.png');a.rgba(fx).save(TD/'088_effect.png')
    atlas=np.frombuffer(indexed_atlas(rr,count)[0],np.uint8).reshape(-1,256);tiles={}
    for t in(7,8):
        tile=atlas[:16,t*16:(t+1)*16].copy();need(set(np.unique(tile))<={0,12},'효과타일 다른 색');source_hash=sha(tile.tobytes());tile[tile==12]=6
        Image.fromarray(tile).save(TD/f'088_effect_tile{t}.png');tiles[str(t)]={'original_all256_nibble_sha256':source_hash,'all256_nibble_sha256':sha(tile.tobytes()),'opaque':int((tile>0).sum()),'color_map':{'12':6}}
    for form,mask in [('before',15),('after',0)]:
        for i,ns in enumerate(((85,86,87),(88,89,90),(91,92))):page([(f'{n} 새 {form}',compose(a,targets[n],mask))for n in ns],a.composite(0,mask)[0],TD/f'{form}_all_{i:02}.png',cols=3,scale=5)
        page([(f'88 기존 {form}',a.composite(88,mask)[0]),(f'89 새 {form}',compose(a,targets[89],mask)),(f'88 새/원효과 {form}',compose(a,targets[88],mask))],a.composite(0,mask)[0],TD/f'effect_{form}_comparison.png',cols=3,scale=5)
    write(TD/'manifest.json',{'parent':P.relative_to(ROOT).as_posix(),'parent_sha256':PARENT,'refs':list(REFS),'parts_banks':list(PBS),'targets':{str(n):{str(b):sha(v.tobytes())for b,v in ll.items()}for n,ll in targets.items()},'source_files':source_files,'registered_sources':SOURCES,'effect88':{'records':fc['parts'],'tiles':tiles,'visible_pixels':83,'color_index':6,'new_body_translation':[-1,0],'overlaps_hidden_by_effect':overlaps,'all16_effect_exact':all(np.array_equal(np.array(compose(a,targets[88],m))[fx>0],np.array(a.rgba(fx))[fx>0])for m in range(16)),'policy':'원US의89 x-1+효과 관계를 따른 신작88. 현재 Ultimate body의198px 차이는 별도 구형 차이이며 원래부터동일했다고 하지 않음. 원효과 두 타일 전체와 좌표/앞그리기 보존.'},'fixed_idle_preserved':True,'old_head_body_copied':False,'arc_written':False,'runtime_verified':False})
    print(json.dumps({'manifest_sha256':sha((TD/'manifest.json').read_bytes()),'source_files':len(source_files),'effect_overlaps':overlaps,'effect_tiles':tiles}))
if __name__=='__main__':main()
