import json
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[4]
D=ROOT/'work/ver_buki_riko/shibuki_armor_capture/20261027T014938107274Z'
records=[];sheet=Image.new('RGB',(1080,900),'#253546');draw=ImageDraw.Draw(sheet)
for i,n in enumerate((33,41,67,69,71,73,75,76,48)):
    if not (D/f'expected_{n:03}.png').exists():continue
    full=Image.open(D/f'expected_{n:03}.png').convert('RGBA');bb=full.getbbox();im=full.crop(bb);best=None
    for page in (0,256):
        sc=Image.open(D/f'observed_{n:03}_{page}.png').convert('RGB');v=np.array(sc)
        for flip in (False,True):
            spr=np.array(im)[:,::-1] if flip else np.array(im);h,w=spr.shape[:2];scores=np.zeros((v.shape[0]-h+1,v.shape[1]-w+1),np.int32)
            for y,x in np.argwhere(spr[:,:,3]>0):scores+=np.all(v[y:y+scores.shape[0],x:x+scores.shape[1]]==spr[y,x,:3],axis=2)
            sy,sx=np.unravel_index(scores.argmax(),scores.shape);score=int(scores[sy,sx]);candidate=(score,page,flip,int(sx),int(sy))
            if best is None or candidate>best:best=candidate
    score,page,flip,x,y=best;spr=im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if flip else im;sc=Image.open(D/f'observed_{n:03}_{page}.png').convert('RGB');crop=sc.crop((x,y,x+im.width,y+im.height))
    s=np.array(spr);v=np.array(crop);bad=np.any(s[:,:,:3]!=v,axis=2)&(s[:,:,3]>0)
    rec={'frame':n,'best':best,'opaque':int((s[:,:,3]>0).sum()),'mismatches':int(bad.sum()),'bad_pixels':[[int(xx),int(yy),s[yy,xx,:3].tolist(),v[yy,xx].tolist()] for yy,xx in np.argwhere(bad)]};records.append(rec)
    left=i%3*360;top=i//3*300;draw.text((left,top),f'{n}: {score}/{rec["opaque"]}',fill='white')
    for j,art in enumerate((spr,crop)):
        art=art.resize((im.width*4,im.height*4),Image.Resampling.NEAREST);sheet.paste(art,(left+j*180,top+28),art if art.mode=='RGBA' else None)
sheet.save(D/'mismatch_review.png');(D/'mismatch_review.json').write_text(json.dumps(records,indent=2));print([{k:v for k,v in r.items() if k!='bad_pixels'} for r in records])
