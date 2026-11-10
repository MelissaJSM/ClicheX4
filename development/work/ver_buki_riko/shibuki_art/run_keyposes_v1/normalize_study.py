"""4포즈 시트를 공통 축척/선택 팔레트로 검토한다. 게임 패치를 생성하지 않는다."""
import json,sys,struct
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.extract_zero import save_image
from scripts.discover_inputs import sha256
work=Path(__file__).parent
im=Image.open(work/'generated.png').convert('RGBA');a=np.array(im);mask=a[:,:,3]>=128
columns=mask.any(axis=0);runs=[];start=None
for x,v in enumerate(np.r_[columns,False]):
    if v and start is None:start=x
    if not v and start is not None:
        if x-start>=20:runs.append((start,x))
        start=None
if len(runs)!=4:raise ValueError(f'Expected four isolated poses, got {runs}')
boxes=[]
for l,r in runs:
    yy,xx=np.nonzero(mask[:,l:r]);boxes.append((l,int(yy.min()),r,int(yy.max()+1)))
selection=json.loads((ROOT/'projects/ver_buki_riko/shibuki_art_selection.json').read_text(encoding='utf-8'))
palette_path=ROOT/selection['candidate']/'palette.bin';words=struct.unpack('<16H',palette_path.read_bytes())
rgb=np.array([[(w&31)*255//31,((w>>5)&31)*255//31,((w>>10)&31)*255//31] for w in words],np.int32)
scale=47/(boxes[0][3]-boxes[0][1]);pics=[];records=[]
for i,bb in enumerate(boxes):
    crop=im.crop(bb);size=(round(crop.width*scale),round(crop.height*scale));src=np.array(crop)
    labels=np.zeros(src.shape[:2],np.uint8)
    for y in range(crop.height):
        delta=src[y,:,:3].astype(np.int32)[:,None,:]-rgb[None,1:,:]
        labels[y]=np.argmin((delta*delta).sum(2),axis=1)+1
    votes=[]
    for n in range(1,16):
        weight=np.where(labels==n,src[:,:,3],0).astype(np.uint8)
        votes.append(np.array(Image.fromarray(weight).resize(size,Image.Resampling.BOX)))
    small=np.argmax(np.stack(votes),axis=0).astype(np.uint8)+1
    alpha=np.array(crop.getchannel('A').resize(size,Image.Resampling.BOX));small[alpha<128]=0
    pic=save_image(small.tobytes(),size,words,work/f'keypose_{i+1:02d}.png').convert('RGBA');pics.append(pic)
    records.append({'pose':i+1,'crop':bb,'native_size':size,'source_x_frame':[29,7,15,21][i]})
idle=Image.open(ROOT/selection['indexed_png']).convert('RGBA')
sheet=Image.new('RGB',(5*252,340),'#222630');draw=ImageDraw.Draw(sheet);font=ImageFont.truetype('C:/Windows/Fonts/consola.ttf',17)
for i,(label,pic) in enumerate([('Accepted idle',idle)]+[(f'Run study {i+1}',p) for i,p in enumerate(pics)]):
    x=i*252;draw.text((x+8,8),label,font=font,fill='white')
    sheet.paste(pic,(x+126-pic.width//2,38+48-pic.height),pic)
    big=pic.resize((pic.width*4,pic.height*4),Image.Resampling.NEAREST)
    sheet.paste(big,(x+126-big.width//2,112+192-big.height),big)
    draw.line((x+6,305,x+246,305),fill='#68788e')
draw.text((8,318),'POSE STUDY ONLY - common scale, no game patch, not the full cycle',font=font,fill='#cbd3e0')
sheet.save(work/'review_1x_4x.png')
report={'task':'x_shibuki','source_sha256':sha256((work/'generated.png').read_bytes()),'palette_sha256':sha256(palette_path.read_bytes()),
        'common_scale':scale,'per_pose_scaling':False,'poses':records,'game_applied':False,'loop_complete':False,
        'pending':['near/far leg alternation','original per-frame pivot and contact mapping','run/shot shared-tile composition','14-frame loop and two startup poses','compression and runtime']}
(work/'study.json').write_text(json.dumps(report,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'output':str(work),'poses':records,'game_applied':False}))
