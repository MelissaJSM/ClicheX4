"""사다리 발 외곽 차이를 원점에 둔 정적 비교. 실제 발판 접촉이라고 주장하지 않는다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;ROOT=H.parents[2];sys.path.insert(0,str(ROOT))
from native_pose_pack import need,sha,write
from scripts.export_x_consistency import Archive
def main():
    o=H/'ultimate_ladder_endpoint_review02';need(not o.exists(),'Fresh review');o.mkdir();paths={'accepted_base':H/'prepared_base_run01/PL00_U.ARC','parent':H/'prepared_ultimate_dash01/PL02_U.ARC','candidate':H/'prepared_ultimate_ladder01/PL02_U.ARC'};arcs={k:Archive(p.read_bytes())for k,p in paths.items()};rows=[];refs=(143,144,146,149,151,153,154,183);lut=np.array(json.loads((H/'ultimate_ladder_common_probe02/report.json').read_text('utf8'))['palette_mapping'])
    for start in(0,4):
        board=Image.new('RGB',(1152,1056),(29,34,44));draw=ImageDraw.Draw(board)
        for ri,n in enumerate(refs[start:start+4]):
            metrics=[]
            for col,(key,mask,label)in enumerate([('accepted_base',0,'accepted base'),('parent',15,'parent jacket'),('candidate',15,'new jacket'),('candidate',0,'new after')]):
                im=arcs[key].composite(n,mask)[0];v=np.array(im);ys,xs=np.nonzero(v[:,:,3]);bottom=int(ys.max()-160);q=im.crop((136,152,184,188)).resize((240,180),Image.Resampling.NEAREST);x=col*288+24;y=ri*264+36;board.paste(q,(x,y),q);draw.text((col*288+8,ri*264+7),f'{n} {label} / lowest y={bottom}',fill='white')
                for gy in(0,8,16,24):draw.line((x,y+(gy+8)*5,x+239,y+(gy+8)*5),fill=(65,74,84));draw.text((x+242,y+(gy+8)*5-5),str(gy),fill=(160,170,180))
                # 수평선은 비교용 좌표선이며 실제 발판이 아니다.
                draw.line((x,y+(bottom+8)*5+4,x+239,y+(bottom+8)*5+4),fill=(235,175,60));metrics.append({'source':key,'mask':mask,'lowest_y':bottom,'lowest_pixels_world':[[int(xx-160),bottom]for xx in xs[ys==ys.max()]]})
            legpath=H/f'ultimate_ladder_common_probe02/{n:03}_legs_mask.png';leg=np.array(Image.open(legpath))>0;b=np.array(arcs['candidate'].composite(n,15)[0]);a=np.array(arcs['candidate'].composite(n,0)[0]);bi=np.array(Image.open(H/f'ultimate_ladder_complete_targets01/before_{n:03}_indices.png'));ai=np.array(Image.open(H/f'ultimate_ladder_complete_targets01/after_{n:03}_indices.png'));need(np.array_equal(lut[bi][leg],ai[leg]),'Common leg registration differs');need(np.array_equal(b[:,:,3][leg],a[:,:,3][leg]),'Leg alpha differs');rows.append({'ref':n,'metrics':metrics,'new_forms_common_leg_palette_mapping_exact':True,'new_forms_common_leg_alpha_exact':True,'different_rgb_pixels_within_original_palettes':int(np.count_nonzero(np.any(b!=a,axis=2)&leg)),'body_transform_applied':[0,0],'whole_body_scaling':False,'physical_rung_contact_verified':False})
        board.save(o/f'feet_{start//4:02}.png')
    write(o/'report.json',{'inputs':{k:{'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p.read_bytes())}for k,p in paths.items()},'rows':rows,'scope':'원점 좌표의 발 외곽과 현재 수용기본형/이전Ultimate 비교. 금색선은 최하단 좌표이고 실제 사다리 발판이 아니다.','palette_mapping':lut.tolist(),'rejected_probe01_assumption':'서로 다른 기존 CLUT의 RGB 전체동일을 요구한 잘못된 검사로 중단. 두 폼은 명시된 최근접 색상 대응과 같은 다리알파를 사용하며 신규 팔레트 변경은 없다.','whole_body_rescale':False,'pose_art_alignment_changed_by_this_report':False,'actual_rung_contact_unverified':True,'known_limit':'새발 최하단이 이전Ultimate보다1~2px 높은 자세가 있다. 자세/신발 외곽 차이를 결함으로 단정하거나 실제접점정확으로 주장하지 않는다.','visual_review_pending':True});print(o.relative_to(ROOT).as_posix())
if __name__=='__main__':main()
