"""Inspect only existing authored rear-head sampling; no native asset edits."""
from pathlib import Path
import sys,json,math,hashlib
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT));D=Path(__file__).parent/'rear_source';D.mkdir(exist_ok=True)
from work.ver_buki_riko.art_pilot.ladder_v1.fit_ladder import component,colors,sample
A=ROOT/'work/ver_buki_riko/art_pilot/ladder_v1';im=Image.open(A/'generated_ladder.png').convert('RGBA');box=(362,0,724,362);cell=im.crop(box);a=np.array(cell);groups=component(a[:,:,3]>=220);keep=np.zeros(a.shape[:2],bool)
for y,x in groups[0]:keep[y,x]=True
a[~keep,3]=0;yy,xx=np.nonzero(keep);ox,oy=int(xx.min()),int(yy.min());a=a[oy:yy.max()+1,ox:xx.max()+1]
ix=sample(cell,.19);gy,gx=np.nonzero(np.isin(ix,[4,8,14]));cx=round((gx.min()+gx.max())/2);cy=int(gy.min())-2;left,top=cx-11,cy
old=np.array(Image.open(A/'rear_head_indexed.png'));native=np.zeros((19,23),np.uint8);part=ix[max(top,0):top+19,max(left,0):left+23];native[max(-top,0):max(-top,0)+part.shape[0],max(-left,0):max(-left,0)+part.shape[1]]=part
assert np.array_equal(old,native),(ix.shape,left,top,int(np.count_nonzero(old!=native)))
variants={'original_native':old};weights=np.ones(16);weights[[1,3,4]]=1.65;weights[8]=1.20
for method in ('area_rgb','area_vote','structure_vote'):
 out=np.zeros((19,23),np.uint8)
 for y in range(19):
  for x in range(23):
   x0,x1=max(0,math.floor((left+x)/.19)),min(a.shape[1],math.ceil((left+x+1)/.19));y0,y1=max(0,math.floor((top+y)/.19)),min(a.shape[0],math.ceil((top+y+1)/.19));p=a[y0:y1,x0:x1];m=p[:,:,3]>=220
   if not m.size or not m.any() or m.mean()<.5:continue
   rgb=p[m,:3].astype(np.float64)
   if method=='area_rgb':out[y,x]=1+np.argmin(((rgb.mean(0)[None,:]-colors[1:])**2).sum(1))
   else:
    indices=1+np.argmin(((rgb[:,None,:]-colors[None,1:])**2).sum(2),1);votes=np.bincount(indices,minlength=16).astype(float)
    if method=='structure_vote':votes*=weights
    out[y,x]=votes.argmax()
 variants[method]=out
palette=Image.open(A/'rear_head_indexed.png').getpalette()
for name,v in variants.items():
 pic=Image.fromarray(v,'P');pic.putpalette(palette);pic.info['transparency']=0;pic.save(D/(name+'.png'))
source_box=(math.floor(left/.19)+ox+box[0],math.floor(top/.19)+oy+box[1],math.ceil((left+23)/.19)+ox+box[0],math.ceil((top+19)/.19)+oy+box[1]);im.crop(source_box).save(D/'authored_head_crop.png')
board=Image.new('RGB',(4*23*16,19*16+30),'#65727a');d=ImageDraw.Draw(board);font=ImageFont.truetype('C:/Windows/Fonts/malgun.ttf',16)
for col,(name,v)in enumerate(variants.items()):
 p=Image.open(D/(name+'.png')).convert('RGBA').resize((23*16,19*16),Image.Resampling.NEAREST);board.paste(p,(col*23*16,30),p);d.text((col*23*16+4,5),name,font=font,fill='white')
board.save(D/'sampling_comparison.png')
report={'source':'work/ver_buki_riko/art_pilot/ladder_v1/generated_ladder.png','source_sha256':hashlib.sha256((A/'generated_ladder.png').read_bytes()).hexdigest(),'source_frame':178,'source_crop':source_box,'scale':.19,'old_native_reproduced_exact':True,'purpose':'원화의 머릿결이 현재 네이티브 크기에서 복구 가능한지 비교. 어깨·손 포함 크롭으로 직접 삽입 금지.','structure_vote_weights':weights.tolist(),'candidate_not_inserted':True}
(D/'inspection.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n','utf8');print(json.dumps(report,ensure_ascii=False))
