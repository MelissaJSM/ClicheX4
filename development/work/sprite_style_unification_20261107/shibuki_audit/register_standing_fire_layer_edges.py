"""새 포스 외곽의 1칸 불일치를 바로 이웃한 새 원화 부위 표본으로 등록."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive,page
from prepare_lowhp_final import compose
from probe_standing_fire_modules import SOURCES
DONORS={87:[((-7,2),(-6,2),'앞소매 아래 테두리')],90:[((8,-12),(7,-12),'뒷머리 장식 테두리'),((-7,4),(-6,4),'상의 옆 테두리'),((-10,7),(-9,7),'옷단 외곽'),((-4,11),(-5,11),'옷단 아래 테두리'),((-3,11),(-3,10),'옷단 아래 테두리'),((-2,11),(-2,10),'옷단 아래 테두리')],91:[((8,-12),(7,-12),'뒷머리 장식 테두리')],92:[((-8,2),(-8,1),'접힌 소매 아래 명암'),((-7,2),(-7,1),'접힌 소매 아래 테두리'),((-8,3),(-7,3),'접힌 소매 외곽')]}
def main():
    s=H/'standing_fire_layers_probe01';d=H/'standing_fire_layers_probe02';need(not d.exists(),'Fresh output');d.mkdir();a=Archive((H/'prepared_standing_special_base01/PL00_U.ARC').read_bytes());rows=[]
    for n in(85,86,87,89,90,91,92):
        ls={b:np.array(Image.open(s/f'{n:03}_bank{b}_indices.png'))for b in(0,5,6,7,8)};owner=np.array(Image.open(s/f'{n:03}_owner.png'));pending=np.array(Image.open(s/f'{n:03}_unresolved_base_visible_mask.png'))>0;source=np.array(Image.open(H/SOURCES[n]/f'fourth_{n:03}_indices.png'));events=[];mask=np.zeros(pending.shape,bool)
        for (x,y),(sx,sy),part in DONORS.get(n,[]):
            need(abs(x-sx)+abs(y-sy)==1,'Not adjacent native sample');py,px=y+160,x+160;q=int(source[160+sy,160+sx]);need(pending[py,px]and q>0,'Invalid unresolved donor');b=int(owner[py,px]);need(b in(5,6,7,8),'Invalid owner');need(not any(ls[k][py,px]for k in(5,6,7,8)),'Already covered');ls[b][py,px]=q;mask[py,px]=1;events.append({'xy':[x,y],'new_source_xy':[sx,sy],'source_index':q,'semantic_part':part,'owner_bank':b})
        need(np.array_equal(pending,mask),'Unresolved cells remain')
        for b,v in ls.items():Image.fromarray(v).save(d/f'{n:03}_bank{b}_indices.png')
        Image.fromarray(mask.astype('uint8')*255).save(d/f'{n:03}_local_registration_mask.png');Image.fromarray(owner).save(d/f'{n:03}_owner.png');a.rgba(ls[0]).save(d/f'base_{n:03}.png');compose(a,ls,15).save(d/f'fourth_{n:03}.png');page([(f'{n} mask{m:X}',compose(a,ls,m))for m in range(16)],a.composite(0,15)[0],d/f'partial_{n:03}.png',cols=4,scale=4);rows.append({'ref':n,'source_indices_sha256':sha(source.tobytes()),'events':events,'base_exact_to_probe01':True,'outside_events_all_layers_exact':True,'layer_hashes':{str(b):sha(v.tobytes())for b,v in ls.items()}})
    for i,refs in enumerate(((85,86,87,89),(90,91,92))):
        pics=[]
        for n in refs:pics.extend([(f'{n} first joint',Image.open(s/f'fourth_{n:03}.png')),(f'{n} local source edge',Image.open(d/f'fourth_{n:03}.png'))])
        page(pics,a.composite(0,15)[0],d/f'fourth_comparison_{i:02}.png',cols=2,scale=5)
    write(d/'report.json',{'previous_probe_sha256':sha((s/'report.json').read_bytes()),'rows':rows,'changed_native_cells':sum(len(r['events'])for r in rows),'registration_policy':'새기본과새포스의1픽셀옷/장식외곽차이를같은새포스원화의맨해튼거리1 표본으로정합. 임의 검정채움/피부채움/옛몸복사/팔늘림 없음.','unresolved_base_cells':0,'other_probe_limitations_still_apply':True,'arc_written':False,'root_review_pending':True,'body_rescale':False})
    print(d)
if __name__=='__main__':main()
