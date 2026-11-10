"""승인 대기48px에서 얻은 단일 축척으로 체이서4포즈를 등록 전 변환한다."""
import json,sys
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from scripts.prepare_rin_chaser import OUT
from scripts.prepare_rin_run import quantize,connected_groups
from scripts.extract_zero import save_image
from scripts.project import digest

def main():
    guide=json.loads((OUT/'guide.json').read_text());words=guide['palette_words'];colors=np.array([[(v>>s&31)*255//31 for s in (0,5,10)] for v in words[1:]],np.int32)
    im=Image.open(OUT/'generated.png').convert('RGBA');a=np.array(im);a[:,:,3]=np.where(a[:,:,3]>=128,255,0);im=Image.fromarray(a);crops=[];boxes=[]
    for i in range(6):
        box=(i%3*im.width//3,i//3*im.height//2,(i%3+1)*im.width//3,(i//3+1)*im.height//2);c=im.crop(box);b=c.getbbox()
        if b is None:raise ValueError('Missing sprite')
        crops.append(c.crop(b));boxes.append([box,b])
    # Common art adjustment: generated heads were wider than the accepted
    # 14..16px heads. Apply one 0.90 factor to the whole sheet, never individual
    # pose heights. Resulting riding heights follow the original bent poses.
    scale=48/crops[0].height*.90;records={};sheet=Image.new('RGB',(4*480,640),(32,35,44));d=ImageDraw.Draw(sheet)
    for i,n in enumerate(guide['slots']):
        px=quantize(crops[i],colors,scale);groups=connected_groups(px>0)
        if any(len(q)>3 for q in groups[1:]):raise ValueError('Detached art feature')
        noise=[len(q) for q in groups[1:]]
        for q in groups[1:]:px[q[:,0],q[:,1]]=0
        yy,xx=np.nonzero(px);px=px[yy.min():yy.max()+1,xx.min():xx.max()+1];path=OUT/(f'prepared_{n}.png' if n else f'calibration_{i}.png');p=save_image(px.tobytes(),(px.shape[1],px.shape[0]),words,path)
        if n is None:continue
        records[str(n)]={'file':path.name,'sha256':digest(path),'size':list(p.size),'crop':boxes[i],'alpha_noise_removed':noise}
        j=[14,22,30,38].index(n);old=Image.open(OUT/f'original_{n}.png').convert('RGBA');old=old.crop(old.getbbox());old=old.resize((old.width*5,old.height*5),Image.Resampling.NEAREST);sheet.paste(old,(j*480+10,30),old)
        p=p.convert('RGBA').resize((p.width*6,p.height*6),Image.Resampling.NEAREST);sheet.paste(p,(j*480+12,335),p);d.text((j*480+10,305),f'{n} '+str(records[str(n)]['size']),fill='white')
    sheet.save(OUT/'prepared_comparison.png');(OUT/'prepared.json').write_text(json.dumps({'scale':scale,'source_sha256':digest(OUT/'generated.png'),'palette_words':words,'frames':records,'per_pose_scaling':False},indent=2)+'\n','utf-8');print(json.dumps({'scale':scale,'sizes':{n:q['size'] for n,q in records.items()}}))

if __name__=='__main__':main()
