"""낮은 대시 사격 두 팔의 원 총구·실제 몸체를 함께 고정하는 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3];sys.path[:0]=[str(D),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write
from prepare_next_guides import page
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/plan['parent_arc']).read_bytes());out=D/'low_arm_reach_v1';need(not out.exists(),'Fresh output');out.mkdir();items=[];detail=Image.new('RGBA',(1536,640));draw=ImageDraw.Draw(detail);font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);records=[]
    for k,n in enumerate((72,76)):
        body=np.array(Image.open(D/'firing_a_joint_probe_v2'/f'rest_body_{n:03}.png'));gun=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'));guide=body.copy();guide[gun>0]=gun[gun>0];items.append((f'FIXED MUZZLE + BODY {n}',a.rgba(guide)))
        crop=Image.open(D/'basic_firing_a_registered_v1'/f'source_{n:03}.png').convert('RGBA');w=720;h=round(crop.height*w/crop.width);crop=crop.resize((w,h),Image.Resampling.NEAREST);detail.alpha_composite(crop,(k*768+24,120));draw.text((k*768+24,20),f'NEW SLEEVE DETAIL {n} - REACH TOO SHORT',font=font,fill=(90,100,110,255));records.append({'ref':n,'body':digest(D/'firing_a_joint_probe_v2'/f'rest_body_{n:03}.png'),'gun':digest(D/'fire_constraints'/f'barrel_{n:03}.png'),'source_art':digest(D/'basic_firing_a_v1/generated.png')})
    page(items,out/'fixed_contacts.png');detail.save(out/'new_sleeve_detail.png');write(out/'inputs.json',{'source_arc_sha256':sha(a.data),'frames':records,'purpose':'새 팔을 그리기 위한 입력. 일부 팔이 비어 있는 것은 지시용이며 최종 자산 아님.'})
if __name__=='__main__':main()
