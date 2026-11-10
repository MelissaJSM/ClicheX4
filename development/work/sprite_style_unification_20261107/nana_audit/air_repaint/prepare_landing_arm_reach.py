"""출처 원화 크롭과 게임 좌표 표식만 담은 사격팔 보완 입력."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,write,digest,need
from register_air_page import crop_count
from review_all_bodies import source as body_source
def main():
    p=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/p['parent_arc']).read_bytes());out=D/'landing_reach_inputs';out.mkdir(exist_ok=True)
    src=Image.open(D/'basic_firing_c_v1/generated.png').convert('RGBA');sheet=Image.new('RGBA',(1536,768));guide=Image.new('RGBA',(1536,768));dr=ImageDraw.Draw(guide);report=[]
    Y,X=np.indices((384,384));xx=X-160;yy=Y-160
    for i,n in enumerate((50,52)):
        crop,box=crop_count(src,i,3);sheet.alpha_composite(crop,(768*i+(768-crop.width)//2,110+(520-crop.height)))
        body=np.array(Image.open(body_source(n-1)/f'base_{n-1:03}.png'));q=next(q for q in p['frames']if q['ref']==n);ex,ey=[int(np.floor(v))for v in q['eye']]
        remove=(xx<=ex+1)&(yy>=ey+4)&(yy<ey+14)&~((xx>=ex-2)&(yy<=ey+5));body[remove]=0
        gun=np.array(Image.open(D/'fire_constraints'/f'barrel_{n:03}.png'));gy,gx=np.nonzero(gun);body[gun>0]=gun[gun>0]
        im=a.rgba(body).crop((112,120,208,216)).resize((768,768),Image.Resampling.NEAREST);guide.alpha_composite(im,(768*i,0));tx=lambda x:768*i+int((x+48)*8);ty=lambda y:int((y+40)*8)
        mx=int(gx.min()-160);my=float(gy.min()+gy.max())/2-160;wrist=(mx+7,my+1);shoulder=(ex+3,ey+8)
        for xy,color in((wrist,(255,60,70,255)),(shoulder,(60,220,255,255))):
            x,y=tx(xy[0]),ty(xy[1]);dr.line((x-7,y,x+7,y),fill=color,width=2);dr.line((x,y-7,x,y+7),fill=color,width=2)
        dr.text((768*i+20,20),f'POSE {n} | FIXED MUZZLE / SHOULDER | DRAW NEW SLEEVE',fill=(170,180,190,255))
        report.append({'ref':n,'source_crop':box,'guide_body_source':str(body_source(n-1).relative_to(ROOT)),'muzzle_x':mx,'wrist_guide':wrist,'shoulder_guide':shoulder})
    sheet.save(out/'authored_two_poses.png');guide.save(out/'native_reach_guide.png');write(out/'manifest.json',{'frames':report,'source_sha256':digest(D/'basic_firing_c_v1/generated.png'),'guide_is_not_final_art':True,'source_crops_only':True})
if __name__=='__main__':main()
