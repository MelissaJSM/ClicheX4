"""57/58의 원화 발끝 보존 및 부분 소유 교정 시각 증거."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,need,write,helper
from prepare_fourth_guides import source
def main():
    a=Archive((D/'packed_wall_candidate_v2/PL00_U.ARC').read_bytes());b=Archive((D/'packed_wall_candidate_v4/PL00_U.ARC').read_bytes());out=D/'packed_wall_candidate_v4';original=np.array(Image.open(source(57)));Y,X=np.indices(original.shape);foot=(X<155)&(Y>=165)&(Y<=170);checks=[]
    for n in(57,58):need(np.array_equal(b.layer(n)[0][foot],original[foot]),'New source boot lost')
    columns=[('새 기본 원화',b.rgba(original)),('교집합 v2',a.composite(57)[0]),('발끝 보존 v4',b.composite(57)[0]),('포스 v4',b.composite(57,15)[0])]
    board=Image.new('RGB',(4*330,730),(187,199,205));draw=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',18)
    for i,(label,im)in enumerate(columns):
        x=i*330;draw.text((x+8,8),label,font=font,fill='black')
        for scale,y in((1,60),(2,145),(6,285)):
            crop=im.crop((140,133,185,184)).resize((45*scale,51*scale),Image.Resampling.NEAREST);board.paste(crop,(x+12,y),crop);draw.text((x+200,y),f'{scale}x',font=font,fill='black')
        part=im.crop((146,162,156,172)).resize((120,120),Image.Resampling.NEAREST);board.paste(part,(x+12,600),part)
    board.save(out/'front_foot_57_review.png')
    for n in range(55,67):
        for mask in(0,15):
            before=np.array(a.composite(n,mask)[0]);after=np.array(b.composite(n,mask)[0]);diff=np.any(before!=after,2)
            if n not in(57,58):need(not diff.any(),'Ownership-only edit changed whole art')
            else:need(not np.any(diff&~foot),'Foot correction left allowed region')
            checks.append({'ref':n,'mask':mask,'changed_pixels':int(diff.sum())})
    helper.grid([(f'ref {n}',[('몸통 v2',a.composite(n,2)[0]),('몸통 v4',b.composite(n,2)[0]),('머리 v4',b.composite(n,1)[0]),('팔 v4',b.composite(n,4)[0])])for n in(55,57,59,61,63,65)],out/'ownership_review.png',5)
    write(out/'local_correction.json',{'passed':True,'source_boot_57_58_exact':True,'foot_world_box':[-14,5,-5,11],'full_basic_other10_exact':True,'checks':checks,'scope':'원화의 앞부츠를 복귀하고 포스 해당 구두만 같은 원화 좌표로 대응. 나머지 전체 그림은 소유 변경 전과 동일.'})
if __name__=='__main__':main()
