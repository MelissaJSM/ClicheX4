"""Current native poses beside accepted idle; inspection sheets, no art edits."""
from pathlib import Path
import json,sys,struct,hashlib
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT));D=Path(__file__).parent
from scripts.overhaul_sprites_audit import render,rgba
from scripts.prepare_riko_ui import entry
P=D/'rin_extension/prepared_air_continuation2_v2/PL01_U.ARC';OUT=D/'rin_extension/next_priority_review';OUT.mkdir(exist_ok=True)
arc=P.read_bytes();sha=hashlib.sha256(arc).hexdigest();assert sha=='ffca3087c17c883e6383b0ff38417b003138d1614c8add8edb1b99199bf322df'
pal=struct.unpack_from('<16H',entry(arc,9),0)
ids=[(0,n)for n in [34,36,37,38,41,45,61,69,81,105,117,133]]+[(1,n)for n in[50,56,65,132,136,142]]+[(0,n)for n in[174,183,200]]+[(1,n)for n in[144,150,158,160,165,171]]+[(0,n)for n in[149,135,213,229]]+[(1,n)for n in[1,5,17,183]]+[(0,249)]
idle=render(arc,0,0,147)[0];rows=[];sheets=[]
for offset in range(0,len(ids),6):
    selected=ids[offset:offset+6];sheet=Image.new('RGB',(1200,430*((len(selected)+1)//2)),'#64717b');draw=ImageDraw.Draw(sheet)
    for i,(bank,n)in enumerate(selected):
        a=render(arc,bank,bank*5,n)[0];ys,xs=np.nonzero(a);bbox=(int(xs.min()),int(ys.min()),int(xs.max())+1,int(ys.max())+1)
        x=(i%2)*600;y=(i//2)*430;draw.text((x+5,y+7),f'IDLE147 | b{bank}_{n:03d}',fill='white')
        left=rgba(idle,pal).crop((125,120,205,200)).resize((240,240),Image.Resampling.NEAREST);sheet.paste(left,(x,y+85),left)
        # A fixed world canvas preserves the origin across every reviewed pose.
        crop=(96,88,216,216)
        if not(crop[0]<=bbox[0]and crop[1]<=bbox[1]and crop[2]>=bbox[2]and crop[3]>=bbox[3]):
            crop=(min(96,bbox[0]),min(88,bbox[1]),max(216,bbox[2]),max(216,bbox[3]))
        right=rgba(a,pal).crop(crop).resize(((crop[2]-crop[0])*3,(crop[3]-crop[1])*3),Image.Resampling.NEAREST)
        assert right.width<=420 and right.height<=405,(bank,n,bbox)
        assert np.count_nonzero(np.array(right.getchannel('A')))==np.count_nonzero(a)*9
        sheet.paste(right,(x+228,y+28),right)
        rows.append({'bank':bank,'ref':n,'bbox':bbox,'crop':crop,'scale':3,'source_sha256':sha})
    path=OUT/f'groups_{offset//6:02d}.png';sheet.save(path);sheets.append(str(path.relative_to(ROOT)))
(OUT/'inventory.json').write_text(json.dumps({'source':str(P.relative_to(ROOT)),'source_sha256':sha,'sheets':sheets,'frames':rows,'scope':'남은 동작의 대표36자세를 대기 기준 옆에서 다시 비교한다. 전체315참조 육안검사 완료라는 뜻은 아니다.'},ensure_ascii=False,indent=2)+'\n','utf8')
print(json.dumps({'poses':len(rows),'sheets':sheets}))
