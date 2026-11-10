"""Read-only native reference-plane audit; not a live collision test."""
from pathlib import Path
import sys,json
ROOT=Path(__file__).resolve().parents[4];D=Path(__file__).parent
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,write,need
from PIL import Image,ImageDraw,ImageFont
import numpy as np

def main():
    manifest=json.loads((D/'inputs.json').read_text('utf8'));a=Archive((ROOT/manifest['source_arc']).read_bytes());need(sha(a.data)==manifest['source_sha256'],'Parent')
    out=D/'contact_grid_audit';out.mkdir(exist_ok=True);records=[];Y,X=np.indices((384,384));font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
    cellw,cellh=384,490;board=Image.new('RGB',(3*cellw,4*cellh),'#bdc5cd');draw=ImageDraw.Draw(board)
    for row,(n,lim)in enumerate([(55,-9),(57,-11),(61,-16),(65,-20)]):
        old=a.layer(n)[0];new=np.array(Image.open(D/'basic_contacts_probe_v3'/f'base_{n:03}.png'));p=next(q for q in manifest['frames']if q['ref']==n);results={}
        for label,m in [('current',old),('candidate',new)]:
            yy,xx=np.nonzero((m>0)&(X>168)&(Y<=160+lim));fy=np.where(m>0)[0].max();fx=np.where(m[fy]>0)[0]
            results[label]={'hand_region_bounds':[int(xx.min()-160),int(yy.min()-160),int(xx.max()-160),int(yy.max()-160)],'rear_lowest_foot_y':int(fy-160),'rear_lowest_foot_xs':[int(x-160)for x in fx]}
        need(results['current']['rear_lowest_foot_y']==results['candidate']['rear_lowest_foot_y'],'Foot y drift')
        need(results['current']['rear_lowest_foot_xs']==results['candidate']['rear_lowest_foot_xs'],'Foot x drift')
        ex,ey=map(int,p['eye_world']);need(new[ey+160,ex+160]==14,'Eye origin drift')
        delta=[b-a for a,b in zip(results['current']['hand_region_bounds'],results['candidate']['hand_region_bounds'])]
        need(max(abs(delta[k])for k in(1,2,3))<=1,'Hand tip/boundary beyond one pixel')
        overlay=np.zeros((384,384,4),np.uint8);overlay[(old>0)&(new==0)]=[235,75,65,255];overlay[(new>0)&(old==0)]=[30,140,220,255];overlay[(old>0)&(new>0)]=[80,80,90,255]
        for col,(title,img)in enumerate([('기존',a.rgba(old)),('신규 원화 정합',a.rgba(new)),('알파: 빨강 기존 / 파랑 신규',Image.fromarray(overlay))]):
            x0=col*cellw;y0=row*cellh+50;crop=img.crop((136,132,184,184)).resize((384,416),Image.Resampling.NEAREST);board.paste(crop,(x0,y0),crop);draw.text((x0+6,row*cellh+8),f'{n} · {title}',font=font,fill='black')
            for gx in range(-24,25,4):
                xx=x0+(gx+24)*8;draw.line((xx,y0,xx,y0+416),fill='#8b9aa6',width=1)
            for gy in range(-28,25,4):
                yy=y0+(gy+28)*8;draw.line((x0,yy,x0+384,yy),fill='#8b9aa6',width=1)
            draw.line((x0+192,y0,x0+192,y0+416),fill='#49606b',width=2);draw.line((x0,y0+224,x0+384,y0+224),fill='#49606b',width=2)
            fx=results['current']['rear_lowest_foot_xs'];fy=results['current']['rear_lowest_foot_y'];draw.rectangle((x0+(min(fx)+24)*8,y0+(fy+28)*8,x0+(max(fx)+25)*8-1,y0+(fy+29)*8-1),outline='#00a000',width=2)
        records.append({'ref':n,**results,'hand_bounds_delta':delta,'eye_anchor':[ex,ey],'foot_anchor_exact':True,'native_indexed_sha256':sha(new.tobytes())})
    board.save(out/'native_grid.png');write(out/'verification.json',{'passed':True,'scope':'Native world origin160 and original hand/foot geometry only. No live wall collision or floor test. Hand-region boundaries differ by at most one pixel; foot end coordinates are exact.','parent_arc_sha256':sha(a.data),'frames':records,'new_art_files':[{'path':str((D/'basic_keys_v2/generated.png').relative_to(ROOT)),'sha256':digest(D/'basic_keys_v2/generated.png')}],'gameplay_verified':False})
    print(json.dumps({'passed':True,'frames':len(records)}))
if __name__=='__main__':main()
