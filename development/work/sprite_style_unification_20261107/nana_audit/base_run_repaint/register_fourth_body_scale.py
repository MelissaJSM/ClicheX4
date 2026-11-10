"""포스의 모자 높이가 몸통 가로비율을 줄이지 않도록 전체원화 배율 비교."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4]
sys.path[:0]=[str(ROOT),str(Path(__file__).parent),str(Path(__file__).parent.parent/'native_restore')]
from register_cycle import PAGES
from register_page import crop_cell,register
from preview_restore import Archive,sha,write,need,helper
from PIL import Image
import numpy as np
D=Path(__file__).parent
def main():
    out=D/'fourth_body_scale';out.mkdir(exist_ok=True);a=Archive((D/'baseline_PL00_U.ARC').read_bytes());plan=json.loads((D/'plan.json').read_text('utf8'));pal=np.array([[(int(w)>>s&31)*255//31 for s in(0,5,10)]for w in a.words[16:32]],float);report=[]
    for page,(_,refs)in enumerate(PAGES,1):
        image=Image.open(D/f'fourth_page{page}_v1/generated.png').convert('RGBA');rows=[]
        for cell,n in enumerate(refs):
            p=next(q for q in plan['frames']if q['ref']==n);crop,box=crop_cell(image,cell);c=np.array(crop);rgb=c[:,:,:3].astype(float);green=(rgb[:,:,1]>rgb[:,:,0]+15)&(rgb[:,:,1]>rgb[:,:,2]+15)&(c[:,:,3]>=128);green[crop.height//2:]=False;sy,sx=np.nonzero(green);split=round(float(np.median(sy))+1)
            ex,ey=p['eye_world_original_registration'];top=p['bbox_world'][1];h1=ey-top+1;h2=p['bbox_world'][3]-ey-1;scale=h2/(crop.height-split);width=round(crop.width*scale)
            upper=register(crop.crop((0,0,crop.width,split)),(width,h1),pal,'area_vote');lower=register(crop.crop((0,split,crop.width,crop.height)),(width,h2),pal,'area_vote');v=np.concatenate((upper,lower));gy,gx=np.nonzero(v==14);cx=round(float(np.median(gx)));v[v==14]=12;v[ey-top,cx]=14
            native=np.zeros((384,384),np.uint8);native[160+top:160+top+len(v),160+ex-cx:160+ex-cx+width]=v
            b=np.array(Image.open(D/'cycle_registered_v1'/f'run_{n:03}.png'));mixed=np.where(native,native,b);Image.fromarray(native).save(out/f'run_{n:03}.png')
            rows.append((f'ref {n}',[('포스 대기',a.composite(0,15)[0]),('새 기본',a.rgba(b)),('원화 몸통비율',a.rgba(native,16)),('기본 포함',a.rgba(mixed,16))]));report.append({'ref':n,'source_crop':box,'body_scale':scale,'missing':int(((b>0)&(native==0)).sum()),'sha256':sha(native.tobytes())})
        helper.grid(rows,out/f'comparison_{page}.png',5)
    write(out/'report.json',{'ready_to_apply':False,'frames':report});print(json.dumps(report))
if __name__=='__main__':main()
