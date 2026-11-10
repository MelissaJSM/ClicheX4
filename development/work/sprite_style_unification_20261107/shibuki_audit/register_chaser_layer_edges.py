"""신작 의상 외곽6셀을 동일 새 포스 부위의 인접 표본으로 정합."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page,metrics
from prepare_lowhp_final import compose
from probe_chaser_layers_v2 import SOURCES,HAND,poly
DONORS={162:[((11,-3),(11,-2),'뒤쪽 땋은머리 외곽')],166:[],170:[((6,-14),(5,-14),'머리 장식 위 외곽'),((7,-14),(7,-13),'머리 장식 위 외곽'),((8,-13),(8,-12),'머리 장식 오른쪽 외곽'),((9,-3),(9,-2),'뒤쪽 땋은머리 외곽')],174:[((5,24),(5,23),'부츠 발끝 외곽')]}
def bbox(mask):
    y,x=np.nonzero(mask)
    return None if not len(x)else[int(x.min()-160),int(y.min()-160),int(x.max()+1-160),int(y.max()+1-160)]
def main():
    src=H/'chaser_layers_probe02';d=H/'chaser_layers_final01';need(not d.exists(),'새 정합 출력 필요');d.mkdir()
    a=Archive((H/'prepared_standing_fire_base01/PL00_U.ARC').read_bytes());rows=[]
    for n,s in SOURCES.items():
        ls={b:np.array(Image.open(src/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};pending=np.array(Image.open(src/f'{n:03}_unresolved_mask.png'))>0
        owner=np.array(Image.open(src/f'{n:03}_owner.png'));fourth=np.array(Image.open(H/s/f'fourth_{n:03}_indices.png'));changed=np.zeros(pending.shape,bool);events=[]
        for(x,y),(sx,sy),part in DONORS[n]:
            need(abs(x-sx)+abs(y-sy)==1,'인접 표본만');py,px=y+160,x+160;bank=int(owner[py,px]);index=int(fourth[sy+160,sx+160])
            need(pending[py,px]and index>0 and bank in(5,6,7,8),'정합 좌표/소유/원화 오류');need(not any(ls[b][py,px]for b in(5,6,7,8)),'다른층 덮음')
            ls[bank][py,px]=index;changed[py,px]=True;events.append({'xy':[x,y],'source_xy':[sx,sy],'source_index':index,'owner_bank':bank,'semantic_part':part})
        need(np.array_equal(pending,changed),'미정합 셀 누락')
        for b,z in ls.items():Image.fromarray(z).save(d/f'{n:03}_bank{b}_indices.png')
        for k in('common','head','hand','front_arm','outline'):(d/f'{n:03}_{k}_mask.png').write_bytes((src/f'{n:03}_{k}_mask.png').read_bytes())
        Image.fromarray(owner).save(d/f'{n:03}_owner.png');Image.fromarray(changed.astype('uint8')*255).save(d/f'{n:03}_local_registration_mask.png')
        for form,m in [('base',0),('fourth',15)]:compose(a,ls,m).save(d/f'{form}_{n:03}.png')
        page([(f'{n} mask{m:X}',compose(a,ls,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4)
        hand=poly(HAND[n]);old=a.layer(n)[0];new=ls[0]
        # 표본은 손 ROI 내 실제 피부색이며 물리적 손잡이의 전체 접점 증명은 아니다.
        oldskin=hand&np.isin(old,[10,12,13]);newskin=hand&np.isin(new,[10,12,13]);eyeroi=np.zeros(old.shape,bool);eyeroi[132:162,146:160]=True
        rows.append({'ref':n,'events':events,'source_registration':s,'base_source_exact':True,'layer_hashes':{str(b):sha(z.tobytes())for b,z in ls.items()},
            'old_hand_skin_bbox':bbox(oldskin),'new_common_hand_skin_bbox':bbox(newskin),'old_gold_eye_region_bbox':bbox(eyeroi&(old==7)),'new_gold_eye_region_bbox':bbox(eyeroi&(new==7)),
            'old_base_metrics':metrics(a.composite(n)[0]),'new_base_metrics':metrics(compose(a,ls,0)),'new_fourth_metrics':metrics(compose(a,ls,15)),
            'old_coarse_head_or_body_copied':False,'body_resized':False,'other_layers_outside_event_cells_unchanged':True})
    for form,m in [('base',0),('fourth',15)]:
        page([(f'{n} 새 부분조립',Image.open(d/f'{form}_{n:03}.png'))for n in SOURCES],a.composite(0,m)[0],d/f'{form}_all.png',cols=2,scale=5)
    write(d/'report.json',{'previous_probe':{'path':(src/'report.json').relative_to(ROOT).as_posix(),'sha256':sha((src/'report.json').read_bytes())},'rows':rows,
        'local_registered_cells':sum(len(r['events'])for r in rows),'unresolved_cells':0,'arc_written':False,'runtime_verified':False,
        'policy':'새 포스 원화 바로 인접한 실제 장식/땋은머리/발끝의 색인6셀만 정합했다. 색축소·일괄검정채움·옛몸체·전신스케일 변경 없음. 모든 기본형 새도트 보존.',
        'limits':['새 손 ROI 피부색 bbox/금색눈 영역은 정적 표본이다. 실제 차량 손잡이/발판 위치를 관측한 실기가 아니다.','추가 실제 원순서/13파생/패킹/부분 독립검사는 아직이다.']})
    print(json.dumps({'output':str(d),'rows':rows}))
if __name__=='__main__':main()
