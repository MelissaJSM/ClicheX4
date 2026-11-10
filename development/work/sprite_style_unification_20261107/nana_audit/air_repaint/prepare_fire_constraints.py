"""공중 사격의 실제 총구와 최초 8열 총몸 기준을 읽기 전용 추출한다."""
from pathlib import Path
import sys,json
import numpy as np
from PIL import Image,ImageDraw,ImageFont
D=Path(__file__).resolve().parent;ROOT=D.parents[3]
sys.path[:0]=[str(ROOT),str(D.parent/'native_restore')]
from preview_restore import Archive,sha,digest,need,write,helper
from src.psx_player import composition_frame
def main():
    plan=json.loads((D/'inputs.json').read_text('utf8'))
    a=Archive((ROOT/plan['parent_arc']).read_bytes());need(sha(a.data)==plan['parent_arc_sha256'],'Parent')
    out=D/'fire_constraints';out.mkdir(exist_ok=True);Y,X=np.indices((384,384));rows=[];reports=[]
    for n in range(34,55,2):
        old=a.layer(n)[0];yy,xx=np.nonzero(old);mx=int(xx.min());my=float(np.median(yy[xx==mx]));mask=(X>=mx)&(X<mx+8)&(Y>=int(np.floor(my))-2)&(Y<=int(np.ceil(my))+3)
        gun=np.where(mask,old,0).astype(np.uint8);need(np.any(gun[:,mx]),'No barrel');Image.fromarray(gun).save(out/f'barrel_{n:03}.png')
        rgba=a.rgba(gun);rgba.save(out/f'barrel_{n:03}_rgba.png')
        display=a.composite(n)[0];draw=ImageDraw.Draw(display);draw.rectangle((mx-1,int(my)-3,mx+8,int(my)+4),outline=(255,80,40,255))
        rows.append((f'fire {n}',[('현재 실제 발사점',display),('보호할 총몸8열',rgba),('비사격 짝',a.composite(n-1)[0])]))
        invariant=[]
        for armor in range(16):
            for arm in (1,2):
                full=np.array(a.composite(n,armor,arm)[0]); y,x=np.nonzero(full[:,:,3]);invariant.append([armor,arm,int(x.min()-160),float(np.median(y[x==x.min()])-160)])
        reports.append({'ref':n,'paired_ref':n-1,'muzzle':[mx-160,my-160],'gun_width':8,'gun_window':[mx-160,int(np.floor(my))-162,mx-152,int(np.ceil(my))-156],
                        'barrel_indexed_sha256':sha(gun.tobytes()),'barrel_rgba_sha256':sha(np.array(rgba).tobytes()),'all_current_mask_muzzles':invariant,
                        'current_parts':{str(pb):len(composition_frame(a.c,pb,n)['parts'])for pb in(0,5,6,7,8)}})
    for i in range(0,len(rows),4):helper.grid(rows[i:i+4],out/f'current_shot_{i//4+1}.png',6)
    write(out/'manifest.json',{'source_arc_sha256':sha(a.data),'frames':reports,'scope':'원래 총구와 앞쪽8열의 출처 추출.8열에 소매가 섞이는지 직접 이미지로 확인한 뒤 보호 범위를 고정한다.',
            'new_arms_generated':False,'native_packed':False})
    print(json.dumps({'muzzles':{r['ref']:r['muzzle']for r in reports},'out':str(out)}))
if __name__=='__main__':main()
